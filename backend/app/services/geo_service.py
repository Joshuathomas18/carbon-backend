"""Geocoding service for Carbon Kheth."""

import logging
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)

class GeoService:
    def __init__(self):
        # Nominatim requires a user_agent
        self.geolocator = Nominatim(user_agent="carbon_kheth_bot")

    async def reverse_geocode(self, lat: float, lon: float) -> str:
        """
        Convert lat/lon to a human-readable location name (Village/District).
        """
        try:
            # Note: geopy's reverse is synchronous, but we wrap it for consistency
            location = self.geolocator.reverse((lat, lon), language='en', timeout=10)
            if not location:
                return f"{lat:.4f}, {lon:.4f}"
            
            address = location.raw.get('address', {})
            
            # Try to build a friendly name: Village/Suburb, City/District
            village = address.get('village') or address.get('suburb') or address.get('town')
            district = address.get('state_district') or address.get('city') or address.get('county')
            state = address.get('state')
            
            parts = []
            if village: parts.append(village)
            if district: parts.append(district)
            if state: parts.append(state)
            
            return ", ".join(parts) if parts else location.address[:50]

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error: {e}")
            return f"{lat:.4f}, {lon:.4f}"
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            return f"{lat:.4f}, {lon:.4f}"
