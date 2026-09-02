"""
Generates the synthetic backtest rainfall fixture.

DESIGN NOTE: values below are hand-authored per scenario, not drawn from
a random distribution. This is a deliberate choice, not a shortcut —
for a landslide-detection backtest, a reviewer needs to be able to look
at the input and reason about why a given episode should (or should
not) trigger a detection. A random-noise generator would be
"reproducible" in the RNG-seed sense but not reviewable in the sense
that actually matters here. Every value is fully deterministic (no RNG
at all), which is a stronger reproducibility guarantee than a seeded
random generator gives anyway.

Run this script to regenerate fixtures/backtest/rainfall_hourly.csv.
The output is committed to the repo (frozen) so tests don't depend on
re-running this script.

ALL DATA IN THIS FILE IS SYNTHETIC. It does not represent real IMD
measurements or real landslide events. See historical_landslides.csv
and docs/adr/model-versions.md for how this is used and labeled.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent / "rainfall_hourly.csv"

# Reusing the same grid cells and coordinates already established in
# services/ingestion/rainfall/fixtures/mock_rainfall_hourly.csv, plus
# one additional backtest-only cell (EKH-006) added purely to give a
# clean true-negative episode. EKH-006 is NOT part of the 5 cells
# currently exposed via the live /risk-assessments API.
GRID_CELLS = {
    "GRID-EKH-001": (25.5788, 91.8933),
    "GRID-EKH-002": (25.4650, 91.8210),
    "GRID-EKH-003": (25.4200, 91.8005),
    "GRID-EKH-004": (25.3480, 91.7690),
    "GRID-EKH-005": (25.2702, 91.7323),
    "GRID-EKH-006": (25.2450, 91.7100),  # backtest-only, approximate
}
DISTRICT = "East Khasi Hills"
STATE = "Meghalaya"
TZ = "+05:30"


def hours(start_iso: str, values: list) -> list:
    """Pair up hourly rainfall values with timestamps starting at start_iso."""
    start = datetime.fromisoformat(start_iso)
    return [(start + timedelta(hours=i), v) for i, v in enumerate(values)]


# --- Scenario A: GRID-EKH-005 — steady buildup, should be DETECTED with decent lead time ---
scenario_a = hours(
    f"2026-07-01T00:00:00{TZ}",
    [1, 2, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2]  # h0-11: quiet baseline
    + [4, 5, 6, 6, 7, 8, 8, 9, 10, 11, 12, 12]  # h12-23: building trend
    + [15, 18, 20, 22, 24, 25],  # h24-29: intensification
)
scenario_a_grid = "GRID-EKH-005"

# --- Scenario B: GRID-EKH-003 — long quiet period then last-minute spike, DETECTED but SHORT lead time ---
scenario_b = hours(
    f"2026-07-05T00:00:00{TZ}",
    [1, 2, 3, 2] * 6
    + [1, 2]  # h0-25: steady low (26 values)
    + [20, 25, 30],  # h26-28: sudden spike
)
scenario_b_grid = "GRID-EKH-003"

# --- Scenario C: GRID-EKH-002 — sustained heavy rain, NO landslide (false-alarm test) ---
scenario_c = hours(
    f"2026-07-08T00:00:00{TZ}",
    [10, 12, 14, 16, 18, 20, 18, 16, 14, 12] * 2
    + [10, 12, 14, 16],  # 24 values, heavy throughout
)
scenario_c_grid = "GRID-EKH-002"

# --- Scenario D: GRID-EKH-001 — rainfall stays low throughout, landslide happens anyway (MISSED — model blind spot) ---
scenario_d = hours(
    f"2026-07-11T00:00:00{TZ}",
    [
        1,
        2,
        1,
        2,
        1,
        3,
        2,
        1,
        2,
        1,
        2,
        3,
        1,
        2,
        1,
        2,
        3,
        1,
        2,
        1,
        2,
        1,
        3,
        2,
        1,
        2,
        1,
        2,
        1,
    ],  # 29 values, always low
)
scenario_d_grid = "GRID-EKH-001"

# --- Scenario E: GRID-EKH-004 — gradual rise to just above ORANGE, borderline DETECTED ---
scenario_e = hours(
    f"2026-07-14T00:00:00{TZ}",
    [1, 2, 1, 2, 3, 2, 1, 2, 1, 2, 3, 2, 1, 2, 3, 2]  # h0-15: low
    + [4, 5, 6, 7, 8, 9, 8, 9, 10, 9, 8, 7],  # h16-27: moderate rise
)
scenario_e_grid = "GRID-EKH-004"

# --- Scenario F: GRID-EKH-006 — calm period, no rain, no event (TRUE NEGATIVE) ---
scenario_f = hours(
    f"2026-07-17T00:00:00{TZ}",
    [
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        2,
    ],  # 24 values, always calm
)
scenario_f_grid = "GRID-EKH-006"

ALL_SCENARIOS = [
    (scenario_a_grid, scenario_a),
    (scenario_b_grid, scenario_b),
    (scenario_c_grid, scenario_c),
    (scenario_d_grid, scenario_d),
    (scenario_e_grid, scenario_e),
    (scenario_f_grid, scenario_f),
]


def generate() -> None:
    rows = []
    for grid_cell_id, series in ALL_SCENARIOS:
        lat, lon = GRID_CELLS[grid_cell_id]
        for timestamp, rainfall_mm in series:
            rows.append(
                {
                    "grid_cell_id": grid_cell_id,
                    "district": DISTRICT,
                    "state": STATE,
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": timestamp.isoformat(),
                    "rainfall_mm": rainfall_mm,
                }
            )

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "grid_cell_id",
                "district",
                "state",
                "latitude",
                "longitude",
                "timestamp",
                "rainfall_mm",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
