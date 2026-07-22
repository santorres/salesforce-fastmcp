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
  channel opportunities-by-status [--status STATUS] [--period PERIOD] [--limit LIMIT] [--json]
  channel partner-metrics [--breakdown TYPE] [--period PERIOD] [--json]
  channel top-partners [--period PERIOD] [--limit LIMIT] [--metric METRIC] [--json]

Examples:
  channel kpi
  channel revenue --period THIS_FISCAL_YEAR
  channel partner "Inetum Spain" --period FY27_Q1
  channel qbr Accenture
  channel opportunities-by-status
  channel opportunities-by-status --status Submitted --period THIS_QUARTER
  channel opportunities-by-status --status "Submitted,In Review" | head -20
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
from api import ChannelAnalyticsAPIImpl, AnalyticsRequest, DEFAULT_CHANNEL_MANAGER
from config.ci_config import COUNTRIES, COUNTRIES_EE

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


def get_api() -> ChannelAnalyticsAPIImpl:
    """Get Analytics API instance with authenticated client."""
    return ChannelAnalyticsAPIImpl(get_sf())


def format_json(data) -> str:
    """Format data as indented JSON."""
    return json.dumps(data, indent=2, default=str)


def format_kpi(data: dict) -> str:
    """Pretty-format KPI snapshot."""
    result = data.get("data", {})
    lines = []
    lines.append("KPI Snapshot")
    lines.append("=" * 80)

    # Revenue Section
    revenue = result.get("revenue", 0)
    if revenue:
        lines.append("\nRevenue (Closed-Won)")
        lines.append("-" * 40)
        lines.append(f"  Amount: ${revenue:,.0f}")
        deal_count = result.get("dealCount", 0)
        lines.append(f"  Deals: {deal_count}")
        attainment = result.get("attainmentPct")
        if attainment:
            lines.append(f"  Attainment: {attainment:.1f}%")
        avg_deal = result.get("averageDealSizeClosed", 0)
        if avg_deal:
            lines.append(f"  Avg Deal Size: ${avg_deal:,.0f}")

    # Pipeline Section
    pipeline = result.get("pipeline", 0)
    if pipeline:
        lines.append("\nPipeline (Open)")
        lines.append("-" * 40)
        lines.append(f"  Amount: ${pipeline:,.0f}")

    # Performance Section
    lines.append("\nPerformance Metrics")
    lines.append("-" * 40)
    
    win_rate = result.get("winRate", 0)
    if win_rate:
        lines.append(f"  Win Rate: {win_rate * 100:.1f}%")
    
    coverage = result.get("coverageRatio")
    if coverage:
        lines.append(f"  Coverage Ratio: {coverage:.1f}x")
    
    active_partners = result.get("activePartners")
    if active_partners:
        lines.append(f"  Active Partners: {active_partners}")
    
    focus_partners = result.get("focusPartners")
    if focus_partners:
        lines.append(f"  Focus Partners: {focus_partners:.0f}")

    # Risk Section
    lines.append("\nRisk Assessment")
    lines.append("-" * 40)
    
    orphan_open = result.get("orphanOpenCount", 0)
    orphan_pct = result.get("orphanOpenPct", 0)
    if orphan_open:
        lines.append(f"  Orphan Opportunities: {orphan_open:.0f} ({orphan_pct:.1f}%)")
    
    concentration = result.get("revenueConcentrationTop3", 0)
    if concentration:
        lines.append(f"  Revenue Concentration (Top 3): {concentration:.1f}%")

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
            label = (item.get("partnerName") or item.get("partner") or 
                    item.get("country") or item.get("quarter") or item.get("stage") or "Unknown")
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
        # Breakdown response - handle different field names for different breakdowns
        for item in result:
            # Different breakdowns use different field names:
            # - partner: partnerName
            # - country: country
            # - stage: stage
            # - quarter: quarter
            label = (item.get("partnerName") or item.get("partner") or 
                    item.get("country") or item.get("stage") or 
                    item.get("quarter") or "Unknown")
            # Note: channel_intelligence returns totalPipeline, totalRevenue, not totalAmount
            amount = item.get("totalPipeline") or item.get("totalRevenue") or item.get("totalAmount") or 0
            count = item.get("dealCount", 0)
            lines.append(f"{label}: ${amount:,.0f} ({count} deals)")
    else:
        # Summary response
        amount = result.get("totalPipeline") or result.get("totalAmount") or 0
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
    lines.append("=" * 80)

    if not result:
        lines.append("No data available.")
        return "\n".join(lines)

    # Header row
    lines.append(f"{'#':<3} {'Partner Name':<40} {metric:>20}")
    lines.append("-" * 80)

    for i, partner in enumerate(result, 1):
        # Try multiple name fields (camelCase and snake_case)
        name = (partner.get("partnerName") or
                partner.get("partner_name") or 
                partner.get("partner") or 
                partner.get("name") or 
                "Unknown")
        name = str(name)[:38]
        
        # Get the metric value (camelCase and snake_case)
        metric_lower = metric.lower()
        value = (partner.get(f"total{metric}") or
                partner.get(f"total_{metric_lower}") or 
                partner.get(f"{metric_lower}") or 
                partner.get("total_amount") or 
                partner.get("total_revenue") or 
                0)
        
        if isinstance(value, (int, float)):
            lines.append(f"{i:<3} {name:<40} ${value:>19,.0f}")
        else:
            lines.append(f"{i:<3} {name:<40} {value:>20}")

    return "\n".join(lines)


def format_opportunities_by_status(data: dict) -> str:
    """Pretty-format opportunities by registration status."""
    result = data.get("data", {})
    opportunities = result.get("opportunities", [])
    lines = []
    
    lines.append(f"Deal Registrations by Status: {data.get('registration_status', 'All')}")
    lines.append(f"Period: {data.get('period', {}).get('label', 'Unknown')}")
    lines.append("=" * 140)
    
    if not opportunities:
        lines.append(f"No Deal Registrations found (Total Amount: €{result.get('total_amount', 0):,.0f})")
        return "\n".join(lines)
    
    # Header row
    lines.append(
        f"{'Deal Name':<40} {'Amount':>12} {'Stage':<15} {'Allbound Partner':<25} "
        f"{'Owner':<15} {'Country':<8} {'Status':<12} {'Close Date':<12}"
    )
    lines.append("-" * 140)
    
    total = 0
    for opp in opportunities:
        name = str(opp.get("name", "Unknown"))[:38]
        amount = opp.get("amount", 0)
        total += amount
        stage = str(opp.get("stageName", "N/A"))[:13]
        partner = str(opp.get("allboundPartner", "N/A"))[:23]
        owner = str(opp.get("ownerName", "Unknown"))[:13]
        country = str(opp.get("country", "N/A"))[:6]
        status = str(opp.get("registrationStatus", "N/A"))[:10]
        close_date = str(opp.get("closeDate", "N/A"))[:10]
        
        lines.append(
            f"{name:<40} €{amount:>10,.0f} {stage:<15} {partner:<25} "
            f"{owner:<15} {country:<8} {status:<12} {close_date:<12}"
        )
    
    lines.append("-" * 140)
    lines.append(
         f"{'TOTAL':<40} €{total:>10,.0f} {len(opportunities)} opportunities"
     )
 
    return "\n".join(lines)


def format_partner_metrics(data: dict) -> str:
    """Pretty-format partner sourced/influenced revenue metrics."""
    breakdown = data.get("breakdown")
    period_str = data.get("period", "Unknown")
    
    if breakdown is None:
        # Total breakdown
        d = data.get("data", {})
        lines = []
        lines.append(f"Partner Revenue Metrics ({period_str})")
        lines.append("=" * 80)
        
        total = d.get("total_revenue", 0)
        total_count = d.get("total_deal_count", 0)
        
        lines.append(f"\n| Type | Revenue | Deal Count | Percentage |")
        lines.append("|---|---|---|---|")
        
        for type_key in ["sourced", "influenced", "fulfillment", "unassigned_direct"]:
            type_data = d.get(type_key, {})
            revenue = type_data.get("revenue", 0)
            count = type_data.get("deal_count", 0)
            pct = type_data.get("percentage", 0)
            type_label = type_key.replace("_", " ").title()
            lines.append(f"| {type_label} | ${revenue:,.2f} | {count} | {pct:.1f}% |")
        
        lines.append("|---|---|---|---|")
        lines.append(f"| **TOTAL** | **${total:,.2f}** | **{total_count}** | **100.0%** |")
        
        return "\n".join(lines)
    
    else:
        # Breakdown by country or partner
        data_rows = data.get("data", [])
        lines = []
        lines.append(f"Partner Revenue Metrics by {breakdown.title()} ({period_str})")
        lines.append("=" * 130)
        
        lines.append(f"\n| {breakdown.title()} | Total Revenue | Sourced % | Influenced % | Fulfillment % | Unassigned % |")
        lines.append("|---|---|---|---|---|---|")
        
        for row in data_rows:
            label = row.get(breakdown, "Unknown")
            total = row.get("total_revenue", 0)
            sourced_pct = row.get("sourced", {}).get("percentage", 0)
            influenced_pct = row.get("influenced", {}).get("percentage", 0)
            fulfillment_pct = row.get("fulfillment", {}).get("percentage", 0)
            unassigned_pct = row.get("unassigned_direct", {}).get("percentage", 0)
            
            lines.append(f"| {label} | ${total:,.2f} | {sourced_pct:.1f}% | {influenced_pct:.1f}% | {fulfillment_pct:.1f}% | {unassigned_pct:.1f}% |")
        
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
        api = get_api()
        response = asyncio.run(api.get_kpi_snapshot(
            _normalize_period(period),
            channel_manager=channel_manager or DEFAULT_CHANNEL_MANAGER
        ))
        result = response.__dict__
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
        api = get_api()
        req = AnalyticsRequest(
            period=_normalize_period(period),
            breakdown=breakdown,
            channel_manager=channel_manager or DEFAULT_CHANNEL_MANAGER
        )
        response = asyncio.run(api.get_revenue(req))
        result = response.__dict__
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
        api = get_api()
        req = AnalyticsRequest(
            period=_normalize_period(period),
            breakdown=breakdown,
            channel_manager=channel_manager or DEFAULT_CHANNEL_MANAGER
        )
        response = asyncio.run(api.get_pipeline(req))
        result = response.__dict__
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
@click.option("--status", default="Submitted,In Review", help="Registration status(es): Submitted, In Review, Approved, Rejected, or comma-separated")
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--limit", default=50, type=int, help="Max results to return")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def opportunities_by_status(status, period, limit, output_json, channel_manager):
    """Get opportunities filtered by registration status with Allbound partner details.
    
    Use --status to filter by registration status (default shows Submitted + In Review).
    
    Examples:
      channel opportunities-by-status
      channel opportunities-by-status --status Submitted
      channel opportunities-by-status --status "Submitted,In Review"
      channel opportunities-by-status --status Approved --period FY27_Q1
    """
    try:
        result = asyncio.run(ci.get_opportunities_by_registration_status(
            get_sf(),
            period=_normalize_period(period),
            registration_status=status,
            channel_manager=channel_manager or None,
            limit=limit
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_opportunities_by_status(result))
    except Exception as e:
        handle_error(e, f"opportunities-by-status ({status})")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--breakdown", default=None, type=click.Choice([None, "country", "partner"]), help="Breakdown by country or partner")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def partner_metrics(period, breakdown, output_json, channel_manager):
    """Show partner-sourced vs influenced revenue breakdown.
    
    Shows closed-won revenue split by Partner_Source_Influence__c:
    - Sourced: Partner originated the deal
    - Influenced: Partner influenced but didn't source
    - Fulfillment: Partner handling fulfillment only
    - Unassigned/Direct: No partner involvement
    
    Examples:
      channel partner-metrics
      channel partner-metrics --breakdown country
      channel partner-metrics --breakdown partner --period THIS_FISCAL_YEAR
    """
    try:
        result = asyncio.run(ci.get_partner_sourced_influenced_revenue(
            get_sf(),
            period=_normalize_period(period),
            breakdown=breakdown,
            channel_manager=channel_manager or None,
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_partner_metrics(result))
    except Exception as e:
        handle_error(e, f"partner-metrics ({breakdown})")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--metric", default="revenue", type=click.Choice(["revenue", "pipeline"]), help="Ranking metric")
@click.option("--limit", default=10, type=int, help="Number of partners to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def top_partners(period, metric, limit, output_json):
    """Get top partners: ranked by revenue or pipeline."""
    try:
        api = get_api()
        response = asyncio.run(api.get_top_partners(
            period=_normalize_period(period),
            metric=metric,
            limit=limit,
            channel_manager=""
        ))
        result = response.__dict__
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_top_partners(result))
    except Exception as e:
        handle_error(e, f"top-partners ({metric})")


@cli.command()
@click.argument("query", required=True)
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
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
@click.option("--period", default="THIS_QUARTER", help="Fiscal period (open opps only)")
@click.option("--region", default=None, type=click.Choice(["SE", "EE", "all"], case_sensitive=False), help="Filter by region: SE (Southern Europe), EE (Eastern Europe), or all")
@click.option("--partner", default=None, help="Filter by partner name")
@click.option("--country", default=None, help="Filter by country (overrides --region if both specified)")
@click.option("--sales-rep", default=None, help="Filter by sales rep name")
@click.option("--stage", default=None, help="Filter by stage (Prospecting, Validation, etc.)")
@click.option("--min-amount", default=None, type=float, help="Minimum opportunity amount")
@click.option("--limit", default=20, type=int, help="Max results (1-100)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def list_opps(period, region, partner, country, sales_rep, stage, min_amount, limit, output_json, channel_manager):
    """List open opportunities with optional filters by region or country."""
    try:
        # If region is specified and country is not, query all countries in that region
        if region and not country:
            countries_to_query = []
            if region.upper() == "SE":
                countries_to_query = COUNTRIES
            elif region.upper() == "EE":
                countries_to_query = COUNTRIES_EE
            
            # Query all countries in the region and combine results
            all_results = []
            for country_name in countries_to_query:
                result = asyncio.run(ci.get_opportunity_list(
                    get_sf(),
                    partner_name=partner,
                    country=country_name,
                    sales_rep=sales_rep,
                    stage=stage,
                    min_amount=min_amount,
                    period=_normalize_period(period),
                    limit=limit,
                    channel_manager=channel_manager or None
                ))
                all_results.extend(result.get("data", []))
            
            # Combine results
            result = {
                "tool": "get_opportunity_list",
                "period": all_results[0].get("period") if all_results else _summarize_period(period),
                "region": region.upper(),
                "filters": {"partnerName": partner, "stage": stage, "minAmount": min_amount},
                "data": all_results
            }
        else:
            # Query specific country or all countries if no filter
            result = asyncio.run(ci.get_opportunity_list(
                get_sf(),
                partner_name=partner,
                country=country,
                sales_rep=sales_rep,
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


def format_sales_rep_revenue(data: dict) -> str:
    """Pretty-format sales rep revenue data."""
    result = data.get("data", [])
    lines = []
    metric = data.get("metric", "revenue").title()
    lines.append(f"Sales Rep {metric} Ranking")
    lines.append("=" * 90)

    if not result:
        lines.append("No data available.")
        return "\n".join(lines)

    # Header row
    lines.append(f"{'#':<3} {'Sales Rep Name':<35} {'Amount':>15} {'Deals':>8} {'Avg Size':>15}")
    lines.append("-" * 90)

    for i, rep in enumerate(result, 1):
        name = str(rep.get("repName", "Unknown"))[:33]
        amount = rep.get("totalAmount", 0)
        deals = rep.get("dealCount", 0)
        avg_size = rep.get("avgDealSize", 0)
        lines.append(f"{i:<3} {name:<35} ${amount:>14,.0f} {deals:>8} ${avg_size:>14,.0f}")

    return "\n".join(lines)


def format_sales_rep_by_country(data: dict) -> str:
    """Pretty-format sales rep revenue by country."""
    result = data.get("data", [])
    lines = []
    metric = data.get("metric", "revenue").title()
    country_filter = data.get("country", "All Countries")
    lines.append(f"Sales Rep {metric} by Country: {country_filter}")
    lines.append("=" * 100)

    if not result:
        lines.append("No data available.")
        return "\n".join(lines)

    for i, rep in enumerate(result, 1):
        name = rep.get("repName", "Unknown")
        total_amount = rep.get("totalAmount", 0)
        total_deals = rep.get("dealCount", 0)

        lines.append(f"\n{i}. {name}")
        lines.append("-" * 100)
        lines.append(f"   Total: ${total_amount:,.0f} ({total_deals} deals)")

        by_country = rep.get("byCountry", {})
        if by_country:
            lines.append(f"   By Country:")
            for country, stats in sorted(by_country.items(), key=lambda x: x[1]["amount"], reverse=True):
                amount = stats["amount"]
                deals = stats["dealCount"]
                avg = stats["avgDealSize"]
                lines.append(f"      {country:<20} ${amount:>12,.0f} ({deals:>2} deals, avg: ${avg:>10,.0f})")

    return "\n".join(lines)


def format_closed_deals_by_sales_rep(data: dict) -> str:
    """Pretty-format closed deals by sales rep."""
    result = data.get("data", [])
    lines = []
    lines.append("Closed-Won Deals by Sales Rep")
    lines.append("=" * 130)

    if not result:
        lines.append("No deals found.")
        return "\n".join(lines)

    for i, rep in enumerate(result, 1):
        rep_name = rep.get("repName", "Unknown")
        revenue = rep.get("closedRevenue", 0)
        deal_count = rep.get("dealCount", 0)
        
        lines.append(f"\n{i}. {rep_name} — ${revenue:,.0f} ({deal_count} deals)")
        lines.append("-" * 130)
        
        # Header for deals
        lines.append(f"  {'Deal Name':<60} {'Amount':>12} {'Close Date':<12} {'Partner':<30}")
        lines.append("  " + "-" * 128)
        
        for deal in rep.get("deals", []):
            name = deal.get("name", "Unknown")[:58]
            amount = deal.get("amount", 0)
            close_date = deal.get("closeDate", "N/A")
            partner = deal.get("partner", "Unknown")[:28]
            lines.append(f"  {name:<60} ${amount:>11,.0f} {close_date:<12} {partner:<30}")

    return "\n".join(lines)


def format_pipeline_deals_by_sales_rep(data: dict) -> str:
    """Pretty-format pipeline deals by sales rep."""
    result = data.get("data", [])
    lines = []
    lines.append("Open Pipeline Deals by Sales Rep")
    lines.append("=" * 140)

    if not result:
        lines.append("No deals found.")
        return "\n".join(lines)

    for i, rep in enumerate(result, 1):
        rep_name = rep.get("repName", "Unknown")
        pipeline = rep.get("pipelineAmount", 0)
        forecast = rep.get("forecastAmount", 0)
        deal_count = rep.get("dealCount", 0)
        
        lines.append(f"\n{i}. {rep_name}")
        lines.append("-" * 140)
        lines.append(f"   Pipeline: ${pipeline:,.0f} | Forecast (weighted): ${forecast:,.0f} | Deals: {deal_count}")
        lines.append("   " + "-" * 136)
        
        # Header for deals
        lines.append(f"   {'Deal Name':<45} {'Amount':>12} {'Stage':<18} {'Prob':>5} {'Forecast':>12}")
        lines.append("   " + "-" * 136)
        
        for deal in rep.get("deals", []):
            name = deal.get("name", "Unknown")[:43]
            amount = deal.get("amount", 0)
            stage = deal.get("stage", "Unknown")[:16]
            prob = deal.get("probability", 0)
            forecast = deal.get("forecast", 0)
            lines.append(f"   {name:<45} ${amount:>11,.0f} {stage:<18} {prob:>4.0f}% ${forecast:>11,.0f}")

    return "\n".join(lines)


def format_sales_rep_by_partner(data: dict) -> str:
    """Pretty-format sales rep revenue by partner."""
    result = data.get("data", [])
    lines = []
    metric = data.get("metric", "revenue").title()
    partner_filter = data.get("partner", "All Partners")
    lines.append(f"Sales Rep {metric} by Partner: {partner_filter}")
    lines.append("=" * 100)

    if not result:
        lines.append("No data available.")
        return "\n".join(lines)

    for i, rep in enumerate(result, 1):
        name = rep.get("repName", "Unknown")
        total_amount = rep.get("totalAmount", 0)
        total_deals = rep.get("dealCount", 0)

        lines.append(f"\n{i}. {name}")
        lines.append("-" * 100)
        lines.append(f"   Total: ${total_amount:,.0f} ({total_deals} deals)")

        by_partner = rep.get("byPartner", {})
        if by_partner:
            lines.append(f"   By Partner:")
            for partner, stats in sorted(by_partner.items(), key=lambda x: x[1]["amount"], reverse=True):
                amount = stats["amount"]
                deals = stats["dealCount"]
                avg = stats["avgDealSize"]
                lines.append(f"      {partner:<40} ${amount:>12,.0f} ({deals:>2} deals, avg: ${avg:>10,.0f})")

    return "\n".join(lines)


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--metric", default="revenue", type=click.Choice(["revenue", "pipeline"]), help="Metric: revenue (closed-won) or pipeline (open)")
@click.option("--region", default=None, type=click.Choice(["SE", "EE", "all"]), help="Filter by region: SE (Southern Europe), EE (Eastern Europe), all (both). Default: all regions combined")
@click.option("--limit", default=50, type=int, help="Max sales reps to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def sales_rep_revenue(period, metric, region, limit, output_json):
    """Get revenue by sales rep: aggregated sales rep performance."""
    try:
        api = get_api()
        response = asyncio.run(api.get_revenue_by_sales_rep_with_region(
            period=_normalize_period(period),
            region=region,
            metric=metric,
            limit=limit,
            channel_manager=""
        ))
        result = response.__dict__
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_sales_rep_revenue(result))
    except Exception as e:
        handle_error(e, "sales-rep-revenue")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--country", default=None, help="Filter by specific country")
@click.option("--metric", default="revenue", type=click.Choice(["revenue", "pipeline"]), help="Metric: revenue (closed-won) or pipeline (open)")
@click.option("--limit", default=50, type=int, help="Max sales reps to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def sales_rep_by_country(period, country, metric, limit, output_json):
    """Get revenue by sales rep, broken down by country."""
    try:
        api = get_api()
        response = asyncio.run(api.get_revenue_by_sales_rep_by_country(
            period=_normalize_period(period),
            country=country,
            metric=metric,
            limit=limit,
            channel_manager=""
        ))
        result = response.__dict__
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_sales_rep_by_country(result))
    except Exception as e:
        handle_error(e, "sales-rep-by-country")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--partner", default=None, help="Filter by specific partner")
@click.option("--metric", default="revenue", type=click.Choice(["revenue", "pipeline"]), help="Metric: revenue (closed-won) or pipeline (open)")
@click.option("--limit", default=50, type=int, help="Max sales reps to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def sales_rep_by_partner(period, partner, metric, limit, output_json):
    """Get revenue by sales rep, broken down by partner."""
    try:
        api = get_api()
        response = asyncio.run(api.get_revenue_by_sales_rep_by_partner(
            period=_normalize_period(period),
            partner_name=partner,
            metric=metric,
            limit=limit,
            channel_manager=""
        ))
        result = response.__dict__
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_sales_rep_by_partner(result))
    except Exception as e:
        handle_error(e, "sales-rep-by-partner")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--rep", default=None, help="Filter by specific sales rep name")
@click.option("--region", default=None, type=click.Choice(["SE", "EE", "all"]), help="Filter by region: SE (Southern Europe), EE (Eastern Europe), all (both). Default: all regions combined")
@click.option("--limit", default=100, type=int, help="Max deals to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def closed_deals_by_rep(period, rep, region, limit, output_json):
    """Get closed-won deals by sales rep with deal details."""
    try:
        api = get_api()
        response = asyncio.run(api.get_closed_deals_by_sales_rep_with_region(
            period=_normalize_period(period),
            region=region,
            sales_rep=rep,
            limit=limit,
            channel_manager=""
        ))
        result = response.__dict__
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_closed_deals_by_sales_rep(result))
    except Exception as e:
        handle_error(e, "closed-deals-by-rep")


@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period")
@click.option("--rep", default=None, help="Filter by specific sales rep name")
@click.option("--region", default=None, type=click.Choice(["SE", "EE", "all"]), help="Filter by region: SE (Southern Europe), EE (Eastern Europe), all (both). Default: all regions combined")
@click.option("--limit", default=100, type=int, help="Max deals to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def pipeline_deals_by_rep(period, rep, region, limit, output_json):
    """Get open pipeline deals by sales rep with deal details, probability, and forecast."""
    try:
        api = get_api()
        response = asyncio.run(api.get_pipeline_deals_by_sales_rep_with_region(
            period=_normalize_period(period),
            region=region,
            sales_rep=rep,
            limit=limit,
            channel_manager=""
        ))
        result = response.__dict__
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_pipeline_deals_by_sales_rep(result))
    except Exception as e:
        handle_error(e, "pipeline-deals-by-rep")


def _normalize_period(period: str) -> str:
    """Normalize period string (delegates to channel_intelligence)."""
    return ci._normalize_period(period)


if __name__ == "__main__":
    cli()
