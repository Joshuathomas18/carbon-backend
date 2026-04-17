"""Data models for Carbon_kheth (SDK Version)."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Farmer(BaseModel):
    """Farmer information with WhatsApp intake funnel tracking."""
    id: Optional[int] = None
    name: Optional[str] = None
    phone: str
    wallet_address: Optional[str] = None

    # WhatsApp bot state machine
    bot_state: str = "NEW"  # NEW, AWAITING_MAP, MAP_RECEIVED, AWAITING_ANSWERS, QUALIFIED

    # Farm data collected during intake
    farm_polygon: Optional[Dict[str, Any]] = None  # GeoJSON polygon
    area_hectares: Optional[float] = None

    # Agronomic answers from WhatsApp questions
    burned_stubble: Optional[str] = None  # "yes", "no", or None
    zero_till: Optional[str] = None  # "yes", "no", or None
    urea_bags: Optional[int] = None  # Number of urea bags per season

    # Carbon estimates
    estimated_tonnes_co2: Optional[float] = None
    estimated_value_inr: Optional[float] = None
    confidence_score: Optional[float] = None

    # Metadata and timestamps
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Plot(BaseModel):
    """Farm plot/land parcel."""
    id: Optional[int] = None
    farmer_id: int
    
    # Store geometry as WKT string or GeoJSON dict
    geometry: Any 
    
    area_hectares: float
    crop_type: Optional[str] = None
    practice: Optional[str] = None
    plot_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CarbonScore(BaseModel):
    """Carbon sequestration ledger for a plot."""
    id: Optional[int] = None
    plot_id: int
    
    tonnes_co2_per_hectare: float
    total_tonnes_co2: float
    confidence_score: float
    value_inr: float
    methodology: str = "Verra VM0042 (Satellite Verified)"
    
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

class FeatureCache(BaseModel):
    """Cache for extracted satellite features."""
    id: Optional[int] = None
    coord_hash: str
    lat: float
    lon: float
    ndvi_median: Optional[float] = None
    soil_organic_carbon: Optional[float] = None
    fire_detected: bool = False
    rainfall_mm: Optional[float] = None
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
