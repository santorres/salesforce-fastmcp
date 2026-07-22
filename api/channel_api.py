"""Channel Analytics API - Formal contracts for CLI and MCP.

This module defines the contract between:
- Request layer (CLI, MCP, future web UI)
- Analytics layer (channel_intelligence.py)

Both CLI and MCP use these exact request/response types, ensuring:
1. Consistency across all interfaces
2. Type safety (IDE autocomplete, static analysis)
3. Easy testing (typed mocks)
4. Self-documenting contracts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .constants import DEFAULT_CHANNEL_MANAGER


@dataclass
class AnalyticsRequest:
    """Request for analytics function.

    Attributes:
        period: Time period for analysis (e.g., 'THIS_QUARTER', 'THIS_FISCAL_YEAR')
        breakdown: How to break down results (e.g., 'partner', 'country', 'stage')
        limit: Maximum number of records to return
        channel_manager: Which channel manager's territory to analyze
        region: Regional filter ('SE', 'EE', 'all', or None for default)
    """

    period: str
    breakdown: str | None = None
    limit: int | None = None
    channel_manager: str = DEFAULT_CHANNEL_MANAGER
    region: str | None = None

    def __post_init__(self):
        """Validate request fields."""
        if not self.period:
            raise ValueError("period is required")
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.region and self.region not in ["SE", "EE", "all"]:
            raise ValueError("region must be 'SE', 'EE', 'all', or None")


@dataclass
class AnalyticsResponse:
    """Response from analytics function.

    This is the canonical response format. Both CLI and MCP must return
    responses that match this structure exactly.

    Attributes:
        tool: Name of the tool that produced this response
        period: The period that was analyzed
        breakdown: How the data was broken down (if applicable)
        data: The actual analytics results (tool-specific structure)
        truncationWarning: Warning if data was truncated due to limits
    """

    tool: str
    period: str
    breakdown: str | None
    data: dict[str, Any]
    truncationWarning: str | None = None

    def __post_init__(self):
        """Validate response fields."""
        if not self.tool:
            raise ValueError("tool is required")
        if not self.period:
            raise ValueError("period is required")
        if self.data is None:
            raise ValueError("data is required")


class ChannelAnalyticsAPI(ABC):
    """Abstract base class for Channel Analytics API.

    Defines the formal interface that both CLI and MCP use.
    This ensures both callers get the same response structure.
    """

    @abstractmethod
    async def get_revenue(self, req: AnalyticsRequest) -> AnalyticsResponse:
        """Get revenue analytics.

        Args:
            req: Analytics request with period, breakdown, limit

        Returns:
            AnalyticsResponse with revenue data
        """
        pass

    @abstractmethod
    async def get_pipeline(self, req: AnalyticsRequest) -> AnalyticsResponse:
        """Get pipeline analytics.

        Args:
            req: Analytics request with period, breakdown, limit

        Returns:
            AnalyticsResponse with pipeline data
        """
        pass

    @abstractmethod
    async def get_top_partners(
        self, period: str, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get top partners ranked by metric.

        Args:
            period: Time period for analysis
            metric: Ranking metric ('revenue' or 'pipeline')
            limit: Maximum number of partners to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with partner rankings
        """
        pass

    @abstractmethod
    async def get_partner_detail(
        self, partner_name: str, period: str | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get detailed metrics for a single partner.

        Args:
            partner_name: Name of partner to analyze
            period: Time period (optional, defaults to current quarter)
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with partner scorecard
        """
        pass

    @abstractmethod
    async def get_partner_pipeline(
        self, partner_name: str, period: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get open pipeline for a specific partner.

        Args:
            partner_name: Name of partner
            period: Time period (optional)
            limit: Max opportunities to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with partner pipeline
        """
        pass

    @abstractmethod
    async def get_kpi_snapshot(self, period: str | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER) -> AnalyticsResponse:
        """Get current KPI snapshot.

        Args:
            period: Time period (optional, defaults to current quarter)
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with KPI data
        """
        pass

    @abstractmethod
    async def get_revenue_by_sales_rep(
        self, period: str, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue aggregated by sales rep.

        Args:
            period: Time period for analysis
            metric: 'revenue' (closed-won) or 'pipeline' (open)
            limit: Maximum number of reps to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with sales rep rankings
        """
        pass

    @abstractmethod
    async def get_revenue_by_sales_rep_by_country(
        self, period: str, country: str | None = None, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue by sales rep, filtered by country.

        Args:
            period: Time period for analysis
            country: Specific country to filter (None = all)
            metric: 'revenue' (closed-won) or 'pipeline' (open)
            limit: Maximum number of reps to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with sales rep rankings by country
        """
        pass

    @abstractmethod
    async def get_revenue_by_sales_rep_by_partner(
        self, period: str, partner_name: str | None = None, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue by sales rep, filtered by partner.

        Args:
            period: Time period for analysis
            partner_name: Specific partner to filter (None = all)
            metric: 'revenue' (closed-won) or 'pipeline' (open)
            limit: Maximum number of reps to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with sales rep rankings by partner
        """
        pass

    @abstractmethod
    async def get_closed_deals_by_sales_rep(
        self, period: str, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get closed-won deals by sales rep with opportunity details.

        Args:
            period: Time period for analysis
            sales_rep: Specific sales rep to filter (None = all)
            limit: Maximum number of deals to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with closed deals grouped by sales rep
        """
        pass

    @abstractmethod
    async def get_pipeline_deals_by_sales_rep(
        self, period: str, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get open pipeline deals by sales rep with opportunity details.

        Args:
            period: Time period for analysis
            sales_rep: Specific sales rep to filter (None = all)
            limit: Maximum number of deals to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with pipeline deals grouped by sales rep
        """
        pass

    @abstractmethod
    async def get_revenue_by_sales_rep_with_region(
        self, period: str, region: str | None = None, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue aggregated by sales rep with optional region filtering.

        Args:
            period: Time period for analysis
            region: 'SE', 'EE', 'all', or None (default=all)
            metric: 'revenue' (closed-won) or 'pipeline' (open)
            limit: Maximum number of reps to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with sales rep rankings by region
        """
        pass

    @abstractmethod
    async def get_pipeline_by_sales_rep_with_region(
        self, period: str, region: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get pipeline aggregated by sales rep with optional region filtering.

        Args:
            period: Time period for analysis
            region: 'SE', 'EE', 'all', or None (default=all)
            limit: Maximum number of reps to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with sales rep pipeline by region
        """
        pass

    @abstractmethod
    async def get_closed_deals_by_sales_rep_with_region(
        self, period: str, region: str | None = None, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get closed-won deals by sales rep with optional region filtering.

        Args:
            period: Time period for analysis
            region: 'SE', 'EE', 'all', or None (default=all)
            sales_rep: Specific sales rep to filter (None = all)
            limit: Maximum number of deals to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with closed deals by sales rep and region
        """
        pass

    @abstractmethod
    async def get_pipeline_deals_by_sales_rep_with_region(
        self, period: str, region: str | None = None, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get pipeline deals by sales rep with optional region filtering.

        Args:
            period: Time period for analysis
            region: 'SE', 'EE', 'all', or None (default=all)
            sales_rep: Specific sales rep to filter (None = all)
            limit: Maximum number of deals to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with pipeline deals by sales rep and region
        """
        pass

    @abstractmethod
    async def get_opportunities_by_registration_status(
        self, period: str, registration_status: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get opportunities filtered by Partner_Registration_Approval__c status.

        Args:
            period: Time period for analysis
            registration_status: Status filter ('Submitted', 'In Review', 'Approved', 'Rejected', or None for all)
            limit: Maximum number of opportunities to return
            channel_manager: Which channel manager's territory

        Returns:
            AnalyticsResponse with opportunities grouped by registration status
        """
        pass


class ChannelAnalyticsAPIImpl(ChannelAnalyticsAPI):
    """Implementation of Channel Analytics API.

    Wraps channel_intelligence functions and ensures all responses
    conform to AnalyticsResponse contract.
    """

    def __init__(self, salesforce_client):
        """Initialize API with Salesforce client.

        Args:
            salesforce_client: Authenticated SalesforceClient instance
        """
        self.sf = salesforce_client

    async def get_revenue(self, req: AnalyticsRequest) -> AnalyticsResponse:
        """Get revenue analytics via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_revenue(self.sf, req.period, req.breakdown, req.limit, req.channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_revenue"),
            period=result.get("period", req.period),
            breakdown=result.get("breakdown", req.breakdown),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_pipeline(self, req: AnalyticsRequest) -> AnalyticsResponse:
        """Get pipeline analytics via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_pipeline(self.sf, req.period, req.breakdown, req.limit, req.channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_pipeline"),
            period=result.get("period", req.period),
            breakdown=result.get("breakdown", req.breakdown),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_top_partners(
        self, period: str, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get top partners via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_top_partners(self.sf, metric, period, limit, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_top_partners"),
            period=result.get("period", period),
            breakdown=result.get("breakdown"),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_partner_detail(
        self, partner_name: str, period: str | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get partner detail via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_partner_detail(self.sf, partner_name, period, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_partner_detail"),
            period=result.get("period", period or "current"),
            breakdown=result.get("breakdown"),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_partner_pipeline(
        self, partner_name: str, period: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get partner pipeline via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_partner_pipeline(self.sf, partner_name, period, limit, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_partner_pipeline"),
            period=result.get("period", period or "current"),
            breakdown=result.get("breakdown"),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
         )

    async def get_kpi_snapshot(self, period: str | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER) -> AnalyticsResponse:
        """Get KPI snapshot via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_kpi_snapshot(self.sf, period, channel_manager=channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_kpi_snapshot"),
            period=result.get("period", period or "current"),
            breakdown=result.get("breakdown"),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_revenue_by_sales_rep(
        self, period: str, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue aggregated by sales rep via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_revenue_by_sales_rep(self.sf, period, metric, limit or 50, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_revenue_by_sales_rep"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_revenue_by_sales_rep_by_country(
        self, period: str, country: str | None = None, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue by sales rep, filtered by country via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_revenue_by_sales_rep_by_country(self.sf, period, country, metric, limit or 50, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_revenue_by_sales_rep_by_country"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_revenue_by_sales_rep_by_partner(
        self, period: str, partner_name: str | None = None, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue by sales rep, filtered by partner via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_revenue_by_sales_rep_by_partner(self.sf, period, partner_name, metric, limit or 50, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_revenue_by_sales_rep_by_partner"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_closed_deals_by_sales_rep(
        self, period: str, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER, all_regions: bool = False
    ) -> AnalyticsResponse:
        """Get closed-won deals by sales rep via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_closed_deals_by_sales_rep(self.sf, period, sales_rep, limit or 100, channel_manager, all_regions)
        return AnalyticsResponse(
            tool=result.get("tool", "get_closed_deals_by_sales_rep"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_pipeline_deals_by_sales_rep(
        self, period: str, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER, all_regions: bool = False
    ) -> AnalyticsResponse:
        """Get open pipeline deals by sales rep via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_pipeline_deals_by_sales_rep(self.sf, period, sales_rep, limit or 100, channel_manager, all_regions)
        return AnalyticsResponse(
            tool=result.get("tool", "get_pipeline_deals_by_sales_rep"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_revenue_by_sales_rep_with_region(
        self, period: str, region: str | None = None, metric: str = "revenue", limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get revenue by sales rep with region filtering via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_revenue_by_sales_rep_with_region(self.sf, period, region, metric, limit or 50, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_revenue_by_sales_rep_with_region"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_pipeline_by_sales_rep_with_region(
        self, period: str, region: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get pipeline by sales rep with region filtering via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_pipeline_by_sales_rep_with_region(self.sf, period, region, limit or 50, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_pipeline_by_sales_rep_with_region"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_closed_deals_by_sales_rep_with_region(
        self, period: str, region: str | None = None, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get closed deals by sales rep with region filtering via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_closed_deals_by_sales_rep_with_region(self.sf, period, region, sales_rep, limit or 100, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_closed_deals_by_sales_rep_with_region"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_pipeline_deals_by_sales_rep_with_region(
        self, period: str, region: str | None = None, sales_rep: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get pipeline deals by sales rep with region filtering via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_pipeline_deals_by_sales_rep_with_region(self.sf, period, region, sales_rep, limit or 100, channel_manager)
        return AnalyticsResponse(
            tool=result.get("tool", "get_pipeline_deals_by_sales_rep_with_region"),
            period=result.get("period", period),
            breakdown=None,
            data=result.get("data", []),
            truncationWarning=result.get("truncationWarning"),
        )

    async def get_opportunities_by_registration_status(
        self, period: str, registration_status: str | None = None, limit: int | None = None, channel_manager: str = DEFAULT_CHANNEL_MANAGER
    ) -> AnalyticsResponse:
        """Get opportunities filtered by registration status via channel_intelligence."""
        import channel_intelligence as ci

        result = await ci.get_opportunities_by_registration_status(
            self.sf, period, registration_status, channel_manager, limit or 50
        )
        return AnalyticsResponse(
            tool=result.get("tool", "get_opportunities_by_registration_status"),
            period=result.get("period", period),
            breakdown=result.get("registration_status"),
            data=result.get("data", {}),
            truncationWarning=result.get("truncationWarning"),
        )
