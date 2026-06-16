#!/usr/bin/env python3
"""
Channel Intelligence CLI — Direct access to Salesforce analytics.

Usage:
  channel kpi [--period PERIOD] [--json] [--channel-manager MANAGER]
  channel revenue [--period PERIOD] [--breakdown TYPE] [--json]
  channel pipeline [--period PERIOD] [--breakdown TYPE] [--json]
  channel partner NAME [--period PERIOD] [--json]
  channel qbr NAME [--period PERIOD] [--revenue-target AMOUNT] [--json]
  channel risk [--period PERIOD] [--json]
  channel registrations [--period PERIOD] [--json]
  channel top-partners [--period PERIOD] [--limit LIMIT] [--metric METRIC] [--json]

Examples:
  channel kpi
  channel revenue --period THIS_FISCAL_YEAR
  channel partner "Inetum Spain" --period FY27_Q1
  channel qbr Accenture
  channel risk --json | jq '.data[] | select(.days_to_close < 14)'
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

import click

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesforce_client import SalesforceClient
import channel_intelligence as ci
from auth_provider import create_auth_provider

# Configure logging
logger = logging.getLogger(__name__)

# Global auth provider and credentials
_auth_provider = None
_credentials = None


async def _initialize_auth():
    """Initialize authentication using auth_provider.
    
    Uses SF CLI if available, falls back to .env environment variables.
    """
    global _auth_provider, _credentials
    
    try:
        _auth_provider = create_auth_provider()
        _credentials = await _auth_provider.get_credentials()
        
        logger.debug(
            f"Authentication successful: "
            f"{_credentials.auth_method} (user: {_credentials.username or 'unknown'})"
        )
    except Exception as e:
        logger.error(f"Authentication initialization failed: {e}")
        raise


def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation using secure authentication.
    
    Returns a Salesforce client configured with credentials from either
    SF CLI (if available) or environment variables (.env file).
    """
    if _credentials is None:
        raise click.ClickException(
            "Authentication not initialized. "
            "This should not happen - auth should be initialized on CLI startup."
        )
    
    return SalesforceClient(
        base_url=_credentials.base_url,
        access_token=_credentials.access_token
    )


def format_json(data) -> str:
    """Format data as indented JSON."""
    return json.dumps(data, indent=2, default=str)


def format_kpi(data: dict) -> str:
    """Pretty-format KPI snapshot."""
    result = data.get("data", {})
    lines = []
    lines.append("KPI Snapshot")
    lines.append("-" * 50)

    revenue = result.get("revenue", 0)
    if revenue:
        lines.append(f"Revenue (Closed-Won): ${revenue:,.0f}")
        lines.append(f"  Deals: {result.get('dealCount', 0)}")
        attainment = result.get("attainmentPct")
        if attainment:
            lines.append(f"  Attainment: {attainment:.1f}%")

    pipeline = result.get("pipeline", 0)
    if pipeline:
        lines.append(f"\nPipeline (Open): ${pipeline:,.0f}")

    coverage = result.get("coverageRatio")
    if coverage:
        lines.append(f"\nCoverage Ratio: {coverage:.1f}x")

    win_rate = result.get("winRate", 0)
    if win_rate:
        lines.append(f"Win Rate: {win_rate * 100:.1f}%")

    active_partners = result.get("activePartners")
    if active_partners:
        lines.append(f"Active Partners: {active_partners}")

    return "\n".join(lines)


def format_revenue(data: dict) -> str:
    """Pretty-format revenue data."""
    result = data.get("data", {})
    lines = []
    lines.append("Revenue Summary")
    lines.append("-" * 50)

    if isinstance(result, list):
        # Breakdown response
        for item in result:
            label = item.get("partner") or item.get("country") or item.get("quarter") or item.get("stage") or "Unknown"
            amount = item.get("totalRevenue", 0)
            deal_count = item.get("dealCount", 0)
            attainment = item.get("attainmentPct")

            if attainment:
                lines.append(f"{label}: ${amount:,.0f} ({attainment:.1f}% attainment, {deal_count} deals)")
            else:
                lines.append(f"{label}: ${amount:,.0f} ({deal_count} deals)")
    else:
        # Summary response
        amount = result.get("totalRevenue", 0)
        attainment = result.get("attainmentPct")
        count = result.get("dealCount", 0)
        lines.append(f"Closed-Won: ${amount:,.0f}")
        lines.append(f"Deals: {count}")
        if attainment:
            lines.append(f"Attainment: {attainment:.1f}%")
        target = result.get("target")
        if target:
            lines.append(f"Target: ${target:,.0f}")

    return "\n".join(lines)


def format_pipeline(data: dict) -> str:
    """Pretty-format pipeline data."""
    result = data.get("data", {})
    lines = []
    lines.append("Pipeline Summary")
    lines.append("-" * 50)

    if isinstance(result, list):
        # Breakdown response
        for item in result:
            label = item.get("partner") or item.get("country") or item.get("stage") or item.get("quarter") or "Unknown"
            amount = item.get("totalAmount", 0)
            count = item.get("dealCount", 0)
            lines.append(f"{label}: ${amount:,.0f} ({count} deals)")
    else:
        # Summary response
        amount = result.get("totalAmount", 0)
        count = result.get("dealCount", 0)
        lines.append(f"Open Pipeline: ${amount:,.0f}")
        lines.append(f"Deal Count: {count}")

        by_stage = result.get("byStage", {})
        if by_stage:
            lines.append("\nBy Stage:")
            for stage, value in by_stage.items():
                lines.append(f"  {stage}: ${value:,.0f}")

    return "\n".join(lines)


def format_partner(data: dict) -> str:
    """Pretty-format partner scorecard."""
    name = data.get("partner", "Partner")
    result = data.get("data", {})
    lines = []
    lines.append(f"Partner Scorecard: {name}")
    lines.append("=" * 60)

    # Revenue
    revenue = result.get("revenue", 0)
    if revenue:
        lines.append("\nRevenue")
        lines.append("-" * 40)
        lines.append(f"  Closed-Won: ${revenue:,.0f}")
        lines.append(f"  Deals: {result.get('dealCount', 0)}")

    # Pipeline
    pipeline = result.get("pipeline", 0)
    if pipeline:
        lines.append("\nPipeline")
        lines.append("-" * 40)
        lines.append(f"  Open: ${pipeline:,.0f}")

    # Metrics
    avg_deal = result.get("avgDealSize", 0)
    if avg_deal:
        lines.append(f"\nAvg Deal Size: ${avg_deal:,.0f}")

    # Top countries
    top_countries = result.get("topCountries", [])
    if top_countries:
        lines.append(f"\nTop Countries: {', '.join(top_countries)}")

    # Stages
    open_stages = result.get("openStages", [])
    if open_stages:
        lines.append("\nOpen by Stage:")
        for stage_info in open_stages:
            stage = stage_info.get("stage", "Unknown")
            count = stage_info.get("count", 0)
            lines.append(f"  {stage}: {count} deals")

    return "\n".join(lines)


def format_qbr(data: dict) -> str:
    """QBR returns markdown report."""
    return data.get("markdown_report", "No QBR data available")


def format_risk(data: dict) -> str:
    """Pretty-format high-risk deals."""
    result = data.get("deals", [])
    lines = []
    threshold = data.get("probability_threshold_pct", 40)
    total = data.get("total_high_risk", 0)

    lines.append(f"High-Risk Deals (probability < {threshold}%, closing within 30 days)")
    lines.append("=" * 80)

    if not result:
        lines.append("No high-risk deals found. ✓")
        return "\n".join(lines)

    lines.append(f"Found: {total} deal(s)\n")

    for deal in result:
        lines.append(f"\n{deal.get('name', 'Unknown')}")
        lines.append("-" * 60)
        lines.append(f"  Amount: ${deal.get('amount', 0):,.0f}")
        lines.append(f"  Probability: {deal.get('probability', 0):.0f}%")
        lines.append(f"  Close Date: {deal.get('closeDate', 'N/A')}")
        lines.append(f"  Days to Close: {deal.get('daysUntilClose', 0)}")
        lines.append(f"  Stage: {deal.get('stage', 'N/A')}")
        lines.append(f"  Partner: {deal.get('partner', 'N/A')}")
        lines.append(f"  Risk Score: {deal.get('riskScore', 0):.0f}")
        lines.append(f"  Action: {deal.get('recommendation', 'Monitor')}")

    return "\n".join(lines)


def format_registrations(data: dict) -> str:
    """Pretty-format deal registrations trend."""
    result = data.get("data", [])
    lines = []
    lines.append("Deal Registrations Trend")
    lines.append("=" * 80)

    if not result:
        lines.append("No data available.")
        return "\n".join(lines)

    # Header row
    lines.append(f"{'Quarter':<12} {'Count':>8} {'Amount':>12} {'Approval %':>12} {'Close %':>10}")
    lines.append("-" * 80)

    for row in result:
        quarter = row.get("quarter", "Unknown")
        count = row.get("total_count", 0)
        amount = row.get("total_amount", 0)
        approval = row.get("approval_rate_pct", 0)
        close = row.get("close_rate_pct", 0)
        lines.append(f"{quarter:<12} {count:>8} ${amount:>11,.0f} {approval:>11.1f}% {close:>9.1f}%")

    return "\n".join(lines)


def format_top_partners(data: dict) -> str:
    """Pretty-format top partners leaderboard."""
    result = data.get("data", [])
    lines = []
    metric = data.get("metric", "revenue").title()
    lines.append(f"Top Partners by {metric}")
    lines.append("=" * 60)

    if not result:
        lines.append("No data available.")
        return "\n".join(lines)

    # Header row
    lines.append(f"{'#':<3} {'Partner Name':<30} {metric:>15}")
    lines.append("-" * 60)

    for i, partner in enumerate(result, 1):
        name = partner.get("partner_name", "Unknown")[:28]
        value = partner.get(f"total_{metric.lower()}", partner.get("total_amount", 0))
        if isinstance(value, (int, float)):
            lines.append(f"{i:<3} {name:<30} ${value:>14,.0f}")
        else:
            lines.append(f"{i:<3} {name:<30} {value:>15}")

    return "\n".join(lines)


def handle_error(error: Exception, context: str = "") -> None:
    """Print error and exit."""
    click.secho(f"Error{f' ({context})' if context else ''}: {str(error)}", fg="red", err=True)
    sys.exit(1)


@click.group()
def cli():
    """Channel Intelligence CLI — Salesforce analytics from the command line."""
    # Initialize authentication when CLI starts
    try:
        asyncio.run(_initialize_auth())
    except Exception as e:
        raise click.ClickException(
            f"Failed to initialize authentication: {e}\n\n"
            "Please ensure one of the following:\n"
            "  1. Salesforce CLI is installed and authenticated:\n"
            "     https://developer.salesforce.com/tools/salesforcecli\n"
            "     Run: sf org login web\n\n"
            "  2. Or set environment variables:\n"
            "     export SALESFORCE_BASE_URL=https://your-org.salesforce.com/services/data/v59.0\n"
            "     export SALESFORCE_ACCESS_TOKEN=<your_token>\n\n"
            "For more info, see: AUTHENTICATION_QUICKSTART.md"
        )


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period (default: THIS_QUARTER)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def kpi(period, output_json, channel_manager):
    """Get KPI snapshot: revenue, pipeline, win rate, coverage."""
    try:
        result = asyncio.run(ci.get_kpi_snapshot(
            get_sf(),
            _normalize_period(period),
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_kpi(result))
    except Exception as e:
        handle_error(e, "kpi")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--breakdown", default="total", type=click.Choice(["total", "partner", "country", "quarter"]), help="Breakdown dimension")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def revenue(period, breakdown, output_json, channel_manager):
    """Get revenue: closed-won amount, attainment %, deals."""
    try:
        result = asyncio.run(ci.get_revenue(
            get_sf(),
            _normalize_period(period),
            breakdown=breakdown,
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_revenue(result))
    except Exception as e:
        handle_error(e, "revenue")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--breakdown", default="total", type=click.Choice(["total", "partner", "country", "stage", "quarter"]), help="Breakdown dimension")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def pipeline(period, breakdown, output_json, channel_manager):
    """Get pipeline: open opportunities, by stage, by partner."""
    try:
        result = asyncio.run(ci.get_pipeline(
            get_sf(),
            _normalize_period(period),
            breakdown=breakdown,
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_pipeline(result))
    except Exception as e:
        handle_error(e, "pipeline")


@cli.command()
@click.argument("partner_name")
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def partner(partner_name, period, output_json):
    """Get partner scorecard: revenue, pipeline, win rate, activity."""
    try:
        result = asyncio.run(ci.get_partner_scorecard(
            get_sf(),
            partner_name,
            _normalize_period(period)
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_partner(result))
    except Exception as e:
        handle_error(e, f"partner ({partner_name})")


@cli.command()
@click.argument("partner_name")
@click.option("--period", default="THIS_QUARTER", help="Review period")
@click.option("--prior-period", default=None, help="Comparison period (auto-calculated if not set)")
@click.option("--revenue-target", default=None, type=float, help="Revenue quota/target amount")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def qbr(partner_name, period, prior_period, revenue_target, output_json):
    """Generate partner QBR: full business review with trends and forward-looking."""
    try:
        result = asyncio.run(ci.generate_partner_qbr(
            get_sf(),
            partner_name,
            period=_normalize_period(period),
            prior_period=_normalize_period(prior_period) if prior_period else None,
            revenue_target=revenue_target
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_qbr(result))
    except Exception as e:
        handle_error(e, f"qbr ({partner_name})")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--probability-threshold", default=40, type=int, help="Low probability threshold (default: 40%)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def risk(period, probability_threshold, output_json, channel_manager):
    """Get high-risk deals: low probability, closing soon (<30 days)."""
    try:
        result = asyncio.run(ci.get_high_risk_deals(
            get_sf(),
            _normalize_period(period),
            probability_threshold=probability_threshold,
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_risk(result))
    except Exception as e:
        handle_error(e, "risk")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def registrations(period, output_json, channel_manager):
    """Get deal registrations trend: count, amount, approval rate, close rate by quarter."""
    try:
        result = asyncio.run(ci.get_deal_registrations_trend(
            get_sf(),
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_registrations(result))
    except Exception as e:
        handle_error(e, "registrations")


@cli.command()
@click.option("--period", default="THIS_FISCAL_YEAR", help="Fiscal period")
@click.option("--metric", default="revenue", type=click.Choice(["revenue", "pipeline"]), help="Ranking metric")
@click.option("--limit", default=10, type=int, help="Number of partners to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def top_partners(period, metric, limit, output_json):
    """Get top partners: ranked by revenue or pipeline."""
    try:
        result = asyncio.run(ci.get_top_partners(
            get_sf(),
            metric=metric,
            period=_normalize_period(period),
            limit=limit
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_top_partners(result))
    except Exception as e:
        handle_error(e, f"top-partners ({metric})")


@cli.command()
@click.argument("query", required=True)
@click.option("--period", default="THIS_FISCAL_YEAR", help="Fiscal period")
@click.option("--stage", default=None, help="Filter by stage (e.g., 'Closed Won' for closed deals)")
@click.option("--partner", default=None, help="Filter by partner name")
@click.option("--country", default=None, help="Filter by country")
@click.option("--limit", default=30, type=int, help="Max results to return (default 30 to include multiple stages)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def search(query, period, stage, partner, country, limit, output_json):
    """Search opportunities by name fragment (returns all stages by default).

    Use --stage 'Closed Won' to see only closed-won deals.
    """
    try:
        result = asyncio.run(ci.search_opportunities(
            get_sf(),
            query=query,
            partner_name=partner,
            country=country,
            period=_normalize_period(period),
            limit=limit
        ))

        # Filter by stage if specified
        if stage:
            result["data"] = [opp for opp in result.get("data", []) if opp.get("stageName") == stage]
            result["stage_filter"] = stage

        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_opportunity_list(result))
    except Exception as e:
        handle_error(e, f"search ({query})")


@cli.command()
@click.option("--period", default="THIS_FISCAL_YEAR", help="Fiscal period (open opps only)")
@click.option("--partner", default=None, help="Filter by partner name")
@click.option("--country", default=None, help="Filter by country")
@click.option("--stage", default=None, help="Filter by stage (Prospecting, Validation, etc.)")
@click.option("--min-amount", default=None, type=float, help="Minimum opportunity amount")
@click.option("--limit", default=20, type=int, help="Max results (1-100)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def list_opps(period, partner, country, stage, min_amount, limit, output_json, channel_manager):
    """List open opportunities with optional filters."""
    try:
        result = asyncio.run(ci.get_opportunity_list(
            get_sf(),
            partner_name=partner,
            country=country,
            stage=stage,
            min_amount=min_amount,
            period=_normalize_period(period),
            limit=limit,
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_opportunity_list(result))
    except Exception as e:
        handle_error(e, "list-opps")


def format_opportunity_list(data: dict) -> str:
    """Pretty-format opportunity list (works for both search and list-opps)."""
    opps = data.get("data", [])
    lines = []
    lines.append(f"Opportunities ({len(opps)} found)")
    lines.append("=" * 130)

    if not opps:
        lines.append("No opportunities found.")
        return "\n".join(lines)

    # Header
    lines.append(f"{'Name':<40} {'Amount':>12} {'Stage':<20} {'Close Date':<12} {'Partner':<25} {'Prob %':>6}")
    lines.append("-" * 130)

    # Rows
    for opp in opps:
        name = opp.get("name", "-")[:38]
        amount = opp.get("amount", 0)
        # Handle both stageName (from search) and stage (from list-opps)
        stage = opp.get("stage") or opp.get("stageName") or "-"
        stage = str(stage)[:18]
        close_date = opp.get("closeDate", "-")
        partner = opp.get("partnerName") or opp.get("partner") or "-"
        partner = str(partner)[:23]
        probability = opp.get("probability", 0)

        lines.append(f"{name:<40} ${amount:>11,.0f} {stage:<20} {close_date:<12} {partner:<25} {probability:>5.0f}%")

    return "\n".join(lines)


def _normalize_period(period: str) -> str:
    """Normalize period string (delegates to channel_intelligence)."""
    return ci._normalize_period(period)


if __name__ == "__main__":
    cli()
