"""Crop type classification from NDVI time series."""

import logging
from typing import List, Tuple

from app.utils.constants import CROP_SIGNATURES

logger = logging.getLogger(__name__)


class CropClassifier:
    """Classify crop type from NDVI curves."""

    def classify(
        self, ndvi_timeseries: List[float], region: str = None
    ) -> Tuple[str, float]:
        """
        Classify crop from NDVI time series.

        Matches observed curve against known crop signatures.
        Returns crop type and confidence score.
        """
        if not ndvi_timeseries or len(ndvi_timeseries) < 6:
            return "unknown", 0.0

        # Calculate features from time series
        ndvi_mean = sum(ndvi_timeseries) / len(ndvi_timeseries)
        ndvi_max = max(ndvi_timeseries)
        ndvi_min = min(ndvi_timeseries)
        ndvi_range = ndvi_max - ndvi_min
        ndvi_var = sum((x - ndvi_mean) ** 2 for x in ndvi_timeseries) / len(
            ndvi_timeseries
        )

        best_match = "unknown"
        best_confidence = 0.0

        # Compare against crop signatures
        for crop_name, signature in CROP_SIGNATURES.items():
            # Score based on:
            # 1. Peak NDVI match
            # 2. Mean NDVI match
            # 3. Variance match (crop cycle duration)

            peak_match = 1.0 - abs(ndvi_max - signature["peak_ndvi"]) / 0.5
            mean_match = 1.0 - abs(ndvi_mean - (signature["peak_ndvi"] * 0.6)) / 0.5
            var_match = 1.0 - abs(ndvi_range - (signature["peak_ndvi"] - signature["min_ndvi_growing"])) / 0.3

            peak_match = max(0, min(1, peak_match))
            mean_match = max(0, min(1, mean_match))
            var_match = max(0, min(1, var_match))

            # Weighted confidence
            confidence = (peak_match * 0.4 + mean_match * 0.3 + var_match * 0.3)

            logger.debug(f"{crop_name}: confidence={confidence:.2f}")

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = crop_name

        return best_match, round(best_confidence, 2)

    def classify_from_seasonal_pattern(
        self, ndvi_timeseries: List[float], months: List[int] = None
    ) -> Tuple[str, float]:
        """
        Classify crop based on seasonal NDVI pattern.

        Analyzes when peak NDVI occurs to identify crop season.
        """
        if not ndvi_timeseries or len(ndvi_timeseries) < 12:
            return "unknown", 0.0

        if not months:
            # Assume monthly data starting from January
            months = [i % 12 for i in range(len(ndvi_timeseries))]

        # Find peaks
        peaks = []
        for i in range(1, len(ndvi_timeseries) - 1):
            if ndvi_timeseries[i] > ndvi_timeseries[i - 1] and ndvi_timeseries[i] > ndvi_timeseries[i + 1]:
                peaks.append((months[i], ndvi_timeseries[i]))

        if not peaks:
            return "unknown", 0.0

        peak_months = [p[0] for p in peaks]

        # Wheat: Oct-Mar growing season, peak in Feb-Mar (months 1-2)
        if any(m in [1, 2, 3] for m in peak_months):
            return "wheat", 0.80

        # Rice: May-Oct growing season, peak in Aug-Sep (months 7-8)
        if any(m in [7, 8, 9] for m in peak_months):
            return "rice", 0.80

        # Sugarcane: Year-round, sustained high NDVI
        if len([v for v in ndvi_timeseries if v > 0.7]) > len(ndvi_timeseries) * 0.6:
            return "sugarcane", 0.75

        # Multiple peaks = likely double crop (rice-wheat)
        if len(peaks) >= 2:
            return "rice_wheat_rotation", 0.75

        return "unknown", 0.50
