"""
Backtest evaluation configuration.

These values define what counts as a "detection" — this is a judgment
call, and per project rules it must be explicit and documented, not
silently embedded in the harness logic.
"""

from services.risk_engine.severity import Severity

BACKTEST_CONFIG = {
    # A warning only counts as a valid detection of a specific event if
    # it was raised within this many hours before the event timestamp.
    # Rationale: an ORANGE/RED reading from three weeks ago is not a
    # meaningful "warning" for today's event — some bound is needed so
    # a stale, long-past crossing can't get credit for a later event.
    # 24h is a prototype assumption sized to "this shift's worth of
    # lead time being operationally useful" — not derived from any
    # real response-time study. Revisit once real response logistics
    # (evacuation time, field-officer travel time) are known.
    "event_tolerance_hours": 24,
    # Minimum severity level that counts as "a warning was raised".
    # ORANGE chosen over YELLOW because severity.py's own definitions
    # describe YELLOW as "elevated — watch" (not yet actionable) and
    # ORANGE as "high — prepare / advisory" (the first tier meant to
    # prompt action). This is a prototype assumption, not a validated
    # operational threshold.
    "minimum_warning_level": Severity.ORANGE,
}
