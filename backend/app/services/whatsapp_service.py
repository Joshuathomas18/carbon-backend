"""Twilio WhatsApp bot service for farmer intake funnel."""

import json
import logging
import os
from typing import Optional, Dict, Any

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
        """Initialize Twilio client."""
        try:
            from twilio.rest import Client
            self.twilio_client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN")
            )
            self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
            self.frontend_url = os.getenv("FRONTEND_URL", "https://carbon-kheth.example.com")
        except ImportError:
            logger.warning("Twilio SDK not installed. Running in mock mode.")
            self.twilio_client = None
            self.twilio_phone = "+1234567890"
            self.frontend_url = "http://localhost:3000"

    async def handle_incoming_message(
        self,
        phone_number: str,
        message_body: str
    ) -> Dict[str, Any]:
        """
        Handle incoming WhatsApp message and run state machine.

        Parameters:
        -----------
        phone_number : str
            Farmer's WhatsApp number (format: +91XXXXXXXXXX)
        message_body : str
            Text content of the message

        Returns:
        --------
        dict
            Result of state transition with response sent
        """
        try:
            # Normalize phone number
            phone_number = self._normalize_phone(phone_number)
            logger.info(f"WhatsApp message from {phone_number}: {message_body[:50]}")

            # In a real app, you'd fetch/create farmer from database
            # For now, we simulate the state transitions

            current_state = "NEW"  # Would be fetched from DB in production

            # Run state machine
            if current_state == "NEW":
                response = await self._handle_new_state(phone_number)
                # Next state: AWAITING_MAP

            elif current_state == "AWAITING_MAP":
                response = await self._handle_awaiting_map_state(phone_number)

            elif current_state == "MAP_RECEIVED":
                response = await self._handle_map_received_state(phone_number)

            elif current_state == "AWAITING_ANSWERS":
                response = await self._handle_awaiting_answers_state(phone_number, message_body)

            elif current_state == "QUALIFIED":
                response = await self._handle_qualified_state(phone_number)

            else:
                response = {"status": "error", "message": f"Unknown state: {current_state}"}

            return response

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {str(e)}", exc_info=True)
            await self.send_message(
                phone_number,
                "Maafi chahta hoon, ek error aaya. Doobara koshish karo."
            )
            return {"status": "error", "message": str(e)}

    async def _handle_new_state(self, phone_number: str) -> Dict[str, Any]:
        """Handle NEW state: Send welcome + magic link."""
        magic_link = f"{self.frontend_url}/map?phone={phone_number}"

        welcome_msg = (
            "🌾 *Namaste!* 🌾\n\n"
            "Carbon Sequestration Program mein aapka swagat hai!\n\n"
            "Humari taraf se, aapke farm ke liye carbon estimate milega aur "
            "aap carbon credits earn kar sakte ho.\n\n"
            f"*Yahan click karke apna farm draw karein:*\n{magic_link}\n\n"
            "Iske baad, hum aapko 3 simple sawal puchenge. Shuruaat karein! 👇"
        )

        await self.send_message(phone_number, welcome_msg)

        return {
            "status": "success",
            "action": "sent_welcome_and_link",
            "magic_link": magic_link
        }

    async def _handle_awaiting_map_state(self, phone_number: str) -> Dict[str, Any]:
        """Handle AWAITING_MAP state: Remind user to complete map."""
        reminder_msg = (
            "🗺️ Map abhi complete nahi hua.\n\n"
            "Kripaya link par click karke apne farm ka polygon draw karein"
        )

        await self.send_message(phone_number, reminder_msg)

        return {
            "status": "pending",
            "action": "awaiting_map",
            "message": "User not yet completed map"
        }

    async def _handle_map_received_state(self, phone_number: str) -> Dict[str, Any]:
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

        await self.send_message(phone_number, questions_msg)

        return {
            "status": "pending",
            "action": "asked_questions",
            "questions": ["burned_stubble", "zero_till", "urea_bags"]
        }

    async def _handle_awaiting_answers_state(
        self,
        phone_number: str,
        message_body: str
    ) -> Dict[str, Any]:
        """Handle AWAITING_ANSWERS state: Extract answers and calculate payout."""
        try:
            # In real app, would use LLM to extract answers
            # For now, mock extraction
            answers = {
                "burned_stubble": "unknown",
                "zero_till": "unknown",
                "urea_bags": None,
                "confidence": 0.6
            }

            # Mock payout calculation
            estimated_value_inr = 8500.0

            payout_msg = (
                f"🎉 *Dhanyavaad!* 🎉\n\n"
                f"Aapke farm ke liye carbon estimate ready hai:\n\n"
                f"💰 *Estimated Payout:* ₹{estimated_value_inr:.0f}\n"
                f"📊 *Carbon:* 3.75 tonnes CO2\n"
                f"✅ *Confidence:* 82%\n\n"
                f"Ek expert aapko 24 ghanton mein call karega details dene ke liye.\n\n"
                f"Shukriya! 🙏"
            )

            await self.send_message(phone_number, payout_msg)

            return {
                "status": "success",
                "action": "qualified",
                "answers": answers,
                "estimated_payout": estimated_value_inr
            }

        except Exception as e:
            logger.error(f"Error extracting answers: {str(e)}")
            retry_msg = (
                "Sorry, samajh nahi aaya. Kripaya doobara try karein:\n"
                "1. Stubble burn: haan/nahi\n"
                "2. Zero-till: haan/nahi\n"
                "3. Urea bags: number"
            )
            await self.send_message(phone_number, retry_msg)
            return {"status": "error", "message": str(e)}

    async def _handle_qualified_state(self, phone_number: str) -> Dict[str, Any]:
        """Handle QUALIFIED state: Farmer already qualified."""
        thankyou_msg = (
            "Shukriya contact ke liye! 🙏\n\n"
            "Aapka expert aapko contact karega.\n"
            "Agar koi sawal hai toh message karein."
        )
        await self.send_message(phone_number, thankyou_msg)

        return {
            "status": "success",
            "action": "already_qualified",
            "message": "Farmer already completed intake"
        }

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
        # Remove all non-digits
        digits = "".join(filter(str.isdigit, phone))

        # If already has country code
        if digits.startswith("91"):
            return f"+{digits}"
        # If just 10 digits (Indian)
        elif len(digits) == 10:
            return f"+91{digits}"
        # Assume it already has +
        else:
            return f"+{digits}" if not digits.startswith("+") else digits
