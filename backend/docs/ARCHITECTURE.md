# System Architecture

## Data Flow

```
Farmer Input (Voice or Web)
    ↓
[Sarvam STT] (Day 5)
    ↓
[Entity Extraction] - Extract lat, lon, area, crop
    ↓
[FastAPI Router] → /api/v1/plots/estimate
    ↓
[EstimateService] - Main orchestration
    ├→ [GEE SoilGrids Service] (Day 1)
    │  └→ Soil data: clay%, organic_carbon
    ├→ [GEE NDVI Service] (Day 1)
    │  └→ Sentinel-2 time series
    ├→ [Crop Classifier] (Day 2)
    │  └→ NDVI curve matching
    ├→ [Burning Detector] (Day 2)
    │  └→ MODIS thermal analysis
    ├→ [Residue Analyzer] (Day 2)
    │  └→ Post-harvest NDVI trends
    └→ [Carbon Model] (Day 3)
       └→ XGBoost inference
    ↓
[Database] - Store plot & carbon score
    ↓
[Response Formatter]
    ├→ JSON (web)
    └→ Sarvam TTS (voice) (Day 5)
    ↓
Farmer Output (Score + Recommendations)
```

## Technology Stack

### Backend
- **Framework:** FastAPI 0.104+
- **Server:** Uvicorn with async/await
- **Database:** PostgreSQL 15 + PostGIS
- **Cache:** Redis

### Data & ML
- **Satellite:** Google Earth Engine
- **ML Model:** XGBoost
- **Data Processing:** Pandas, NumPy, GeoPandas
- **Feature Engineering:** Scikit-learn

### Voice & Language
- **ASR/TTS:** Sarvam AI
- **NLP:** spaCy (lightweight)

### Deployment
- **Containerization:** Docker
- **Orchestration:** Docker Compose (dev), GCP Cloud Run (prod)
- **CI/CD:** GitHub Actions

## Database Schema

### Tables (MVP)

**plots**
- id (PK)
- phone, lat, lon, area_hectares, crop_type
- metadata (JSON)
- created_at, updated_at

**carbon_scores**
- id (PK)
- plot_id (FK)
- tonnes_co2_per_hectare, total_tonnes_co2, value_inr
- confidence_score, methodology
- breakdown, practices (JSON)
- calculated_at

**feature_cache**
- id (PK)
- coord_hash (unique)
- ndvi_timeseries, evi_timeseries (TEXT/JSON)
- soil_clay, soil_organic_carbon
- burning_detected, residue_score
- cached_at, expires_at

## API Contract

### Request Format
```json
{
  "lat": float (-90 to 90),
  "lon": float (-180 to 180),
  "area_hectares": float (> 0),
  "phone": string (optional),
  "language": string (hi|kn|pa|en)
}
```

### Response Format
```json
{
  "plot_id": int | null,
  "tonnes_co2_per_hectare": float,
  "total_tonnes_co2": float,
  "value_inr": float,
  "confidence_score": float (0-1),
  "methodology": string,
  "breakdown": {
    "crop_type": string,
    "soil_clay_percent": float,
    "soil_organic_carbon": float,
    "ndvi_mean": float,
    "burning_detected": bool,
    "residue_score": float,
    "data_sources": [string]
  },
  "practices": [
    {
      "name": string,
      "current": bool,
      "impact_increase_percent": float,
      "if_implemented_value_inr": float
    }
  ],
  "calculated_at": datetime (ISO 8601)
}
```

## Confidence Intervals

### High Confidence (0.80-1.0)
- Complete satellite data coverage
- Clear crop type detected
- Soil data available

### Medium Confidence (0.60-0.80)
- Partial cloud cover (< 30%)
- Crop type probable (not certain)
- Soil data interpolated

### Low Confidence (0.50-0.60)
- High cloud cover (> 30%)
- Crop type unclear
- Soil data missing (using regional average)

## Performance Targets

- Carbon estimate: < 5 seconds
- GEE data fetch: < 2 seconds
- ML inference: < 100ms
- Voice processing (STT+TTS): < 3 seconds
- Total voice query: < 5 seconds

## Error Handling

- GEE unavailable → Use Verra baseline + adjustments
- Satellite data incomplete → Lower confidence score, still return estimate
- Invalid coordinates → 422 Unprocessable Entity
- Database error → 500 Internal Server Error
- Rate limit exceeded → 429 Too Many Requests

## Security

- Environment variables for secrets
- CORS enabled for web frontend
- Input validation via Pydantic
- Async database queries (no SQL injection)
- Rate limiting (future)

## Monitoring

- Structured JSON logging
- Error tracking via Sentry (optional)
- Metrics: API latency, GEE failures, model accuracy
- Health checks on /health endpoint

