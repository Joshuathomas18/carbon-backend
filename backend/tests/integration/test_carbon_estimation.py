"""Integration tests for carbon estimation pipeline."""

import pytest


@pytest.mark.asyncio
async def test_estimate_carbon_end_to_end():
    """Test full carbon estimation pipeline."""
    from app.services.estimate_service import EstimateService

    service = EstimateService()

    # Test with Haryana wheat farm
    result = await service.estimate_carbon(
        lat=29.0,
        lon=77.5,
        area_hectares=2.5,
    )

    # Assertions
    assert result is not None
    assert "tonnes_co2_per_hectare" in result
    assert result["tonnes_co2_per_hectare"] > 0.5
    assert result["tonnes_co2_per_hectare"] < 5.0
    assert result["total_tonnes_co2"] > 0
    assert result["value_inr"] > 0
    assert 0.5 <= result["confidence_score"] <= 1.0
    assert "wheat" in result["breakdown"]["crop_type"].lower()
    assert len(result["practices"]) > 0


@pytest.mark.asyncio
async def test_voice_query_hindi():
    """Test voice query in Hindi."""
    from app.api.v1.routes import voice_query, VoiceQueryRequest

    request = VoiceQueryRequest(
        audio_base64="mock_audio_data",
        language="hi",
    )

    response = await voice_query(request)

    assert response.transcribed_text
    assert response.response_text
    assert "namaste" in response.response_text.lower() or "carbon" in response.response_text.lower()


@pytest.mark.asyncio
async def test_entity_extraction():
    """Test entity extraction from voice queries."""
    from app.services.entity_extractor import EntityExtractor

    extractor = EntityExtractor()

    # Test Hindi query
    entities = extractor.extract_entities(
        "mere paas 5 acres sugarcane hai mandya mein, aur maine burning band kar di",
        language="hi",
    )

    assert entities["area_hectares"] is not None
    assert 1.5 < entities["area_hectares"] < 3.0  # 5 acres ≈ 2 hectares
    assert "sugarcane" in entities["crop_type"].lower()
    assert "mandya" in (entities["location"] or "").lower() or entities["location"] == "Karnataka"
    assert entities["overall_confidence"] > 0.5


@pytest.mark.asyncio
async def test_crop_classification():
    """Test crop type classification from NDVI."""
    from app.services.crop_classifier import CropClassifier

    classifier = CropClassifier()

    # Mock wheat NDVI: single peak in Feb-Mar
    wheat_ndvi = [
        0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.65, 0.68, 0.72, 0.70, 0.6, 0.4, 0.2
    ]

    crop, confidence = classifier.classify(wheat_ndvi)

    assert crop in ["wheat", "unknown"]
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_burning_detection():
    """Test burning detection from NDVI."""
    from app.services.burning_detector import BurningDetector

    detector = BurningDetector()

    # Mock NDVI with sharp drop (harvest) + high variance (burning)
    ndvi_with_burning = [
        0.6, 0.7, 0.72, 0.7, 0.2, 0.25, 0.15, 0.1, 0.2, 0.1, 0.3, 0.4, 0.5
    ]

    result = await detector.detect_burning(28.5, 77.2, ndvi_with_burning)

    assert "burning_detected" in result
    assert "num_events" in result
    assert result["confidence"] > 0.5


@pytest.mark.asyncio
async def test_residue_analysis():
    """Test residue management inference."""
    from app.services.residue_analyzer import ResidueAnalyzer

    analyzer = ResidueAnalyzer()

    # NDVI with quick recovery after harvest = residue retained
    ndvi_with_retained = [
        0.6, 0.7, 0.72, 0.7, 0.2, 0.45, 0.55, 0.6, 0.62, 0.6, 0.5, 0.4, 0.5
    ]

    result = analyzer.analyze_residue_management(ndvi_with_retained)

    assert "residue_score" in result
    assert 0.0 <= result["residue_score"] <= 1.0
    assert result["confidence"] >= 0.0


def test_api_health_endpoint(client):
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_api_root_endpoint(client):
    """Test root / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_api_carbon_estimate(client):
    """Test carbon estimation via API."""
    response = client.post(
        "/api/v1/plots/estimate",
        json={
            "lat": 28.5,
            "lon": 77.2,
            "area_hectares": 2.5,
            "language": "hi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "tonnes_co2_per_hectare" in data
    assert "value_inr" in data
    assert "practices" in data
