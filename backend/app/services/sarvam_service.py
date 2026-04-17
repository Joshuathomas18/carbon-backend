"""Sarvam AI integration for voice I/O (ASR, TTS)."""

import base64
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SarvamService:
    """Sarvam AI wrapper for speech-to-text and text-to-speech."""

    def __init__(self, api_key: str = ""):
        """Initialize Sarvam service."""
        self.api_key = api_key
        self.base_url = "https://api.sarvam.ai"
        self.models = {
            "asr": "sarvam-2-en",  # Speech-to-text
            "tts": "sarvam-tts-v1",  # Text-to-speech
            "translation": "sarvam-translate-v1",
        }

    async def transcribe_audio(
        self, audio_base64: str, language: str = "hi"
    ) -> Tuple[str, float]:
        """
        Transcribe audio to text using Sarvam ASR.

        Args:
            audio_base64: Base64-encoded audio
            language: 'hi', 'kn', 'pa', 'en'

        Returns:
            (transcribed_text, confidence_score)
        """
        logger.info(f"Transcribing audio ({language})")

        try:
            # In production, would call:
            # response = await httpx.post(
            #     f"{self.base_url}/v1/speech-to-text",
            #     json={
            #         "model": self.models["asr"],
            #         "audio_base64": audio_base64,
            #         "language": language,
            #     },
            #     headers={"Authorization": f"Bearer {self.api_key}"},
            # )

            # For MVP, return mock transcription
            mock_transcriptions = {
                "hi": "mere pass 5 acre sugarcane hai, maine last year se burning band kar di",
                "kn": "nanu mandya district yinda 3 hectare field irutte",
                "pa": "mera 2 acre wheat farm hai punjab vich",
                "en": "I have 5 acres of sugarcane in Karnataka",
            }

            text = mock_transcriptions.get(
                language, "I have some farm land"
            )

            logger.info(f"✓ Transcribed: {text}")
            return text, 0.92

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "", 0.0

    async def text_to_speech(
        self, text: str, language: str = "hi"
    ) -> Optional[bytes]:
        """
        Convert text to speech using Sarvam TTS.

        Args:
            text: Text to synthesize
            language: 'hi', 'kn', 'pa', 'en'

        Returns:
            Audio bytes (MP3) or None on error
        """
        logger.info(f"Synthesizing speech ({language}): {text[:50]}...")

        try:
            # In production, would call:
            # response = await httpx.post(
            #     f"{self.base_url}/v1/text-to-speech",
            #     json={
            #         "model": self.models["tts"],
            #         "text": text,
            #         "language": language,
            #         "voice": "bulbul",  # Female voice
            #     },
            #     headers={"Authorization": f"Bearer {self.api_key}"},
            # )
            # return response.content

            # For MVP, return mock audio (empty bytes with marker)
            mock_audio = b"MOCK_AUDIO_" + language.encode() + b"_" + text[:20].encode()
            logger.info(f"✓ Generated speech ({len(mock_audio)} bytes)")
            return mock_audio

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """
        Translate text between languages.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        logger.info(f"Translating from {source_lang} to {target_lang}")

        try:
            # In production, call Sarvam translation API
            # For MVP, return original text
            return text

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

    async def process_voice_query(
        self, audio_base64: str, language: str = "hi"
    ) -> dict:
        """
        End-to-end voice query processing.

        1. Transcribe audio
        2. Extract entities
        3. Call carbon estimation
        4. Translate response
        5. Synthesize to speech

        Returns:
            dict with transcription, response text, and audio
        """
        logger.info("Processing voice query")

        try:
            # Step 1: Transcribe
            transcribed_text, transcription_confidence = await self.transcribe_audio(
                audio_base64, language
            )

            if not transcribed_text:
                return {
                    "error": "Could not transcribe audio",
                    "transcribed_text": "",
                    "response_text": "",
                    "response_audio": None,
                }

            # Step 2: Extract entities (handled by EntityExtractor)
            # This will be called by the route handler

            # Step 3 & 4: Carbon estimation and response generation
            # (handled by route handler)

            return {
                "transcribed_text": transcribed_text,
                "transcription_confidence": transcription_confidence,
            }

        except Exception as e:
            logger.error(f"Voice query error: {e}")
            return {
                "error": str(e),
                "transcribed_text": "",
                "response_text": "",
                "response_audio": None,
            }

    def encode_audio_response(self, audio_bytes: bytes) -> str:
        """Encode audio bytes to base64 for JSON response."""
        return base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""
