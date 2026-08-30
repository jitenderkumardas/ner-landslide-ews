from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_risk_assessments_returns_five_grid_cells():
    response = client.get("/risk-assessments")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5
    assert len(data["assessments"]) == 5


def test_risk_assessments_includes_disclaimer():
    response = client.get("/risk-assessments")
    data = response.json()
    assert "PRE-PILOT MOCK DATA" in data["disclaimer"]


def test_risk_assessments_district_filter():
    response = client.get("/risk-assessments", params={"district": "East Khasi Hills"})
    data = response.json()
    assert data["count"] == 5  # all fixture cells are in this district


def test_risk_assessments_unknown_district_returns_empty():
    response = client.get(
        "/risk-assessments", params={"district": "Nonexistent District"}
    )
    data = response.json()
    assert data["count"] == 0
    assert data["assessments"] == []


def test_risk_assessments_shape_matches_model():
    response = client.get("/risk-assessments")
    data = response.json()
    first = data["assessments"][0]
    assert set(first.keys()) == {
        "grid_cell_id",
        "district",
        "state",
        "latitude",
        "longitude",
        "severity",
        "cumulative_rainfall_mm",
        "window_hours",
        "window_end",
        "threshold_version",
        "computed_at",
    }
    assert first["severity"] in {"GREEN", "YELLOW", "ORANGE", "RED"}
