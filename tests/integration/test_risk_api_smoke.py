"""Integration smoke test for the rainfall risk API pipeline.

Validates the in-process data flow:
    MockRainfallAdapter -> calculate_rainfall_risk() -> FastAPI /risk-assessments

Checks response structure, required attributes, severity value constraints,
pre-pilot mock disclaimers, and district filtering contracts.
"""

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)

ALLOWED_SEVERITIES = {"GREEN", "YELLOW", "ORANGE", "RED"}


def test_risk_assessments_pipeline_smoke():
    """End-to-end smoke test validating the complete in-process pipeline.

    Fetches risk assessments and confirms the response schema, presence of
    geographic coordinates, allowed severity values, and the mandatory
    pre-pilot mock disclaimer.
    """
    response = client.get("/risk-assessments")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)

    # Top-level contract validation
    assert "disclaimer" in data
    assert "PRE-PILOT" in data["disclaimer"].upper()
    assert "MOCK" in data["disclaimer"].upper()
    assert "count" in data
    assert "assessments" in data
    assert "threshold_version" in data

    assessments = data["assessments"]
    assert isinstance(assessments, list)
    assert len(assessments) == data["count"]
    assert len(assessments) > 0

    # Record-level contract and geographic sanity
    for record in assessments:
        assert "grid_cell_id" in record
        assert (
            isinstance(record["grid_cell_id"], str) and record["grid_cell_id"].strip()
        )

        assert "latitude" in record
        assert isinstance(record["latitude"], (int, float))

        assert "longitude" in record
        assert isinstance(record["longitude"], (int, float))

        assert "severity" in record
        assert record["severity"] in ALLOWED_SEVERITIES

        assert "district" in record
        assert "state" in record
        assert "cumulative_rainfall_mm" in record
        assert "window_hours" in record
        assert "threshold_version" in record

        # Consistency check: record threshold version matches top-level version
        assert record["threshold_version"] == data["threshold_version"]


def test_risk_assessments_district_filter_smoke():
    """Validates that district filtering returns only matching records."""
    target_district = "East Khasi Hills"
    response = client.get("/risk-assessments", params={"district": target_district})
    assert response.status_code == 200

    data = response.json()
    assert data["count"] > 0
    assert len(data["assessments"]) == data["count"]

    for record in data["assessments"]:
        assert record["district"].lower() == target_district.lower()


def test_risk_assessments_empty_district_contract():
    """Validates contract behavior when a district filter yields no records.

    Ensures the API returns HTTP 200 with an empty list and 0 count,
    retaining the mandatory pre-pilot disclaimer.
    """
    response = client.get(
        "/risk-assessments", params={"district": "Nonexistent District 999"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 0
    assert data["assessments"] == []
    assert data["threshold_version"] is None
    assert "disclaimer" in data
    assert "PRE-PILOT" in data["disclaimer"].upper()
