"""Supabase client initialization."""

from supabase import create_client, Client
from app.config import settings

# Initialize Supabase client
# Uses URL and Key from .env - no direct DB password needed
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_supabase() -> Client:
    """Dependency for yielding Supabase client."""
    return supabase
