"""
Mock rainfall adapter — reads a CSV fixture and returns RainfallRecord
objects shaped like the real IMD adapter eventually will.

This is intentional: we don't have IMD API access yet (see
.agents/rules/core-rules.md, section 3), so everything upstream
(risk_engine, GIS layer) is built and tested against this mock first.
Swapping to the real adapter later should require zero changes outside
this file and real_adapter.py, because both implement RainfallAdapter.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from .base import RainfallAdapter, RainfallRecord

DEFAULT_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mock_rainfall_hourly.csv"


class MockRainfallAdapter(RainfallAdapter):
    """Reads rainfall data from a local CSV fixture instead of a live API."""

    def __init__(self, fixture_path: Path = DEFAULT_FIXTURE_PATH):
        self.fixture_path = fixture_path
        self.source_label = "IMD_mock"

    def _load_all_records(self) -> List[RainfallRecord]:
        records: List[RainfallRecord] = []
        with open(self.fixture_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(
                    RainfallRecord(
                        grid_cell_id=row["grid_cell_id"],
                        district=row["district"],
                        state=row["state"],
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        rainfall_mm=float(row["rainfall_mm"]),
                        source_timestamp=datetime.fromisoformat(row["timestamp"]),
                        source=self.source_label,
                    )
                )
        return records

    def fetch_latest(self) -> List[RainfallRecord]:
        """Return the single latest reading per grid cell."""
        all_records = self._load_all_records()
        latest_by_cell = {}
        for rec in all_records:
            existing = latest_by_cell.get(rec.grid_cell_id)
            if existing is None or rec.source_timestamp > existing.source_timestamp:
                latest_by_cell[rec.grid_cell_id] = rec
        return list(latest_by_cell.values())

    def fetch_range(self, start: datetime, end: datetime) -> List[RainfallRecord]:
        """Return all records with source_timestamp within [start, end]."""
        all_records = self._load_all_records()
        return [rec for rec in all_records if start <= rec.source_timestamp <= end]
