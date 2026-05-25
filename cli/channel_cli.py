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
from pathlib import Path

import click
from dotenv import load_dotenv

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesforce_client import SalesforceClient
import channel_intelligence as ci

load_dotenv()


def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation."""
    return SalesforceClient()


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
    result = data.get("data", {})
    lines = []
    name = result.get("partner_name", "Partner")
    lines.append(f"Partner Scorecard: {name}")
    lines.append("=" * 60)

    # Revenue
    revenue = result.get("revenue", {})
    if revenue:
        lines.append("\nRevenue")
        lines.append("-" * 40)
        lines.append(f"  Closed-Won: ${revenue.get('total_amount', 0):,.0f}")
        lines.append(f"  Deals: {revenue.get('count', 0)}")
        if revenue.get("attainment_pct"):
            lines.append(f"  Attainment: {revenue.get('attainment_pct', 0):.1f}%")

    # Pipeline
    pipeline = result.get("pipeline", {})
    if pipeline:
        lines.append("\nPipeline")
        lines.append("-" * 40)
        lines.append(f"  Open: ${pipeline.get('total_amount', 0):,.0f}")
        lines.append(f"  Deals: {pipeline.get('count', 0)}")

    # Metrics
    win_rate = result.get("win_rate_pct")
    if win_rate:
        lines.append(f"\nWin Rate: {win_rate:.1f}%")

    avg_deal = result.get("average_deal_size")
    if avg_deal:
        lines.append(f"Avg Deal Size: ${avg_deal:,.0f}")

    return "\n".join(lines)


def format_qbr(data: dict) -> str:
    """QBR is markdown, just return it as-is."""
    return data.get("data", "")


def format_risk(data: dict) -> str:
    """Pretty-format high-risk deals."""
    result = data.get("data", [])
    lines = []
    lines.append(f"High-Risk Deals (closing in next 30 days)")
    lines.append("=" * 80)

    if not result:
        lines.append("No high-risk deals found.")
        return "\n".join(lines)

    for deal in result:
        lines.append(f"\n{deal.get('opportunity_name', 'Unknown')}")
        lines.append("-" * 60)
        lines.append(f"  Amount: ${deal.get('amount', 0):,.0f}")
        lines.append(f"  Probability: {deal.get('probability_pct', 0):.0f}%")
        lines.append(f"  Close Date: {deal.get('close_date', 'N/A')}")
        lines.append(f"  Days to Close: {deal.get('days_to_close', 0)}")
        lines.append(f"  Partner: {deal.get('partner_name', 'N/A')}")

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
    pass


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
            breakdown=breakdown if breakdown != "total" else None,
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
            breakdown=breakdown if breakdown != "total" else None,
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


def _normalize_period(period: str) -> str:
    """Normalize period string (delegates to channel_intelligence)."""
    return ci._normalize_period(period)


if __name__ == "__main__":
    cli()
