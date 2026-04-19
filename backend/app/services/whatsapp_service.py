"""Twilio WhatsApp bot service for farmer intake funnel."""

import json
import logging
import os
from typing import Optional, Dict, Any

from app.db.database import supabase
from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppBotService:
    """Manage WhatsApp bot state machine for farmer onboarding.

    States:
    - NEW: User just texted, receives welcome + magic link
    - AWAITING_MAP: User clicked link, waiting for polygon on React app
    - MAP_RECEIVED: Backend got polygon, asks 3 agronomic questions
    - AWAITING_ANSWERS: Waiting for farmer to answer questions
    - QUALIFIED: Carbon estimate calculated, expert will contact
    """

    def __init__(self):
        """Initialize Twilio and Database Shim."""
        try:
            from twilio.rest import Client
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            self.twilio_phone = settings.TWILIO_PHONE_NUMBER
            self.frontend_url = settings.FRONTEND_URL
            
            # Use the SQLite shim from database.py
            self.db = supabase
        except Exception as e:
            logger.warning(f"Initialization error: {e}. Running in mock mode.")
            self.twilio_client = None
            self.db = supabase # Still try to use the shim

    async def handle_incoming_message(
        self,
        phone_number: str,
        message_body: str
    ) -> str:
        """
        Handle incoming WhatsApp message and run state machine.
        Returns the message text to be sent back.
        """
        try:
            phone_number = self._normalize_phone(phone_number)
            logger.info(f"WhatsApp message from {phone_number}: {message_body[:50]}")

            # 1. Fetch/Create farmer in DB
            farmer_resp = self.db.table("farmers").select("*").eq("phone", phone_number).execute()
            farmer_data = farmer_resp.data
            
            if not farmer_data:
                # NEW Farmer
                farmer_insert = {"phone": phone_number, "bot_state": "NEW"}
                new_farmer = self.db.table("farmers").insert(farmer_insert).execute()
                current_state = "NEW"
            else:
                current_state = farmer_data[0].get("bot_state", "NEW")

            # 2. Run state machine
            if current_state == "NEW":
                reply = await self._handle_new_state(phone_number)
                self.db.table("farmers").update({"bot_state": "AWAITING_MAP"}).eq("phone", phone_number).execute()

            elif current_state == "AWAITING_MAP":
                reply = await self._handle_awaiting_map_state(phone_number)

            elif current_state == "MAP_RECEIVED":
                reply = await self._handle_map_received_state(phone_number)
                self.db.table("farmers").update({"bot_state": "AWAITING_ANSWERS"}).eq("phone", phone_number).execute()

            elif current_state == "AWAITING_ANSWERS":
                reply = await self._handle_awaiting_answers_state(phone_number, message_body)

            elif current_state == "QUALIFIED":
                reply = await self._handle_qualified_state(phone_number)

            else:
                reply = f"Unknown state: {current_state}"

            return reply

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {str(e)}", exc_info=True)
            return "Sorry, something went wrong on our end. Please try again later."

    async def _handle_new_state(self, phone_number: str) -> str:
        """Handle NEW state: Send welcome + magic link."""
        # The correct route in the frontend is /discover, not /map
        magic_link = f"{self.frontend_url}/discover?phone={phone_number}"

        welcome_msg = (
            "🌾 *Namaste!* 🌾\n\n"
            "Carbon Sequestration Program mein aapka swagat hai!\n\n"
            "Humari taraf se, aapke farm ke liye carbon estimate milega aur "
            "aap carbon credits earn kar sakte ho.\n\n"
            f"*Yahan click karke apna farm draw karein:*\n{magic_link}\n\n"
            "Iske baad, hum aapko 3 simple sawal puchenge. Shuruaat karein! 👇"
        )
        return welcome_msg

    async def _handle_awaiting_map_state(self, phone_number: str) -> str:
        """Handle AWAITING_MAP state: Remind user to complete map."""
        reminder_msg = (
            "🗺️ Map abhi complete nahi hua.\n\n"
            "Kripaya link par click karke apne farm ka polygon draw karein"
        )
        return reminder_msg

    async def _handle_map_received_state(self, phone_number: str) -> str:
        """Handle MAP_RECEIVED state: Ask 3 agronomic questions."""
        questions_msg = (
            "✅ Shukriya! Aapka farm map mila.\n\n"
            "*Aab yeh 3 sawal jawaab dein:*\n\n"
            "1️⃣ *Kya aap stubble burn karte ho?*\n"
            "   Jawab: haan ya nahi\n\n"
            "2️⃣ *Kya aap zero-till farming karte ho?*\n"
            "   Jawab: haan ya nahi\n\n"
            "3️⃣ *Aap kitne urea bags use karte ho per season?*\n"
            "   Jawab: number (jaise 5 ya 10)\n\n"
            "Saare 3 questions ke jawab ek sath bhej dein!"
        )
        return questions_msg

    async def _handle_awaiting_answers_state(
        self,
        phone_number: str,
        message_body: str
    ) -> str:
        """Handle AWAITING_ANSWERS state: Extract answers and calculate payout."""
        try:
            # 1. Very basic answer extraction
            message_lower = message_body.lower()
            burned = "yes" if "ha" in message_lower or "yes" in message_lower else "no"
            zero_till = "yes" if "ha" in message_lower or "yes" in message_lower else "no"
            
            # Simple number extraction for urea
            import re
            numbers = re.findall(r'\d+', message_body)
            urea_bags = int(numbers[0]) if numbers else 5

            # 2. Trigger the High-Fidelity GEE Estimate with these survey results
            from app.services.estimate_service import EstimateService
            
            # Get the plot centroid from database
            plot_resp = self.db.table("plots").select("*, farmers!inner(phone)").eq("farmers.phone", phone_number).execute()
            if not plot_resp.data:
                return "Sorry, aapka map polygon nahi mila. Dubara draw karein."
            
            plot_data = plot_resp.data[0]
            lat = plot_data["plot_metadata"].get("lat", 30.9)
            lon = plot_data["plot_metadata"].get("lon", 75.8)
            area = plot_data["area_hectares"]

            service = EstimateService()
            estimate = await service.estimate_carbon(
                lat=lat,
                lon=lon,
                area_hectares=area,
                db=self.db,
                phone=phone_number,
                zero_till=(zero_till == "yes"),
                burned_stubble=(burned == "yes")
            )

            payout_msg = (
                f"🎉 *Dhanyavaad!* 🎉\n\n"
                f"Aapke farm ke liye carbon estimate ready hai:\n\n"
                f"💰 *Estimated Payout:* ₹{estimate['value_inr']:.0f}\n"
                f"📊 *Carbon:* {estimate['total_tonnes_co2']:.2f} tonnes CO2\n"
                f"✅ *Confidence:* {estimate['confidence_score']*100:.0f}%\n\n"
                f"Ek expert aapko 24 ghanton mein call karega details dene ke liye.\n\n"
                f"Shukriya! 🙏"
            )

            # 3. Update Farmer state and answers
            self.db.table("farmers").update({
                "bot_state": "QUALIFIED",
                "burned_stubble": burned,
                "zero_till": zero_till,
                "urea_bags": urea_bags,
                "estimated_tonnes_co2": estimate['total_tonnes_co2'],
                "estimated_value_inr": estimate['value_inr']
            }).eq("phone", phone_number).execute()

            return payout_msg

        except Exception as e:
            logger.error(f"Error extracting answers: {str(e)}")
            return "Maaf kijiye, humein answers process karne mein dikkat ho rahi hai. Kripaya dubara koshish karein."

    async def _handle_qualified_state(self, phone_number: str) -> str:
        """Handle QUALIFIED state: Farmer already qualified."""
        thankyou_msg = (
            "Shukriya contact ke liye! 🙏\n\n"
            "Aapka expert aapko contact karega.\n"
            "Agar koi sawal hai toh message karein."
        )
        return thankyou_msg

    async def send_message(self, to_phone: str, message_body: str) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio."""
        try:
            if not self.twilio_client:
                logger.warning(f"Mock mode: Would send to {to_phone}: {message_body[:50]}...")
                return {"status": "mock", "sid": "SMxxxxxx"}

            message = self.twilio_client.messages.create(
                from_=f"whatsapp:{self.twilio_phone}",
                to=f"whatsapp:{to_phone}",
                body=message_body
            )

            logger.info(f"Sent WhatsApp message {message.sid} to {to_phone}")
            return {"status": "sent", "sid": message.sid}

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +91XXXXXXXXXX format."""
        digits = "".join(filter(str.isdigit, phone))
        if digits.startswith("91") and len(digits) == 12:
            return f"+{digits}"
        elif len(digits) == 10:
            return f"+91{digits}"
        else:
            return f"+{digits}" if not digits.startswith("+") else digits
