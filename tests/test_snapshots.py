"""Meta/integrity tests — catch consistency issues across files."""

import re
import ast

import pytest
import yaml

import channel_intelligence as ci
import prompts


def _count_mcp_tools_in_server() -> int:
    with open("server.py", "r") as f:
        content = f.read()
    return content.count("@mcp.tool")


def _readme_claimed_tool_count() -> int | None:
    with open("README.md", "r") as f:
        content = f.read()
    m = re.search(r"\*\*Total:\s*(\d+)\s*tools\*\*", content)
    return int(m.group(1)) if m else None


def _yaml_country_names() -> set[str]:
    with open("config/sales_targets.yaml", "r") as f:
        config = yaml.safe_load(f)
    countries = set()
    for terr in config.get("territories", {}).values():
        countries.update(terr.get("countries", {}).keys())
    return countries


class TestToolCount:
    def test_readme_matches_server(self):
        actual = _count_mcp_tools_in_server()
        claimed = _readme_claimed_tool_count()
        assert claimed is not None, "README.md has no 'Total: N tools' line"
        assert claimed == actual, (
            f"README claims {claimed} tools but server.py has {actual} @mcp.tool decorators. "
            "Update the README."
        )


class TestCountryListConsistency:
    def test_channel_intelligence_has_malta(self):
        assert "Malta" in ci.COUNTRIES

    def test_prompts_has_malta(self):
        assert "Malta" in prompts.COUNTRIES

    def test_prompts_matches_channel_intelligence(self):
        ci_set = set(ci.COUNTRIES)
        prompts_set = set(prompts.COUNTRIES)
        diff = ci_set.symmetric_difference(prompts_set)
        assert not diff, (
            f"COUNTRIES mismatch between channel_intelligence and prompts: {diff}"
        )

    def test_yaml_countries_subset_of_ci(self):
        yaml_countries = _yaml_country_names()
        ci_set = set(ci.COUNTRIES)
        extra = yaml_countries - ci_set
        assert not extra, (
            f"YAML defines countries not in channel_intelligence.COUNTRIES: {extra}"
        )


class TestPeriodListComplete:
    def test_all_canonical_periods_resolve(self):
        from datetime import date
        now = date(2026, 5, 19)  # fixed date for determinism

        # FY##_Q# is a pattern, not a literal period
        literal_periods = [p for p in ci.PERIODS if not p.startswith("FY##")]
        for period in literal_periods:
            try:
                r = ci._get_period_range(period, now=now)
                assert "start" in r, f"Period {period!r} returned no 'start' key"
                assert "end" in r,   f"Period {period!r} returned no 'end' key"
            except ValueError as e:
                pytest.fail(f"Period {period!r} raised ValueError: {e}")

    def test_fy26_q1_historical_resolves(self):
        r = ci._get_period_range("FY26_Q1")
        assert r["start"].year >= 2025

    def test_fy25_q3_historical_resolves(self):
        r = ci._get_period_range("FY25_Q3")
        assert r["start"].month == 8


class TestModuleImports:
    def test_channel_intelligence_importable(self):
        import channel_intelligence  # noqa: F401

    def test_server_importable_without_env(self):
        # server.py should not crash on import without Salesforce credentials
        # (credentials are only checked when get_client() is called)
        # Skip if FastMCP isn't installed in this environment
        fastmcp = pytest.importorskip("fastmcp", reason="fastmcp not installed")
        import sys
        sys.modules.pop("server", None)
        try:
            import server  # noqa: F401
        except Exception as e:
            pytest.fail(f"server.py raised on import: {e}")
