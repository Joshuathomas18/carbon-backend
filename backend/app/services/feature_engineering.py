"""Feature engineering pipeline - combine satellite + soil + practice data."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Prepare features for ML model from raw satellite/soil data."""

    STATE_CODES = {
        "Punjab": 0,
        "Haryana": 1,
        "Karnataka": 2,
        "Maharashtra": 3,
        "Madhya_Pradesh": 4,
    }

    CROP_CODES = {
        "rice": 0,
        "wheat": 1,
        "maize": 2,
        "sugarcane": 3,
        "cotton": 4,
        "chickpea": 5,
    }

    def prepare_features(
        self,
        state: str,
        crop_type: str,
        soil_clay: float,
        soil_organic_carbon: float,
        burning_detected: bool,
        residue_score: float,
        years_since_baseline: int = 2,
    ) -> Dict[str, float]:
        """
        Prepare features for XGBoost prediction.

        Returns:
            Dict with encoded features ready for model
        """
        # Encode categorical variables
        state_code = self.STATE_CODES.get(state, 0)
        crop_code = self.CROP_CODES.get(crop_type.lower(), 2)

        # Normalize features to 0-1 range
        soil_clay_norm = min(1.0, soil_clay / 50)  # Clay typically 0-50%
        soil_carbon_norm = min(1.0, soil_organic_carbon / 2)  # Org carbon typically 0-2%

        # Burning: 1 if no burning (good), 0 if burning detected
        burning_history = 1 if not burning_detected else 0

        # Residue: normalize score to 0-1
        residue_retained = max(0, min(1, residue_score))

        return {
            "state_code": state_code,
            "crop_code": crop_code,
            "soil_clay": soil_clay,
            "soil_org_carbon": soil_organic_carbon,
            "burning_history": burning_history,
            "residue_retained": residue_retained,
            "cover_crop": 0,  # Will be 1 if farmer reports using cover crops
            "years_since_baseline": years_since_baseline,
        }

    def add_practice_adjustments(
        self, base_carbon: float, features: Dict
    ) -> float:
        """
        Apply practice adjustment factors to base carbon prediction.

        Adjustments:
        - No burning: +15%
        - Residue retained: +8%
        - Cover crop: +12%
        - Zero tillage: +10% (estimated from residue retention)
        """
        adjusted = base_carbon

        # Burning adjustment
        if features.get("burning_history") == 1:
            adjusted *= 1.15  # +15% if no burning
        else:
            adjusted *= 0.85  # -15% if burning

        # Residue adjustment
        residue_score = features.get("residue_retained", 0.5)
        if residue_score >= 0.75:
            adjusted *= 1.08  # +8% if residue retained
        elif residue_score < 0.25:
            adjusted *= 0.92  # -8% if burned

        # Cover crop adjustment
        if features.get("cover_crop") == 1:
            adjusted *= 1.12  # +12% if cover cropping

        return adjusted

    def generate_recommendations(
        self, features: Dict, carbon_score: float
    ) -> list:
        """
        Generate practice recommendations based on features and carbon score.

        Returns:
            List of recommendations with impact estimates
        """
        recommendations = []

        # Burning
        if features.get("burning_history") == 0:
            recommendations.append({
                "name": "Stop stubble burning",
                "current": False,
                "impact_increase_percent": 15,
                "effort": "medium",
                "cost_estimate_inr": 500,
            })

        # Residue retention
        if features.get("residue_retained") < 0.75:
            recommendations.append({
                "name": "Retain crop residue",
                "current": features.get("residue_retained", 0) > 0.25,
                "impact_increase_percent": 8,
                "effort": "low",
                "cost_estimate_inr": 0,
            })

        # Cover cropping
        if features.get("cover_crop") == 0:
            recommendations.append({
                "name": "Plant cover crops",
                "current": False,
                "impact_increase_percent": 12,
                "effort": "high",
                "cost_estimate_inr": 2000,
            })

        # Soil carbon improvement
        if features.get("soil_org_carbon") < 1.0:
            recommendations.append({
                "name": "Apply compost or manure",
                "current": False,
                "impact_increase_percent": 5,
                "effort": "medium",
                "cost_estimate_inr": 1500,
            })

        # Sort by impact
        recommendations.sort(
            key=lambda x: x["impact_increase_percent"], reverse=True
        )

        return recommendations[:3]  # Top 3 recommendations
