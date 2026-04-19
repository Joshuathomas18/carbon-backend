"""
Database shim for SQLite to mimic Supabase SDK functionality.
Enables local development without a cloud Supabase instance.
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, create_mock_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, session
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# ============================================================================
# SQLAlchemy Models for SQLite
# ============================================================================

class FarmerModel(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=False)
    wallet_address = Column(String, nullable=True)
    bot_state = Column(String, default="NEW")
    language = Column(String, default="hinglish")
    crop_type = Column(String, nullable=True)
    expert_requested = Column(Boolean, default=False)
    expert_ref_code = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    report_accuracy = Column(String, nullable=True)
    session_expires_at = Column(DateTime, nullable=True)
    farm_polygon = Column(JSON, nullable=True)
    area_hectares = Column(Float, nullable=True)
    burned_stubble = Column(String, nullable=True)
    zero_till = Column(String, nullable=True)
    urea_bags = Column(Integer, nullable=True)
    estimated_tonnes_co2 = Column(Float, nullable=True)
    estimated_value_inr = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlotModel(Base):
    __tablename__ = "plots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    geometry = Column(String)  # Stored as WKT or GeoJSON string
    area_hectares = Column(Float)
    crop_type = Column(String, nullable=True)
    practice = Column(String, nullable=True)
    plot_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CarbonScoreModel(Base):
    __tablename__ = "carbon_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    plot_id = Column(Integer, ForeignKey("plots.id"))
    tonnes_co2_per_hectare = Column(Float)
    total_tonnes_co2 = Column(Float)
    confidence_score = Column(Float)
    value_inr = Column(Float)
    methodology = Column(String, default="Verra VM0042 (Satellite Verified)")
    breakdown = Column(JSON, default={})
    calculated_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# Supabase SDK Shim
# ============================================================================

class ResponseShim:
    """Mock response that mimics PostgREST response object."""
    def __init__(self, data: Any):
        self.data = data
        self.count = len(data) if isinstance(data, list) else 1

class TableQueryShim:
    """Mock query builder for fluent interface."""
    def __init__(self, session_factory, model_class, table_name):
        self.session_factory = session_factory
        self.model_class = model_class
        self.table_name = table_name
        self._filters = []
        self._action = "select"
        self._payload = None

    def select(self, *columns):
        self._action = "select"
        return self

    def insert(self, data: Union[Dict, List[Dict]]):
        self._action = "insert"
        self._payload = data
        return self

    def update(self, data: Dict):
        self._action = "update"
        self._payload = data
        return self

    def eq(self, column: str, value: Any):
        self._filters.append((column, value))
        return self

    def execute(self):
        with self.session_factory() as session:
            if self._action == "select":
                query = session.query(self.model_class)
                for col, val in self._filters:
                    query = query.filter(getattr(self.model_class, col) == val)
                results = query.all()
                return ResponseShim([self._to_dict(r) for r in results])

            elif self._action == "insert":
                items = self._payload if isinstance(self._payload, list) else [self._payload]
                new_objects = []
                for item in items:
                    obj = self.model_class(**item)
                    session.add(obj)
                    new_objects.append(obj)
                session.commit()
                # Refresh to get IDs
                for obj in new_objects:
                    session.refresh(obj)
                return ResponseShim([self._to_dict(r) for r in new_objects])

            elif self._action == "update":
                query = session.query(self.model_class)
                for col, val in self._filters:
                    query = query.filter(getattr(self.model_class, col) == val)
                
                targets = query.all()
                for target in targets:
                    for key, val in self._payload.items():
                        setattr(target, key, val)
                session.commit()
                return ResponseShim([self._to_dict(r) for r in targets])

    def _to_dict(self, obj):
        """Helper to convert SQLAlchemy model to dict."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

class SupabaseSQLiteShim:
    """Shim that provides the same interface as supabase-py but uses SQLite."""
    def __init__(self, db_url=None):
        if db_url is None:
            # Fallback to absolute path in backend folder
            base_dir = os.path.dirname(os.path.abspath(__file__)) # ...app/db
            backend_dir = os.path.dirname(os.path.dirname(base_dir))
            db_url = f"sqlite:///{os.path.join(backend_dir, 'carbon.db')}"
            
        if "./" in db_url:
            # Convert relative to absolute based on backend directory
            base_dir = os.path.dirname(os.path.abspath(__file__)) # ...app/db
            backend_dir = os.path.dirname(os.path.dirname(base_dir))
            db_name = db_url.split("./")[-1]
            db_url = f"sqlite:///{os.path.join(backend_dir, db_name)}"

        logger.info(f"SupabaseSQLiteShim initializing with {db_url}")
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.table_map = {
            "farmers": FarmerModel,
            "plots": PlotModel,
            "carbon_scores": CarbonScoreModel
        }

    def table(self, table_name: str):
        if table_name not in self.table_map:
            raise ValueError(f"Table {table_name} not implemented in SQLite Shim")
        return TableQueryShim(self.SessionLocal, self.table_map[table_name], table_name)

# ============================================================================
# Initialization
# ============================================================================

def get_db_client():
    if "sqlite" in settings.DATABASE_URL.lower():
        logger.info(f"Using SQLite Shim: {settings.DATABASE_URL}")
        return SupabaseSQLiteShim(settings.DATABASE_URL)
    else:
        from supabase import create_client
        logger.info(f"Using Remote Supabase: {settings.SUPABASE_URL}")
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Singleton client
supabase = get_db_client()

def get_supabase():
    """Dependency for yielding DB client."""
    return supabase
