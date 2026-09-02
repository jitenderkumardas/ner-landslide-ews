"""
Runs the full backtest and writes the report files to reports/backtest/.

Usage: python -m tests.backtests.run_backtest
"""

import json
from pathlib import Path

from .harness import run_full_backtest
from .metrics import compute_metrics

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports" / "backtest"


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    result = run_full_backtest()
    event_results = result["event_results"]
    episode_results = result["episode_results"]
    metrics = compute_metrics(event_results, episode_results)

    # --- baseline_metrics.json ---
    metrics_path = REPORTS_DIR / "baseline_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "SYNTHETIC_MOCK_DATA_WARNING": (
                    "THIS IS A SYNTHETIC/MOCK BACKTEST AND MUST NOT BE "
                    "PRESENTED AS VALIDATED REAL-WORLD PERFORMANCE."
                ),
                "threshold_version_tested": "rainfall-threshold-v0.1-placeholder",
                "metrics": metrics,
            },
            f,
            indent=2,
        )

    # --- event_results.csv ---
    import csv

    events_csv_path = REPORTS_DIR / "event_results.csv"
    with open(events_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "event_id",
                "grid_cell_id",
                "event_timestamp",
                "warning_time",
                "lead_time_hours",
                "predicted_severity",
                "detected",
            ],
        )
        writer.writeheader()
        for r in event_results:
            writer.writerow(r.as_dict())

    # --- summary.md ---
    summary_path = REPORTS_DIR / "summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(_render_summary(event_results, episode_results, metrics))

    print(f"Wrote reports to {REPORTS_DIR}")


def _render_summary(event_results, episode_results, metrics) -> str:
    lines = []
    lines.append("# Backtest Summary — Rainfall Threshold Baseline\n")
    lines.append(
        "> **THIS IS A SYNTHETIC/MOCK BACKTEST AND MUST NOT BE PRESENTED "
        "AS VALIDATED REAL-WORLD PERFORMANCE.** All events and rainfall "
        "data in this report are hand-authored synthetic fixtures for "
        "the East Khasi Hills pilot corridor — none of this is real "
        "GSI/IMD/NH historical data.\n"
    )
    lines.append(
        "**Threshold version tested:** `rainfall-threshold-v0.1-placeholder`\n"
    )

    lines.append("## Confusion matrix (episode-level)\n")
    cm = metrics["confusion_matrix"]
    lines.append(
        f"| | Predicted: Warning | Predicted: No Warning |\n"
        f"|---|---|---|\n"
        f"| **Actual: Event** | TP = {cm['true_positives']} | FN = {cm['false_negatives']} |\n"
        f"| **Actual: No Event** | FP = {cm['false_positives']} | TN = {cm['true_negatives']} |\n"
    )

    lines.append("\n## Metrics\n")
    for key in [
        "precision",
        "recall",
        "f1",
        "false_positive_rate",
        "false_negative_rate",
        "detection_rate",
        "average_lead_time_hours",
        "median_lead_time_hours",
        "minimum_lead_time_hours",
        "missed_events",
        "number_of_false_alarms",
    ]:
        lines.append(f"- **{key.replace('_', ' ')}:** {metrics[key]}")

    lines.append(f"\n> {metrics['sample_size_warning']}\n")

    lines.append("## Event-level results\n")
    lines.append(
        "| Event | Grid Cell | Event Time | Warning Time | Lead Time (h) | Detected |"
    )
    lines.append("|---|---|---|---|---|---|")
    for r in event_results:
        lines.append(
            f"| {r.event_id} | {r.grid_cell_id} | {r.event_timestamp} | "
            f"{r.warning_time or '—'} | {r.lead_time_hours if r.lead_time_hours is not None else '—'} | "
            f"{'✅ Yes' if r.detected else '❌ No'} |"
        )

    lines.append("\n## No-event episode results\n")
    lines.append("| Grid Cell | Warning Raised | Outcome |")
    lines.append("|---|---|---|")
    for r in episode_results:
        lines.append(f"| {r.grid_cell_id} | {r.warning_raised} | {r.outcome} |")

    lines.append("\n## Why the miss matters\n")
    lines.append(
        "BTEST-003 (GRID-EKH-001) is a landslide with no meaningful "
        "rainfall signal beforehand — a deliberate test of this model's "
        "real limitation. A rainfall-only baseline cannot catch events "
        "driven by factors it doesn't see: antecedent soil saturation, "
        "slope instability, geology, or land-cover change. This is "
        "expected and documents exactly why the Phase 3 design calls "
        "for fusing in soil moisture, susceptibility mapping, and "
        "satellite-derived features before this system could be relied "
        "on for real warnings.\n"
    )

    lines.append("## Current limitations\n")
    lines.append("- All data is synthetic — no real historical landslide events used")
    lines.append(
        "- Rainfall-only signal — no terrain, slope, soil moisture, geology, or satellite features"
    )
    lines.append(
        "- Thresholds are uncalibrated placeholders (`rainfall-threshold-v0.1-placeholder`)"
    )
    lines.append(
        "- Sample size (4 events, 2 no-event episodes) is illustrative only, not statistically meaningful"
    )
    lines.append("- No real historical event validation has been performed\n")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
