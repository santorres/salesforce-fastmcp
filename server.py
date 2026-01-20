"""FastMCP server for Salesforce integration."""

import json
from typing import Annotated, Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field

from salesforce_client import SalesforceClient, SalesforceError

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
# Main entry point
# =============================================================================


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
