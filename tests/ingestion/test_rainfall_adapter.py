"""
Tests for the mock rainfall adapter.

These tests exist to catch exactly the failure modes flagged in
.agents/rules/core-rules.md: missing provenance fields, and any future
change that silently breaks the mock/real adapter contract.
"""

from datetime import datetime, timezone

import pytest

from services.ingestion.rainfall import (
    MockRainfallAdapter,
    RainfallRecord,
    get_rainfall_adapter,
)


@pytest.fixture
def adapter() -> MockRainfallAdapter:
    return MockRainfallAdapter()


def test_fetch_latest_returns_one_record_per_grid_cell(adapter):
    records = adapter.fetch_latest()
    grid_cells = [r.grid_cell_id for r in records]
    assert len(grid_cells) == len(
        set(grid_cells)
    ), "fetch_latest should return exactly one record per grid cell"
    assert len(records) == 5  # 5 grid cells in the fixture


def test_fetch_latest_picks_the_most_recent_timestamp(adapter):
    records = adapter.fetch_latest()
    rec = next(r for r in records if r.grid_cell_id == "GRID-EKH-005")
    # fixture's last row for GRID-EKH-005 is 03:00 with 31.4mm
    assert rec.rainfall_mm == 31.4


def test_every_record_has_required_provenance_fields(adapter):
    records = adapter.fetch_latest()
    for rec in records:
        assert rec.source == "IMD_mock"
        assert rec.source_timestamp is not None
        assert rec.ingestion_timestamp is not None
        assert rec.transformation_version == "v1"


def test_fetch_range_filters_correctly(adapter):
    start = datetime.fromisoformat("2026-06-14T01:00:00+05:30")
    end = datetime.fromisoformat("2026-06-14T02:00:00+05:30")
    records = adapter.fetch_range(start, end)
    # 5 grid cells x 2 hourly readings (01:00, 02:00) = 10 records
    assert len(records) == 10
    for rec in records:
        assert start <= rec.source_timestamp <= end


def test_negative_rainfall_is_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        RainfallRecord(
            grid_cell_id="GRID-TEST",
            district="Test District",
            state="Test State",
            latitude=25.0,
            longitude=91.0,
            rainfall_mm=-5.0,
            source_timestamp=datetime.now(timezone.utc),
            source="unit_test",
        )


def test_invalid_latitude_is_rejected():
    with pytest.raises(ValueError, match="invalid latitude"):
        RainfallRecord(
            grid_cell_id="GRID-TEST",
            district="Test District",
            state="Test State",
            latitude=200.0,
            longitude=91.0,
            rainfall_mm=5.0,
            source_timestamp=datetime.now(timezone.utc),
            source="unit_test",
        )


def test_factory_defaults_to_mock_when_env_unset(monkeypatch):
    monkeypatch.delenv("USE_MOCK_ADAPTERS", raising=False)
    result = get_rainfall_adapter()
    assert isinstance(result, MockRainfallAdapter)


def test_factory_returns_mock_when_explicitly_set(monkeypatch):
    monkeypatch.setenv("USE_MOCK_ADAPTERS", "true")
    result = get_rainfall_adapter()
    assert isinstance(result, MockRainfallAdapter)


def test_factory_raises_clear_error_for_real_adapter_without_credentials(
    monkeypatch,
):
    monkeypatch.setenv("USE_MOCK_ADAPTERS", "false")
    monkeypatch.delenv("IMD_API_KEY", raising=False)
    monkeypatch.delenv("IMD_API_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="requires IMD_API_BASE_URL"):
        get_rainfall_adapter()
