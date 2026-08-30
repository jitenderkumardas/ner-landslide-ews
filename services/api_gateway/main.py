"""
Minimal API gateway — exposes current rainfall-based risk assessments.

This is a Tier 2 service (see docs/adr/tiering.md), but it surfaces
Tier 0/1 output (risk_engine assessments), so it carries the same
"do not overclaim" discipline: every response is explicitly labeled as
pre-pilot mock data, not live operational output. Do not remove that
disclaimer as a "cleanup" later — remove it only when there's a real,
signed-off live data pipeline behind this endpoint.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from services.ingestion.rainfall import get_rainfall_adapter
from services.risk_engine import calculate_rainfall_risk

app = FastAPI(
    title="NER Landslide EWS — Risk API (pre-pilot)",
    description=(
        "Pre-pilot API surfacing mock-data risk assessments for the "
        "East Khasi Hills pilot corridor. Not connected to live sensors "
        "or alerting. See docs/adr/model-versions.md for threshold "
        "calibration status."
    ),
    version="0.1.0",
)

# CORS: wide open for local dev only. Before this touches anything
# beyond a laptop demo, restrict allow_origins to the actual dashboard
# domain(s) — "*" here is a deliberate, temporary dev convenience, not
# a production setting. Flag this in review if it's still "*" once
# real deployment is discussed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# How far back to look for records to feed into the windowed risk
# calculation. Wide enough to comfortably include the mock fixture's
# fixed dates regardless of the actual current date.
LOOKBACK_DAYS = 365


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/risk-assessments")
def get_risk_assessments(
    district: Optional[str] = Query(
        default=None, description="Filter by district name, e.g. 'East Khasi Hills'"
    ),
) -> dict:
    adapter = get_rainfall_adapter()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=LOOKBACK_DAYS)

    records = adapter.fetch_range(start, end)
    assessments = calculate_rainfall_risk(records)

    if district:
        assessments = [a for a in assessments if a.district.lower() == district.lower()]

    return {
        "disclaimer": (
            "PRE-PILOT MOCK DATA. Not connected to live sensors, "
            "not validated against historical events, not used for "
            "any real alerting. See docs/adr/model-versions.md."
        ),
        "threshold_version": assessments[0].threshold_version if assessments else None,
        "count": len(assessments),
        "assessments": [a.as_dict() for a in assessments],
    }
