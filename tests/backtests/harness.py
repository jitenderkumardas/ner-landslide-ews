"""
Backtest harness — evaluates the existing rainfall risk engine against
synthetic historical-style events.

LEAKAGE PREVENTION (read this before touching the logic below):
For every candidate "as-of" timestamp T we evaluate, we pass
calculate_rainfall_risk() ONLY the records for that grid cell with
source_timestamp <= T. This is enforced by _records_up_to(), which is
the single choke point all rainfall data passes through before
reaching the risk engine. Never call calculate_rainfall_risk() directly
from anywhere else in this module — always go through this function,
or a future edit could accidentally leak post-event data into a
"prediction."

This module does NOT modify services/risk_engine/ in any way — it only
calls the existing, unmodified calculate_rainfall_risk(), per the
Tier 0/1 rule against silently changing risk-engine logic.
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from services.ingestion.rainfall.base import RainfallRecord
from services.risk_engine import Severity, calculate_rainfall_risk
from services.risk_engine.thresholds import DEFAULT_THRESHOLDS, ThresholdSet

from .config import BACKTEST_CONFIG

FIXTURES_DIR = Path(__file__).parent / "fixtures"
RAINFALL_FIXTURE = FIXTURES_DIR / "rainfall_hourly.csv"
EVENTS_FIXTURE = FIXTURES_DIR / "historical_landslides.csv"


@dataclass(frozen=True)
class LandslideEvent:
    event_id: str
    event_timestamp: datetime
    grid_cell_id: str
    latitude: float
    longitude: float
    district: str
    event_type: str
    severity: str
    source: str  # "synthetic_fixture" | "gsi_verified" | etc.


@dataclass(frozen=True)
class BacktestResult:
    event_id: str
    grid_cell_id: str
    event_timestamp: datetime
    warning_time: Optional[datetime]
    lead_time_hours: Optional[float]
    predicted_severity_at_warning: Optional[str]
    detected: bool

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "grid_cell_id": self.grid_cell_id,
            "event_timestamp": self.event_timestamp.isoformat(),
            "warning_time": self.warning_time.isoformat()
            if self.warning_time
            else None,
            "lead_time_hours": self.lead_time_hours,
            "predicted_severity": self.predicted_severity_at_warning,
            "detected": self.detected,
        }


@dataclass(frozen=True)
class EpisodeResult:
    """
    For no-event episodes (false-alarm / true-negative test windows),
    there's no LandslideEvent to attach a BacktestResult to, so we
    track these separately using the grid cell + a label.
    """

    grid_cell_id: str
    had_event: bool
    warning_raised: bool
    outcome: str  # "TP" | "FN" | "FP" | "TN"


def load_backtest_rainfall(path: Path = RAINFALL_FIXTURE) -> List[RainfallRecord]:
    records = []
    with open(path, newline="", encoding="utf-8") as f:
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
                    source="backtest_synthetic",
                )
            )
    return records


def load_events(path: Path = EVENTS_FIXTURE) -> List[LandslideEvent]:
    events = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(
                LandslideEvent(
                    event_id=row["event_id"],
                    event_timestamp=datetime.fromisoformat(row["event_timestamp"]),
                    grid_cell_id=row["grid_cell_id"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    district=row["district"],
                    event_type=row["event_type"],
                    severity=row["severity"],
                    source=row["source"],
                )
            )
    return events


def _group_by_cell(records: List[RainfallRecord]) -> Dict[str, List[RainfallRecord]]:
    grouped: Dict[str, List[RainfallRecord]] = {}
    for r in records:
        grouped.setdefault(r.grid_cell_id, []).append(r)
    for cell_records in grouped.values():
        cell_records.sort(key=lambda r: r.source_timestamp)
    return grouped


def _records_up_to(
    cell_records: List[RainfallRecord], as_of: datetime
) -> List[RainfallRecord]:
    """
    THE leakage-prevention choke point. Returns only records with
    source_timestamp <= as_of. Strictly enforces no-lookahead: nothing
    with a timestamp after `as_of` is ever included.
    """
    return [r for r in cell_records if r.source_timestamp <= as_of]


def find_first_warning(
    cell_records: List[RainfallRecord],
    before: datetime,
    thresholds: ThresholdSet = DEFAULT_THRESHOLDS,
    minimum_warning_level: Severity = BACKTEST_CONFIG["minimum_warning_level"],
) -> Optional[tuple]:
    """
    Walk forward through this grid cell's timestamps strictly before
    `before`, and return (warning_time, severity) for the first
    timestamp at which calculate_rainfall_risk() — called with data
    available only up to that timestamp — reaches minimum_warning_level.

    Returns None if no such timestamp exists (no warning would have
    been raised before `before`).
    """
    candidate_times = sorted(
        {r.source_timestamp for r in cell_records if r.source_timestamp < before}
    )

    for t in candidate_times:
        subset = _records_up_to(cell_records, t)
        if not subset:
            continue
        assessments = calculate_rainfall_risk(subset, thresholds=thresholds)
        # subset is scoped to a single grid cell already, so at most
        # one assessment comes back.
        if not assessments:
            continue
        assessment = assessments[0]
        if assessment.severity >= minimum_warning_level:
            return (t, assessment.severity)

    return None


def evaluate_event(
    event: LandslideEvent,
    all_records_by_cell: Dict[str, List[RainfallRecord]],
    config: dict = BACKTEST_CONFIG,
) -> BacktestResult:
    cell_records = all_records_by_cell.get(event.grid_cell_id, [])
    result = find_first_warning(
        cell_records,
        before=event.event_timestamp,
        minimum_warning_level=config["minimum_warning_level"],
    )

    if result is None:
        return BacktestResult(
            event_id=event.event_id,
            grid_cell_id=event.grid_cell_id,
            event_timestamp=event.event_timestamp,
            warning_time=None,
            lead_time_hours=None,
            predicted_severity_at_warning=None,
            detected=False,
        )

    warning_time, severity = result
    lead_time_hours = (event.event_timestamp - warning_time).total_seconds() / 3600.0
    detected = lead_time_hours <= config["event_tolerance_hours"]

    return BacktestResult(
        event_id=event.event_id,
        grid_cell_id=event.grid_cell_id,
        event_timestamp=event.event_timestamp,
        warning_time=warning_time,
        lead_time_hours=round(lead_time_hours, 2),
        predicted_severity_at_warning=str(severity),
        detected=detected,
    )


def evaluate_no_event_episode(
    grid_cell_id: str,
    all_records_by_cell: Dict[str, List[RainfallRecord]],
    config: dict = BACKTEST_CONFIG,
) -> EpisodeResult:
    """
    For a grid cell/window with no ground-truth event, check whether a
    warning was ever raised anywhere in its data — that's a false
    alarm. No warning raised = true negative.
    """
    cell_records = all_records_by_cell.get(grid_cell_id, [])
    if not cell_records:
        return EpisodeResult(
            grid_cell_id, had_event=False, warning_raised=False, outcome="TN"
        )

    last_timestamp = cell_records[-1].source_timestamp
    # Use "before = last_timestamp + a tick" so the last real reading
    # itself is eligible to be evaluated as a candidate warning time.
    result = find_first_warning(
        cell_records,
        before=last_timestamp + __import__("datetime").timedelta(seconds=1),
        minimum_warning_level=config["minimum_warning_level"],
    )
    warning_raised = result is not None
    return EpisodeResult(
        grid_cell_id=grid_cell_id,
        had_event=False,
        warning_raised=warning_raised,
        outcome="FP" if warning_raised else "TN",
    )


def run_full_backtest(
    rainfall_path: Path = RAINFALL_FIXTURE,
    events_path: Path = EVENTS_FIXTURE,
    no_event_grid_cells: Optional[List[str]] = None,
) -> dict:
    """
    Runs the complete backtest: event-level results for every ground
    truth event, plus episode-level results for specified no-event grid
    cells (false-alarm / true-negative test windows).
    """
    records = load_backtest_rainfall(rainfall_path)
    events = load_events(events_path)
    by_cell = _group_by_cell(records)

    event_grid_cells = {e.grid_cell_id for e in events}
    if no_event_grid_cells is None:
        # anything in the fixture that has no ground-truth event
        no_event_grid_cells = [c for c in by_cell if c not in event_grid_cells]

    event_results = [evaluate_event(e, by_cell) for e in events]
    episode_results = [
        evaluate_no_event_episode(c, by_cell) for c in no_event_grid_cells
    ]

    return {
        "event_results": event_results,
        "episode_results": episode_results,
    }
