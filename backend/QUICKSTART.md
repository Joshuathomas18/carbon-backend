# Carbon Backend MVP - Quick Start

**Status: ✅ MVP Ready**

## What is This?

Carbon Backend is a **Verra VM0042-compliant, satellite-based carbon scoring system** for smallholder farmers in India.

**In 90 seconds:**
1. Farmer says: *"I have 5 acres of sugarcane in Mandya"*
2. System analyzes satellite data (NDVI, thermal, soil)
3. Returns: *"Your carbon worth ₹8,100. Stop burning to earn ₹1,215 more."*

## Features

✅ **Verra-Compliant Carbon Estimates** - Baseline data + practice adjustments  
✅ **Real Satellite Data** - Sentinel-2 NDVI, MODIS thermal, SoilGrids  
✅ **ML Predictions** - XGBoost trained on 25 verified Verra projects  
✅ **Voice Interface** - Hindi, Kannada, Punjabi, English (Sarvam AI)  
✅ **Web API** - REST endpoints for web/mobile  
✅ **Practice Recommendations** - Burning, residue retention, cover crops  

## 5-Minute Setup

### Option 1: Docker (Recommended)

```bash
# Clone repo
git clone https://github.com/Joshuathomas18/carbon-backend.git
cd carbon-backend

# Setup environment
cp .env.example .env

# Start (automatically pulls images, creates DB, starts services)
docker-compose up -d

# Wait 30 seconds for database to initialize
sleep 30

# Test it
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/plots/estimate \
  -H "Content-Type: application/json" \
  -d '{"lat": 28.5, "lon": 77.2, "area_hectares": 2}'

# View API docs
open http://localhost:8000/docs
```

### Option 2: Python (Local)

```bash
# Clone repo
git clone https://github.com/Joshuathomas18/carbon-backend.git
cd carbon-backend

# Setup Python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start services (PostgreSQL + Redis must be running)
# On macOS: brew services start postgresql && brew services start redis
# On Linux: sudo systemctl start postgresql && sudo systemctl start redis-server

# Run app
uvicorn app.main:app --reload

# Test at http://localhost:8000/docs
```

## Quick API Examples

### 1. Carbon Estimate (REST)

```bash
curl -X POST http://localhost:8000/api/v1/plots/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 29.0,
    "lon": 77.5,
    "area_hectares": 2.5,
    "language": "hi"
  }'
```

**Response:**
```json
{
  "tonnes_co2_per_hectare": 1.85,
  "total_tonnes_co2": 4.63,
  "value_inr": 185,
  "confidence_score": 0.82,
  "breakdown": {
    "crop_type": "wheat",
    "soil_clay_percent": 30,
    "burning_detected": false,
    "residue_score": 0.75
  },
  "practices": [
    {
      "name": "Stop stubble burning",
      "impact_increase_percent": 15,
      "if_implemented_value_inr": 28
    }
  ]
}
```

### 2. Voice Query (Hindi)

```bash
# Create mock audio (in real app, send actual WAV/MP3)
curl -X POST http://localhost:8000/api/v1/voice/query \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "mock_audio_data",
    "language": "hi"
  }'
```

**Response:**
```json
{
  "transcribed_text": "mere 5 acres sugarcane hai...",
  "response_text": "Namaste! Carbon ₹8,100 ke barabar hai. Burning band karne se...",
  "response_audio_base64": "...",
  "carbon_estimate": {
    "tonnes_co2_per_hectare": 1.62,
    "value_inr": 324
  }
}
```

### 3. Health Check

```bash
curl http://localhost:8000/health

# Response
{
  "status": "ok",
  "timestamp": "2026-04-15T10:30:00Z",
  "gee_available": true,
  "sarvam_available": true
}
```

## How It Works

```
Voice Input (Hindi/Kannada)
    ↓
[Sarvam STT] → Transcribe to text
    ↓
[Entity Extractor] → Extract area, crop, location, practices
    ↓
[EstimateService] Main orchestration:
    ├→ [GEE SoilGrids] → Soil properties (clay%, organic carbon)
    ├→ [GEE Sentinel-2] → NDVI time series (3 years)
    ├→ [Crop Classifier] → Detect crop from NDVI curve
    ├→ [Burning Detector] → MODIS thermal analysis
    ├→ [Residue Analyzer] → Post-harvest trends
    └→ [XGBoost] → Carbon prediction
    ↓
[Feature Engineer] → Apply practice adjustments
    ↓
[Carbon Score + Recommendations]
    ↓
[Sarvam TTS] → Synthesize response to speech
    ↓
Voice Response (Hindi/Kannada)
```

## Data Sources

| Component | Source | Resolution | Update |
|-----------|--------|-----------|--------|
| Vegetation (NDVI) | Sentinel-2 | 10m | Weekly |
| Temperature | MODIS | 1km | Daily |
| Soil Data | SoilGrids | 250m | Quarterly |
| Baselines | Verra Registry | Point | Static |
| Recommendations | Rule-based + ML | - | Static |

## Architecture

- **Backend:** FastAPI (async Python)
- **ML:** XGBoost trained on 25 Verra projects
- **Database:** PostgreSQL + PostGIS (geospatial)
- **Cache:** Redis (satellite data, responses)
- **Voice:** Sarvam AI (ASR, TTS)
- **Satellite:** Google Earth Engine

## Testing

```bash
# Run all tests
pytest -v

# Run specific test
pytest tests/unit/test_health.py -v

# With coverage
pytest --cov=app --cov-report=html
```

## Deployment

```bash
# Production with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# GCP Cloud Run
gcloud run deploy carbon-backend --image gcr.io/YOUR_PROJECT/carbon-backend

# See docs/DEPLOYMENT.md for full guide
```

## Environment Variables

Required (`.env`):
```
DATABASE_URL=postgresql://user:pass@localhost:5432/carbon_db
REDIS_URL=redis://localhost:6379/0
GEE_PROJECT_ID=your-gee-project-id  # Optional: uses mock data if not set
SARVAM_API_KEY=your-sarvam-key      # Optional: uses mock responses if not set
```

Optional:
```
ENVIRONMENT=development|production
DEBUG=true|false
LOG_LEVEL=INFO|DEBUG
SECRET_KEY=your-secret-key
```

## Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # FastAPI

# Kill and restart
docker-compose down
docker-compose up -d
```

### Database errors
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### API returning 500
```bash
# Check logs
docker-compose logs fastapi
docker-compose logs postgres
```

## API Documentation

**Interactive Docs:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc  
**OpenAPI JSON:** http://localhost:8000/openapi.json

## Next Steps

1. **Local Testing:** Run MVP locally, test carbon estimates
2. **Farmer Testing:** Share voice query feature with 5-10 farmers
3. **Data Collection:** Gather feedback on accuracy vs. ground truth
4. **Deployment:** Deploy to production (GCP Cloud Run recommended)
5. **Phase 2:** Add FPO dashboard + portfolio aggregation

## Timeline

- **Day 1:** ✅ Verra baseline data + GEE integration
- **Day 2:** ✅ Crop classification + burning detection
- **Day 3:** ✅ ML model training (XGBoost)
- **Day 4:** ✅ API integration
- **Day 5:** ✅ Sarvam voice interface
- **Day 6:** ✅ Integration tests
- **Day 7:** ✅ Deployment setup

**Total:** Verra-compliant, production-ready MVP in 7 days

## Support

- GitHub Issues: https://github.com/Joshuathomas18/carbon-backend/issues
- Docs: See `/docs` folder
- Architecture: Read `docs/ARCHITECTURE.md`
- API Reference: Read `docs/API.md`

## License

MIT

---

**Built with ❤️ for Indian farmers**  
*Verra VM0042 Compliant | Sarvam Voice | Google Earth Engine*
