"""
Rainfall risk thresholds — PLACEHOLDER, NOT YET CALIBRATED.

These threshold values (mm of rainfall in a rolling window) are a
first-pass design assumption, not derived from a backtest against real
GSI historical landslide events. Per .agents/rules/core-rules.md
section 6 ("do not claim yet"), this module must never be described as
validated or production-accuracy in any docstring, log message, or UI
copy until docs/adr/model-versions.md has a real backtest entry
superseding this version.

version: "rainfall-threshold-v0.1-placeholder"
"""

from dataclasses import dataclass

from .severity import Severity

THRESHOLD_VERSION = "rainfall-threshold-v0.1-placeholder"

# Rolling window used to sum rainfall before comparing against thresholds.
WINDOW_HOURS = 3


@dataclass(frozen=True)
class ThresholdSet:
    """mm of cumulative rainfall in WINDOW_HOURS needed to reach each level."""

    yellow_mm: float
    orange_mm: float
    red_mm: float

    def classify(self, cumulative_mm: float) -> Severity:
        if cumulative_mm >= self.red_mm:
            return Severity.RED
        if cumulative_mm >= self.orange_mm:
            return Severity.ORANGE
        if cumulative_mm >= self.yellow_mm:
            return Severity.YELLOW
        return Severity.GREEN


# PLACEHOLDER VALUES — see module docstring. These are round-number
# starting guesses for a high-rainfall NER hill district, not a
# calibrated result. Must be revisited in Phase 4 against GSI historical
# landslide records for the East Khasi Hills pilot corridor.
DEFAULT_THRESHOLDS = ThresholdSet(
    yellow_mm=15.0,
    orange_mm=25.0,
    red_mm=40.0,
)
