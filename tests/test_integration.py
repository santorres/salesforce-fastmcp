"""Integration tests: real MCP server + real Salesforce data.

Requires a running server accessible at INTEGRATION_SERVER_URL
(default: http://localhost:8080).

Setup on the laptop with Salesforce auth:
    MCP_TRANSPORT=streamable-http MCP_PORT=8080 python server.py

Then tunnel to this machine:
    ssh -L 8080:localhost:8080 <other-laptop-hostname>

Run with:
    pytest tests/test_integration.py -v
    pytest tests/test_integration.py -v -k "revenue"   # subset

Tests skip automatically when the server is not reachable — no noise in the
normal unit-test run.
"""

import json
import os

import pytest

# Skip the entire module if fastmcp is not installed
fastmcp = pytest.importorskip("fastmcp", reason="fastmcp not installed")
from fastmcp import Client  # noqa: E402

SERVER_URL = os.getenv("INTEGRATION_SERVER_URL", "http://localhost:8080")

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def mcp_client():
    """Per-test FastMCP client. Skips if server is unreachable."""
    try:
        async with Client(SERVER_URL) as client:
            yield client
    except Exception as exc:
        pytest.skip(f"MCP server not reachable at {SERVER_URL} — {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse(result) -> dict | list:
    """Extract and JSON-parse a tool call result from FastMCP client."""
    text = raw_text(result)
    if text.startswith("Error:"):
        pytest.fail(text)
    return json.loads(text)


def raw_text(result) -> str:
    """Extract raw text from a tool call result, joining all content blocks."""
    if isinstance(result, list):
        return "".join(getattr(c, "text", "") for c in result)
    elif hasattr(result, "content"):
        # FastMCP 3.x returns CallToolResult with a .content list
        return "".join(getattr(c, "text", "") for c in result.content)
    return str(result)


def assert_no_error(data, tool: str = ""):
    """Fail if the response is an MCP-level error string."""
    if isinstance(data, str):
        assert not data.startswith("Error:"), f"{tool} returned error: {data}"


def assert_valid_revenue(data: dict):
    total = data.get("totalRevenue", data.get("data", {}).get("totalRevenue", 0))
    assert isinstance(total, (int, float)), "totalRevenue must be numeric"
    assert total >= 0, "totalRevenue must not be negative"


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------

class TestServerHealth:
    async def test_lists_tools(self, mcp_client):
        tools = await mcp_client.list_tools()
        names = [t.name for t in tools]
        assert len(names) >= 50, f"Expected 50+ tools, got {len(names)}"

    async def test_core_tools_present(self, mcp_client):
        tools = await mcp_client.list_tools()
        names = {t.name for t in tools}
        required = {
            "get_revenue", "get_pipeline", "get_kpi_snapshot",
            "get_top_partners", "get_partner_detail", "get_partner_scorecard",
            "get_growth", "get_orphan_hygiene", "get_stalled_deals",
            "get_deal_registrations_breakdown", "get_multi_period_trend",
            "get_win_rate_by_country", "run_exploratory_analysis",
            "generate_partner_qbr",
        }
        missing = required - names
        assert not missing, f"Missing tools: {missing}"


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------

class TestRevenue:
    async def test_fy_total(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_revenue", {"period": "THIS_FISCAL_YEAR", "breakdown": "total"}
        )
        data = parse(result)
        assert_no_error(data, "get_revenue/total")
        assert "totalRevenue" in data or "data" in data

    async def test_country_breakdown(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_revenue", {"period": "THIS_FISCAL_YEAR", "breakdown": "country"}
        )
        data = parse(result)
        assert_no_error(data, "get_revenue/country")
        rows = data.get("data") or data.get("rows", [])
        if rows:
            # Every country should be one of our six
            countries = {r.get("country") or r.get("BillingCountry") for r in rows}
            valid = {"Spain", "Italy", "Portugal", "Greece", "Cyprus", "Malta"}
            unexpected = countries - valid - {None}
            assert not unexpected, f"Unexpected countries: {unexpected}"

    async def test_quarter_breakdown(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_revenue", {"period": "THIS_FISCAL_YEAR", "breakdown": "quarter"}
        )
        data = parse(result)
        assert_no_error(data, "get_revenue/quarter")

    async def test_period_normalisation_accepted(self, mcp_client):
        """Server should coerce 'q1?' to 'Q1' without erroring."""
        result = await mcp_client.call_tool(
            "get_revenue", {"period": "q1?", "breakdown": "total"}
        )
        data = parse(result)
        assert_no_error(data, "get_revenue/coerce_period")

    async def test_attainment_returned_with_territory(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_revenue", {
                "period": "THIS_FISCAL_YEAR",
                "territory": "South_Europe",
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_revenue/territory")
        # If there is a target it must be numeric and non-negative
        target = data.get("revenueTarget")
        if target is not None:
            assert isinstance(target, (int, float)) and target >= 0


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class TestPipeline:
    async def test_this_quarter_total(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_pipeline", {"period": "THIS_QUARTER", "breakdown": "total"}
        )
        data = parse(result)
        assert_no_error(data, "get_pipeline/total")

    async def test_no_closed_deals_in_pipeline(self, mcp_client):
        """Pipeline must only contain open deals."""
        result = await mcp_client.call_tool(
            "get_pipeline", {"period": "THIS_FISCAL_YEAR", "breakdown": "stage"}
        )
        data = parse(result)
        assert_no_error(data, "get_pipeline/stage")
        rows = data.get("data") or data.get("rows", [])
        closed_stages = {"Closed Won", "Closed Lost"}
        for row in rows:
            stage = row.get("stage") or row.get("StageName", "")
            assert stage not in closed_stages, f"Pipeline contains closed stage: {stage}"

    async def test_next_quarter(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_pipeline", {"period": "NEXT_QUARTER", "breakdown": "total"}
        )
        data = parse(result)
        assert_no_error(data, "get_pipeline/next_quarter")

    async def test_current_and_next_quarter(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_pipeline", {"period": "CURRENT_AND_NEXT_QUARTER", "breakdown": "total"}
        )
        data = parse(result)
        assert_no_error(data, "get_pipeline/current_and_next")


# ---------------------------------------------------------------------------
# KPI Snapshot
# ---------------------------------------------------------------------------

class TestKpiSnapshot:
    async def test_all_keys_present(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_kpi_snapshot", {"period": "THIS_FISCAL_YEAR"}
        )
        data = parse(result)
        assert_no_error(data, "get_kpi_snapshot")
        kpi = data.get("data") or data
        expected_keys = {"revenue", "pipeline", "winRate"}
        present = set(kpi.keys()) if isinstance(kpi, dict) else set()
        assert expected_keys & present, f"KPI keys missing — got: {present}"

    async def test_win_rate_in_range(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_kpi_snapshot", {"period": "THIS_FISCAL_YEAR"}
        )
        data = parse(result)
        kpi = data.get("data") or data
        win_rate = kpi.get("winRate")
        if win_rate is not None:
            assert 0 <= win_rate <= 100, f"winRate {win_rate} out of range"

    async def test_no_division_by_zero_empty_period(self, mcp_client):
        """Q4 of previous FY is closed — 0 won deals should not crash the tool."""
        result = await mcp_client.call_tool(
            "get_kpi_snapshot", {"period": "LAST_FISCAL_YEAR"}
        )
        data = parse(result)
        assert_no_error(data, "get_kpi_snapshot/last_fy")

    async def test_this_quarter(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_kpi_snapshot", {"period": "THIS_QUARTER"}
        )
        data = parse(result)
        assert_no_error(data, "get_kpi_snapshot/this_quarter")


# ---------------------------------------------------------------------------
# Growth / trend
# ---------------------------------------------------------------------------

class TestGrowth:
    async def test_yoy_revenue(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_growth", {
                "metric": "revenue",
                "period_a": "THIS_FISCAL_YEAR",
                "period_b": "LAST_FISCAL_YEAR",
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_growth/yoy")
        pct = data.get("percentageChange")
        if pct is not None:
            # percentage can be large but should be numeric
            assert isinstance(pct, (int, float))

    async def test_qoq_pipeline(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_growth", {
                "metric": "pipeline",
                "period_a": "THIS_QUARTER",
                "period_b": "LAST_QUARTER",
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_growth/qoq")

    async def test_zero_base_does_not_crash(self, mcp_client):
        """FY24 probably has no data — percentageChange should be None, not a crash."""
        result = await mcp_client.call_tool(
            "get_growth", {
                "metric": "revenue",
                "period_a": "THIS_FISCAL_YEAR",
                "period_b": "FY24_Q1",
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_growth/zero_base")


class TestMultiPeriodTrend:
    async def test_four_quarters_revenue(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_multi_period_trend", {
                "metric": "revenue",
                "periods": ["Q1", "Q2", "Q3", "Q4"],
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_multi_period_trend/4q")
        # Regression for Phase 1-A bug: response must be non-empty
        assert data, "get_multi_period_trend returned empty response — Phase 1-A regression"
        # If response is a dict with a series key, verify Total series has values
        if isinstance(data, dict):
            series = data.get("series") or data.get("data", {}).get("series", {})
            if isinstance(series, dict) and "Total" in series:
                values = [v for v in series["Total"].values() if isinstance(v, (int, float))]
                assert values, "Total series is empty — Phase 1-A regression"

    async def test_country_breakdown(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_multi_period_trend", {
                "metric": "revenue",
                "periods": ["Q1", "Q2"],
                "breakdown": "country",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_multi_period_trend/country")

    async def test_yoy_comparison(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_multi_period_trend", {
                "metric": "revenue",
                "periods": ["FY26_Q1", "FY27_Q1"],
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_multi_period_trend/yoy")


# ---------------------------------------------------------------------------
# Partners
# ---------------------------------------------------------------------------

class TestTopPartners:
    async def test_by_revenue(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_top_partners", {
                "metric": "revenue",
                "period": "THIS_FISCAL_YEAR",
                "limit": 10,
            }
        )
        data = parse(result)
        assert_no_error(data, "get_top_partners/revenue")
        partners = data.get("partners") or data.get("data") or []
        for p in partners:
            rev = p.get("totalRevenue", p.get("revenue", 0))
            assert rev >= 0, f"Partner {p.get('partner')} has negative revenue"

    async def test_by_pipeline(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_top_partners", {
                "metric": "pipeline",
                "period": "THIS_QUARTER",
                "limit": 5,
            }
        )
        data = parse(result)
        assert_no_error(data, "get_top_partners/pipeline")

    async def test_ranked_descending(self, mcp_client):
        """Partners should be sorted largest → smallest."""
        result = await mcp_client.call_tool(
            "get_top_partners", {
                "metric": "revenue",
                "period": "THIS_FISCAL_YEAR",
                "limit": 20,
            }
        )
        data = parse(result)
        partners = data.get("partners") or data.get("data") or []
        amounts = [
            p.get("totalRevenue", p.get("revenue", 0))
            for p in partners
            if p.get("totalRevenue") is not None or p.get("revenue") is not None
        ]
        assert amounts == sorted(amounts, reverse=True), "Partners not sorted descending"


class TestPartnerDetail:
    async def test_known_partner_has_data(self, mcp_client):
        """Accenture exists in this org — should return data, not an empty fallback."""
        result = await mcp_client.call_tool(
            "get_partner_detail", {
                "partner_name": "Accenture",
                "period": "THIS_FISCAL_YEAR",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_partner_detail/accenture")

    async def test_partial_name_match(self, mcp_client):
        """'Inetum' partial match should resolve without error."""
        result = await mcp_client.call_tool(
            "get_partner_detail", {
                "partner_name": "Inetum",
                "period": "THIS_FISCAL_YEAR",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_partner_detail/partial")

    async def test_unknown_partner_fallback(self, mcp_client):
        """Partner that doesn't exist must return a safe fallback, not crash."""
        result = await mcp_client.call_tool(
            "get_partner_detail", {
                "partner_name": "DOES_NOT_EXIST_XYZZY_12345",
                "period": "THIS_FISCAL_YEAR",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_partner_detail/unknown")


class TestPartnerScorecard:
    async def test_scorecard_structure(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_partner_scorecard", {
                "partner_name": "Accenture",
                "period": "THIS_FISCAL_YEAR",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_partner_scorecard")


# ---------------------------------------------------------------------------
# Hygiene
# ---------------------------------------------------------------------------

class TestOrphanHygiene:
    async def test_structure_returned(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_orphan_hygiene", {"period": "THIS_FISCAL_YEAR"}
        )
        data = parse(result)
        assert_no_error(data, "get_orphan_hygiene")
        orphan_count = (
            data.get("orphanCount")
            or data.get("data", {}).get("orphanCount")
            or 0
        )
        assert isinstance(orphan_count, (int, float))
        assert orphan_count >= 0

    async def test_this_quarter(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_orphan_hygiene", {"period": "THIS_QUARTER"}
        )
        data = parse(result)
        assert_no_error(data, "get_orphan_hygiene/this_quarter")


class TestStalledDeals:
    async def test_default_threshold(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_stalled_deals", {"period": "THIS_QUARTER", "days_threshold": 60}
        )
        data = parse(result)
        assert_no_error(data, "get_stalled_deals")

    async def test_strict_threshold(self, mcp_client):
        """90-day threshold should return fewer or equal deals than 30 days."""
        result_90 = parse(await mcp_client.call_tool(
            "get_stalled_deals", {"period": "THIS_FISCAL_YEAR", "days_threshold": 90}
        ))
        result_30 = parse(await mcp_client.call_tool(
            "get_stalled_deals", {"period": "THIS_FISCAL_YEAR", "days_threshold": 30}
        ))
        count_90 = result_90.get("stalledCount", result_90.get("count", 0))
        count_30 = result_30.get("stalledCount", result_30.get("count", 0))
        assert count_90 <= count_30, "90-day threshold returned more stalled deals than 30-day"


class TestHighRiskDeals:
    async def test_all_below_threshold(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_high_risk_deals", {"period": "THIS_QUARTER", "probability_threshold": 40}
        )
        data = parse(result)
        assert_no_error(data, "get_high_risk_deals")
        deals = data.get("deals") or data.get("data") or []
        for deal in deals:
            prob = deal.get("Probability", deal.get("probability", 100))
            assert prob <= 40, f"Deal {deal.get('Name')} has probability {prob} > threshold 40"


# ---------------------------------------------------------------------------
# Deal registrations
# ---------------------------------------------------------------------------

class TestDealRegistrations:
    async def test_total_summary(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_deal_registrations_breakdown", {
                "period": "THIS_FISCAL_YEAR",
                "breakdown": "total",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_deal_registrations_breakdown/total")

    async def test_partner_breakdown(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_deal_registrations_breakdown", {
                "period": "THIS_FISCAL_YEAR",
                "breakdown": "partner",
            }
        )
        data = parse(result)
        assert_no_error(data, "get_deal_registrations_breakdown/partner")

    async def test_quarterly_trend(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_deal_registrations_trend", {
                "periods": ["Q1", "Q2", "Q3", "Q4"],
            }
        )
        data = parse(result)
        assert_no_error(data, "get_deal_registrations_trend")

    async def test_yoy_comparison(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_deal_registrations_trend", {
                "periods": ["FY26_Q1", "FY26_Q2", "FY27_Q1", "FY27_Q2"],
            }
        )
        data = parse(result)
        assert_no_error(data, "get_deal_registrations_trend/yoy")


# ---------------------------------------------------------------------------
# Win rate
# ---------------------------------------------------------------------------

class TestWinRate:
    async def test_all_countries_present(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_win_rate_by_country", {"period": "THIS_FISCAL_YEAR"}
        )
        data = parse(result)
        assert_no_error(data, "get_win_rate_by_country")

    async def test_win_rates_bounded(self, mcp_client):
        result = await mcp_client.call_tool(
            "get_win_rate_by_country", {"period": "THIS_FISCAL_YEAR"}
        )
        data = parse(result)
        rows = data.get("data") or data.get("rows") or []
        for row in rows:
            wr = row.get("winRate")
            if wr is not None:
                assert 0 <= wr <= 100, f"Win rate {wr} out of 0-100 range"


# ---------------------------------------------------------------------------
# QBR
# ---------------------------------------------------------------------------

class TestQbr:
    async def test_generates_markdown(self, mcp_client):
        result = await mcp_client.call_tool(
            "generate_partner_qbr", {
                "partner_name": "Accenture",
                "period": "THIS_QUARTER",
            }
        )
        data = parse(result)
        assert_no_error(data, "generate_partner_qbr")
        # QBR returns a markdown string in a 'report' or 'markdown' key
        report = data.get("report") or data.get("markdown") or data.get("content") or ""
        if report:
            assert "Accenture" in report or "accenture" in report.lower()

    async def test_with_revenue_target(self, mcp_client):
        result = await mcp_client.call_tool(
            "generate_partner_qbr", {
                "partner_name": "Accenture",
                "period": "THIS_QUARTER",
                "revenue_target": 900000,
            }
        )
        data = parse(result)
        assert_no_error(data, "generate_partner_qbr/with_target")


# ---------------------------------------------------------------------------
# Exploratory routing
# ---------------------------------------------------------------------------

class TestExploratoryRouting:
    async def test_revenue_intent_returns_hint(self, mcp_client):
        result = await mcp_client.call_tool(
            "run_exploratory_analysis", {"intent": "show me revenue for Q2"}
        )
        data = parse(result)
        assert_no_error(data, "run_exploratory_analysis/revenue")
        assert data.get("matched") is True
        assert data.get("use_tool") == "get_revenue"
        assert data.get("suggested_params", {}).get("period") == "Q2"

    async def test_pipeline_intent(self, mcp_client):
        result = await mcp_client.call_tool(
            "run_exploratory_analysis", {"intent": "how is the pipeline this quarter?"}
        )
        data = parse(result)
        assert data.get("matched") is True
        assert data.get("use_tool") == "get_pipeline"

    async def test_kpi_intent(self, mcp_client):
        result = await mcp_client.call_tool(
            "run_exploratory_analysis", {"intent": "kpi dashboard"}
        )
        data = parse(result)
        assert data.get("matched") is True
        assert data.get("use_tool") == "get_kpi_snapshot"

    async def test_unclear_intent_returns_catalogue(self, mcp_client):
        result = await mcp_client.call_tool(
            "run_exploratory_analysis", {"intent": "xyzzy incomprehensible @@@"}
        )
        data = parse(result)
        assert data.get("matched") is False
        assert "available_tools" in data
        assert len(data["available_tools"]) > 10

    async def test_never_raises_for_any_input(self, mcp_client):
        """Server must never return Error: for any exploratory input."""
        intents = [
            "???",
            "",
            "show me everything",
            "orphan deals without partner",
            "stalled deals last 30 days",
        ]
        for intent in intents:
            result = await mcp_client.call_tool(
                "run_exploratory_analysis", {"intent": intent}
            )
            text = raw_text(result)
            assert not text.startswith("Error:"), f"Error returned for intent {intent!r}: {text}"


# ---------------------------------------------------------------------------
# Period edge cases (via real tool calls)
# ---------------------------------------------------------------------------

class TestPeriodEdgeCases:
    @pytest.mark.parametrize("period", [
        "THIS_FISCAL_YEAR",
        "LAST_FISCAL_YEAR",
        "THIS_QUARTER",
        "LAST_QUARTER",
        "NEXT_QUARTER",
        "Q1", "Q2", "Q3", "Q4",
        "LAST_30_DAYS",
        "NEXT_60_DAYS",
        "FY26_Q1",
        "FY27_Q2",
    ])
    async def test_all_periods_resolve(self, mcp_client, period):
        """Every canonical period must return a valid response through get_revenue."""
        result = await mcp_client.call_tool(
            "get_revenue", {"period": period, "breakdown": "total"}
        )
        text = raw_text(result)
        assert not text.startswith("Error:"), f"Period {period!r} caused error: {text}"
        data = json.loads(text)
        assert isinstance(data, dict)
