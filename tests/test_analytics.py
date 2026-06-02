"""Async analytics tests using MockSF to avoid real Salesforce calls."""

import pytest

from core import channel_intelligence as ci
from tests.conftest import MockSF, soql_response, agg_response


def _period_start(period: str) -> str:
    """Return the SOQL-ready start date string for a period."""
    return ci._get_period_range(period)["start"].isoformat()


def _period_end(period: str) -> str:
    return ci._get_period_range(period)["end"].isoformat()


class TestGetRevenue:
    async def test_total_sums_correctly(self):
        sf = MockSF({
            "totalRevenue": agg_response({"totalRevenue": 500_000.0, "dealCount": 5}),
        })
        result = await ci.get_revenue(sf, "THIS_FISCAL_YEAR", breakdown="total", channel_manager="")
        assert result["data"]["totalRevenue"] == 500_000.0
        assert result["data"]["dealCount"] == 5.0

    async def test_total_with_target_calculates_attainment(self):
        sf = MockSF({
            "totalRevenue": agg_response({"totalRevenue": 250_000.0, "dealCount": 3}),
        })
        result = await ci.get_revenue(
            sf, "THIS_FISCAL_YEAR", breakdown="total",
            channel_manager="", revenue_target=1_000_000,
        )
        data = result["data"]
        assert data["target"] == 1_000_000
        assert data["attainmentPct"] == 25.0
        assert data["gap"] == 750_000

    async def test_zero_revenue_no_crash(self):
        sf = MockSF({
            "totalRevenue": agg_response({"totalRevenue": None, "dealCount": 0}),
        })
        result = await ci.get_revenue(sf, "THIS_FISCAL_YEAR", breakdown="total", channel_manager="")
        assert result["data"]["totalRevenue"] == 0.0

    async def test_period_summary_in_result(self):
        sf = MockSF({
            "totalRevenue": agg_response({"totalRevenue": 0, "dealCount": 0}),
        })
        result = await ci.get_revenue(sf, "THIS_FISCAL_YEAR", breakdown="total", channel_manager="")
        assert "startDate" in result["period"]
        assert "endDate" in result["period"]
        assert "fiscalLabel" in result["period"]


class TestGetPipeline:
    async def test_total_pipeline(self):
        sf = MockSF({
            "totalPipeline": agg_response({"totalPipeline": 2_000_000.0, "dealCount": 12}),
        })
        result = await ci.get_pipeline(sf, "THIS_QUARTER", breakdown="total", channel_manager="")
        assert result["data"]["totalPipeline"] == 2_000_000.0

    async def test_open_deals_count(self):
        sf = MockSF({
            "totalPipeline": agg_response({"totalPipeline": 0, "dealCount": 7}),
        })
        result = await ci.get_pipeline(sf, "THIS_QUARTER", breakdown="total", channel_manager="")
        assert result["data"]["dealCount"] == 7.0


class TestGetGrowth:
    async def test_positive_growth(self):
        fy_start = _period_start("THIS_FISCAL_YEAR")
        last_fy_start = _period_start("LAST_FISCAL_YEAR")
        sf = MockSF({
            fy_start: agg_response({"totalRevenue": 100_000.0, "dealCount": 5}),
            last_fy_start: agg_response({"totalRevenue": 80_000.0, "dealCount": 4}),
        })
        result = await ci.get_growth(sf, "revenue", "THIS_FISCAL_YEAR", "LAST_FISCAL_YEAR",
                                     breakdown="total", channel_manager="")
        data = result["data"]
        assert data["valueA"] == 100_000.0
        assert data["valueB"] == 80_000.0
        assert data["absoluteChange"] == 20_000.0
        assert abs(data["percentageChange"] - 0.25) < 1e-6

    async def test_zero_base_returns_none_pct(self):
        fy_start = _period_start("THIS_FISCAL_YEAR")
        last_fy_start = _period_start("LAST_FISCAL_YEAR")
        sf = MockSF({
            fy_start: agg_response({"totalRevenue": 50_000.0, "dealCount": 3}),
            last_fy_start: agg_response({"totalRevenue": 0.0, "dealCount": 0}),
        })
        result = await ci.get_growth(sf, "revenue", "THIS_FISCAL_YEAR", "LAST_FISCAL_YEAR",
                                     breakdown="total", channel_manager="")
        assert result["data"]["percentageChange"] is None

    async def test_negative_growth(self):
        fy_start = _period_start("THIS_FISCAL_YEAR")
        last_fy_start = _period_start("LAST_FISCAL_YEAR")
        sf = MockSF({
            fy_start: agg_response({"totalRevenue": 60_000.0, "dealCount": 2}),
            last_fy_start: agg_response({"totalRevenue": 100_000.0, "dealCount": 5}),
        })
        result = await ci.get_growth(sf, "revenue", "THIS_FISCAL_YEAR", "LAST_FISCAL_YEAR",
                                     breakdown="total", channel_manager="")
        assert result["data"]["absoluteChange"] < 0
        assert result["data"]["percentageChange"] < 0


class TestGetKpiSnapshot:
    def _make_sf(self, *, total_closed=5, won_closed=3, revenue=300_000, pipeline=500_000,
                 open_count=10, avg=60_000, orphan_count=2, partner_records=None,
                 focus_partners=5):
        partner_records = partner_records or []
        return MockSF({
            "wonCount":      agg_response({"revenue": revenue,   "wonCount": won_closed}),
            "openCount":     agg_response({"pipeline": pipeline, "openCount": open_count}),
            "totalClosed":   agg_response({"totalClosed": total_closed}),
            "wonClosed":     agg_response({"wonClosed": won_closed}),
            "avgClosedDeal": agg_response({"avgClosedDeal": avg}),
            "orphanCount":   agg_response({"orphanCount": orphan_count}),
            "partnerId":     soql_response(partner_records),
            "focusPartners": agg_response({"focusPartners": focus_partners}),
        })

    async def test_win_rate_normal(self):
        sf = self._make_sf(total_closed=4, won_closed=3)
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["winRate"] == pytest.approx(0.75)

    async def test_win_rate_zero_when_no_closed(self):
        sf = self._make_sf(total_closed=0, won_closed=0)
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["winRate"] == 0

    async def test_orphan_pct_calculated(self):
        sf = self._make_sf(open_count=10, orphan_count=4)
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["orphanOpenPct"] == pytest.approx(0.4)

    async def test_orphan_pct_zero_when_no_open(self):
        sf = self._make_sf(open_count=0, orphan_count=0)
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["orphanOpenPct"] == 0

    async def test_active_partners_count(self):
        partner_rows = [
            {"partnerId": "001", "amount": 50_000},
            {"partnerId": "002", "amount": 30_000},
        ]
        sf = self._make_sf(partner_records=partner_rows)
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["activePartners"] == 2

    async def test_coverage_ratio_with_target(self):
        sf = self._make_sf(pipeline=500_000)
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", revenue_target=1_000_000, channel_manager="")
        assert result["data"]["coverageRatio"] == pytest.approx(0.5)

    async def test_coverage_ratio_none_without_target(self):
        sf = self._make_sf()
        result = await ci.get_kpi_snapshot(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["coverageRatio"] is None


class TestGetMultiPeriodTrend:
    async def test_total_breakdown_not_empty(self):
        """Regression for Phase 1-A bug: series_map['Total'] was never populated."""
        q1_start = _period_start("Q1")
        q2_start = _period_start("Q2")
        sf = MockSF({
            q1_start: agg_response({"totalRevenue": 100_000.0, "dealCount": 5}),
            q2_start: agg_response({"totalRevenue": 200_000.0, "dealCount": 8}),
        })
        result = await ci.get_multi_period_trend(sf, metric="revenue", periods=["Q1", "Q2"],
                                                  breakdown="total", channel_manager="")
        assert result["data"], "data must not be empty (regression for Phase 1-A bug)"
        assert result["data"][0]["label"] == "Total"

    async def test_total_breakdown_values_correct(self):
        q1_start = _period_start("Q1")
        q2_start = _period_start("Q2")
        sf = MockSF({
            q1_start: agg_response({"totalRevenue": 100_000.0, "dealCount": 5}),
            q2_start: agg_response({"totalRevenue": 200_000.0, "dealCount": 8}),
        })
        result = await ci.get_multi_period_trend(sf, metric="revenue", periods=["Q1", "Q2"],
                                                  breakdown="total", channel_manager="")
        totals = result["data"][0]
        values = [v for k, v in totals.items() if k != "label"]
        assert 100_000.0 in values
        assert 200_000.0 in values

    async def test_country_breakdown_keys(self):
        q1_start = _period_start("Q1")
        q2_start = _period_start("Q2")
        sf = MockSF({
            q1_start: soql_response([
                {"country": "Spain",    "totalRevenue": 80_000.0, "dealCount": 3},
                {"country": "Italy",    "totalRevenue": 20_000.0, "dealCount": 2},
            ]),
            q2_start: soql_response([
                {"country": "Spain",    "totalRevenue": 90_000.0, "dealCount": 4},
                {"country": "Portugal", "totalRevenue": 10_000.0, "dealCount": 1},
            ]),
        })
        result = await ci.get_multi_period_trend(sf, metric="revenue", periods=["Q1", "Q2"],
                                                  breakdown="country", channel_manager="")
        countries = {row["label"] for row in result["data"]}
        assert "Spain" in countries
        assert "Italy" in countries
        assert "Portugal" in countries

    async def test_invalid_metric_raises(self):
        sf = MockSF({})
        with pytest.raises(ValueError, match="metric"):
            await ci.get_multi_period_trend(sf, metric="invalid", periods=["Q1"])

    async def test_too_many_periods_raises(self):
        sf = MockSF({})
        with pytest.raises(ValueError, match="max 8"):
            await ci.get_multi_period_trend(sf, metric="revenue",
                                             periods=["Q1"] * 9)


class TestGetOrphanHygiene:
    async def test_structure_returned(self):
        sf = MockSF({
            # Summary: only query with no GROUP BY and starts with SELECT COUNT(Id) orphanCount
            "SELECT COUNT(Id) orphanCount, SUM": agg_response(
                {"orphanCount": 15, "orphanValue": 750_000}
            ),
            # Top opps: has Id, Name, Amount ... ORDER BY Amount
            "Id, Name, Amount, StageName, CloseDate": soql_response([]),
            # Stage breakdown: starts with SELECT StageName stage
            "StageName stage, COUNT": soql_response([
                {"stage": "Proposal", "orphanCount": 8, "orphanValue": 400_000},
            ]),
            # Country breakdown: starts with SELECT Account.BillingCountry country
            "BillingCountry country, COUNT": soql_response([
                {"country": "Spain", "orphanCount": 10, "orphanValue": 500_000},
            ]),
        })
        result = await ci.get_orphan_hygiene(sf, "THIS_QUARTER", channel_manager="")
        assert result["data"]["orphanCount"] == 15.0
        assert result["data"]["orphanValue"] == 750_000.0
        assert isinstance(result["data"]["byStage"], list)
        assert isinstance(result["data"]["byCountry"], list)
        assert result["data"]["byStage"][0]["stage"] == "Proposal"
        assert result["data"]["byCountry"][0]["country"] == "Spain"


class TestGetPartnerDetail:
    async def test_no_accounts_uses_name_fallback(self):
        """When no Account records match, falls back to Partner__r.Name LIKE query."""
        sf = MockSF({
            # Account lookup returns nothing
            "SELECT Id, Name FROM Account": soql_response([]),
            # All metrics queries use these distinctive keywords
            "totalRevenue": agg_response({"totalRevenue": 50_000.0, "wonCount": 1}),
            "totalPipeline": agg_response({"totalPipeline": 100_000.0, "openCount": 3}),
            "totalClosed":   agg_response({"totalClosed": 2}),
            "wonClosed":     agg_response({"wonClosed": 1}),
            # Open opps list
            "ORDER BY Amount DESC NULLS LAST LIMIT": soql_response([]),
        })
        result = await ci.get_partner_detail(sf, "TestPartner", "THIS_QUARTER", channel_manager="")
        assert result["matchedPartners"] == []
        assert result["data"]["revenue"] == 50_000.0
        assert result["data"]["pipeline"] == 100_000.0

    async def test_partner_with_accounts(self):
        sf = MockSF({
            "SELECT Id, Name FROM Account": soql_response([
                {"Id": "001XX", "Name": "Accenture Spain"},
            ]),
            "totalRevenue": agg_response({"totalRevenue": 200_000.0, "wonCount": 2}),
            "totalPipeline": agg_response({"totalPipeline": 400_000.0, "openCount": 5}),
            "totalClosed":   agg_response({"totalClosed": 3}),
            "wonClosed":     agg_response({"wonClosed": 2}),
            "ORDER BY Amount DESC NULLS LAST LIMIT": soql_response([]),
        })
        result = await ci.get_partner_detail(sf, "Accenture", "THIS_QUARTER", channel_manager="")
        assert len(result["matchedPartners"]) == 1
        assert result["matchedPartners"][0]["name"] == "Accenture Spain"
        assert result["data"]["revenue"] == 200_000.0

    async def test_win_rate_zero_when_no_closed(self):
        sf = MockSF({
            "SELECT Id, Name FROM Account": soql_response([]),
            "totalRevenue": agg_response({"totalRevenue": 0, "wonCount": 0}),
            "totalPipeline": agg_response({"totalPipeline": 0, "openCount": 0}),
            "totalClosed":   agg_response({"totalClosed": 0}),
            "wonClosed":     agg_response({"wonClosed": 0}),
            "ORDER BY Amount DESC NULLS LAST LIMIT": soql_response([]),
        })
        result = await ci.get_partner_detail(sf, "Nobody", "THIS_QUARTER", channel_manager="")
        assert result["data"]["winRate"] == 0


class TestGetTopPartners:
    async def test_diagnostics_when_no_revenue_data(self):
        """When no partner revenue data, diagnostics block explains why."""
        sf = MockSF({
            # get_revenue with breakdown=partner returns empty list
            "GROUP BY Partner__c, Partner__r.Name": soql_response([]),
            # diagnostics queries
            "totalWon":     agg_response({"totalWon": 3}),
            "partneredWon": agg_response({"partneredWon": 0}),
        })
        result = await ci.get_top_partners(sf, "revenue", "THIS_QUARTER", channel_manager="")
        assert result["data"] == []
        assert result["diagnostics"] is not None
        assert result["diagnostics"]["noData"] is True
        assert "Partner__c" in result["diagnostics"]["reason"]

    async def test_data_returned_when_present(self):
        sf = MockSF({
            "GROUP BY Partner__c, Partner__r.Name": soql_response([
                {"partnerId": "001", "partnerName": "Accenture", "totalRevenue": 300_000.0, "dealCount": 3},
                {"partnerId": "002", "partnerName": "Inetum",    "totalRevenue": 200_000.0, "dealCount": 2},
            ]),
        })
        result = await ci.get_top_partners(sf, "revenue", "THIS_QUARTER", channel_manager="")
        assert len(result["data"]) == 2
        assert result["diagnostics"] is None
        assert result["data"][0]["partnerName"] == "Accenture"
