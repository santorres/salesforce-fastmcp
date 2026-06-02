"""Tests for Phase 4 LLM-layer improvements.

Covers:
- run_exploratory_analysis routing and structured hints
- _detect_period period extraction from free text
- _coerce_period normalisation helper (requires fastmcp to be installed)
- format_result truncation warning logging (requires fastmcp to be installed)
"""

import importlib.util
import json
import logging
import pytest

from core import channel_intelligence as ci

# Mark server-dependent tests to skip when fastmcp is not installed
_has_fastmcp = importlib.util.find_spec("fastmcp") is not None
skip_no_fastmcp = pytest.mark.skipif(not _has_fastmcp, reason="fastmcp not installed")


# ---------------------------------------------------------------------------
# _detect_period
# ---------------------------------------------------------------------------

class TestDetectPeriod:
    def test_q1_abbreviation(self):
        assert ci._detect_period("show me q1 numbers") == "Q1"

    def test_q2_abbreviation(self):
        assert ci._detect_period("q2 pipeline") == "Q2"

    def test_next_quarter(self):
        assert ci._detect_period("what's coming next quarter?") == "NEXT_QUARTER"

    def test_last_quarter(self):
        assert ci._detect_period("last quarter revenue") == "LAST_QUARTER"

    def test_this_quarter(self):
        assert ci._detect_period("this quarter pipeline") == "THIS_QUARTER"

    def test_last_fiscal_year(self):
        assert ci._detect_period("compare to last fiscal year") == "LAST_FISCAL_YEAR"

    def test_last_30_days(self):
        assert ci._detect_period("activity last 30 days") == "LAST_30_DAYS"

    def test_next_60_days(self):
        assert ci._detect_period("opportunities closing next 60 days") == "NEXT_60_DAYS"

    def test_fy_quarter_format(self):
        assert ci._detect_period("fy26_q2 results") == "FY26_Q2"

    def test_defaults_to_this_fy(self):
        assert ci._detect_period("show me all revenue") == "THIS_FISCAL_YEAR"


# ---------------------------------------------------------------------------
# run_exploratory_analysis routing
# ---------------------------------------------------------------------------

class MockSFSimple:
    """Minimal mock — should not be called for hint-return routes."""
    async def query(self, soql):
        raise AssertionError(f"MockSF.query called unexpectedly: {soql!r}")


class TestRunExploratoryAnalysis:
    async def test_slash_pipeline_routes_to_execution(self):
        """Slash commands still execute (not hint-only)."""
        from tests.conftest import MockSF, soql_response, agg_response
        sf = MockSF({
            "totalPipeline": agg_response({"totalPipeline": 1_000_000, "dealCount": 5}),
        })
        result = await ci.run_exploratory_analysis(sf, "/pipeline")
        assert result["tool"] != "run_exploratory_analysis" or result.get("data") is not None

    async def test_revenue_intent_returns_hint(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "show me revenue for q2")
        assert result["matched"] is True
        assert result["use_tool"] == "get_revenue"
        assert "suggested_params" in result
        assert result["suggested_params"]["period"] == "Q2"
        assert "hint" in result

    async def test_pipeline_intent_returns_hint(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "how does our pipeline look this quarter?")
        assert result["matched"] is True
        assert result["use_tool"] == "get_pipeline"
        assert result["suggested_params"]["period"] == "THIS_QUARTER"

    async def test_kpi_intent_returns_hint(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "give me a kpi snapshot")
        assert result["matched"] is True
        assert result["use_tool"] == "get_kpi_snapshot"

    async def test_orphan_intent_returns_hint(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "show orphan deals without partner")
        assert result["matched"] is True
        assert result["use_tool"] == "get_orphan_hygiene"

    async def test_growth_intent_returns_hint(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "revenue growth yoy")
        assert result["matched"] is True
        assert result["use_tool"] == "get_growth"
        assert result["suggested_params"]["period_a"] == "THIS_FISCAL_YEAR"

    async def test_stalled_deals_covered(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "show stalled deals")
        assert result["matched"] is True
        assert result["use_tool"] == "get_stalled_deals"

    async def test_win_rate_covered(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "what is our win rate by country?")
        assert result["matched"] is True
        assert result["use_tool"] == "get_win_rate_by_country"

    async def test_deal_registration_covered(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "deal registration summary")
        assert result["matched"] is True
        assert result["use_tool"] == "get_deal_registrations_breakdown"

    async def test_channel_manager_injected_in_params(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "revenue q1", channel_manager="Jane")
        assert result["suggested_params"].get("channel_manager") == "Jane"

    async def test_unclear_intent_returns_catalogue(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "xyzzy incomprehensible @@@@")
        assert result["matched"] is False
        assert "available_tools" in result
        assert len(result["available_tools"]) > 10
        assert "hint" in result

    async def test_period_detected_in_hint(self):
        sf = MockSFSimple()
        result = await ci.run_exploratory_analysis(sf, "pipeline next quarter?")
        assert result["matched"] is True
        assert result["suggested_params"]["period"] == "NEXT_QUARTER"

    async def test_no_value_error_on_any_input(self):
        """run_exploratory_analysis must never raise ValueError."""
        sf = MockSFSimple()
        for intent in ["???", "", "   ", "show me stuff", "q99 invalid period test"]:
            try:
                result = await ci.run_exploratory_analysis(sf, intent)
                assert isinstance(result, dict), f"Expected dict for intent {intent!r}"
            except Exception as e:
                pytest.fail(f"Raised {type(e).__name__} for intent {intent!r}: {e}")


# ---------------------------------------------------------------------------
# _coerce_period (server-level normalisation) — requires fastmcp
# ---------------------------------------------------------------------------

@skip_no_fastmcp
class TestCoercePeriod:
    def test_normalises_typo(self):
        import server
        assert server._coerce_period("Q1?") == "Q1"

    def test_normalises_alias(self):
        import server
        assert server._coerce_period("THISQ") == "THIS_QUARTER"

    def test_none_passthrough(self):
        import server
        assert server._coerce_period(None) is None

    def test_valid_unchanged(self):
        import server
        assert server._coerce_period("THIS_FISCAL_YEAR") == "THIS_FISCAL_YEAR"


# ---------------------------------------------------------------------------
# format_result truncation warning logging — requires fastmcp
# ---------------------------------------------------------------------------

@skip_no_fastmcp
class TestFormatResultTruncation:
    def test_logs_truncation_at_warn(self, caplog):
        import server
        data = {
            "tool": "get_partner_scorecard",
            "truncationWarning": "Partner has >2000 opportunities — results may be partial.",
            "data": {},
        }
        with caplog.at_level(logging.WARNING, logger="mcp.requests"):
            server.format_result(data)
        assert any("TRUNCATION" in r.message for r in caplog.records)
        assert any("get_partner_scorecard" in r.message for r in caplog.records)

    def test_no_log_without_warning_key(self, caplog):
        import server
        data = {"tool": "get_revenue", "data": {"totalRevenue": 100}}
        with caplog.at_level(logging.WARNING, logger="mcp.requests"):
            server.format_result(data)
        assert not any("TRUNCATION" in r.message for r in caplog.records)

    def test_returns_valid_json(self):
        import server
        data = {"x": 1, "y": [1, 2, 3]}
        result = server.format_result(data)
        assert json.loads(result) == data
