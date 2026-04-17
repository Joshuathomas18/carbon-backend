"""Google Earth Engine configuration and setup."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# GEE Configuration
GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID", "")
GEE_SERVICE_ACCOUNT_JSON = os.getenv("GEE_SERVICE_ACCOUNT_JSON", "")


def init_gee() -> bool:
    """
    Initialize Google Earth Engine API.

    Returns:
        bool: True if initialization successful, False otherwise.
    """
    try:
        import ee

        # Check if already authenticated
        try:
            ee.Initialize(opt_url="https://earthengine.googleapis.com")
            logger.info("GEE already initialized")
            return True
        except Exception:
            # Try service account authentication
            if GEE_SERVICE_ACCOUNT_JSON and Path(GEE_SERVICE_ACCOUNT_JSON).exists():
                ee.Authenticate()
                ee.Initialize(opt_url="https://earthengine.googleapis.com")
                logger.info("GEE initialized with service account")
                return True
            else:
                logger.warning("GEE_SERVICE_ACCOUNT_JSON not found, GEE not initialized")
                return False

    except ImportError:
        logger.error("google-earth-engine not installed")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize GEE: {e}")
        return False


# Collection configurations
SENTINEL2_CONFIG = {
    "collection": "COPERNICUS/S2_SR_HARMONIZED",
    "resolution": 10,  # meters
    "cloud_filter": 20,  # Max 20% cloud cover
    "bands": {
        "blue": "B2",
        "green": "B3",
        "red": "B4",
        "nir": "B8",
        "swir1": "B11",
        "swir2": "B12",
    },
}

MODIS_CONFIG = {
    "thermal_collection": "MODIS/061/MOD14A1",
    "temperature_band": "MaxT",
    "confidence_band": "Confidence",
    "resolution": 1000,  # meters (1km)
    "temperature_threshold": 320,  # Kelvin (47°C for burning detection)
}

SOILGRIDS_CONFIG = {
    "soilgrids_assets": {
        "organic_carbon_0_20cm": "OpenLandMap/SOILS/OCSTHA_M/v0.2",
        "organic_carbon_20_50cm": "OpenLandMap/SOILS/OCSTHA_S/v0.2",
        "clay_content_0_20cm": "OpenLandMap/SOILS/CLYPPT_M/v0.2",
        "clay_content_20_50cm": "OpenLandMap/SOILS/CLYPPT_S/v0.2",
        "ph_h2o_0_20cm": "OpenLandMap/SOILS/PHIHOX_M/v0.2",
        "ph_h2o_20_50cm": "OpenLandMap/SOILS/PHIHOX_S/v0.2",
    },
    "resolution": 250,  # meters
}

# Performance configuration
GEE_API_TIMEOUT = 60  # seconds
GEE_MAX_RETRIES = 3
GEE_CACHE_DAYS = 7

# Feature extraction parameters
NDVI_CALCULATION = {
    "formula": "(NIR - RED) / (NIR + RED)",
    "min_value": -1.0,
    "max_value": 1.0,
    "description": "Normalized Difference Vegetation Index",
}

EVI_CALCULATION = {
    "formula": "2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)",
    "description": "Enhanced Vegetation Index",
}
