import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.estimate_service import EstimateService

async def test_calculation():
    print("Testing Carbon Calculator Integration...")
    service = EstimateService()
    
    # Sample coordinates (Punjab)
    lat, lon = 30.9, 75.85
    area = 5.0
    
    print(f"Running estimate for {area}ha at ({lat}, {lon})...")
    result = await service.estimate_carbon(lat=lat, lon=lon, area_hectares=area)
    
    print("\n--- RESULTS ---")
    print(f"Methodology: {result['methodology']}")
    print(f"Tonnes CO2/ha: {result['tonnes_co2_per_hectare']}")
    print(f"Total Tonnes: {result['total_tonnes_co2']}")
    print(f"Total Value: INR {result['value_inr']}")
    
    print("\n--- BREAKDOWN ---")
    components = result['breakdown']['vcu_components']
    print(f"SOC Removals: {components['soc_removals']} t")
    print(f"Fertilizer Reductions: {components['fert_reductions']} t")
    print(f"Burning Reductions: {components['burn_reductions']} t")
    
    print("\n--- SATELLITE DATA ---")
    sat = result['breakdown']['satellite_data']
    print(f"Crop: {sat['crop_type']}")
    print(f"Burning Detected: {sat['burning_detected']}")
    print(f"Bulk Density: {sat['bulk_density']}")
    print(f"Baseline SOC: {sat['baseline_soc']}%")
    
    # Basic assertions
    assert result['total_tonnes_co2'] > 0
    assert result['value_inr'] == result['total_tonnes_co2'] * 40
    print("\n✓ Integration Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_calculation())
