"""Contract tests for the static GIS dashboard (services/gis_dashboard/index.html).

Validates static contract integrity between the Leaflet frontend and the
FastAPI /risk-assessments backend without requiring browser automation or network access.
"""

from pathlib import Path

DASHBOARD_PATH = (
    Path(__file__).parent.parent.parent / "services" / "gis_dashboard" / "index.html"
)


def test_dashboard_file_exists_and_non_empty():
    """Confirms the dashboard HTML file exists at the expected location and has content."""
    assert DASHBOARD_PATH.is_file(), f"Dashboard not found at {DASHBOARD_PATH}"
    assert DASHBOARD_PATH.stat().st_size > 0


def test_dashboard_contains_mock_disclaimer():
    """Confirms the dashboard contains the mandatory pre-pilot mock banner."""
    content = DASHBOARD_PATH.read_text(encoding="utf-8")
    assert "PRE-PILOT" in content.upper()
    assert "MOCK" in content.upper()


def test_dashboard_targets_expected_api_endpoint():
    """Validates that the dashboard references the correct API endpoint.

    Ensures that /risk-assessments is present and that no outdated or hallucinated
    endpoints (e.g., /risk_assessments or /alerts) are being queried.
    """
    content = DASHBOARD_PATH.read_text(encoding="utf-8")

    # Confirms presence of the real endpoint
    assert "/risk-assessments" in content

    # Detects accidental drift to snake_case or unreleased endpoints
    assert "/risk_assessments" not in content
    assert "/api/v1" not in content


def test_dashboard_references_required_assessment_fields():
    """Confirms that JavaScript code in index.html references the API contract fields."""
    content = DASHBOARD_PATH.read_text(encoding="utf-8")

    expected_fields = [
        "grid_cell_id",
        "latitude",
        "longitude",
        "severity",
        "district",
        "state",
        "cumulative_rainfall_mm",
        "window_hours",
        "threshold_version",
    ]

    for field in expected_fields:
        assert (
            field in content
        ), f"Dashboard contract missing reference to field '{field}'"


def test_dashboard_contains_leaflet_initialization():
    """Confirms standard Leaflet map and layer initialization are present."""
    content = DASHBOARD_PATH.read_text(encoding="utf-8")

    assert "L.map" in content
    assert "L.tileLayer" in content
    assert "L.circleMarker" in content
