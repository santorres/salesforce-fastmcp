"""FastMCP server for Salesforce integration."""

import json
import logging
import os
import sys
from typing import Annotated, Any
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field

from salesforce_client import SalesforceClient, SalesforceError
import channel_intelligence as ci
from prompts import (
    quarterly_pipeline_analysis,
    closed_won_partner_analysis,
    partner_engagement_health,
    partner_sourced_pipeline,
    at_risk_pipeline,
    new_vs_existing_business,
    lead_conversion_analysis,
    stalled_opportunities,
    country_pipeline_dashboard,
    forecast_vs_actuals,
    partner_scorecard,
    weekly_briefing,
    partner_qbr_prep,
    competitive_analysis,
    COUNTRIES,
    QUARTERS,
)

# Load environment variables
load_dotenv()

# Setup request logger
def _setup_logger() -> logging.Logger:
    log_file = os.getenv("MCP_LOG_FILE", "mcp_requests.log")
    fmt = "%(asctime)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    handlers = [
        logging.StreamHandler(sys.stderr),
        RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt, handlers=handlers)
    return logging.getLogger("mcp.requests")

logger = _setup_logger()

# Initialize FastMCP server
mcp = FastMCP("Salesforce Connector")

# Global client instance (lazy initialized)
_client: SalesforceClient | None = None


def get_client() -> SalesforceClient:
    """Get or create the Salesforce client instance."""
    global _client
    if _client is None:
        _client = SalesforceClient()
    return _client


def format_result(data: Any) -> str:
    """Format result data as JSON string."""
    return json.dumps(data, indent=2, default=str)


# =============================================================================
# Basic CRUD Tools (8 tools)
# =============================================================================


@mcp.tool
async def salesforce_query(
    q: Annotated[str, Field(description="The SOQL query to execute")],
) -> str:
    """Execute SOQL queries against Salesforce.

    IMPORTANT - Querying Lookup/Reference Fields:
    Lookup fields (like Partner__c, Account__c, etc.) store record IDs, not names.
    To query by name, use the relationship syntax with __r:
      ❌ WRONG:   WHERE Partner__c = 'Inetum - Spain (Partner)'
      ✅ CORRECT: WHERE Partner__r.Name = 'Inetum - Spain (Partner)'

    To SELECT lookup field names, use:
      ✅ SELECT Partner__r.Name, Account__r.Name FROM Opportunity

    Common lookup fields in Opportunity:
      - Partner__c → use Partner__r.Name for partner name
      - Account__c → use Account.Name or Account__r.Name
      - Owner__c → use Owner.Name

    For custom lookup fields ending in __c, use __r.Name to access the related record's name.
    """
    try:
        client = get_client()
        result = await client.query(q)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_sobjects() -> str:
    """List all available Salesforce objects."""
    try:
        client = get_client()
        result = await client.get_sobjects()
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_recent(
    limit: Annotated[
        int, Field(description="Maximum number of recent records to return")
    ] = 20,
) -> str:
    """Fetch recently accessed Salesforce records."""
    try:
        client = get_client()
        result = await client.get_recent(limit)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_search(
    q: Annotated[str, Field(description="The SOSL search query to execute")],
) -> str:
    """Execute SOSL searches against Salesforce."""
    try:
        client = get_client()
        result = await client.search(q)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_describe(
    object_name: Annotated[
        str,
        Field(
            description="The name of the Salesforce object to describe (e.g., Account, Contact)"
        ),
    ],
) -> str:
    """Get detailed metadata for a Salesforce object including field information."""
    try:
        client = get_client()
        result = await client.describe(object_name)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_describe_fields(
    object_name: Annotated[
        str,
        Field(
            description="The name of the Salesforce object (e.g., Account, Contact, Opportunity)"
        ),
    ],
    field_filter: Annotated[
        str | None,
        Field(
            description="Optional: filter fields by name pattern (case-insensitive, e.g., 'partner', 'amount')"
        ),
    ] = None,
    field_types: Annotated[
        list[str] | None,
        Field(
            description="Optional: filter by field types (e.g., ['reference', 'picklist', 'currency'])"
        ),
    ] = None,
) -> str:
    """Get field metadata for a Salesforce object with optional filtering.

    Use this instead of salesforce_describe when you only need field information,
    especially for objects with many fields like Opportunity.
    """
    try:
        client = get_client()
        result = await client.describe(object_name)

        fields = result.get("fields", [])
        filtered_fields = []

        for field in fields:
            # Apply name filter
            if field_filter:
                if field_filter.lower() not in field.get("name", "").lower():
                    continue

            # Apply type filter
            if field_types:
                if field.get("type") not in field_types:
                    continue

            # Return only essential field metadata
            filtered_fields.append({
                "name": field.get("name"),
                "label": field.get("label"),
                "type": field.get("type"),
                "referenceTo": field.get("referenceTo"),
                "picklistValues": [
                    {"value": pv.get("value"), "label": pv.get("label")}
                    for pv in field.get("picklistValues", [])[:20]  # Limit picklist values
                ] if field.get("type") == "picklist" else None,
                "required": not field.get("nillable", True),
                "updateable": field.get("updateable"),
            })

        return format_result({
            "object": object_name,
            "fieldCount": len(filtered_fields),
            "filter": field_filter,
            "typeFilter": field_types,
            "fields": filtered_fields,
        })
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_find_partner(
    search_term: Annotated[
        str,
        Field(
            description="Partner name to search for (e.g., 'Adaptit', 'Acme')"
        ),
    ],
) -> str:
    """Find a partner account by name and return its ID for use in opportunity queries.

    Partner accounts typically have '(Partner)' in their name.
    Returns the Account ID which can be used to filter opportunities by Partner__c field.
    """
    try:
        client = get_client()

        # Search for partner accounts
        query = f"""
            SELECT Id, Name, BillingCountry, Type, Partner_Status__c
            FROM Account
            WHERE Name LIKE '%{search_term}%'
            ORDER BY Name
            LIMIT 10
        """
        result = await client.query(query.strip())

        records = result.get("records", [])
        if not records:
            return format_result({
                "message": f"No accounts found matching '{search_term}'",
                "suggestion": "Try a different search term or partial name",
            })

        return format_result({
            "message": f"Found {len(records)} account(s) matching '{search_term}'",
            "accounts": [
                {
                    "id": r.get("Id"),
                    "name": r.get("Name"),
                    "country": r.get("BillingCountry"),
                    "type": r.get("Type"),
                    "partnerStatus": r.get("Partner_Status__c"),
                    "useInQuery": f"Partner__c = '{r.get('Id')}'",
                }
                for r in records
            ],
        })
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_create(
    object_name: Annotated[
        str,
        Field(description="The name of the Salesforce object (e.g., Account, Contact)"),
    ],
    record_data: Annotated[
        dict[str, Any], Field(description="The field values for the new record")
    ],
) -> str:
    """Create a new record in Salesforce."""
    try:
        client = get_client()
        result = await client.create_record(object_name, record_data)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_update(
    object_name: Annotated[
        str,
        Field(description="The name of the Salesforce object (e.g., Account, Contact)"),
    ],
    record_id: Annotated[str, Field(description="The ID of the record to update")],
    record_data: Annotated[
        dict[str, Any], Field(description="The field values to update")
    ],
) -> str:
    """Update an existing record in Salesforce."""
    try:
        client = get_client()
        result = await client.update_record(object_name, record_id, record_data)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_delete(
    object_name: Annotated[
        str,
        Field(description="The name of the Salesforce object (e.g., Account, Contact)"),
    ],
    record_id: Annotated[str, Field(description="The ID of the record to delete")],
) -> str:
    """Delete a record from Salesforce."""
    try:
        client = get_client()
        result = await client.delete_record(object_name, record_id)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


# =============================================================================
# Navigation & Relationships Tools (3 tools)
# =============================================================================


@mcp.tool
async def salesforce_relationships(
    object_name: Annotated[
        str,
        Field(
            description="The name of the parent Salesforce object (e.g., Account, Contact)"
        ),
    ],
    record_id: Annotated[str, Field(description="The ID of the parent record")],
    relationship_name: Annotated[
        str | None,
        Field(
            description="Optional: specific relationship to query (e.g., Contact, Opportunity). If not provided, returns all available relationships"
        ),
    ] = None,
) -> str:
    """Get related records for a Salesforce record (e.g., Contacts for an Account)."""
    try:
        client = get_client()
        result = await client.get_related_records(
            object_name, record_id, relationship_name
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_lookup(
    object_name: Annotated[
        str,
        Field(
            description="The Salesforce object to search in (e.g., Account, Contact, Lead)"
        ),
    ],
    search_term: Annotated[
        str,
        Field(
            description='The term to search for (e.g., "John Smith", "acme", "john@example.com")'
        ),
    ],
    search_fields: Annotated[
        list[str] | None,
        Field(
            description='Optional: fields to search in (default: ["Name"]). Examples: ["Name", "Email"], ["Name", "Phone"]'
        ),
    ] = None,
    limit: Annotated[
        int, Field(description="Maximum number of results to return (default: 10)")
    ] = 10,
) -> str:
    """Search for Salesforce records by name, email, or other fields."""
    try:
        client = get_client()
        result = await client.lookup_records(
            object_name, search_term, search_fields, limit
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_hierarchy(
    object_name: Annotated[
        str, Field(description="The Salesforce object (e.g., Account, Contact)")
    ],
    record_id: Annotated[str, Field(description="The ID of the record")],
    direction: Annotated[
        str,
        Field(
            description='Direction to navigate: "up" for parent records, "down" for child records (default: "down")'
        ),
    ] = "down",
) -> str:
    """Navigate parent-child relationships in Salesforce records."""
    try:
        client = get_client()
        result = await client.get_hierarchy(object_name, record_id, direction)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


# =============================================================================
# Analytics Tools (3 tools)
# =============================================================================


@mcp.tool
async def salesforce_aggregate(
    object_name: Annotated[
        str,
        Field(
            description="The Salesforce object to analyze (e.g., Opportunity, Case, Lead)"
        ),
    ],
    aggregates: Annotated[
        list[dict[str, Any]],
        Field(
            description='Array of aggregation functions to apply. Each item should have "function" (COUNT, SUM, AVG, MAX, MIN), optional "field" (e.g., Amount, Id), and optional "alias"'
        ),
    ],
    group_by: Annotated[
        str | None,
        Field(
            description="Field to group results by (e.g., StageName, Owner.Name)"
        ),
    ] = None,
    where_clause: Annotated[
        str | None,
        Field(
            description='Optional WHERE condition (e.g., "CreatedDate = THIS_MONTH")'
        ),
    ] = None,
    limit: Annotated[
        int, Field(description="Maximum number of results (default: 100)")
    ] = 100,
) -> str:
    """Get statistical analysis of Salesforce data (COUNT, SUM, AVG, MAX, MIN)."""
    try:
        client = get_client()
        result = await client.get_aggregated_data(
            object_name, aggregates, group_by, where_clause, limit
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_reports(
    report_id: Annotated[
        str | None, Field(description="Specific report ID to run")
    ] = None,
    report_name: Annotated[
        str | None, Field(description="Name of the report to find and run")
    ] = None,
) -> str:
    """Access and run existing Salesforce reports."""
    try:
        client = get_client()
        result = await client.get_report_data(report_id, report_name)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_trend_analysis(
    object_name: Annotated[
        str,
        Field(
            description="The Salesforce object to analyze (e.g., Opportunity, Case, Lead)"
        ),
    ],
    date_field: Annotated[
        str, Field(description="Date field to analyze trends (default: CreatedDate)")
    ] = "CreatedDate",
    period: Annotated[
        str,
        Field(description='Time period for grouping: "day", "week", or "month" (default: month)'),
    ] = "month",
    metrics: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description='Metrics to track over time. Each item should have "function" (COUNT, SUM, AVG, MAX, MIN), optional "field", and optional "alias". Default: COUNT of records'
        ),
    ] = None,
    timeframe: Annotated[
        int, Field(description="Number of periods to look back (default: 6)")
    ] = 6,
) -> str:
    """Analyze trends over time for Salesforce data."""
    try:
        client = get_client()
        result = await client.get_trend_analysis(
            object_name, date_field, period, metrics, timeframe
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


# =============================================================================
# Business Intelligence Tools (3 tools)
# =============================================================================


@mcp.tool
async def salesforce_pipeline(
    timeframe: Annotated[
        str,
        Field(
            description="Time period to analyze (default: THIS_QUARTER). Examples: THIS_MONTH, THIS_YEAR, LAST_QUARTER"
        ),
    ] = "THIS_QUARTER",
    owner_id: Annotated[
        str | None, Field(description="Optional: Specific sales rep ID to analyze")
    ] = None,
    include_forecasting: Annotated[
        bool, Field(description="Include forecast calculations (default: false)")
    ] = False,
) -> str:
    """Comprehensive sales pipeline analysis with forecasting and conversion rates."""
    try:
        client = get_client()
        result = await client.get_pipeline_analysis(
            timeframe, owner_id, include_forecasting
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_case_insights(
    timeframe: Annotated[
        str,
        Field(
            description="Time period to analyze (default: THIS_MONTH). Examples: THIS_WEEK, THIS_QUARTER"
        ),
    ] = "THIS_MONTH",
    priority: Annotated[
        str | None,
        Field(
            description="Filter by case priority (e.g., High, Medium, Low, Critical)"
        ),
    ] = None,
    status: Annotated[
        str | None,
        Field(
            description="Filter by case status (e.g., New, Working, Escalated, Closed)"
        ),
    ] = None,
) -> str:
    """Support case analysis including volume, resolution times, and escalations."""
    try:
        client = get_client()
        result = await client.get_case_insights(timeframe, priority, status)
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_lead_funnel(
    source: Annotated[
        str | None,
        Field(
            description="Optional: Filter by lead source (e.g., Website, Partner, Event)"
        ),
    ] = None,
    timeframe: Annotated[
        str, Field(description="Time period to analyze (default: THIS_QUARTER)")
    ] = "THIS_QUARTER",
    conversion_stage: Annotated[
        str, Field(description="Target conversion stage (default: Opportunity)")
    ] = "Opportunity",
) -> str:
    """Lead conversion funnel analysis by source with quality metrics."""
    try:
        client = get_client()
        result = await client.get_lead_funnel_analysis(
            source, timeframe, conversion_stage
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


@mcp.tool
async def salesforce_opportunities_by_partner(
    partner_name: Annotated[
        str,
        Field(
            description='The partner name to search for (e.g., "Inetum - Spain (Partner)", "Accenture", "Deloitte")'
        ),
    ],
    is_closed: Annotated[
        bool | None,
        Field(
            description="Optional: Filter by IsClosed status (true for closed deals, false for open pipeline, omit for all)"
        ),
    ] = None,
    stage_name: Annotated[
        str | None,
        Field(
            description='Optional: Filter by specific stage (e.g., "Prospecting", "Negotiation", "Closed Won")'
        ),
    ] = None,
    min_amount: Annotated[
        float | None,
        Field(description="Optional: Minimum opportunity amount to include"),
    ] = None,
    start_date: Annotated[
        str | None,
        Field(description="Optional: Start date filter (YYYY-MM-DD format)"),
    ] = None,
    end_date: Annotated[
        str | None,
        Field(description="Optional: End date filter (YYYY-MM-DD format)"),
    ] = None,
    limit: Annotated[
        int, Field(description="Maximum number of results (default: 100)")
    ] = 100,
) -> str:
    """Find opportunities by partner name. This tool automatically handles the lookup relationship syntax (Partner__r.Name) so you can just provide the partner name directly.

    Use this instead of manually constructing SOQL queries with Partner__c fields.

    Example: To find deals with "Inetum - Spain (Partner)", just pass that as the partner_name parameter.
    """
    try:
        client = get_client()
        result = await client.get_opportunities_by_partner(
            partner_name=partner_name,
            is_closed=is_closed,
            stage_name=stage_name,
            min_amount=min_amount,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return format_result(result)
    except SalesforceError as e:
        return f"Error: {e}"


# =============================================================================
# Channel Director Prompts (14 prompts)
# =============================================================================


@mcp.prompt(
    name="quarterly_pipeline",
    description="Analyze open pipeline for a specific quarter with partner breakdown",
    tags={"pipeline", "quarterly", "channel-director"},
)
def prompt_quarterly_pipeline(
    quarter: Annotated[
        str,
        Field(description="Fiscal quarter: Q1, Q2, Q3, or Q4 (FY27: Feb 2026 - Jan 2027)"),
    ] = "Q1",
) -> str:
    """Quarterly open pipeline analysis with country and partner breakdown."""
    return quarterly_pipeline_analysis(quarter)


@mcp.prompt(
    name="closed_won_partners",
    description="Analyze Closed-Won deals with partner contribution metrics",
    tags={"revenue", "partners", "channel-director"},
)
def prompt_closed_won_partners(
    quarter: Annotated[
        str, Field(description="Specific quarter (Q1-Q4) or leave empty for full year")
    ] = "",
    full_year: Annotated[
        bool, Field(description="Analyze full fiscal year FY27")
    ] = True,
) -> str:
    """Closed-Won partner contribution analysis."""
    return closed_won_partner_analysis(quarter, full_year)


@mcp.prompt(
    name="partner_health",
    description="Health check on partner engagement across active opportunities",
    tags={"partners", "engagement", "channel-director"},
)
def prompt_partner_health() -> str:
    """Partner engagement health check - identifies gaps and late-stage alerts."""
    return partner_engagement_health()


@mcp.prompt(
    name="partner_sourced",
    description="Analyze top partner-sourced opportunities",
    tags={"partners", "sourcing", "channel-director"},
)
def prompt_partner_sourced(
    limit: Annotated[
        int, Field(description="Number of top deals to show")
    ] = 10,
) -> str:
    """Top partner-sourced pipeline analysis."""
    return partner_sourced_pipeline(limit)


@mcp.prompt(
    name="at_risk_pipeline",
    description="Identify at-risk opportunities: late stage but low probability",
    tags={"risk", "pipeline", "channel-director"},
)
def prompt_at_risk() -> str:
    """At-risk pipeline analysis - late stage with low probability."""
    return at_risk_pipeline()


@mcp.prompt(
    name="new_vs_existing",
    description="Analyze pipeline split between new and existing business",
    tags={"pipeline", "business-type", "channel-director"},
)
def prompt_new_vs_existing(
    quarter: Annotated[
        str, Field(description="Specific quarter (Q1-Q4) or leave empty for full year")
    ] = "",
) -> str:
    """New vs Existing business analysis with partner coverage."""
    return new_vs_existing_business(quarter)


@mcp.prompt(
    name="lead_conversion",
    description="Analyze lead funnel with partner attribution tracking",
    tags={"leads", "conversion", "channel-director"},
)
def prompt_lead_conversion() -> str:
    """Lead conversion and partner attribution analysis."""
    return lead_conversion_analysis()


@mcp.prompt(
    name="stalled_deals",
    description="Identify opportunities that haven't progressed recently",
    tags={"risk", "pipeline", "channel-director"},
)
def prompt_stalled_deals(
    days_stalled: Annotated[
        int, Field(description="Number of days without activity to flag as stalled")
    ] = 60,
) -> str:
    """Stalled opportunities analysis."""
    return stalled_opportunities(days_stalled)


@mcp.prompt(
    name="country_dashboard",
    description="Generate a country-level pipeline dashboard",
    tags={"dashboard", "regional", "channel-director"},
)
def prompt_country_dashboard(
    quarter: Annotated[
        str, Field(description="Specific quarter (Q1-Q4) or leave empty for full year")
    ] = "",
) -> str:
    """Country-level pipeline dashboard with partner coverage."""
    return country_pipeline_dashboard(quarter)


@mcp.prompt(
    name="forecast_vs_actuals",
    description="Compare forecast (weighted pipeline) vs actual closed revenue",
    tags={"forecast", "quarterly", "channel-director"},
)
def prompt_forecast_vs_actuals(
    quarter: Annotated[
        str, Field(description="Fiscal quarter: Q1, Q2, Q3, or Q4")
    ] = "Q1",
) -> str:
    """Quarterly forecast vs actuals analysis."""
    return forecast_vs_actuals(quarter)


@mcp.prompt(
    name="partner_scorecard",
    description="Generate a performance scorecard for partners",
    tags={"partners", "performance", "channel-director"},
)
def prompt_partner_scorecard(
    partner_name: Annotated[
        str, Field(description="Specific partner name or leave empty for all partners")
    ] = "",
) -> str:
    """Partner performance scorecard - individual or leaderboard."""
    return partner_scorecard(partner_name)


@mcp.prompt(
    name="weekly_briefing",
    description="Generate a weekly briefing for the Channel Director",
    tags={"briefing", "weekly", "channel-director"},
)
def prompt_weekly_briefing() -> str:
    """Weekly Channel Director briefing - quick overview of key metrics."""
    return weekly_briefing()


@mcp.prompt(
    name="partner_qbr",
    description="Prepare data for a Quarterly Business Review with a partner",
    tags={"partners", "qbr", "channel-director"},
)
def prompt_partner_qbr(
    partner_name: Annotated[
        str, Field(description="Partner name for QBR preparation")
    ],
    quarter: Annotated[
        str, Field(description="Fiscal quarter: Q1, Q2, Q3, or Q4")
    ] = "Q1",
) -> str:
    """QBR preparation report for a specific partner."""
    return partner_qbr_prep(partner_name, quarter)


@mcp.prompt(
    name="competitive_analysis",
    description="Analyze deals where competitors are involved",
    tags={"competitive", "win-loss", "channel-director"},
)
def prompt_competitive(
    competitor: Annotated[
        str, Field(description="Specific competitor name or leave empty for all")
    ] = "",
) -> str:
    """Competitive deal analysis with partner impact."""
    return competitive_analysis(competitor)


# =============================================================================
# Southern Europe Channel Intelligence Tools
# =============================================================================


@mcp.tool
async def get_revenue(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, Q1, Q2, Q3, Q4, THIS_QUARTER, LAST_QUARTER, LAST_FISCAL_YEAR, NEXT_60_DAYS, LAST_30_DAYS)")],
    breakdown: Annotated[str, Field(description="Aggregation breakdown: total | country | quarter | partner")] = "total",
    limit: Annotated[int, Field(description="Max rows for grouped breakdowns (default 10, max 50)")] = 10,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c value (leave blank for all)")] = None,
    partner_name: Annotated[str | None, Field(description="Filter by partner name (partial match)")] = None,
    country: Annotated[str | None, Field(description="Filter by billing country (exact match)")] = None,
    territory: Annotated[str | None, Field(description="Territory name for target lookup (e.g. 'South_Europe' from config)")] = None,
    revenue_target: Annotated[int | None, Field(description="Override revenue target (if not using config-based lookup)")] = None,
) -> str:
    """Closed-Won revenue analytics for Southern Europe (Italy, Spain, Portugal, Greece, Cyprus, Malta).

    Now with optional territory/revenue_target parameters to fetch targets from config and calculate attainment %.
    Example: get_revenue(period="THIS_FISCAL_YEAR", territory="South_Europe", country="Italy")
    → Returns revenue + target from config + attainment %
    """
    try:
        result = await ci.get_revenue(
            get_client(), period, breakdown, limit,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
            partner_name, country, territory, revenue_target,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_pipeline(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, Q1, THIS_QUARTER, NEXT_QUARTER, CURRENT_AND_NEXT_QUARTER)")],
    breakdown: Annotated[str, Field(description="Aggregation breakdown: total | country | stage | quarter | partner")] = "total",
    limit: Annotated[int, Field(description="Max rows for grouped breakdowns (default 10, max 50)")] = 10,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c (leave blank for all)")] = None,
    partner_name: Annotated[str | None, Field(description="Filter by partner name (partial match)")] = None,
    country: Annotated[str | None, Field(description="Filter by billing country")] = None,
) -> str:
    """Open pipeline analytics for Southern Europe. Excludes Closed Won and Closed Lost."""
    try:
        result = await ci.get_pipeline(
            get_client(), period, breakdown, limit,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
            partner_name, country,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_top_partners(
    metric: Annotated[str, Field(description="Metric to rank by: revenue | pipeline")],
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_QUARTER, THIS_FISCAL_YEAR)")],
    limit: Annotated[int, Field(description="Number of top partners to return (default 10, max 50)")] = 10,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c (leave blank for all)")] = None,
) -> str:
    """Top partners ranked by closed-won revenue or open pipeline for Southern Europe."""
    try:
        result = await ci.get_top_partners(
            get_client(), metric, period, limit,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_partner_detail(
    partner_name: Annotated[str, Field(description="Partner name (partial match supported)")],
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, THIS_QUARTER)")],
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c (leave blank for all)")] = None,
    open_opp_limit: Annotated[int, Field(description="Max open opportunities to list (default 20)")] = 20,
) -> str:
    """Detailed scorecard for a single partner: revenue, pipeline, win rate, open deals."""
    try:
        result = await ci.get_partner_detail(
            get_client(), partner_name, period,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
            open_opp_limit,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_partner_pipeline(
    partner_name: Annotated[str, Field(description="Partner name (partial match supported)")],
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, THIS_QUARTER)")],
    open_opp_limit: Annotated[int, Field(description="Max open opportunities to list (default 20)")] = 20,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c (leave blank for all)")] = None,
) -> str:
    """Partner-specific open pipeline summary with opportunity list in markdown format."""
    try:
        result = await ci.get_partner_pipeline(
            get_client(), partner_name, period, open_opp_limit,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def search_opportunities(
    query: Annotated[str, Field(description="Name fragment to search for in opportunity names")],
    period: Annotated[str, Field(description="Fiscal period to scope the search")] = "THIS_FISCAL_YEAR",
    partner_name: Annotated[str | None, Field(description="Optional partner name filter")] = None,
    country: Annotated[str | None, Field(description="Optional country filter (e.g. 'Italy', 'Spain', 'Greece')")] = None,
    limit: Annotated[int, Field(description="Max results (default 10, max 50)")] = 10,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Search opportunities by name fragment in Southern Europe, with optional partner/country and period filters."""
    try:
        result = await ci.search_opportunities(
            get_client(), query, partner_name, country, period, limit,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_opportunity_detail(
    opportunity_id: Annotated[str | None, Field(description="Salesforce opportunity ID (15/18 chars)")] = None,
    opportunity_name: Annotated[str | None, Field(description="Opportunity name (partial match)")] = None,
    partner_name: Annotated[str | None, Field(description="Optional partner name filter")] = None,
    country: Annotated[str | None, Field(description="Optional country filter (e.g. 'Italy', 'Spain', 'Greece')")] = None,
    period: Annotated[str | None, Field(description="Optional fiscal period filter")] = None,
    channel_manager: Annotated[str | None, Field(description="Optional Channel_Manager__c filter")] = None,
) -> str:
    """Full detail for a specific opportunity by ID or name. Returns markdown summary plus raw data.

    Example: get_opportunity_detail(country='Greece') to find opportunities in Greece
    """
    try:
        result = await ci.get_opportunity_detail(
            get_client(), opportunity_id, opportunity_name, partner_name, country, period,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_deal_registrations(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, THIS_QUARTER)")],
) -> str:
    """Count deal registrations (Deal_Registration__c) for the given period."""
    try:
        result = await ci.get_deal_registrations(get_client(), period)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_growth(
    metric: Annotated[str, Field(description="Metric to compare: revenue | pipeline")],
    period_a: Annotated[str, Field(description="Period A (the 'current' or 'newer' period)")],
    period_b: Annotated[str, Field(description="Period B (the 'prior' or 'comparison' period)")],
    breakdown: Annotated[str, Field(description="Aggregation: total | country | partner | quarter")] = "total",
    limit: Annotated[int, Field(description="Max rows for grouped breakdowns")] = 10,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Growth comparison between two fiscal periods (absolute and percentage change)."""
    try:
        result = await ci.get_growth(
            get_client(), metric, period_a, period_b, breakdown, limit,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_orphan_hygiene(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_QUARTER, THIS_FISCAL_YEAR)")],
    limit: Annotated[int, Field(description="Max orphan opportunities to list (default 20)")] = 20,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Open opportunities missing a primary partner (Partner__c = null). Breakdown by stage and country."""
    try:
        result = await ci.get_orphan_hygiene(
            get_client(), period, limit,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_kpi_snapshot(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, THIS_QUARTER)")],
    revenue_target: Annotated[float | None, Field(description="Optional revenue target for coverage ratio calculation")] = None,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Core KPI bundle: revenue, pipeline, win rate, avg deal size, partner coverage, orphan %, concentration."""
    try:
        result = await ci.get_kpi_snapshot(
            get_client(), period, revenue_target,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def route_slash_command(
    input: Annotated[str, Field(description="Slash command string (e.g. /pipeline, /revenue, /top_partners revenue, /orphans, /pipeline partner Accenture)")],
    channel_manager: Annotated[str | None, Field(description="Default channel manager filter")] = None,
) -> str:
    """Deterministic slash command router. Supported: /pipeline, /revenue, /top_partners, /orphans, /pipeline partner <name>."""
    try:
        result = await ci.route_slash_command(
            get_client(), input,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def run_exploratory_analysis(
    intent: Annotated[str, Field(description="Natural language intent (e.g. 'show pipeline for Q2', 'top partners by revenue this quarter')")],
    channel_manager: Annotated[str | None, Field(description="Default channel manager filter")] = None,
) -> str:
    """Maps natural-language intents to canonical tools deterministically. Not a free-form AI query."""
    try:
        result = await ci.run_exploratory_analysis(
            get_client(), intent,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_opportunity_list(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, THIS_QUARTER)")] = "THIS_FISCAL_YEAR",
    partner_name: Annotated[str | None, Field(description="Filter by partner name (partial match)")] = None,
    country: Annotated[str | None, Field(description="Filter by billing country")] = None,
    stage: Annotated[str | None, Field(description="Filter by stage name (exact)")] = None,
    min_amount: Annotated[float | None, Field(description="Minimum opportunity amount")] = None,
    limit: Annotated[int, Field(description="Max results (default 20, max 100)")] = 20,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Paginated open opportunity list with filters for partner, country, stage, and amount."""
    try:
        result = await ci.get_opportunity_list(
            get_client(), partner_name, country, stage, min_amount, period, limit,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_partner_scorecard(
    partner_name: Annotated[str, Field(description="Partner name (exact or partial match)")],
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR)")] = "THIS_FISCAL_YEAR",
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Deep-dive partner scorecard: revenue, pipeline, deal count, avg deal size, countries, stages, quarterly trend."""
    try:
        result = await ci.get_partner_scorecard(
            get_client(), partner_name, period,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def list_available_metrics() -> str:
    """List all available tools, supported periods, metrics, and runtime configuration."""
    return format_result(ci.list_available_metrics())


@mcp.tool
async def admin_discover_targets(
    admin_key: Annotated[str, Field(description="Admin key (must match ADMIN_KEY env var)")],
    limit: Annotated[int, Field(description="Max records per query (default 30)")] = 30,
) -> str:
    """Admin-only: discover quota/target fields and objects in the Salesforce org."""
    try:
        result = await ci.admin_discover_targets(get_client(), admin_key, limit)
        return format_result(result)
    except (ValueError, PermissionError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_weighted_pipeline(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR, THIS_QUARTER)")] = "THIS_FISCAL_YEAR",
    breakdown: Annotated[str, Field(description="Aggregation: total | country | partner | stage")] = "total",
    limit: Annotated[int, Field(description="Max rows for breakdown (default 20)")] = 20,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
    min_probability: Annotated[float, Field(description="Minimum probability % to include (default 0)")] = 0,
) -> str:
    """Open pipeline weighted by probability (Amount × Probability / 100). Provides coverage ratio."""
    try:
        result = await ci.get_weighted_pipeline(
            get_client(), period, breakdown, limit,
            channel_manager if channel_manager is not None else "",
            min_probability,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_channel_manager_performance(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR)")] = "THIS_FISCAL_YEAR",
    metric: Annotated[str, Field(description="Metric filter: revenue | pipeline | both")] = "both",
    limit: Annotated[int, Field(description="Max managers to return (default 20)")] = 20,
    channel_manager: Annotated[str | None, Field(description="Scope to specific manager (leave blank for all)")] = None,
) -> str:
    """Channel manager performance leaderboard: revenue, pipeline, deal count, and win rate."""
    try:
        result = await ci.get_channel_manager_performance(
            get_client(), period, metric, limit,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_multi_period_trend(
    metric: Annotated[str, Field(description="Metric: revenue | pipeline")] = "revenue",
    periods: Annotated[list[str] | None, Field(description="List of fiscal periods to compare (max 8, e.g. ['Q1','Q2','Q3','Q4'])")] = None,
    breakdown: Annotated[str, Field(description="Aggregation: total | country | partner")] = "total",
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Multi-period trend analysis — compare revenue or pipeline across up to 8 fiscal periods."""
    try:
        result = await ci.get_multi_period_trend(
            get_client(), metric, periods, breakdown,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_deal_registrations_breakdown(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR)")] = "THIS_FISCAL_YEAR",
    breakdown: Annotated[str, Field(description="Aggregation: total | partner | country")] = "total",
    limit: Annotated[int, Field(description="Max rows for breakdown (default 20)")] = 20,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Deal registration count with optional breakdown by partner or country."""
    try:
        result = await ci.get_deal_registrations_breakdown(
            get_client(), period, breakdown, limit,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_win_rate_by_country(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR)")] = "THIS_FISCAL_YEAR",
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Win rate analysis by country: won deals, total deals, revenue, and average deal size."""
    try:
        result = await ci.get_win_rate_by_country(
            get_client(), period,
            channel_manager if channel_manager is not None else "",
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_time_to_close_stats(
    period: Annotated[str, Field(description="Fiscal period (e.g. THIS_FISCAL_YEAR)")] = "THIS_FISCAL_YEAR",
    breakdown: Annotated[str, Field(description="Aggregation: total | country | partner | stage")] = "total",
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Time-to-close statistics for Closed Won deals: avg, median, min, max days from creation to close."""
    try:
        result = await ci.get_time_to_close_stats(
            get_client(), period, breakdown,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


# =============================================================================
# PHASE 1: Activity, Risk, Lost Deals, Stage Velocity Tools
# =============================================================================

@mcp.tool
async def get_stalled_deals(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER, THIS_FISCAL_YEAR)")] = "THIS_QUARTER",
    days_threshold: Annotated[int, Field(description="Days without modification (default 60)")] = 60,
    stage_filter: Annotated[str | None, Field(description="Filter by stage name (e.g., Prospecting)")] = None,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Find deals that haven't been modified in X days.

    Identifies stalled/at-risk opportunities by modification age. Useful for bottleneck detection.
    """
    try:
        result = await ci.get_stalled_deals(get_client(), period, days_threshold, stage_filter, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_partner_activity_summary(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER)")] = "THIS_QUARTER",
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Partner activity summary based on deal modification frequency.

    Shows open pipeline, deal count, and last deal activity for each partner.
    Proxy for engagement level (who's active vs. who's gone quiet).
    """
    try:
        result = await ci.get_partner_activity_summary(get_client(), period, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_opportunity_recency(
    opportunity_id_or_name: Annotated[str, Field(description="Opportunity ID or name fragment")],
) -> str:
    """Get opportunity details including modification recency.

    Shows last modified date and days since activity for a specific deal.
    """
    try:
        result = await ci.get_opportunity_recency(get_client(), opportunity_id_or_name)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_lost_deals(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER)")] = "THIS_QUARTER",
    group_by: Annotated[str | None, Field(description="Group by: 'stage', 'partner', 'country', or None for total")] = None,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Analyze lost deals by count, amount, and grouping.

    Shows loss rate and identifies where deals are being lost (stage, partner, country).
    """
    try:
        result = await ci.get_lost_deals(get_client(), period, group_by, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_new_vs_existing(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER)")] = "THIS_QUARTER",
    breakdown: Annotated[str | None, Field(description="Breakdown by: 'partner', 'country', or None for total")] = None,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """New business vs. existing/renewal business split.

    Shows revenue and pipeline breakdown by Type (New Business vs. Renewal/Expansion).
    """
    try:
        result = await ci.get_new_vs_existing(get_client(), period, breakdown, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_stage_risk_profile(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER)")] = "THIS_QUARTER",
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Stage risk profile: probability distribution and confidence by stage.

    Identifies high-risk stages (avg prob < 40%), medium (40-60%), low (> 60%).
    Useful for forecast confidence assessment.
    """
    try:
        result = await ci.get_stage_risk_profile(get_client(), period, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_deal_aging_by_stage(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER)")] = "THIS_QUARTER",
    days_threshold: Annotated[int, Field(description="Aging threshold in days (default 60)")] = 60,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Bottleneck detection: deal aging by stage.

    Shows how many deals are stalled in each stage (aged beyond threshold).
    """
    try:
        result = await ci.get_deal_aging_by_stage(get_client(), period, days_threshold, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_high_risk_deals(
    period: Annotated[str, Field(description="Time period (e.g., THIS_QUARTER)")] = "THIS_QUARTER",
    probability_threshold: Annotated[int, Field(description="Probability threshold % (default 40)")] = 40,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """High-risk deals: low probability + closing soon.

    Alerts on deals with probability < threshold AND closing within 30 days.
    Useful for early intervention.
    """
    try:
        result = await ci.get_high_risk_deals(get_client(), period, probability_threshold, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def get_stage_progression_velocity(
    lookback_period: Annotated[str, Field(description="Historical period for velocity (default LAST_FISCAL_YEAR)")] = "LAST_FISCAL_YEAR",
    lookback_periods: Annotated[int, Field(description="Number of periods to analyze (default 4)")] = 4,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c")] = None,
) -> str:
    """Historical stage progression velocity and current deal aging.

    Shows average days in each stage (from closed-won deals) and identifies current deals that are aged vs. historical norms.
    """
    try:
        result = await ci.get_stage_progression_velocity(get_client(), lookback_period, lookback_periods, channel_manager)
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


@mcp.tool
async def generate_partner_qbr(
    partner_name: Annotated[str, Field(description="Partner name (partial match supported, e.g. 'Inetum Spain')")],
    period: Annotated[str, Field(description="Review period (e.g. THIS_QUARTER, LAST_QUARTER, FY27_Q1, FY26_Q4)")] = "THIS_QUARTER",
    prior_period: Annotated[str | None, Field(description="Comparison period for YoY (auto-calculated as same quarter 1 FY back if not provided)")] = None,
    channel_manager: Annotated[str | None, Field(description="Filter by Channel_Manager__c (leave blank for all)")] = None,
    revenue_target: Annotated[float | None, Field(description="Optional revenue target — enables attainment % and pipeline coverage % in the report")] = None,
    top_opps_limit: Annotated[int, Field(description="Number of top open opportunities to include (default 10, max 20)")] = 10,
) -> str:
    """Generate a complete QBR document for a partner.

    Returns a structured markdown report covering:
    - Business Performance: closed-won revenue, YoY growth, win rate, avg deal size, time to close, deal registrations
    - Pipeline Health: open pipeline by stage with top opportunities list
    - Geography: revenue and pipeline breakdown by country
    - Forward Looking: next quarter pipeline and deals closing in 60 days

    Example: generate_partner_qbr(partner_name='Inetum Spain', period='FY27_Q1', revenue_target=500000)
    """
    try:
        result = await ci.generate_partner_qbr(
            get_client(), partner_name, period, prior_period,
            channel_manager if channel_manager is not None else ci.DEFAULT_CHANNEL_MANAGER,
            revenue_target, top_opps_limit,
        )
        return format_result(result)
    except (ValueError, Exception) as e:
        return f"Error: {e}"


# =============================================================================
# Request logging middleware
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.method == "POST":
            client_ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or (request.client.host if request.client else "unknown")
            )
            try:
                body_bytes = await request.body()
                body = json.loads(body_bytes)
                method = body.get("method", "?")
                if method == "tools/call":
                    tool = body.get("params", {}).get("name", "?")
                    logger.info(f"{client_ip} | {method} | tool={tool}")
                else:
                    logger.info(f"{client_ip} | {method}")
            except Exception:
                logger.info(f"{client_ip} | [unparseable request]")

        return await call_next(request)


# =============================================================================
# Main entry point
# =============================================================================


def main():
    """Run the MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    ssl_certfile = os.getenv("MCP_SSL_CERTFILE")
    ssl_keyfile = os.getenv("MCP_SSL_KEYFILE")

    if transport == "stdio":
        mcp.run()
    else:
        kwargs = {"transport": transport, "host": host, "port": port}
        if ssl_certfile and ssl_keyfile:
            kwargs["uvicorn_config"] = {
                "ssl_certfile": ssl_certfile,
                "ssl_keyfile": ssl_keyfile,
            }
        # Attach request logging middleware
        mcp.http_app().add_middleware(RequestLoggerMiddleware)
        mcp.run(**kwargs)


if __name__ == "__main__":
    main()
