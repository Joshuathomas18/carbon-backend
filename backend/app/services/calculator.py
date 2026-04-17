"""Dertiministic carbon calculator core logic based on IPCC and Verra VM0042."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Constants from Master Logic Document
EF1 = 0.01  # Direct N2O EF
EF4 = 0.01  # Indirect N2O EF (Volatilization)
EF5 = 0.0075  # Indirect N2O EF (Leaching)
FRAC_GASF = 0.10  # Volatilization fraction for synthetic N
FRAC_LEACH = 0.30  # Leaching fraction
GWP_N2O = 265  # AR5
GWP_CH4 = 28   # AR5
MW_RATIO_N2O_N = 44 / 28
MW_RATIO_CO2_C = 44 / 12

# Biomass Burning Constants (IPCC)
CF_CROPS = 0.90  # Combustion Factor
EF_CH4_BURN = 2.7  # g CH4 / kg dm
EF_N2O_BURN = 0.07 # g N2O / kg dm


def calc_fertilizer_emissions(urea_kg: float) -> Dict[str, float]:
    """
    Calculate direct and indirect N2O emissions from Urea application.
    Urea is 46% Nitrogen.
    """
    nitrogen_kg = urea_kg * 0.46
    
    # 1. Direct Emissions
    # N2O-N = N * EF1
    n2o_n_direct = nitrogen_kg * EF1
    
    # 2. Indirect Emissions - Volatilization
    # N2O-N = (N * FracGASF) * EF4
    n2o_n_volat = (nitrogen_kg * FRAC_GASF) * EF4
    
    # 3. Indirect Emissions - Leaching
    # N2O-N = (N * FracLEACH) * EF5
    # Note: Only in regions where leaching occurs (simplified to True for MVP)
    n2o_n_leach = (nitrogen_kg * FRAC_LEACH) * EF5
    
    total_n2o_n = n2o_n_direct + n2o_n_volat + n2o_n_leach
    total_n2o_kg = total_n2o_n * MW_RATIO_N2O_N
    
    co2e_tonnes = (total_n2o_kg * GWP_N2O) / 1000
    
    return {
        "nitrogen_kg": nitrogen_kg,
        "n2o_kg": total_n2o_kg,
        "co2e_tonnes": co2e_tonnes,
        "breakdown": {
            "direct_tonnes": (n2o_n_direct * MW_RATIO_N2O_N * GWP_N2O) / 1000,
            "indirect_volat_tonnes": (n2o_n_volat * MW_RATIO_N2O_N * GWP_N2O) / 1000,
            "indirect_leach_tonnes": (n2o_n_leach * MW_RATIO_N2O_N * GWP_N2O) / 1000,
        }
    }


def calc_burning_emissions(residue_kg_dm: float) -> Dict[str, float]:
    """
    Calculate CH4 and N2O emissions from biomass burning.
    Based on VM0042 Eq 14 & 32.
    """
    # Mass of fuel consumed
    mass_consumed = residue_kg_dm * CF_CROPS
    
    # CH4 emissions (tonnes)
    ch4_g = mass_consumed * EF_CH4_BURN
    ch4_tonnes = ch4_g * 1e-6
    ch4_co2e = ch4_tonnes * GWP_CH4
    
    # N2O emissions (tonnes)
    n2o_g = mass_consumed * EF_N2O_BURN
    n2o_tonnes = n2o_g * 1e-6
    n2o_co2e = n2o_tonnes * GWP_N2O
    
    total_co2e = ch4_co2e + n2o_co2e
    
    return {
        "total_co2e": total_co2e,
        "ch4_tonnes": ch4_tonnes,
        "n2o_tonnes": n2o_tonnes,
        "breakdown": {
            "ch4_co2e": ch4_co2e,
            "n2o_co2e": n2o_co2e
        }
    }


def calc_soc_change(
    baseline_soc_percent: float,
    project_soc_percent: float,
    bulk_density: float,
    area_ha: float,
    depth_cm: float = 30
) -> Dict[str, float]:
    """
    Calculate SOC stock change using simplified ESM adjustment.
    Fixed depth approach corrected for area and density.
    """
    # Soil mass per hectare (tonnes/ha)
    # 1 ha = 10,000 m2
    # depth in m = depth_cm / 100
    # volume = 10,000 * depth_m = 100 * depth_cm
    # density in Mg/m3 = bulk_density
    # mass = volume * density
    soil_mass_ha = (100 * depth_cm) * bulk_density
    
    # SOC stock (t C / ha)
    soc_stock_t0 = (baseline_soc_percent / 100) * soil_mass_ha
    soc_stock_t1 = (project_soc_percent / 100) * soil_mass_ha
    
    soc_change_t_c_ha = soc_stock_t1 - soc_stock_t0
    total_soc_change_t_c = soc_change_t_c_ha * area_ha
    
    # Convert C to CO2e (44/12)
    total_co2e = total_soc_change_t_c * MW_RATIO_CO2_C
    
    return {
        "baseline_stock_t_c_ha": soc_stock_t0,
        "project_stock_t_c_ha": soc_stock_t1,
        "change_t_c_ha": soc_change_t_c_ha,
        "total_co2e": total_co2e
    }


def calculate_final_vcu(
    baseline_data: Dict[str, Any],
    project_data: Dict[str, Any]
) -> Dict[str, float]:
    """
    Aggregate all components to calculate Verified Carbon Units (VCU).
    VCU = Reductions (Reduced Emissions) + Removals (Increased SOC)
    """
    # 1. Removals (SOC)
    soc_result = calc_soc_change(
        baseline_soc_percent=baseline_data["soc_percent"],
        project_soc_percent=project_data["soc_percent"],
        bulk_density=baseline_data["bulk_density"],
        area_ha=project_data["area_ha"]
    )
    
    # 2. Reduction in Fertilizer Emissions
    bsl_fert = calc_fertilizer_emissions(baseline_data.get("urea_kg", 0))
    proj_fert = calc_fertilizer_emissions(project_data.get("urea_kg", 0))
    fert_reduction = bsl_fert["co2e_tonnes"] - proj_fert["co2e_tonnes"]
    
    # 3. Reduction in Burning Emissions
    bsl_burn = calc_burning_emissions(baseline_data.get("burn_residue_kg", 0))
    proj_burn = calc_burning_emissions(project_data.get("burn_residue_kg", 0))
    burn_reduction = bsl_burn["total_co2e"] - proj_burn["total_co2e"]
    
    total_vcu = soc_result["total_co2e"] + fert_reduction + burn_reduction
    
    return {
        "total_vcu": total_vcu,
        "soc_removals": soc_result["total_co2e"],
        "fert_reductions": fert_reduction,
        "burn_reductions": burn_reduction,
        "vcu_per_ha": total_vcu / project_data["area_ha"]
    }
