# Carbon Calculator Master Logic Document

This document serves as the technical "brain" for the Python carbon calculator engine. It contains exact formulas, variables, and constants extracted from Verra VM0042 and IPCC 2006 Guidelines (Vol 4).

## 1. Soil Organic Carbon (SOC) - Equivalent Soil Mass (ESM) basis

### Goal
Quantify SOC stock changes while correcting for fluctuations in soil bulk density.

### Formulas
$$SOC_{mass, layer} = C_{content} \times Soil_{mass, layer}$$
$$Soil_{mass} = Area \times Depth \times BulkDensity$$

**Equivalent Soil Mass (ESM) Adjustment:**
To compare time $t_0$ and $t_1$, SOC must be reported for a reference cumulative soil mass ($M_{ref}$).
1. Calculate cumulative soil mass and cumulative SOC mass for sampled layers.
2. Use a **Cubic Spline function** (or linear interpolation as a simplification) to determine the SOC mass corresponding exactly to $M_{ref}$.

### Variables
- $C_{content}$: Soil Organic Carbon concentration (g C / kg soil or %).
- $BulkDensity$: Dry bulk density ($g/cm^3$ or $Mg/m^3$).
- $Area$: 1 hectare ($10,000 m^2$).
- $M_{ref}$: Reference soil mass (e.g., $1950 Mg/ha$ for a nominal $30 cm$ depth).

---

## 2. N2O Emissions from Synthetic Fertilizer

### Formulas
Total N2O emissions from managed soils are the sum of direct and indirect pathways.

#### A. Direct Emissions (IPCC Eq 11.1)
$$N_2O_{direct} = F_{SN} \times EF_1 \times \frac{44}{28}$$
- $F_{SN}$: Annual synthetic N fertilizer applied (kg N).
- $EF_1$: Emission factor for N additions. **Default: 0.01** (1%).
- $EF_{1FR}$: For flooded rice. **Default: 0.003**.

#### B. Indirect Emissions - Volatilization (IPCC Eq 11.9)
$$N_2O_{ATD} = (F_{SN} \times Frac_{GASF}) \times EF_4 \times \frac{44}{28}$$
- $Frac_{GASF}$: Fraction of synthetic N that volatilizes. **Default: 0.10**.
- $EF_4$: Emission factor for atmospheric deposition. **Default: 0.01**.

#### C. Indirect Emissions - Leaching/Runoff (IPCC Eq 11.10)
$$N_2O_{L} = (F_{SN} + FON + FCR) \times Frac_{LEACH} \times EF_5 \times \frac{44}{28}$$
- $Frac_{LEACH}$: Fraction of N lost through leaching. **Default: 0.30** (in regions where rainfall > ET).
- $EF_5$: Emission factor for leaching/runoff. **Default: 0.0075**.

### Constants
- $GWP_{N2O}$: **265** (t CO2e / t N2O) - IPCC AR5.
- $44/28$: Molar mass ratio to convert $N_2O-N$ to $N_2O$.

---

## 3. Emissions from Biomass Burning

### Formulas (VM0042 Eq 14 & 32)
Emissions occur if crop residues are burned on-field.

#### A. Methane (CH4)
$$CH_{4,burn} = (M_B \times C_F \times EF_{CH4}) \times 10^{-6}$$
- $M_B$: Mass of agricultural residues burned (kg dry matter).
- $C_F$: Combustion Factor (proportion of fuel consumed). **Default: 0.90** for crops.
- $EF_{CH4}$: Emission factor (g CH4 / kg dm). **Default: 2.7** (IPCC).

#### B. Nitrous Oxide (N2O)
$$N_2O_{burn} = (M_B \times C_F \times EF_{N2O}) \times 10^{-6}$$
- $EF_{N2O}$: Emission factor (g N2O / kg dm). **Default: 0.07** (IPCC).

### Constants
- $GWP_{CH4}$: **28** (t CO2e / t CH4).
- $GWP_{N2O}$: **265** (t CO2e / t N2O).

---

## 4. Crop Residue Nitrogen (F_CR)

### Formula (IPCC Eq 11.6)
$$F_{CR} = Yield \times DRY \times (1 - Frac_{Burn} \times C_F) \times [R_{AG} \times N_{AG} \times (1 - Frac_{Remove}) + R_{BG} \times N_{BG}]$$

### Default Factors (Grains/Cereals)
- $DRY$ (Dry matter fraction): **0.88**
- $R_{AG}$ (Residue:Yield ratio): Calculated as $(AGDM \times 1000 / Yield)$.
- $N_{AG}$ (N content above-ground): **0.006**
- $R_{BG}$ (Below-ground ratio): **0.22**
- $N_{BG}$ (N content below-ground): **0.009**

---

## 5. Summary Table for Developer Integration

| Variable | Unit | Default Value | Source |
| :--- | :--- | :--- | :--- |
| EF1 | kg N2O-N / kg N | 0.01 | IPCC Table 11.1 |
| EF4 | kg N2O-N / kg N | 0.01 | IPCC Table 11.3 |
| EF5 | kg N2O-N / kg N | 0.0075 | IPCC Table 11.3 |
| FracGASF | kg N / kg N | 0.10 | IPCC Table 11.3 |
| FracLEACH | kg N / kg N | 0.30 | IPCC Table 11.3 |
| GWP_N2O | - | 265 | AR5 |
| GWP_CH4 | - | 28 | AR5 |
| C:N Ratio | - | 15 (Forest to Crop), 10 (Crop) | IPCC Eq 11.8 |
