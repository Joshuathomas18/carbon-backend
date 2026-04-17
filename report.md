# Carbon_kheth: Technical Validation & Estimation Report

This report explains the data integrity, scientific methodology, and financial valuation logic used to calculate carbon credits for the **Carbon_kheth** project.

---

## 1. Analysis Area & Geographic Scope
- **Target Region**: Primary focus on smallholder farmers in **Punjab and Haryana, India**.
- **Sample Unit**: 5.0 Hectare test plots.
- **Coordinates Analyzed**: Punjab center (`30.901 N, 75.857 E`).
- **Precision**: 10m spatial resolution for crop health (Sentinel-2) and 250m for soil baselines (SoilGrids).

---

## 2. Multi-Layer Satellite Data Sources
We use a "Triangulation Approach" to ensure data validity. We don't just guess; we ping four distinct planetary-scale datasets:

| Data Layer | Source | What we extract | Why it matters |
| :--- | :--- | :--- | :--- |
| **Soil Carbon** | [SoilGrids (ISRIC)](https://www.isric.org/explore/soilgrids) | SOC (Soil Organic Carbon) & Bulk Density | Sets the scientific baseline of "hidden" carbon in the ground. |
| **Crop Health** | [Sentinel-2 (ESA)](https://sentinel.esa.int/) | Median NDVI (Vegetation Index) | Proves that a crop was actually planted and is actively breathing CO2. |
| **Fire History** | [MODIS (NASA)](https://modis.gsfc.nasa.gov/) | Active Thermal Anomalies | Verifies the "Zero Burn" claim. If fire is detected, credits are disqualified. |
| **Precipitation** | [CHIRPS (Daily)](https://www.chg.ucsb.edu/data/chirps) | Cumulative Rainfall (mm) | Correlates carbon growth with weather to ensure the data isn't an anomaly. |

---

## 3. Scientific Methodology (Master Logic)
Our calculation engine follows the **Verra VM0042** and **IPCC Tier 1/2** frameworks. The final "Verified Carbon Unit" (VCU) is the sum of two actions:

### A. Carbon Removals (Increased SOC)
We calculate how much carbon is added to the soil through regenerative practices (e.g., No-Tilling, Cover Cropping).
- **Formula**: `SOC Change = (Project SOC % - Baseline SOC %) * Soil Mass (t/ha) * Area (ha) * 3.67 (C to CO2 ratio)`
- **Standard Baseline**: ~1.1% SOC (Soil Organic Carbon).
- **Project Goal**: Increase of ~0.15% over the intervention period.

### B. Emission Reductions (Avoided N2O/CH4)
We reward farmers for **reducing** toxic emissions:
- **Fertilizer Reduction**: Switching from heavy Urea (46% Nitrogen) to organic alternatives reduces N2O emissions. (GWP of N2O = 265x CO2).
- **Zero Burning**: Avoiding residue burning stops the immediate release of Methane (CH4) and Nitrous Oxide (N2O).

---

## 4. Calculation Engine (The Math)
Our "Master Logic" uses three primary buckets of calculation to reach the final valuation.

### Bucket A: Soil Organic Carbon (SOC) Stock
This is the "Removals" part of the equation.
- **Formula**: `∆SOC = (SOC_p - SOC_b) × Soil_Mass × 3.67`
- **Variables**:
    - `Soil_Mass (t/ha)` = `Depth (30cm) × Bulk Density (t/m³) × 100`
    - `3.67` = The molecular conversion ratio from Carbon (C) to Carbon Dioxide (CO2).
- **Logic**: We measure the baseline SOC % from SoilGrids. The project intervention (Intercropping/No-Till) target is a +0.15% increase.

### Bucket B: Reduced Fertilizer Emissions (N2O)
Nitrous Oxide (N2O) is 265x more powerful than CO2.
- **Formula**: `CO2e_fert = (Σ N2O-N) × (44/28) × 265 / 1000`
- **Logic**:
    - `Nitrogen = Urea_kg × 0.46`
    - `Direct Emissions` = `N × 0.01` (EF1)
    - `Indirect Volatilization` = `(N × 0.1) × 0.01` (EF4)
    - `Indirect Leaching` = `(N × 0.3) × 0.0075` (EF5)

### Bucket C: Avoided Burning (Zero Burn)
- **Formula**: `CO2e_burn = (CH4_emissions × 28) + (N2O_emissions × 265)`
- **Variables**:
    - `Mass Consumed = Crop Residue (kg) × 0.90` (Combustion Factor)
    - `CH4 = Mass × 2.7g/kg`
    - `N2O = Mass × 0.07g/kg`
- **Logic**: If the **MODIS satellite** detects zero firing anomalies on the plot boundary, the farmer is credited with the *avoidment* of these emissions compared to the regional baseline practice.

---

## 5. Financial Valuation & Ledger
Once the total Tonnes of CO2e (Carbon Dioxide Equivalent) is calculated, we convert it to a transparent financial payout.

- **Current Rate**: **₹40 / Tonne CO2e** (Verified Smallholder Rate).
- **Confidence Score**:
    - **92% Confidence**: Satellite data is 100% matched and permissioned.
    - **70% Confidence**: Partial data available (Simulation mode).
- **Storage**: Every result is hashed and saved to a **PostGIS Cloud Database (Supabase)**, ensuring the boundaries (Polygons) are immutable and audit-ready.

---

## 5. Sample Result (Test Plot #1)
- **Area**: 5.0 Hectares
- **Total Carbon Generated**: **120.26 Tonnes CO2e**
- **Financial Payout**: **₹4,810.00**
- **Verification Signature**: `Verra VM0042 (Satellite Verified)`

> [!IMPORTANT]
> **Data Validity Disclaimer**: This report is generated based on a combination of real GEE satellite pings and deterministic IPCC algorithms. All data in the "Mission Control" dashboard is live and synced with the Supabase ledger.
