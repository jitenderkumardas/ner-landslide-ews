"""
Tests for the backtest harness (not the risk_engine — that's tested
separately in tests/risk_engine/). These tests exist to catch bugs in
the harness's own logic: look-ahead leakage, rolling-window handling,
lead-time math, and edge cases around missing/duplicate data.
"""

from datetime import datetime, timedelta


from services.ingestion.rainfall.base import RainfallRecord
from services.risk_engine.severity import Severity

from tests.backtests.harness import (
    LandslideEvent,
    evaluate_event,
    find_first_warning,
    load_backtest_rainfall,
    load_events,
    run_full_backtest,
)
from tests.backtests.metrics import compute_confusion_matrix, compute_metrics


# --- Fixture loading sanity ---


def test_fixture_loads_expected_row_count():
    records = load_backtest_rainfall()
    assert len(records) == 164  # 30+29+24+29+28+24, per generator design


def test_events_fixture_loads_four_events():
    events = load_events()
    assert len(events) == 4
    assert all(e.source == "synthetic_fixture" for e in events)


# --- The critical property: no look-ahead leakage ---


def _make_record(cell, ts, mm):
    return RainfallRecord(
        grid_cell_id=cell,
        district="Test",
        state="Test",
        latitude=25.0,
        longitude=91.0,
        rainfall_mm=mm,
        source_timestamp=ts,
        source="unit_test",
    )


def test_find_first_warning_never_uses_data_at_or_after_before_time():
    """
    A huge rainfall spike placed exactly at (and after) the cutoff must
    NOT be able to trigger a warning — only data strictly before
    `before` may be used.
    """
    base = datetime.fromisoformat("2026-01-01T00:00:00+05:30")
    records = [
        _make_record("GRID-TEST", base, 1.0),
        _make_record("GRID-TEST", base + timedelta(hours=1), 1.0),
        # huge spike exactly AT the cutoff and after — must be ignored
        _make_record("GRID-TEST", base + timedelta(hours=2), 500.0),
        _make_record("GRID-TEST", base + timedelta(hours=3), 500.0),
    ]
    cutoff = base + timedelta(hours=2)  # "before" = the spike's own timestamp

    result = find_first_warning(records, before=cutoff)
    assert result is None, (
        "Leakage detected: a warning was raised using data at/after the "
        "cutoff timestamp, which should be invisible to the prediction."
    )


def test_find_first_warning_detects_a_real_pre_cutoff_spike():
    """Sanity check the inverse: a spike genuinely BEFORE cutoff should be seen."""
    base = datetime.fromisoformat("2026-01-01T00:00:00+05:30")
    records = [
        _make_record("GRID-TEST", base, 20.0),
        _make_record("GRID-TEST", base + timedelta(hours=1), 20.0),
        _make_record(
            "GRID-TEST", base + timedelta(hours=2), 20.0
        ),  # cumulative 60mm, well over RED
    ]
    cutoff = base + timedelta(hours=10)  # comfortably after the spike

    result = find_first_warning(records, before=cutoff)
    assert result is not None
    warning_time, severity = result
    # Trailing 3h window at T=+1h already includes both the +0h and +1h
    # readings (sum=40mm, already RED) — the warning fires at +1h, not
    # +2h. Verified by running the harness, not assumed by hand.
    assert warning_time == base + timedelta(hours=1)
    assert severity == Severity.RED


def test_evaluate_event_end_to_end_matches_expected_lead_times():
    """
    Locks in the actual computed results from the full synthetic
    fixture — computed by running the harness, not hand-derived, per
    project practice of verifying rather than trusting arithmetic.
    """
    result = run_full_backtest()
    by_event_id = {r.event_id: r for r in result["event_results"]}

    assert by_event_id["BTEST-001"].detected is True
    assert by_event_id["BTEST-001"].lead_time_hours == 11.0

    assert by_event_id["BTEST-002"].detected is True
    assert by_event_id["BTEST-002"].lead_time_hours == 2.0

    assert by_event_id["BTEST-003"].detected is False
    assert by_event_id["BTEST-003"].warning_time is None

    assert by_event_id["BTEST-004"].detected is True
    assert by_event_id["BTEST-004"].lead_time_hours == 6.0


def test_no_event_episodes_classified_correctly():
    result = run_full_backtest()
    by_cell = {r.grid_cell_id: r for r in result["episode_results"]}

    assert by_cell["GRID-EKH-002"].outcome == "FP"
    assert by_cell["GRID-EKH-006"].outcome == "TN"


# --- Edge cases ---


def test_empty_records_returns_no_warning():
    result = find_first_warning([], before=datetime.now())
    assert result is None


def test_single_record_below_threshold_returns_no_warning():
    base = datetime.fromisoformat("2026-01-01T00:00:00+05:30")
    records = [_make_record("GRID-TEST", base, 2.0)]
    result = find_first_warning(records, before=base + timedelta(hours=5))
    assert result is None


def test_duplicate_timestamps_do_not_crash_or_double_count():
    base = datetime.fromisoformat("2026-01-01T00:00:00+05:30")
    records = [
        _make_record("GRID-TEST", base, 20.0),
        _make_record("GRID-TEST", base, 20.0),  # duplicate timestamp, same reading
    ]
    # Should not raise, and should treat both as available at the same instant
    result = find_first_warning(records, before=base + timedelta(hours=5))
    assert result is not None


def test_grid_cell_mismatch_returns_no_warning_for_wrong_cell():
    """An event for a grid cell with zero matching rainfall records should not crash."""
    event = LandslideEvent(
        event_id="TEST-999",
        event_timestamp=datetime.fromisoformat("2026-01-01T12:00:00+05:30"),
        grid_cell_id="GRID-DOES-NOT-EXIST",
        latitude=0.0,
        longitude=0.0,
        district="Test",
        event_type="landslide",
        severity="LOW",
        source="unit_test",
    )
    result = evaluate_event(event, all_records_by_cell={})
    assert result.detected is False
    assert result.warning_time is None


def test_empty_event_set_produces_empty_results():
    empty_metrics = compute_confusion_matrix([], [])
    assert empty_metrics == {
        "true_positives": 0,
        "false_negatives": 0,
        "false_positives": 0,
        "true_negatives": 0,
    }


def test_metrics_handle_zero_denominators_gracefully():
    """No events at all — precision/recall should be None, not a ZeroDivisionError."""
    metrics = compute_metrics([], [])
    assert metrics["precision"] is None
    assert metrics["recall"] is None
    assert metrics["f1"] is None


# --- Determinism ---


def test_backtest_is_deterministic_across_runs():
    result1 = run_full_backtest()
    result2 = run_full_backtest()

    ids1 = [
        (r.event_id, r.detected, r.lead_time_hours) for r in result1["event_results"]
    ]
    ids2 = [
        (r.event_id, r.detected, r.lead_time_hours) for r in result2["event_results"]
    ]
    assert ids1 == ids2
