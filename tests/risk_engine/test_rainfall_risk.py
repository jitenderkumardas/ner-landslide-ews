"""
Tests for the first-pass rainfall risk engine.

Expected values below are computed by hand from
services/ingestion/rainfall/fixtures/mock_rainfall_hourly.csv — a
3-hour trailing sum ending at each grid cell's last reading (03:00):

GRID-EKH-001: 3.1 + 5.6 + 8.2  = 16.9  -> YELLOW (>=15, <25)
GRID-EKH-002: 4.0 + 9.5 + 14.7 = 28.2  -> ORANGE (>=25, <40)
GRID-EKH-003: 6.2 + 11.0 + 19.3 = 36.5 -> ORANGE
GRID-EKH-004: 5.4 + 10.8 + 22.6 = 38.8 -> ORANGE
GRID-EKH-005: 9.8 + 18.2 + 31.4 = 59.4 -> RED (>=40)

If you change the fixture CSV, these expected values must be recomputed
by hand too — don't just update them to whatever the code outputs.
"""

import pytest

from services.ingestion.rainfall import MockRainfallAdapter
from services.risk_engine import Severity, calculate_rainfall_risk
from services.risk_engine.thresholds import ThresholdSet


@pytest.fixture
def all_rainfall_records():
    adapter = MockRainfallAdapter()
    return adapter.fetch_range(
        start=__import__("datetime").datetime.fromisoformat(
            "2026-06-14T00:00:00+05:30"
        ),
        end=__import__("datetime").datetime.fromisoformat("2026-06-14T03:00:00+05:30"),
    )


@pytest.fixture
def assessments(all_rainfall_records):
    return calculate_rainfall_risk(all_rainfall_records)


def test_one_assessment_per_grid_cell(assessments):
    assert len(assessments) == 5


def test_expected_cumulative_and_severity_per_cell(assessments):
    expected = {
        "GRID-EKH-001": (16.9, Severity.YELLOW),
        "GRID-EKH-002": (28.2, Severity.ORANGE),
        "GRID-EKH-003": (36.5, Severity.ORANGE),
        "GRID-EKH-004": (38.8, Severity.ORANGE),
        "GRID-EKH-005": (59.4, Severity.RED),
    }
    by_cell = {a.grid_cell_id: a for a in assessments}

    for grid_cell_id, (expected_mm, expected_severity) in expected.items():
        actual = by_cell[grid_cell_id]
        assert (
            actual.cumulative_rainfall_mm == pytest.approx(expected_mm, abs=0.01)
        ), f"{grid_cell_id}: expected {expected_mm}mm, got {actual.cumulative_rainfall_mm}"
        assert actual.severity == expected_severity, (
            f"{grid_cell_id}: expected {expected_severity}, "
            f"got {actual.severity} (cumulative={actual.cumulative_rainfall_mm}mm)"
        )


def test_severity_ordering_matches_rainfall_intensity(assessments):
    """The corridor's wettest cell (closest to Sohra) should be highest severity."""
    by_cell = {a.grid_cell_id: a for a in assessments}
    assert by_cell["GRID-EKH-005"].severity > by_cell["GRID-EKH-001"].severity


def test_threshold_version_is_recorded_on_every_assessment(assessments):
    for a in assessments:
        assert a.threshold_version == "rainfall-threshold-v0.1-placeholder"


def test_custom_thresholds_are_respected():
    """A stricter threshold set should push GRID-EKH-001 up to ORANGE."""
    strict = ThresholdSet(yellow_mm=5.0, orange_mm=10.0, red_mm=20.0)
    adapter = MockRainfallAdapter()
    from datetime import datetime

    records = adapter.fetch_range(
        datetime.fromisoformat("2026-06-14T00:00:00+05:30"),
        datetime.fromisoformat("2026-06-14T03:00:00+05:30"),
    )
    results = calculate_rainfall_risk(records, thresholds=strict)
    by_cell = {a.grid_cell_id: a for a in results}
    # 16.9mm with yellow=5/orange=10/red=20 lands in ORANGE (>=10, <20)
    assert by_cell["GRID-EKH-001"].severity == Severity.ORANGE


def test_empty_input_returns_empty_list():
    assert calculate_rainfall_risk([]) == []


def test_as_dict_serialization_shape(assessments):
    d = assessments[0].as_dict()
    assert set(d.keys()) == {
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
    assert isinstance(d["severity"], str)
