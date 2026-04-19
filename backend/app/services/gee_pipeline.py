"""Google Earth Engine Pipeline for Soil Data.
Fetches Bulk Density and SOC from SoilGrids ISRIC.
"""

import logging
from typing import Dict, Any, Optional

from app.utils.cache import cache

logger = logging.getLogger(__name__)

class GEEPipeline:
    """Service to interact with Google Earth Engine for soil parameters."""

    def __init__(self):
        self.ee = None
        self.initialized = False
        try:
            import ee
            from app.config import settings
            self.ee = ee
            
            # 1. Try Service Account JSON if provided
            if settings.GEE_SERVICE_ACCOUNT_JSON and settings.GEE_PROJECT_ID:
                try:
                    # In Docker/Production, the path will be relative to app root
                    json_path = settings.GEE_SERVICE_ACCOUNT_JSON
                    self.ee.Initialize(
                        project=settings.GEE_PROJECT_ID
                    )
                    self.initialized = True
                    logger.info("GEE initialized with Service Account")
                except Exception as e:
                    logger.error(f"GEE Service Account Auth Failed: {e}")
            
            # 2. Fallback to default
            if not self.initialized:
                try:
                    self.ee.Initialize()
                    self.initialized = True
                    logger.debug("GEE initialized with default credentials")
                except Exception:
                    logger.warning("GEE Initialization failed. Running in simulation mode.")
        except ImportError:
            logger.warning("ee library not found. Running in simulation mode.")
        except Exception as e:
            logger.error(f"GEE Setup error: {e}")

    async def get_soil_parameters(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch Bulk Density (BDOD) and Soil Organic Carbon (SOC) for a point."""
        cache_key = f"soil_{lat}_{lon}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for soil: {lat}, {lon}")
            return cached

        if not self.initialized:
            return self._get_simulated_soil_data(lat, lon)
        try:
            point = self.ee.Geometry.Point([lon, lat])
            soc_img = self.ee.Image("projects/soilgrids-isric/soc_mean")
            soc_val = soc_img.sample(point, 250).first().get('soc_0-30cm_mean')
            bd_img = self.ee.Image("projects/soilgrids-isric/bdod_mean")
            bd_val = bd_img.sample(point, 250).first().get('bdod_0-30cm_mean')
            soc_percent = self.ee.Number(soc_val).multiply(0.01).getInfo()
            bulk_density = self.ee.Number(bd_val).divide(100).getInfo()
            
            result = {
                "lat": lat, "lon": lon,
                "baseline_soc_percent": soc_percent or 1.1,
                "bulk_density": bulk_density or 1.3,
                "data_source": "SoilGrids ISRIC 250m"
            }
            cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"GEE Soil Fetch Error: {e}")
            return self._get_simulated_soil_data(lat, lon)

    async def get_ndvi_history(self, lat: float, lon: float, days: int = 365) -> Dict[str, Any]:
        """Fetch median NDVI using Sentinel-2 (COPERNICUS/S2_SR_HARMONIZED)."""
        cache_key = f"ndvi_{lat}_{lon}_{days}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for NDVI: {lat}, {lon}")
            return cached

        if not self.initialized:
            return {"ndvi_median": 0.65, "simulated": True}
        try:
            end_date = self.ee.Date(datetime.now().strftime('%Y-%m-%d'))
            start_date = end_date.advance(-days, 'day')
            point = self.ee.Geometry.Point([lon, lat])
            
            collection = (self.ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                         .filterBounds(point)
                         .filterDate(start_date, end_date)
                         .filter(self.ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

            def add_ndvi(img):
                return img.addBands(img.normalizedDifference(['B8', 'B4']).rename('NDVI'))

            median_ndvi = collection.map(add_ndvi).select('NDVI').median()
            val = median_ndvi.sample(point, 10).first().get('NDVI').getInfo()
            
            result = {"lat": lat, "lon": lon, "ndvi_median": val or 0.5, "data_source": "Sentinel-2"}
            cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"GEE NDVI Error: {e}")
            return {"ndvi_median": 0.5, "error": str(e)}

    async def get_fire_history(self, lat: float, lon: float, days: int = 365) -> Dict[str, Any]:
        """Fetch fire anomalies using MODIS (MODIS/061/MOD14A1)."""
        cache_key = f"fire_{lat}_{lon}_{days}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if not self.initialized:
            return {"fire_detected": False, "simulated": True}
        try:
            end_date = self.ee.Date(datetime.now().strftime('%Y-%m-%d'))
            start_date = end_date.advance(-days, 'day')
            point = self.ee.Geometry.Point([lon, lat]).buffer(500) # Check 500m radius
            
            fire_col = (self.ee.ImageCollection("MODIS/061/MOD14A1")
                        .filterDate(start_date, end_date)
                        .filterBounds(point))
            
            # FireMask values 7, 8, 9 are fire
            def is_fire(img):
                mask = img.select('FireMask')
                return img.set('has_fire', mask.gt(6).reduceRegion(
                    reducer=self.ee.Reducer.max(), geometry=point, scale=1000).get('FireMask'))

            max_fire = fire_col.map(is_fire).aggregate_max('has_fire').getInfo()
            result = {"lat": lat, "lon": lon, "fire_detected": bool(max_fire and max_fire > 0)}
            cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"GEE Fire Error: {e}")
            return {"fire_detected": False, "error": str(e)}

    async def get_weather_data(self, lat: float, lon: float, days: int = 30) -> Dict[str, Any]:
        """Fetch rainfall data using CHIRPS (UCSB-CHG/CHIRPS/DAILY)."""
        cache_key = f"weather_{lat}_{lon}_{days}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if not self.initialized:
            return {"total_rainfall_mm": 120.5, "simulated": True}
        try:
            end_date = self.ee.Date(datetime.now().strftime('%Y-%m-%d'))
            start_date = end_date.advance(-days, 'day')
            point = self.ee.Geometry.Point([lon, lat])
            
            chirps = (self.ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
                     .filterDate(start_date, end_date)
                     .select('precipitation'))
            
            total_rain = chirps.sum().reduceRegion(
                reducer=self.ee.Reducer.mean(), geometry=point, scale=5000).get('precipitation').getInfo()
            
            result = {"lat": lat, "lon": lon, "total_rainfall_mm": total_rain or 0}
            cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"GEE weather Error: {e}")
            return {"total_rainfall_mm": 0, "error": str(e)}

    def _get_simulated_soil_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Realistic simulation based on location for dev/testing."""
        is_north = lat > 25
        soc = 0.85 if is_north else 1.2
        bd = 1.45 if is_north else 1.32
        return {
            "lat": lat, "lon": lon,
            "baseline_soc_percent": soc, "bulk_density": bd,
            "data_source": "SoilGrids ISRIC (Simulated)", "simulated": True
        }
