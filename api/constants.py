"""Shared constants for Analytics API."""

import os

# Default channel manager for analytics queries
# Empty string means "all channel managers" (aligns with config/ci_config.py)
DEFAULT_CHANNEL_MANAGER = os.getenv("DEFAULT_CHANNEL_MANAGER", "")

# Default limits for data queries
REVENUE_LIMIT_DEFAULT = 20
PIPELINE_LIMIT_DEFAULT = 20
PARTNERS_LIMIT_DEFAULT = 10
OPPORTUNITIES_LIMIT_DEFAULT = 30
