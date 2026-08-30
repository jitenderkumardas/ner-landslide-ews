"""
Real IMD rainfall adapter — NOT YET AUTHORIZED.

We do not have live IMD API credentials yet (see .env.example:
IMD_API_BASE_URL / IMD_API_KEY are blank, and
.agents/rules/core-rules.md section 3 forbids fabricating a real
response schema without documentation).

This stub exists so the factory in __init__.py has a real target to
switch to once access is granted — the interface (RainfallAdapter) is
already fixed by base.py, so implementing this later should not require
changing risk_engine, GIS, or alerting code at all.

TODO: real API — not yet authorized. Do not implement request logic
against an assumed schema; wait for actual IMD API documentation.
"""

from datetime import datetime
from typing import List

from .base import RainfallAdapter, RainfallRecord


class RealIMDRainfallAdapter(RainfallAdapter):
    def __init__(self, api_base_url: str, api_key: str):
        if not api_base_url or not api_key:
            raise ValueError(
                "RealIMDRainfallAdapter requires IMD_API_BASE_URL and "
                "IMD_API_KEY to be set — see .env.example. "
                "If you don't have these yet, use MockRainfallAdapter "
                "(USE_MOCK_ADAPTERS=true) instead."
            )
        self.api_base_url = api_base_url
        self.api_key = api_key

    def fetch_latest(self) -> List[RainfallRecord]:
        raise NotImplementedError(
            "Real IMD adapter not yet implemented — API access pending. "
            "See .agents/rules/core-rules.md section 3."
        )

    def fetch_range(self, start: datetime, end: datetime) -> List[RainfallRecord]:
        raise NotImplementedError(
            "Real IMD adapter not yet implemented — API access pending."
        )
