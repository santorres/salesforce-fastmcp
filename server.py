"""FastMCP server for Salesforce integration."""

import json
from typing import Annotated, Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field

from salesforce_client import SalesforceClient, SalesforceError
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
    """Execute SOQL queries against Salesforce."""
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
# Main entry point
# =============================================================================


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
