"""Output model for a single grid cell's rainfall-based risk assessment."""

from dataclasses import dataclass
from datetime import datetime

from .severity import Severity


@dataclass(frozen=True)
class RiskAssessment:
    grid_cell_id: str
    district: str
    state: str
    latitude: float
    longitude: float
    severity: Severity
    cumulative_rainfall_mm: float
    window_hours: int
    window_end: datetime
    threshold_version: str
    computed_at: datetime

    def as_dict(self) -> dict:
        """Serializable form for the API layer / dashboard."""
        return {
            "grid_cell_id": self.grid_cell_id,
            "district": self.district,
            "state": self.state,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "severity": str(self.severity),
            "cumulative_rainfall_mm": round(self.cumulative_rainfall_mm, 1),
            "window_hours": self.window_hours,
            "window_end": self.window_end.isoformat(),
            "threshold_version": self.threshold_version,
            "computed_at": self.computed_at.isoformat(),
        }
