# Carbon Backend - MVP

**Carbon Sequestration Estimation for Indian Smallholder Farmers**

A Verra VM0042-compliant, satellite-based system for estimating carbon sequestration on farm plots using Google Earth Engine, XGBoost ML models, and Sarvam voice interface.

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Google Earth Engine account
- Sarvam API key

### Local Development (Docker)

```bash
# Clone and enter project
git clone https://github.com/Joshuathomas18/carbon-backend.git
cd carbon-backend

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start services (PostgreSQL, Redis, FastAPI)
docker-compose up --build

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## 7-Day Sprint

**Status: Day 1 - Project scaffolding ✅**

### Timeline
- **Day 1:** Verra compliance + satellite data foundation (TODAY)
- **Day 2:** Satellite feature engineering
- **Day 3:** ML model training
- **Day 4:** API scaffolding & integration
- **Day 5:** Sarvam voice integration
- **Day 6:** Integration testing
- **Day 7:** Deployment & demo

## Key Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Carbon estimate
curl -X POST http://localhost:8000/api/v1/plots/estimate \
  -H "Content-Type: application/json" \
  -d '{"lat": 28.5, "lon": 77.2, "area_hectares": 2}'

# API docs
open http://localhost:8000/docs
```

## Documentation

- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- [GEE Integration](docs/GEE_GUIDE.md)

## Contributing

See individual file headers and docstrings for implementation details.

## License

MIT
