"""Twilio WhatsApp bot service for farmer intake funnel (PRD v2.1)."""

import json
import logging
import os
import re
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from app.db.database import supabase
from app.config import settings
from app.services.i18n import get_text
from app.services.geo_service import GeoService

logger = logging.getLogger(__name__)


class WhatsAppBotService:
    """Manage 10-state WhatsApp bot for farmer onboarding."""

    # Map state codes to PRD states
    STATES = {
        "NEW": "LANGUAGE_SELECTION",
        "LANGUAGE_SELECTION": "GREETING",
        "GREETING": "LOCATION",
        "LOCATION": "LOCATION_CONFIRM",
        "LOCATION_CONFIRM": "AREA",
        "AREA": "CROP_QUESTION",
        "CROP_QUESTION": "UREA_QUESTION",
        "UREA_QUESTION": "BURNING_QUESTION",
        "BURNING_QUESTION": "SUMMARY",
        "SUMMARY": "PROCESSING",
        "PROCESSING": "QUALIFIED",
        "QUALIFIED": "FINISHED"
    }

    def __init__(self):
        """Initialize and Load Dependencies."""
        try:
            from twilio.rest import Client
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            self.twilio_phone = settings.TWILIO_WHATSAPP_NUMBER or f"whatsapp:{settings.TWILIO_PHONE_NUMBER}"
            self.frontend_url = settings.FRONTEND_URL
            self.db = supabase
            self.geo = GeoService()
        except Exception as e:
            logger.warning(f"Metadata init error: {e}")
            self.twilio_client = None
            self.db = supabase
            self.geo = GeoService()

        # Unit mapping for normalization
        self.UNIT_MAP = {
            "hectare": 1.0,
            "ha": 1.0,
            "acre": 0.4047,
            "acr": 0.4047,
            "bigha": 0.25,
            "kanal": 0.05,
            "marla": 0.00125
        }

    async def handle_incoming_message(
        self,
        phone_number: str,
        message_body: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Main routing for incoming WhatsApp messages."""
        try:
            phone_number = self._normalize_phone(phone_number)
            message_text = message_body.strip()
            metadata = metadata or {}
            
            # 1. Fetch Session
            farmer_resp = self.db.table("farmers").select("*").eq("phone", phone_number).execute()
            farmer_data = farmer_resp.data
            
            if not farmer_data:
                # NEW User
                farmer = {
                    "phone": phone_number,
                    "bot_state": "LANGUAGE_SELECTION",
                    "session_expires_at": datetime.utcnow() + timedelta(hours=48)
                }
                self.db.table("farmers").insert(farmer).execute()
                return get_text("welcome")
            
            farmer = farmer_data[0]
            current_state = farmer.get("bot_state", "LANGUAGE_SELECTION")
            lang = farmer.get("language", "hinglish")

            # 2. Global Reset Check
            if message_text.lower() == "reset":
                self.db.table("farmers").update({
                    "bot_state": "LANGUAGE_SELECTION",
                    "session_expires_at": datetime.utcnow() + timedelta(hours=48)
                }).eq("phone", phone_number).execute()
                return get_text("welcome")

            # 3. Session Expiry Check
            expiry = farmer.get("session_expires_at")
            if expiry:
                if isinstance(expiry, str):
                    expiry = datetime.fromisoformat(expiry)
                
                if datetime.utcnow() > expiry:
                    self.db.table("farmers").update({"bot_state": "LANGUAGE_SELECTION"}).eq("phone", phone_number).execute()
                    return "⏰ Time out! Chaliye phir se start karte hain.\n\n" + get_text("welcome")

            # Update expiry
            self.db.table("farmers").update({
                "session_expires_at": datetime.utcnow() + timedelta(hours=48)
            }).eq("phone", phone_number).execute()

            # 4. State Routing Logic
            return await self._route_state_logic(phone_number, message_text, current_state, lang, farmer, metadata)

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {str(e)}", exc_info=True)
            return "Maaf kijiye, humein thodi dikat ho rahi hai. Kripaya 'reset' likh kar 'send' karein."

    async def _route_state_logic(self, phone, text, state, lang, farmer, meta) -> str:
        """Route to specific state handlers."""
        
        # State 0: LANGUAGE_SELECTION
        if state == "LANGUAGE_SELECTION":
            choice = self._match_choice(text, {"1": "hinglish", "2": "english", "3": "hindi"})
            if choice:
                self.db.table("farmers").update({"language": choice, "bot_state": "GREETING"}).eq("phone", phone).execute()
                return get_text("greeting", lang=choice)
            return get_text("welcome", lang="hinglish")

        # State 1: GREETING
        elif state == "GREETING":
            # State Jump Check (Premium Feel)
            extracted = self._extract_entities_for_jumps(text)
            if extracted.get("area"):
                return await self._handle_jump_from_greeting(phone, lang, extracted)

            choice = self._match_choice(text, {"1": "yes", "2": "about", "haan": "yes", "shuru": "yes"})
            if choice == "yes":
                self.db.table("farmers").update({"bot_state": "LOCATION"}).eq("phone", phone).execute()
                return get_text("location_prompt", lang=lang)
            elif choice == "about":
                return get_text("about", lang=lang) + "\n\n" + get_text("greeting", lang=lang)
            return get_text("greeting", lang=lang)

        # State 2: LOCATION
        elif state == "LOCATION":
            lat = meta.get("latitude")
            lon = meta.get("longitude")
            
            if lat and lon:
                # GPS Received
                name = await self.geo.reverse_geocode(lat, lon)
                self.db.table("farmers").update({
                    "latitude": lat, 
                    "longitude": lon, 
                    "bot_state": "LOCATION_CONFIRM",
                    "metadata_json": {**farmer.get("metadata_json", {}), "loc_name": name}
                }).eq("phone", phone).execute()
                return get_text("location_confirm", lang=lang, name=name)
            
            # Text Fallback Validation
            # If user sent valid location text (e.g. "Ludhiana, Punjab")
            if len(text.split()) >= 2 and text.lower() not in ["ok", "done", "theek hai"]:
                name = text[:50]
                self.db.table("farmers").update({
                    "bot_state": "LOCATION_CONFIRM",
                    "metadata_json": {**farmer.get("metadata_json", {}), "loc_name": name}
                }).eq("phone", phone).execute()
                return get_text("location_confirm", lang=lang, name=name)
            else:
                # Re-prompt specifically for the 📎 icon
                prompt = (
                    "Maaf kijiyega, humein location nahi mili. 😅\n\n"
                    "Kripaya niche **📎 (paperclip)** icon dabayein -> **Location** -> **'Share Current Location'** par click karein.\n\n"
                    "Ya phir apne Gaon (Village) aur District ka naam likh kar bhejein."
                )
                if lang == "english":
                    prompt = (
                        "Sorry, we didn't get your location. 😅\n\n"
                        "Please tap the **📎 (paperclip)** icon -> **Location** -> **'Share Current Location'**.\n\n"
                        "Or type your exact **Village and District** name."
                    )
                return prompt

        # State 3: LOCATION_CONFIRM
        elif state == "LOCATION_CONFIRM":
            choice = self._match_choice(text, {"1": "yes", "2": "no", "haan": "yes", "nahi": "no"})
            if choice == "yes":
                # Updated path to /map as per frontend
                magic_link = f"{self.frontend_url}/map?phone={phone}"
                self.db.table("farmers").update({"bot_state": "AREA"}).eq("phone", phone).execute()
                return get_text("area_prompt", lang=lang, link=magic_link)
            else:
                self.db.table("farmers").update({"bot_state": "LOCATION"}).eq("phone", phone).execute()
                return get_text("location_prompt", lang=lang)

        # State 4: AREA
        elif state == "AREA":
            area_data = self._smart_extract_area(text)
            if area_data["value"] is None:
                return get_text("area_retry", lang=lang)
            
            self.db.table("farmers").update({
                "area_hectares": area_data["value"],
                "bot_state": "CROP_QUESTION"
            }).eq("phone", phone).execute()
            return get_text("crop_prompt", lang=lang)

        # State 5: CROP_QUESTION
        elif state == "CROP_QUESTION":
            crops = {"1": "Wheat", "2": "Paddy", "3": "Maize", "4": "Other"}
            crop = crops.get(text[0]) if text[0] in crops else text[:20]
            self.db.table("farmers").update({"crop_type": crop, "bot_state": "UREA_QUESTION"}).eq("phone", phone).execute()
            return get_text("urea_prompt", lang=lang)

        # State 6: UREA_QUESTION
        elif state == "UREA_QUESTION":
            bags = {"1": 1, "2": 4, "3": 8, "4": 12}
            count = bags.get(text[0]) if text[0] in bags else self._extract_number(text)
            self.db.table("farmers").update({"urea_bags": count or 3, "bot_state": "BURNING_QUESTION"}).eq("phone", phone).execute()
            return get_text("burning_prompt", lang=lang)

        # State 7: BURNING_QUESTION
        elif state == "BURNING_QUESTION":
            burn = {"1": "yes", "2": "no", "3": "sometimes"}
            choice = burn.get(text[0]) if text[0] in burn else ("yes" if "ha" in text.lower() else "no")
            self.db.table("farmers").update({"burned_stubble": choice, "bot_state": "SUMMARY"}).eq("phone", phone).execute()
            
            # Prepare Summary
            f_resp = self.db.table("farmers").select("*").eq("phone", phone).execute()
            f = f_resp.data[0]
            summary = get_text("summary_confirm", lang=lang, 
                              loc=f.get("metadata_json", {}).get("loc_name", "Fixed"),
                              area=f"{f['area_hectares']:.2f} ha",
                              crop=f.get("crop_type"),
                              urea=f"{f['urea_bags']} bags",
                              burning=choice.capitalize())
            return summary

        # State 8: SUMMARY
        elif state == "SUMMARY":
            choice = self._match_choice(text, {"1": "yes", "2": "loc", "3": "reset"})
            if choice == "yes":
                self.db.table("farmers").update({"bot_state": "PROCESSING"}).eq("phone", phone).execute()
                asyncio.create_task(self._run_async_estimate(phone))
                return get_text("processing", lang=lang)
            elif choice == "loc":
                self.db.table("farmers").update({"bot_state": "LOCATION"}).eq("phone", phone).execute()
                return get_text("location_prompt", lang=lang)
            else:
                self.db.table("farmers").update({"bot_state": "LANGUAGE_SELECTION"}).eq("phone", phone).execute()
                return get_text("welcome", lang=lang)

        # State 10 (QUALIFIED): EXPERT_CTA
        elif state == "QUALIFIED":
            choice = self._match_choice(text, {"1": "yes", "2": "no"})
            if choice == "yes":
                code = f"KK-{random.randint(1000, 9999)}"
                self.db.table("farmers").update({"expert_requested": True, "expert_ref_code": code, "bot_state": "FINISHED"}).eq("phone", phone).execute()
                return get_text("expert_confirmed", lang=lang, code=code)
            else:
                self.db.table("farmers").update({"bot_state": "FINISHED"}).eq("phone", phone).execute()
                return get_text("finish", lang=lang)

        return get_text("welcome", lang="hinglish")

    def _match_choice(self, text: str, options: Dict[str, str]) -> Optional[str]:
        """Fuzzy match numerical options or keywords."""
        text = text.lower().strip()
        # Direct digit match
        if text[0] in options:
            return options[text[0]]
        
        # Keyword match
        for key, val in options.items():
            if key in text:
                return val
        return None

    def _extract_entities_for_jumps(self, text: str) -> Dict[str, Any]:
        """Strict extraction for state jumps."""
        res = {"area": None}
        # Only jump if number + unit found
        area_data = self._smart_extract_area(text)
        if area_data["value"] and area_data["note"]: # Only jump if a unit was explicitly mentioned
            res["area"] = area_data["value"]
        return res

    async def _handle_jump_from_greeting(self, phone, lang, extracted) -> str:
        """Process high-confidence jumps."""
        self.db.table("farmers").update({
            "area_hectares": extracted["area"],
            "bot_state": "CROP_QUESTION"
        }).eq("phone", phone).execute()
        return "📍 Location note kar liya (approx) aur 📏 Area bhi!\n\n" + get_text("crop_prompt", lang=lang)

    def _smart_extract_area(self, text: str) -> Dict[str, Any]:
        """Refined area extraction with text-numbers and plurals."""
        result = {"value": None, "note": None}
        text = text.lower()
        
        # Word numbers to digits
        text = text.replace("half", "0.5").replace("aadha", "0.5").replace("dedh", "1.5")
        
        # Handle ranges first
        range_match = re.search(r'(\d+\.?\d*)\s*(?:-|to)\s*(\d+\.?\d*)', text)
        if range_match:
            base_val = (float(range_match.group(1)) + float(range_match.group(2))) / 2
            result["note"] = "range"
        else:
            match = re.search(r'\d+\.?\d*', text)
            if not match: return result
            base_val = float(match.group())

        # Unit match (plurals supported)
        unit = "hectare"
        found_unit = False
        sorted_units = sorted(self.UNIT_MAP.keys(), key=len, reverse=True)
        for u in sorted_units:
            if re.search(rf'\b{u}s?\b', text):
                unit = u
                found_unit = True
                break
        
        result["value"] = base_val * self.UNIT_MAP[unit]
        if found_unit: result["note"] = unit
        return result

    async def _run_async_estimate(self, phone_number: str):
        """Run GEE estimation with 90s timeout."""
        try:
            from app.services.estimate_service import EstimateService
            farmer_resp = self.db.table("farmers").select("*").eq("phone", phone_number).execute()
            if not farmer_resp.data: return
            farmer = farmer_resp.data[0]
            
            service = EstimateService()
            
            # GEE Task with timeout
            try:
                estimate = await asyncio.wait_for(service.estimate_carbon(
                    lat=farmer["latitude"] or 30.9,
                    lon=farmer["longitude"] or 75.8,
                    area_hectares=farmer["area_hectares"],
                    db=self.db, phone=phone_number,
                    burned_stubble=(farmer["burned_stubble"] == "yes")
                ), timeout=90.0)
                
                # Delivery
                report = self._prepare_report(farmer, estimate)
                await self.send_message(phone_number, report)
                self.db.table("farmers").update({"bot_state": "QUALIFIED"}).eq("phone", phone_number).execute()
                await self.send_message(phone_number, get_text("expert_cta", lang=farmer["language"]))
                
            except asyncio.TimeoutError:
                await self.send_message(phone_number, get_text("processing_timeout", lang=farmer["language"]))
                
        except Exception as e:
            logger.error(f"Async estimate error: {e}")

    def _prepare_report(self, farmer, estimate) -> str:
        """Formatted report in chosen language."""
        lang = farmer["language"]
        msg = f"*🌱 Carbon Impact Report*\n\n"
        if lang == "hindi":
            msg += f"📏 क्षेत्रफल: {farmer['area_hectares']:.1f} ha\n"
            msg += f"📊 अनुमानित क्रेडिट: {estimate['total_tonnes_co2']:.1f} tons/year\n"
            msg += f"💰 संभावित कमाई: ₹{estimate['value_inr']:.0f}/year\n\n"
        else:
            msg += f"📏 Area: {farmer['area_hectares']:.1f} ha\n"
            msg += f"📊 Estimated Credits: {estimate['total_tonnes_co2']:.1f} tons/year\n"
            msg += f"💰 Potential Earnings: ₹{estimate['value_inr']:.0f}/year\n\n"
        
        msg += f"Accuracy: {farmer.get('report_accuracy', 'Medium')}\n"
        return msg

    async def send_message(self, to_phone: str, message_body: str) -> Dict[str, Any]:
        """Twilio client wrapper."""
        if not self.twilio_client: return {"status": "mock"}
        to_phone = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
        self.twilio_client.messages.create(from_=self.twilio_phone, to=to_phone, body=message_body)
        return {"status": "sent"}

    def _normalize_phone(self, phone: str) -> str:
        if phone.startswith("whatsapp:"): phone = phone[9:]
        digits = "".join(filter(str.isdigit, phone))
        return f"+91{digits}" if len(digits) == 10 else f"+{digits}"

    def _extract_number(self, text: str) -> Optional[float]:
        match = re.search(r'\d+\.?\d*', text)
        return float(match.group()) if match else None
