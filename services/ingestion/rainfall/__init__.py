"""
Rainfall ingestion package.

Use get_rainfall_adapter() everywhere else in the codebase instead of
importing MockRainfallAdapter or RealIMDRainfallAdapter directly — this
keeps the mock/real switch to one place (this file), driven by the
USE_MOCK_ADAPTERS environment variable.
"""

import os

from .base import RainfallAdapter, RainfallRecord
from .mock_adapter import MockRainfallAdapter
from .real_adapter import RealIMDRainfallAdapter

__all__ = [
    "RainfallAdapter",
    "RainfallRecord",
    "MockRainfallAdapter",
    "RealIMDRainfallAdapter",
    "get_rainfall_adapter",
]


def get_rainfall_adapter() -> RainfallAdapter:
    """
    Return the configured rainfall adapter.

    Controlled by USE_MOCK_ADAPTERS in .env — defaults to mock (safe
    default) if the variable is missing or unrecognized, rather than
    silently trying to hit a real API with no credentials.
    """
    use_mock = os.environ.get("USE_MOCK_ADAPTERS", "true").lower() == "true"

    if use_mock:
        return MockRainfallAdapter()

    api_base_url = os.environ.get("IMD_API_BASE_URL", "")
    api_key = os.environ.get("IMD_API_KEY", "")
    return RealIMDRainfallAdapter(api_base_url=api_base_url, api_key=api_key)
