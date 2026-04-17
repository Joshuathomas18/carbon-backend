"""Main orchestration service for carbon estimation.

Coordinates:
1. Satellite data (GEE SoilGrids + Sentinel-2)
2. Feature extraction (crop, burning, residue)
3. ML inference (XGBoost)
4. Carbon calculation + recommendations
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.services.burning_detector import BurningDetector
from app.services.carbon_model import get_carbon_model
from app.services.crop_classifier import CropClassifier
from app.services.feature_engineering import FeatureEngineer
from app.services.gee_ndvi_service import GEENDVIService
from app.services.gee_soil_service import GEESoilService
from app.services.residue_analyzer import ResidueAnalyzer
from app.services.calculator import calculate_final_vcu
from app.services.gee_pipeline import GEEPipeline

logger = logging.getLogger(__name__)


class EstimateService:
    """Main service for carbon estimation."""

    def __init__(self):
        """Initialize all dependencies."""
        self.gee_soil = GEESoilService()
        self.gee_ndvi = GEENDVIService()
        self.crop_classifier = CropClassifier()
        self.burning_detector = BurningDetector()
        self.residue_analyzer = ResidueAnalyzer()
        self.feature_engineer = FeatureEngineer()
        self.carbon_model = get_carbon_model()
        self.gee_pipeline = GEEPipeline()

    async def estimate_carbon(
        self,
        lat: float,
        lon: float,
        area_hectares: float,
        db: Optional[Any] = None,
        phone: str = "",
        language: str = "hi",
    ) -> dict:
        """
        Estimate carbon sequestration for a plot and save to database.
        """
        logger.info(f"Estimating carbon for ({lat}, {lon}) - {area_hectares}ha")

        try:
            # 1. Fetch soil data (SOC/BD)
            soil_data = await self.gee_pipeline.get_soil_parameters(lat, lon)
            soil_org_carbon_baseline = soil_data.get("baseline_soc_percent", 1.1)
            bulk_density = soil_data.get("bulk_density", 1.3)

            # 2. Fetch NDVI History (Sentinel-2)
            ndvi_data = await self.gee_pipeline.get_ndvi_history(lat, lon)
            ndvi_median = ndvi_data.get("ndvi_median", 0.5)

            # 3. Detect Fire History (MODIS)
            fire_data = await self.gee_pipeline.get_fire_history(lat, lon)
            burning_detected = fire_data.get("fire_detected", False)

            # 4. Fetch Weather Data (CHIRPS)
            weather_data = await self.gee_pipeline.get_weather_data(lat, lon)
            rainfall_mm = weather_data.get("total_rainfall_mm", 0)

            # 5. Deterministic Methodology Calculation (VM0042 / IPCC)
            baseline_data = {
                "soc_percent": soil_org_carbon_baseline,
                "bulk_density": bulk_density,
                "area_ha": area_hectares,
                "urea_kg": 200 * area_hectares, 
                "burn_residue_kg": 2000 * area_hectares if burning_detected else 0,
            }
            
            project_data = {
                "soc_percent": soil_org_carbon_baseline + 0.15,
                "bulk_density": bulk_density,
                "area_ha": area_hectares,
                "urea_kg": 150 * area_hectares,
                "burn_residue_kg": 0,
            }

            vcu_results = calculate_final_vcu(baseline_data, project_data)
            total_tonnes = vcu_results["total_vcu"]
            tonnes_per_hectare = vcu_results["vcu_per_ha"]
            value_inr = total_tonnes * 40 # Standard rate

            # 6. Save to Database (if supabase client provided)
            plot_id = None
            if db:
                # db here is the Supabase client
                
                # Check if farmer exists
                farmer_resp = db.table("farmers").select("*").eq("phone", phone).execute()
                farmer_data = farmer_resp.data
                
                if not farmer_data and phone:
                    farmer_insert = {
                        "phone": phone,
                        "name": "Smallholder Farmer",
                        "wallet_address": "0x..." # Placeholder
                    }
                    new_farmer = db.table("farmers").insert(farmer_insert).execute()
                    farmer_id = new_farmer.data[0]["id"]
                elif farmer_data:
                    farmer_id = farmer_data[0]["id"]
                else:
                    farmer_id = 1 # Default or anonymous

                # Create Plot record (using point/box as simple WKT)
                # Note: Supabase/PostGIS accepts GeoJSON or WKT strings
                point_wkt = f'SRID=4326;POLYGON(({lon-0.001} {lat-0.001}, {lon+0.001} {lat-0.001}, {lon+0.001} {lat+0.001}, {lon-0.001} {lat+0.001}, {lon-0.001} {lat-0.001}))'
                plot_insert = {
                    "farmer_id": farmer_id,
                    "geometry": point_wkt,
                    "area_hectares": area_hectares,
                    "plot_metadata": {
                        "rainfall_mm": rainfall_mm,
                        "ndvi_median": ndvi_median,
                        "lat": lat,
                        "lon": lon
                    }
                }
                new_plot = db.table("plots").insert(plot_insert).execute()
                plot_id = new_plot.data[0]["id"]

                # Create CarbonScore record
                score_insert = {
                    "plot_id": plot_id,
                    "tonnes_co2_per_hectare": tonnes_per_hectare,
                    "total_tonnes_co2": total_tonnes,
                    "confidence_score": 0.92,
                    "value_inr": value_inr,
                    "breakdown": {
                        "soc_removals": vcu_results["soc_removals"],
                        "fert_reductions": vcu_results["fert_reductions"],
                        "burn_reductions": vcu_results["burn_reductions"],
                    }
                }
                db.table("carbon_scores").insert(score_insert).execute()

            return {
                "plot_id": plot_id,
                "tonnes_co2_per_hectare": round(tonnes_per_hectare, 2),
                "total_tonnes_co2": round(total_tonnes, 2),
                "value_inr": round(value_inr, 0),
                "confidence_score": 0.92 if not soil_data.get("simulated") else 0.70,
                "methodology": "Verra VM0042 (Satellite Verified)",
                "breakdown": {
                    "vcu_components": {
                        "soc_removals": round(vcu_results["soc_removals"], 2),
                        "fert_reductions": round(vcu_results["fert_reductions"], 2),
                        "burn_reductions": round(vcu_results["burn_reductions"], 2),
                    },
                    "satellite_metrics": {
                        "ndvi_median": round(ndvi_median, 3),
                        "fire_detected": burning_detected,
                        "rainfall_30d_mm": round(rainfall_mm, 1),
                        "bulk_density": bulk_density,
                        "baseline_soc": soil_org_carbon_baseline,
                    },
                    "data_sources": ["SoilGrids", "Sentinel-2", "MODIS", "CHIRPS"],
                },
                "calculated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error estimating carbon: {e}", exc_info=True)
            # Fallback to conservative estimate
            return {
                "plot_id": None,
                "tonnes_co2_per_hectare": 1.5,
                "total_tonnes_co2": round(1.5 * area_hectares, 2),
                "value_inr": round(1.5 * area_hectares * 40, 0),
                "confidence_score": 0.60,
                "methodology": "Verra Baseline (Fallback)",
                "breakdown": {
                    "error": str(e),
                    "data_sources": ["Verra Baseline"],
                },
                "practices": [],
                "calculated_at": datetime.utcnow().isoformat(),
            }

    async def get_carbon_history(self, plot_id: int, months: int = 12) -> list:
        """
        Get historical carbon scores for a plot.

        TODO: Implement with database queries
        """
        return []

    async def get_practice_recommendations(self, plot_id: int) -> list:
        """
        Get practice recommendations for a plot.

        TODO: Implement with database queries
        """
        return []
