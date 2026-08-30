"""
Risk severity levels for the landslide EWS.

Matches the GREEN/YELLOW/ORANGE/RED scheme implied by the dashboard's
"risk severity" concept in the Phase 3 design doc. Ordered so severity
levels can be compared (RED > ORANGE > YELLOW > GREEN).
"""

from enum import IntEnum


class Severity(IntEnum):
    GREEN = 0  # no significant risk signal
    YELLOW = 1  # elevated — watch
    ORANGE = 2  # high — prepare / advisory
    RED = 3  # severe — alert-worthy

    def __str__(self) -> str:
        return self.name
