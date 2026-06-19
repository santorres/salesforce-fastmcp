"""Analytics API - Formal contracts for channel intelligence."""

from .channel_api import (
    AnalyticsRequest,
    AnalyticsResponse,
    ChannelAnalyticsAPI,
    ChannelAnalyticsAPIImpl,
)
from .constants import DEFAULT_CHANNEL_MANAGER, REVENUE_LIMIT_DEFAULT

__all__ = [
    "AnalyticsRequest",
    "AnalyticsResponse",
    "ChannelAnalyticsAPI",
    "ChannelAnalyticsAPIImpl",
    "DEFAULT_CHANNEL_MANAGER",
    "REVENUE_LIMIT_DEFAULT",
]
