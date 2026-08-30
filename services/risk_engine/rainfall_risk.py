"""
Rainfall-based risk calculation — first pass.

Takes RainfallRecord objects (from services.ingestion.rainfall) grouped
by grid cell, sums rainfall over a trailing window, and classifies each
grid cell's severity using the placeholder thresholds in thresholds.py.

This is intentionally the simplest possible rule (cumulative rainfall
threshold) — it does NOT yet account for soil moisture, slope,
susceptibility mapping, or antecedent-rainfall decay, all of which are
in the Phase 3 design as separate fusion inputs. This module is the
rainfall trigger signal only.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from services.ingestion.rainfall.base import RainfallRecord

from .models import RiskAssessment
from .thresholds import (
    DEFAULT_THRESHOLDS,
    THRESHOLD_VERSION,
    WINDOW_HOURS,
    ThresholdSet,
)


def _group_by_grid_cell(
    records: List[RainfallRecord],
) -> Dict[str, List[RainfallRecord]]:
    grouped: Dict[str, List[RainfallRecord]] = defaultdict(list)
    for rec in records:
        grouped[rec.grid_cell_id].append(rec)
    for cell_records in grouped.values():
        cell_records.sort(key=lambda r: r.source_timestamp)
    return grouped


def _cumulative_rainfall(
    cell_records: List[RainfallRecord],
    window_end: datetime,
    window_hours: int,
) -> float:
    """
    Sum rainfall strictly after (window_end - window_hours) and up to
    and including window_end. With hourly readings and a 3-hour window
    ending at T, this includes the readings at T, T-1h, T-2h (three
    readings), excluding T-3h — matching a trailing N-hour accumulation.
    """
    window_start = window_end - timedelta(hours=window_hours)
    return sum(
        r.rainfall_mm
        for r in cell_records
        if window_start < r.source_timestamp <= window_end
    )


def calculate_rainfall_risk(
    records: List[RainfallRecord],
    thresholds: ThresholdSet = DEFAULT_THRESHOLDS,
    window_hours: int = WINDOW_HOURS,
) -> List[RiskAssessment]:
    """
    Compute a RiskAssessment per grid cell, using the latest available
    timestamp in that cell's records as the window end.
    """
    grouped = _group_by_grid_cell(records)
    computed_at = datetime.now(timezone.utc)
    assessments: List[RiskAssessment] = []

    for grid_cell_id, cell_records in grouped.items():
        if not cell_records:
            continue
        window_end = cell_records[-1].source_timestamp
        cumulative = _cumulative_rainfall(cell_records, window_end, window_hours)
        severity = thresholds.classify(cumulative)
        latest = cell_records[-1]

        assessments.append(
            RiskAssessment(
                grid_cell_id=grid_cell_id,
                district=latest.district,
                state=latest.state,
                latitude=latest.latitude,
                longitude=latest.longitude,
                severity=severity,
                cumulative_rainfall_mm=cumulative,
                window_hours=window_hours,
                window_end=window_end,
                threshold_version=THRESHOLD_VERSION,
                computed_at=computed_at,
            )
        )

    return assessments
