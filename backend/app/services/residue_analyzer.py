"""Crop residue management inference from post-harvest NDVI trends."""

import logging
from typing import List

logger = logging.getLogger(__name__)


class ResidueAnalyzer:
    """Analyze crop residue management from satellite NDVI."""

    def analyze_residue_management(
        self, ndvi_timeseries: List[float], harvest_indices: List[int] = None
    ) -> dict:
        """
        Infer residue management from post-harvest NDVI recovery.

        Logic:
        - Residue retained: NDVI recovers quickly (0.4+ within 30 days)
        - Residue burned/removed: NDVI stays low for 60+ days
        - Returns: residue_score (0-1), management_type
        """
        if not ndvi_timeseries or len(ndvi_timeseries) < 6:
            return {
                "residue_score": 0.5,
                "management_type": "unknown",
                "confidence": 0.0,
            }

        residue_scores = []
        management_events = []

        # Analyze each potential harvest (NDVI drop)
        for i in range(len(ndvi_timeseries) - 2):
            # Detect harvest: sharp NDVI drop
            if ndvi_timeseries[i] > 0.6 and ndvi_timeseries[i + 1] < ndvi_timeseries[i] - 0.2:
                # Harvest detected at index i
                harvest_ndvi = ndvi_timeseries[i + 1]

                # Look at recovery in next 1-2 months
                if i + 2 < len(ndvi_timeseries):
                    recovery_ndvi = ndvi_timeseries[i + 2]
                    recovery_rate = recovery_ndvi - harvest_ndvi

                    # Score based on recovery speed
                    if recovery_rate > 0.15:
                        # Fast recovery = residue retained
                        score = 0.85
                        mgmt_type = "residue_retained"
                    elif recovery_rate > 0.05:
                        # Moderate recovery = partial retention
                        score = 0.60
                        mgmt_type = "partial_retention"
                    else:
                        # Slow/no recovery = burned or removed
                        score = 0.20
                        mgmt_type = "residue_burned_or_removed"

                    residue_scores.append(score)
                    management_events.append(
                        {
                            "harvest_month": i,
                            "recovery_rate": round(recovery_rate, 3),
                            "management_type": mgmt_type,
                            "score": score,
                        }
                    )

        # Aggregate scores
        if residue_scores:
            avg_score = sum(residue_scores) / len(residue_scores)
            dominant_type = max(
                set(e["management_type"] for e in management_events),
                key=lambda x: sum(1 for e in management_events if e["management_type"] == x),
            )
        else:
            avg_score = 0.5
            dominant_type = "unknown"

        return {
            "residue_score": round(avg_score, 2),
            "management_type": dominant_type,
            "management_events": management_events,
            "confidence": 0.75 if management_events else 0.0,
        }

    def get_residue_carbon_impact(self, residue_score: float) -> dict:
        """
        Estimate carbon impact based on residue management.

        Retained residue: +8% to +12% carbon
        Burned residue: -8% carbon
        """
        if residue_score >= 0.75:
            # Retained residue
            return {
                "carbon_adjustment_percent": 0.10,
                "description": "Residue retained: +10% carbon",
                "practice": "Continue retaining residue",
            }
        elif residue_score >= 0.50:
            # Partial retention
            return {
                "carbon_adjustment_percent": 0.05,
                "description": "Partial residue retention: +5% carbon",
                "practice": "Increase residue retention",
            }
        else:
            # Burned/removed
            return {
                "carbon_adjustment_percent": -0.08,
                "description": "Residue burned/removed: -8% carbon",
                "practice": "Switch to residue retention (potential +15%)",
            }

    async def estimate_residue_quantity(
        self, crop_type: str, area_hectares: float
    ) -> dict:
        """
        Estimate crop residue quantity for given crop and area.

        Typical residue production:
        - Rice: 5-6 tonnes/ha
        - Wheat: 4-5 tonnes/ha
        - Sugarcane: 12-15 tonnes/ha
        """
        residue_production = {
            "rice": {"min": 5, "max": 6, "avg": 5.5},
            "wheat": {"min": 4, "max": 5, "avg": 4.5},
            "maize": {"min": 4, "max": 5, "avg": 4.5},
            "sugarcane": {"min": 12, "max": 15, "avg": 13.5},
            "cotton": {"min": 2, "max": 3, "avg": 2.5},
            "chickpea": {"min": 1.5, "max": 2, "avg": 1.75},
        }

        prod = residue_production.get(
            crop_type.lower(), {"min": 3, "max": 4, "avg": 3.5}
        )

        total_residue = prod["avg"] * area_hectares

        return {
            "crop_type": crop_type,
            "area_hectares": area_hectares,
            "residue_tonnes_per_hectare": prod["avg"],
            "total_residue_tonnes": round(total_residue, 1),
            "carbon_value_if_retained": round(
                total_residue * 0.5, 1
            ),  # ~0.5 tonnes CO2 per tonne residue
        }
