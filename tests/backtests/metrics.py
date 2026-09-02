"""
Metrics computed from a backtest run.

For a small synthetic fixture (4 events + 2 no-event episodes), these
numbers are illustrative of the harness working correctly, NOT a
meaningful estimate of real-world performance. Do not report a
precision/recall number from this module as if it were a validated
accuracy claim — see docs/adr/model-versions.md and the loud disclaimer
in reports/backtest/summary.md.
"""

import statistics
from typing import List

from .harness import BacktestResult, EpisodeResult


def compute_confusion_matrix(
    event_results: List[BacktestResult], episode_results: List[EpisodeResult]
) -> dict:
    tp = sum(1 for r in event_results if r.detected)
    fn = sum(1 for r in event_results if not r.detected)
    fp = sum(1 for r in episode_results if r.outcome == "FP")
    tn = sum(1 for r in episode_results if r.outcome == "TN")
    return {
        "true_positives": tp,
        "false_negatives": fn,
        "false_positives": fp,
        "true_negatives": tn,
    }


def compute_metrics(
    event_results: List[BacktestResult], episode_results: List[EpisodeResult]
) -> dict:
    cm = compute_confusion_matrix(event_results, episode_results)
    tp, fn, fp, tn = (
        cm["true_positives"],
        cm["false_negatives"],
        cm["false_positives"],
        cm["true_negatives"],
    )

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    fpr = fp / (fp + tn) if (fp + tn) > 0 else None
    fnr = fn / (fn + tp) if (fn + tp) > 0 else None
    detection_rate = tp / (tp + fn) if (tp + fn) > 0 else None

    lead_times = [
        r.lead_time_hours
        for r in event_results
        if r.detected and r.lead_time_hours is not None
    ]

    return {
        "confusion_matrix": cm,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "f1": round(f1, 3) if f1 is not None else None,
        "false_positive_rate": round(fpr, 3) if fpr is not None else None,
        "false_negative_rate": round(fnr, 3) if fnr is not None else None,
        "detection_rate": round(detection_rate, 3)
        if detection_rate is not None
        else None,
        "total_events": len(event_results),
        "missed_events": fn,
        "number_of_false_alarms": fp,
        "average_lead_time_hours": round(statistics.mean(lead_times), 2)
        if lead_times
        else None,
        "median_lead_time_hours": round(statistics.median(lead_times), 2)
        if lead_times
        else None,
        "minimum_lead_time_hours": round(min(lead_times), 2) if lead_times else None,
        "sample_size_warning": (
            f"Based on {len(event_results)} synthetic events and "
            f"{len(episode_results)} no-event episodes — far too small "
            f"a sample for these numbers to be statistically meaningful. "
            f"This backtest validates that the harness and detection "
            f"logic work correctly, not that the model performs well."
        ),
    }
