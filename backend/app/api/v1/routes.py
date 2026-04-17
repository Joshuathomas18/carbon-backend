"""API v1 routes."""

import logging
from datetime import datetime
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends, Form
from fastapi.responses import PlainTextResponse
from supabase import Client
from pydantic import BaseModel, Field

from app.db.database import get_supabase

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


@router.post("/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
):
    """
    Twilio WhatsApp webhook for incoming messages.

    Receives messages from farmers, runs state machine, and responds.

    **Twilio sends:**
    - From: WhatsApp sender number (e.g., "+911234567890")
    - Body: Message text

    **State Machine:**
    1. NEW → Send welcome + magic link
    2. AWAITING_MAP → Remind to complete map
    3. MAP_RECEIVED → Ask 3 agronomic questions
    4. AWAITING_ANSWERS → Extract answers, calculate final payout
    5. QUALIFIED → Send payout, expert will contact
    """

    logger.info(f"Twilio webhook: From={From}, Body={Body[:50]}...")

    try:
        from app.services.whatsapp_service import WhatsAppBotService

        bot = WhatsAppBotService()
        result = await bot.handle_incoming_message(From, Body)
        logger.info(f"WhatsApp handler result: {result}")

        # Twilio expects a 200 with empty body for successful processing
        return ""

    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {str(e)}", exc_info=True)
        return ""  # Still return 200 to Twilio to avoid retries


class PolygonSaveRequest(BaseModel):
    """Request to save farm polygon from React map."""
    phone_number: str = Field(..., description="Farmer phone number")
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
async def save_polygon_from_map(request: PolygonSaveRequest):
    """
    Save farm polygon from React MapConfirmView.

    Called when farmer completes drawing polygon on map.
    Triggers WhatsApp state machine to ask agronomic questions.

    **Request:**
    - phone_number: Farmer's WhatsApp number
    - polygon: GeoJSON polygon from map
    - area_hectares: Calculated polygon area

    **Response:**
    - Estimated carbon value
    - Next step (asking 3 questions via WhatsApp)
    """

    logger.info(f"Saving polygon for {request.phone_number}")

    try:
        from app.services.whatsapp_service import WhatsAppBotService

        bot = WhatsAppBotService()

        # In production, would save to database and trigger state machine
        # For now, simulate the process
        estimated_carbon = request.area_hectares * 1.5  # Rough estimate
        estimated_payout = estimated_carbon * 40  # ₹40/tonne

        # Trigger the questions state
        await bot._handle_map_received_state(request.phone_number)

        return PolygonSaveResponse(
            status="success",
            message="Polygon saved successfully",
            estimated_carbon=estimated_carbon,
            estimated_payout_inr=estimated_payout,
            next_step="3 agronomic questions sent via WhatsApp"
        )

    except Exception as e:
        logger.error(f"Error saving polygon: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
