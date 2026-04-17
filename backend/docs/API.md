# Carbon Backend API Reference

## Base URL

```
/api/v1
```

## Endpoints

### Health Check

**GET** `/health`

Returns service status.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-04-15T10:30:00Z",
  "gee_available": true,
  "sarvam_available": true
}
```

### Carbon Estimate

**POST** `/plots/estimate`

Estimate carbon sequestration for a plot.

**Request:**
```json
{
  "lat": 28.5,
  "lon": 77.2,
  "area_hectares": 2.5,
  "phone": "9876543210",
  "language": "hi"
}
```

**Response:**
```json
{
  "plot_id": 1,
  "tonnes_co2_per_hectare": 1.85,
  "total_tonnes_co2": 4.625,
  "value_inr": 185,
  "confidence_score": 0.82,
  "methodology": "Verra VM0042 v2.0 + Sentinel-2",
  "breakdown": {...},
  "practices": [...],
  "calculated_at": "2026-04-15T10:30:00Z"
}
```

### Carbon History

**GET** `/plots/{plot_id}/history`

Get historical carbon scores (Day 4+).

### Practice Recommendations

**GET** `/plots/{plot_id}/practices`

Get practice recommendations (Day 4+).

### Voice Query

**POST** `/voice/query`

Process voice query from farmer (Day 5).

