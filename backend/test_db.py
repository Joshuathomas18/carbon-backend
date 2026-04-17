import sys
import os

sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.database import engine
from app.db.models import Base

print("Testing database engine connection to Supabase...")
print(f"URL: {engine.url}")

try:
    print("Creating tables in Supabase...")
    # This requires the postgis extension to be enabled in Supabase!
    # Usually Supabase has it enabled, but we might need to verify
    Base.metadata.create_all(engine)
    print("✓ Tables created successfully!")
except Exception as e:
    print(f"Error connecting to database: {e}")
