"""API v1 routes."""

import logging
from datetime import datetime
import html
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends, Form
from fastapi.responses import PlainTextResponse
from supabase import Client
from pydantic import BaseModel, Field

from app.db.database import get_supabase
from shapely.geometry import shape

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class PlotEstimateRequest(BaseModel):
    """Request to estimate carbon for a plot."""

    lat: float = Field(..., description="Latitude", ge=-90, le=90)
    lon: float = Field(..., description="Longitude", ge=-180, le=180)
    area_hectares: float = Field(..., description="Plot area in hectares", gt=0)
    phone: str = Field(default="", description="Farmer phone number (optional)")
    language: str = Field(default="hi", description="Language for response (hi, kn, pa, en)")


class PracticeRecommendation(BaseModel):
    """Practice recommendation."""

    name: str
    current: bool
    impact_increase_percent: float
    if_implemented_value_inr: float = 0


class CarbonEstimate(BaseModel):
    """Carbon estimate response."""

    plot_id: int | None = None
    tonnes_co2_per_hectare: float
    total_tonnes_co2: float
    value_inr: float
    confidence_score: float
    methodology: str = "Verra VM0042 v2.0 + Master Logic Engine"
    breakdown: dict = Field(default_factory=dict)
    practices: list[PracticeRecommendation] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    gee_available: bool = True
    sarvam_available: bool = True


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint with service status."""
    return HealthCheckResponse(
        status="ok",
        gee_available=True,  # TODO: Check GEE API availability
        sarvam_available=True,  # TODO: Check Sarvam AI availability
    )


@router.post("/plots/estimate", response_model=CarbonEstimate)
async def estimate_carbon(
    request: PlotEstimateRequest, 
    db: Client = Depends(get_supabase)
):
    """
    Estimate carbon sequestration for a plot and save to Supabase.
    """

    logger.info(
        f"Estimating carbon for ({request.lat}, {request.lon}) - {request.area_hectares}ha"
    )

    try:
        from app.services.estimate_service import EstimateService

        service = EstimateService()
        result = await service.estimate_carbon(
            lat=request.lat,
            lon=request.lon,
            area_hectares=request.area_hectares,
            db=db,
            phone=request.phone,
            language=request.language,
        )

        # Convert practices list to response objects
        practices_list = result.get("practices", [])
        if not practices_list:
            # Generate default if empty for MVP presentation
            practices_list = [
                {"name": "Stop Crop Residue Burning", "current": False, "impact_increase_percent": 15.0},
                {"name": "Adopt Zero Tillage", "current": False, "impact_increase_percent": 10.0},
                {"name": "Cover Cropping", "current": False, "impact_increase_percent": 8.0}
            ]

        practices = [
            PracticeRecommendation(
                name=p["name"],
                current=p.get("current", False),
                impact_increase_percent=p.get("impact_increase_percent", 0),
                if_implemented_value_inr=result["value_inr"]
                * (p.get("impact_increase_percent", 0) / 100),
            )
            for p in practices_list
        ]

        return CarbonEstimate(
            plot_id=result.get("plot_id"),
            tonnes_co2_per_hectare=result["tonnes_co2_per_hectare"],
            total_tonnes_co2=result["total_tonnes_co2"],
            value_inr=result["value_inr"],
            confidence_score=result["confidence_score"],
            methodology=result["methodology"],
            breakdown=result.get("breakdown", {}),
            practices=practices,
        )
    except Exception as e:
        logger.error(f"Error estimating carbon: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/calculate-carbon", response_model=CarbonEstimate)
async def calculate_carbon(
    request: PlotEstimateRequest,
    db: Client = Depends(get_supabase)
):
    """
    Direct endpoint for methodology-based carbon calculation.
    (Alias for /plots/estimate using the new Master Logic Engine)
    """
    return await estimate_carbon(request, db=db)


@router.get("/plots/{plot_id}/history")
async def get_carbon_history(
    plot_id: int,
    months: int = Query(12, ge=1, le=36, description="Number of months to retrieve"),
):
    """
    Get historical carbon scores for a plot.
    """
    return {
        "plot_id": plot_id,
        "message": "Historical data not yet available",
        "note": "This endpoint will return time series data pulled from the carbon_scores table.",
    }


class VoiceQueryRequest(BaseModel):
    """Voice query request."""

    audio_base64: str = Field(..., description="Base64-encoded audio")
    language: str = Field(default="hi", description="Language (hi, kn, pa, en)")


class VoiceQueryResponse(BaseModel):
    """Voice query response."""

    transcribed_text: str
    response_text: str
    response_audio_base64: str = ""
    estimated_plot: dict = Field(default_factory=dict)
    carbon_estimate: dict = Field(default_factory=dict)


@router.post("/voice/query", response_model=VoiceQueryResponse)
async def voice_query(
    request: VoiceQueryRequest,
    db: Client = Depends(get_supabase)
):
    """
    Process voice query from farmer - End-to-end voice interface.
    """

    logger.info(f"Voice query: {request.language}")

    try:
        from app.services.entity_extractor import EntityExtractor
        from app.services.estimate_service import EstimateService
        from app.services.sarvam_service import SarvamService

        sarvam = SarvamService()
        extractor = EntityExtractor()
        estimator = EstimateService()

        # Step 1: Transcribe
        transcribed_text, _ = await sarvam.transcribe_audio(
            request.audio_base64, request.language
        )

        if not transcribed_text:
            return VoiceQueryResponse(
                transcribed_text="",
                response_text="Sorry, could not understand. Please try again.",
            )

        logger.info(f"Transcribed: {transcribed_text}")

        # Step 2: Extract entities
        entities = extractor.extract_entities(transcribed_text, request.language)
        logger.info(f"Extracted: {entities}")

        # Handle missing area (default)
        if not entities.get("area_hectares"):
            entities["area_hectares"] = 2.5

        # Handle missing crop (default)
        if not entities.get("crop_type"):
            entities["crop_type"] = "wheat"

        # Step 3: Estimate carbon (saves to DB)
        estimate = await estimator.estimate_carbon(
            lat=28.5,  # TODO: Reverse geocode from location
            lon=77.2,
            area_hectares=entities["area_hectares"],
            db=db,
            language=request.language,
        )

        # Step 4: Format response
        response_text = _format_response(
            estimate, entities, request.language
        )

        # Step 5: Synthesize speech
        audio_bytes = await sarvam.text_to_speech(response_text, request.language)
        audio_base64 = sarvam.encode_audio_response(audio_bytes)

        return VoiceQueryResponse(
            transcribed_text=transcribed_text,
            response_text=response_text,
            response_audio_base64=audio_base64,
            estimated_plot={
                "area_hectares": entities["area_hectares"],
                "crop_type": entities["crop_type"],
                "location": entities.get("location", "Unknown"),
            },
            carbon_estimate={
                "plot_id": estimate.get("plot_id"),
                "tonnes_co2_per_hectare": estimate["tonnes_co2_per_hectare"],
                "total_tonnes_co2": estimate["total_tonnes_co2"],
                "value_inr": estimate["value_inr"],
                "confidence": estimate["confidence_score"],
            },
        )

    except Exception as e:
        logger.error(f"Voice query error: {e}", exc_info=True)
        return VoiceQueryResponse(
            transcribed_text="",
            response_text=f"Error: {str(e)}",
        )


def _format_response(estimate: dict, entities: dict, language: str) -> str:
    """Format carbon estimate as natural language response."""
    tonnes = estimate["tonnes_co2_per_hectare"]
    value = estimate["value_inr"]
    area = entities["area_hectares"]
    crop = entities["crop_type"]

    responses = {
        "hi": f"Namaste! Aapke {area:.1f} hectares {crop} par estimated carbon INR {value:.0f} ke barabar hai. "
        f"{tonnes:.2f} tonnes CO2 per hectare. Burning band karne se aap 15% aur kamaa sakte ho.",
        "kn": f"Namaskara! Aapna {area:.1f} hectares {crop} bhoomige carbon estimate INR {value:.0f} baraber ade. "
        f"Burning irlilla hage!",
        "pa": f"Sat Sri Akal! Tuhada {area:.1f} acre {crop} da carbon estimate INR {value:.0f} hai. "
        f"Burning band karke 15% aur kama sakde ho.",
        "en": f"Hello! Your {area:.1f} hectares of {crop} has an estimated carbon value of INR {value:.0f}. "
        f"That's {tonnes:.2f} tonnes CO2 per hectare. Stop burning to earn 15% more!",
    }

    return responses.get(language, responses["en"])


# ============================================================================
# Twilio WhatsApp Endpoints
# ============================================================================

from fastapi import Request


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp webhook for incoming messages.
    Returns TwiML MessagingResponse for immediate reply.
    """
    from fastapi import Response
    from twilio.twiml.messaging_response import MessagingResponse
    from app.services.whatsapp_service import WhatsAppBotService

    # 1. Get Form Data
    form = await request.form()
    phone_from = form.get("From", "")
    message_body = form.get("Body", "")
    
    # 1.1 Capture Location Data
    latitude = form.get("Latitude")
    longitude = form.get("Longitude")
    address = form.get("Address")
    
    metadata = {
        "latitude": float(latitude) if latitude else None,
        "longitude": float(longitude) if longitude else None,
        "address": address
    }

    logger.info(f"Twilio webhook: From={phone_from}, Body={message_body[:50]}..., GPS={latitude},{longitude}")

    try:
        bot = WhatsAppBotService()
        reply = await bot.handle_incoming_message(phone_from, message_body, metadata=metadata)
        
        # MessagingResponse will escape automatically, no need to double escape
        safe_reply = reply
        logger.info(f"WhatsApp reply: {reply[:50]}...")
    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {str(e)}", exc_info=True)
        safe_reply = "Sorry, we encountered an error. Please try again later."

    # 3. Return TwiML response
    resp = MessagingResponse()
    resp.message(safe_reply)

    # Unescape HTML entities so WhatsApp displays properly
    # TwiML escapes: ' → &#x27;, > → &gt;, etc.
    # But WhatsApp doesn't unescape on display, so we must do it here
    twiml_str = html.unescape(str(resp))

    return Response(
        content=twiml_str,
        media_type="application/xml"
    )


class PolygonSaveRequest(BaseModel):
    """Request to save farm polygon from React map."""
    phone_number: Optional[str] = Field(None, description="Farmer phone number (deprecated, use token)")
    token: Optional[str] = Field(None, description="Session token from magic link")
    polygon: dict = Field(..., description="GeoJSON polygon")
    area_hectares: float = Field(..., description="Farm area in hectares", gt=0)


class PolygonSaveResponse(BaseModel):
    """Response after saving polygon."""
    status: str
    message: str
    estimated_carbon: Optional[float] = None
    estimated_payout_inr: Optional[float] = None
    next_step: str = "3 agronomic questions sent via WhatsApp"


@router.post("/plots/save-with-phone", response_model=PolygonSaveResponse)
async def save_polygon_from_map(
    request: PolygonSaveRequest,
    db: Client = Depends(get_supabase)
):
    """
    Save farm polygon and trigger GEE estimate.
    Supports both legacy phone_number and secure token-based requests.
    """
    # Resolve phone from token or use direct phone_number
    phone = None
    if request.token:
        try:
            session_resp = db.table("sessions").select("phone, expires_at").eq("token", request.token).execute()
            if session_resp.data:
                session = session_resp.data[0]
                expires_at_raw = session.get("expires_at")
                if expires_at_raw:
                    expires_at = datetime.fromisoformat(expires_at_raw) if isinstance(expires_at_raw, str) else expires_at_raw
                    if datetime.utcnow() > expires_at:
                        raise HTTPException(status_code=401, detail="Token expired")
                phone = session["phone"]
        except Exception as e:
            logger.warning(f"Token lookup failed: {e}")
            phone = request.phone_number
    else:
        phone = request.phone_number

    if not phone:
        raise HTTPException(status_code=400, detail="Either token or phone_number required")

    logger.info(f"Saving polygon for {phone}")

    try:
        from app.services.estimate_service import EstimateService
        from app.services.whatsapp_service import WhatsAppBotService

        # 1. Parse Polygon and calculate area from geometry
        poly = shape(request.polygon)
        centroid = poly.centroid

        # Auto-calculate area from polygon in square meters, convert to hectares
        area_hectares = poly.area / 10000  # 1 hectare = 10000 m²

        # Log area calculation for debugging
        logger.info(f"Calculated area from polygon: {area_hectares:.2f} ha (polygon area: {poly.area:.1f} m²)")

        # 2. Trigger Full Satellite Pipeline
        service = EstimateService()
        estimate = await service.estimate_carbon(
            lat=centroid.y,
            lon=centroid.x,
            area_hectares=area_hectares,
            db=db,
            phone=phone
        )

        # 3. Inform WhatsApp Bot to send crop question and update state
        # _handle_map_received_state sets state to CROP_QUESTION and returns the question text
        bot = WhatsAppBotService()
        questions = await bot._handle_map_received_state(phone, area_hectares=area_hectares)

        # Send the crop question message to farmer
        await bot.send_message(phone, questions)

        return PolygonSaveResponse(
            status="success",
            message="Farm verified via satellite. Survey questions sent to WhatsApp.",
            estimated_carbon=estimate["total_tonnes_co2"],
            estimated_payout_inr=estimate["value_inr"],
            next_step="Please answer the 3 questions on WhatsApp to finalize."
        )

    except Exception as e:
        logger.error(f"Error saving polygon: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{token}")
async def get_session_info(token: str, db: Client = Depends(get_supabase)):
    """
    Retrieve session info (phone and coordinates) for a session token.
    Used by React map to center correctly and identify the farmer.
    """
    try:
        session_resp = db.table("sessions").select("phone, expires_at").eq("token", token).execute()
        if not session_resp.data:
            raise HTTPException(status_code=404, detail="Invalid or expired token")

        session = session_resp.data[0]
        phone = session["phone"]

        # Check expiry
        expires_at_raw = session.get("expires_at")
        if expires_at_raw:
            expires_at = datetime.fromisoformat(expires_at_raw) if isinstance(expires_at_raw, str) else expires_at_raw
            if datetime.utcnow() > expires_at:
                raise HTTPException(status_code=401, detail="Token expired")

        # Fetch farmer coordinates
        farmer_resp = db.table("farmers").select("latitude, longitude").eq("phone", phone).execute()
        coords = {"lat": 28.6139, "lon": 77.2090} # Default to Delhi
        if farmer_resp.data:
            f = farmer_resp.data[0]
            coords = {
                "lat": f.get("latitude") or 28.6139,
                "lon": f.get("longitude") or 77.2090
            }

        return {
            "phone": phone,
            "lat": coords["lat"],
            "lon": coords["lon"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

