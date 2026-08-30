"""
Base interface for rainfall data adapters.

Every rainfall adapter (mock or real) must return records in this shape.
This is the contract that lets us swap the mock adapter for the real IMD
adapter later without touching anything downstream (risk-engine, GIS layer).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass(frozen=True)
class RainfallRecord:
    """
    One rainfall observation for one grid cell at one point in time.

    Provenance fields (source, source_timestamp, ingestion_timestamp,
    transformation_version) are mandatory per project rules
    (.agents/rules/core-rules.md, section 4) — every ingested record
    must carry them, no exceptions.
    """

    grid_cell_id: str
    district: str
    state: str
    latitude: float
    longitude: float
    rainfall_mm: float
    source_timestamp: datetime  # when the source says this reading is from

    # Provenance — required, not optional
    source: str
    ingestion_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    transformation_version: str = "v1"

    def __post_init__(self) -> None:
        if self.rainfall_mm < 0:
            raise ValueError(
                f"rainfall_mm cannot be negative, got {self.rainfall_mm} "
                f"for grid cell {self.grid_cell_id}"
            )
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"invalid longitude: {self.longitude}")


class RainfallAdapter(ABC):
    """Contract every rainfall adapter (mock or real) must implement."""

    @abstractmethod
    def fetch_latest(self) -> List[RainfallRecord]:
        """Return the latest available rainfall records."""
        raise NotImplementedError

    @abstractmethod
    def fetch_range(self, start: datetime, end: datetime) -> List[RainfallRecord]:
        """Return rainfall records between start and end (inclusive)."""
        raise NotImplementedError
