"""Extract entities from transcribed text using NLP."""

import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract location, area, crop from farmer voice queries."""

    # Number words in Indian languages
    HINDI_NUMBERS = {
        "ek": 1,
        "do": 2,
        "teen": 3,
        "char": 4,
        "paanch": 5,
        "chhe": 6,
        "saat": 7,
        "aath": 8,
        "nau": 9,
        "das": 10,
    }

    KANNADA_NUMBERS = {
        "ondu": 1,
        "eradu": 2,
        "mooru": 3,
        "nalku": 4,
        "aide": 5,
    }

    # Crop names in Indian languages
    CROPS = {
        # Hindi
        "rice": ["chawal", "dhan"],
        "wheat": ["gehun", "gehu"],
        "maize": ["makkai", "corn"],
        "sugarcane": ["ganna", "ukshu"],
        "cotton": ["kapas", "cotton"],
        "chickpea": ["chana", "kabuli"],
        # Kannada
        "sugarcane": ["ukshu", "ennegallu"],
        "rice": ["batta", "annam"],
        # English
        "rice": ["rice"],
        "wheat": ["wheat"],
        "maize": ["maize", "corn"],
        "sugarcane": ["sugarcane"],
        "cotton": ["cotton"],
        "chickpea": ["chickpea", "chana"],
    }

    def extract_entities(self, text: str, language: str = "hi") -> Dict:
        """
        Extract entities from text.

        Looks for: area, crop type, location, practices

        Returns:
            dict with extracted fields and confidence scores
        """
        text_lower = text.lower()

        # Extract area
        area, area_confidence = self._extract_area(text_lower, language)

        # Extract crop
        crop, crop_confidence = self._extract_crop(text_lower)

        # Extract location (state)
        location, location_confidence = self._extract_location(text_lower)

        # Extract practices
        practices = self._extract_practices(text_lower)

        return {
            "area_hectares": area,
            "area_confidence": area_confidence,
            "crop_type": crop,
            "crop_confidence": crop_confidence,
            "location": location,
            "location_confidence": location_confidence,
            "practices": practices,
            "overall_confidence": (
                area_confidence + crop_confidence + location_confidence
            )
            / 3,
        }

    def _extract_area(
        self, text: str, language: str = "hi"
    ) -> Tuple[Optional[float], float]:
        """Extract plot area in hectares or acres."""
        # Pattern: number + unit
        patterns = [
            r"(\d+)\s*(hectare|hectares|ha|हेक्टेयर)",  # Hectares
            r"(\d+)\s*(acre|acres|एकड़)",  # Acres
            r"(\d+)\s*(bigha|बीघा)",  # Bigha (1 bigha ≈ 0.67 hectare)
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()

                # Convert to hectares
                if "acre" in unit:
                    value *= 0.4047  # 1 acre = 0.4047 hectare
                elif "bigha" in unit:
                    value *= 0.67  # 1 bigha ≈ 0.67 hectare

                return value, 0.90

        # Try Hindi number words
        for word, num in self.HINDI_NUMBERS.items():
            if f"{word} acre" in text or f"{word} एकड़" in text:
                return num * 0.4047, 0.80
            if f"{word} hectare" in text or f"{word} हेक्टेयर" in text:
                return float(num), 0.85

        return None, 0.0

    def _extract_crop(self, text: str) -> Tuple[Optional[str], float]:
        """Extract crop type."""
        for crop_name, keywords in self.CROPS.items():
            for keyword in keywords:
                if keyword in text:
                    return crop_name, 0.85

        # Default guess if we find farming-related words
        if any(w in text for w in ["farm", "field", "खेत", "field"]):
            return "unknown", 0.50

        return None, 0.0

    def _extract_location(self, text: str) -> Tuple[Optional[str], float]:
        """Extract state/region."""
        states = {
            "Punjab": ["punjab", "पंजाब"],
            "Haryana": ["haryana", "हरियाणा"],
            "Karnataka": ["karnataka", "कर्नाटक", "mandya", "मांड्या"],
            "Maharashtra": ["maharashtra", "महाराष्ट्र"],
            "Madhya_Pradesh": ["madhya pradesh", "म.प्र", "indore"],
        }

        for state, keywords in states.items():
            for keyword in keywords:
                if keyword in text:
                    return state, 0.90

        return None, 0.0

    def _extract_practices(self, text: str) -> list:
        """Extract farming practices mentioned."""
        practices = []

        practice_keywords = {
            "no_burning": ["burning band", "stop burning", "जलाना बंद"],
            "residue_retained": [
                "residue retain",
                "stubble retain",
                "पराली रखी",
            ],
            "cover_crop": ["cover crop", "कवर क्रॉप"],
            "zero_till": ["zero till", "जीरो टिल"],
        }

        for practice, keywords in practice_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    practices.append(practice)

        return practices
