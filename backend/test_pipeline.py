"""Integration test for the full Carbon_kheth pipeline (SDK version)."""

import sys
import os
import asyncio
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.database import get_supabase
from app.services.estimate_service import EstimateService

async def test_full_pipeline():
    print("Starting Carbon_kheth Pipeline Test (SDK Version)")
    
    # 1. Initialize Supabase Client
    supabase = get_supabase()
    print("--- Supabase Client initialized.")

    # 2. Setup Estimate Service
    service = EstimateService()
    print("--- Estimate Service ready.")

    # 3. Run Estimation
    # Coordinates for a farm in Punjab, India
    test_lat = 30.901
    test_lon = 75.857
    test_area = 5.0
    test_phone = "+919988776655"

    print(f"--- Estimating carbon for {test_area}ha at ({test_lat}, {test_lon})...")
    
    try:
        # Note: We pass the supabase client as the 'db' session
        result = await service.estimate_carbon(
            lat=test_lat,
            lon=test_lon,
            area_hectares=test_area,
            db=supabase,
            phone=test_phone,
            language="en"
        )
        
        print("\n[SUCCESS] Estimation Complete!")
        print("-" * 30)
        print(f"Total Tonnes CO2: {result['total_tonnes_co2']}")
        print(f"Value (INR): {result['value_inr']}")
        print(f"Methodology: {result['methodology']}")
        print(f"Plot ID (Saved to DB): {result.get('plot_id')}")
        print("-" * 30)
        
        # 4. Verify DB storage
        if result.get('plot_id'):
            print("--- Verifying DB storage...")
            score_resp = supabase.table("carbon_scores").select("*").eq("plot_id", result['plot_id']).execute()
            if score_resp.data:
                print(f"--- Found score record in Supabase: {score_resp.data[0]['id']}")
            else:
                print("⚠️ Estimate returned but record not found in Supabase. Did you create the tables in the SQL Editor?")
        else:
            print("⚠️ Plot was not saved. Check if you created the tables or if the credentials are valid.")

    except Exception as e:
        print(f"❌ Error during pipeline test: {e}")
        print("\nPossible solutions:")
        print("1. Ensure you ran the SQL script in your Supabase Dashboard to create tables.")
        print("2. Check your .env for valid SUPABASE_URL and SUPABASE_KEY.")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
