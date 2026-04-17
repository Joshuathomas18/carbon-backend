"""Google Earth Engine NDVI/EVI extraction from Sentinel-2."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


class GEENDVIService:
    """Service for extracting NDVI/EVI time series from Sentinel-2."""

    def __init__(self):
        """Initialize GEE NDVI service."""
        self.ee = None
        self.gee_initialized = False
        try:
            import ee
            self.ee = ee
            try:
                self.ee.Initialize()
                self.gee_initialized = True
                logger.info("GEE initialized for NDVI data")
            except Exception as e:
                logger.warning(f"GEE not initialized: {e}. NDVI data will be mocked.")
        except ImportError:
            logger.warning("ee package not installed. NDVI data will be mocked.")

    async def get_ndvi_timeseries(
        self,
        lat: float,
        lon: float,
        start_date: str = "2023-01-01",
        end_date: str = "2026-04-15",
        frequency: str = "monthly",
    ) -> dict:
        """
        Get NDVI time series for a location.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            frequency: 'monthly' or 'weekly'

        Returns:
            dict with:
                - timestamps: List of dates
                - ndvi_values: List of NDVI values (0-1 scale)
                - evi_values: List of EVI values
                - cloud_cover: List of cloud cover percentages
        """
        logger.info(f"Fetching NDVI time series for ({lat}, {lon})")

        if not self.gee_initialized:
            logger.warning("GEE not initialized, returning mock NDVI time series")
            return self._get_mock_ndvi_timeseries(lat, lon)

        try:
            # TODO: Implement actual GEE API calls to Sentinel-2
            # For MVP, return mock time series data

            return self._get_mock_ndvi_timeseries(lat, lon)

        except Exception as e:
            logger.error(f"Error fetching NDVI time series: {e}")
            return self._get_mock_ndvi_timeseries(lat, lon)

    def _get_mock_ndvi_timeseries(self, lat: float, lon: float) -> dict:
        """
        Generate mock NDVI time series.

        Simulates wheat-rice cropping pattern typical in North India.
        """
        from datetime import datetime, timedelta

        timestamps = []
        ndvi_values = []
        evi_values = []
        cloud_cover = []

        # Start from 3 years ago
        current_date = datetime(2023, 4, 15)
        end_date = datetime(2026, 4, 15)

        while current_date <= end_date:
            timestamps.append(current_date.isoformat())

            # Simulate wheat-rice rotation NDVI pattern
            # Month of year determines season
            month = current_date.month

            # Wheat season (Oct-Apr): Growing Nov-Mar
            if 10 <= month <= 12 or 1 <= month <= 3:  # Rabi/winter season
                if month in [11, 12, 1, 2, 3]:  # Growing period
                    base_ndvi = 0.4 + 0.35 * (
                        (month - 11) % 12 / 5.0 if month >= 11 else (month + 12 - 11) / 5.0
                    )
                else:
                    base_ndvi = 0.3  # Pre-plant or harvest
            # Rice season (May-Oct): Growing Jun-Sep
            elif 5 <= month <= 10:
                if month in [6, 7, 8, 9]:  # Growing period
                    base_ndvi = 0.3 + 0.55 * ((month - 6) / 4.0)
                else:
                    base_ndvi = 0.2  # Pre-plant or harvest
            else:
                base_ndvi = 0.15  # Fallow period

            # Add some variation
            import math
            noise = math.sin(current_date.timetuple().tm_yday / 365 * 2 * math.pi) * 0.05
            ndvi = max(0.0, min(1.0, base_ndvi + noise))

            # EVI typically higher than NDVI, more responsive to high biomass
            evi = ndvi * 1.2 + 0.1

            ndvi_values.append(round(ndvi, 3))
            evi_values.append(round(min(1.0, evi), 3))
            cloud_cover.append(15)  # Average cloud cover in India

            # Move to next month
            current_date += timedelta(days=30)

        return {
            "lat": lat,
            "lon": lon,
            "timestamps": timestamps,
            "ndvi_values": ndvi_values,
            "evi_values": evi_values,
            "cloud_cover": cloud_cover,
            "ndvi_mean": round(sum(ndvi_values) / len(ndvi_values), 3),
            "ndvi_max": round(max(ndvi_values), 3),
            "ndvi_min": round(min(ndvi_values), 3),
            "data_source": "Sentinel-2 (Simulated for MVP)",
            "collection": "COPERNICUS/S2_SR_HARMONIZED",
            "resolution": "10m",
            "timestamp": "2026-04-15",
        }

    async def get_vegetation_indices(
        self, lat: float, lon: float, end_date: str = "2026-04-15"
    ) -> dict:
        """
        Get current vegetation indices (NDVI, EVI) for a location.

        Returns latest available sentinel-2 observations.
        """
        timeseries = await self.get_ndvi_timeseries(lat, lon, end_date=end_date)

        if timeseries["ndvi_values"]:
            return {
                "lat": lat,
                "lon": lon,
                "ndvi": timeseries["ndvi_values"][-1],  # Latest value
                "evi": timeseries["evi_values"][-1],
                "ndvi_mean": timeseries["ndvi_mean"],
                "ndvi_trend": self._calculate_trend(timeseries["ndvi_values"]),
                "latest_date": timeseries["timestamps"][-1],
                "data_source": "Sentinel-2 (Simulated for MVP)",
            }

        return {
            "error": "No vegetation data available",
            "lat": lat,
            "lon": lon,
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend in values (increasing, decreasing, stable)."""
        if len(values) < 3:
            return "insufficient_data"

        recent_mean = sum(values[-3:]) / 3
        older_mean = sum(values[:3]) / 3

        if recent_mean > older_mean + 0.1:
            return "increasing"
        elif recent_mean < older_mean - 0.1:
            return "decreasing"
        else:
            return "stable"
