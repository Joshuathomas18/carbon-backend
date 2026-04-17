"""Constants and lookup tables."""

# NDVI Crop Signatures (for Day 2 crop classification)
# These will be used to match observed NDVI curves to crop types
CROP_SIGNATURES = {
    "rice": {
        "peak_ndvi": 0.85,
        "min_ndvi_growing": 0.4,
        "cycle_length_days": 150,
        "peaks_per_year": 1,
        "description": "Bimodal if double-cropped, high EVI",
        "states": ["Punjab", "Haryana", "Karnataka", "Tamil Nadu"],
    },
    "wheat": {
        "peak_ndvi": 0.72,
        "min_ndvi_growing": 0.35,
        "cycle_length_days": 120,
        "peaks_per_year": 1,
        "description": "Unimodal, moderate plateau",
        "states": ["Punjab", "Haryana", "Madhya Pradesh"],
    },
    "sugarcane": {
        "peak_ndvi": 0.80,
        "min_ndvi_growing": 0.50,
        "cycle_length_days": 365,
        "peaks_per_year": 1,
        "description": "Sustained high NDVI year-round",
        "states": ["Karnataka", "Maharashtra", "Uttar Pradesh"],
    },
    "maize": {
        "peak_ndvi": 0.75,
        "min_ndvi_growing": 0.35,
        "cycle_length_days": 110,
        "peaks_per_year": 1,
        "description": "Single peak, moderate recovery",
        "states": ["Himachal Pradesh", "Uttarakhand", "Karnataka"],
    },
    "cotton": {
        "peak_ndvi": 0.68,
        "min_ndvi_growing": 0.30,
        "cycle_length_days": 150,
        "peaks_per_year": 1,
        "description": "Lower NDVI plateau, sparse canopy",
        "states": ["Gujarat", "Maharashtra", "Andhra Pradesh"],
    },
    "chickpea": {
        "peak_ndvi": 0.55,
        "min_ndvi_growing": 0.25,
        "cycle_length_days": 100,
        "peaks_per_year": 1,
        "description": "Low NDVI, sparse vegetation",
        "states": ["Madhya Pradesh", "Rajasthan", "Karnataka"],
    },
}

# Verra VM0042 Baseline Carbon Estimates (tonnes CO2/hectare)
# These are placeholders - will be populated from Verra Registry on Day 1
VERRA_BASELINES = {
    "Punjab": {
        "rice": 1.8,
        "wheat": 1.5,
        "maize": 1.2,
    },
    "Haryana": {
        "rice": 1.7,
        "wheat": 1.4,
        "maize": 1.1,
    },
    "Karnataka": {
        "sugarcane": 2.2,
        "maize": 1.3,
        "cotton": 0.9,
    },
    "Maharashtra": {
        "cotton": 1.0,
        "sugarcane": 2.1,
        "chickpea": 0.7,
    },
}

# Practice Adjustment Factors (% increase in carbon)
PRACTICE_ADJUSTMENTS = {
    "no_burning": 0.15,  # Stop stubble burning: +15%
    "residue_retained": 0.08,  # Retain crop residue: +8%
    "cover_crop": 0.12,  # Cover cropping: +12%
    "zero_tillage": 0.10,  # Zero tillage: +10%
    "reduced_tillage": 0.06,  # Reduced tillage: +6%
    "compost_applied": 0.05,  # Compost/manure application: +5%
}

# Carbon Credit Value (INR per tonne CO2)
CARBON_VALUE_SCHEMES = {
    "conservative": 40,  # Baseline - Voluntary Carbon Market
    "moderate": 80,  # Mid-range - ESG funds
    "premium": 150,  # Premium - Carbon credit buyers
}

# GEE Configuration
GEE_SENTINEL2_CONFIG = {
    "collection": "COPERNICUS/S2",
    "resolution": 10,  # meters
    "cloud_filter": 20,  # Max 20% cloud cover
    "bands": ["B4", "B5", "B8", "B11"],  # Red, RE, NIR, SWIR
    "computed_bands": ["NDVI", "EVI"],
}

GEE_MODIS_CONFIG = {
    "thermal_collection": "MODIS/061/MOD14A1",
    "soil_collection": "OpenLandMap/SOILS/OCSTHA_M/v0.2",
    "temperature_threshold": 50,  # Celsius, for burning detection
}

# Regional Information
INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Puducherry",
]

# Language Configuration
SUPPORTED_LANGUAGES = {
    "hi": {"name": "Hindi", "code": "hi-IN"},
    "kn": {"name": "Kannada", "code": "kn-IN"},
    "pa": {"name": "Punjabi", "code": "pa-IN"},
    "en": {"name": "English", "code": "en-IN"},
}
