"""Unit tests for ConfigManager — revenue target lookups and fiscal calendar."""

import pytest
from datetime import date

import channel_intelligence as ci


def make_config() -> ci.ConfigManager:
    """Build a ConfigManager pre-loaded with test data (no YAML file needed)."""
    cfg = ci.ConfigManager.__new__(ci.ConfigManager)
    cfg.config_path = "<test>"
    cfg.config = {}
    cfg.accounts = {}
    cfg.fiscal_calendar = {
        "fy_start": "02-01",
        "quarters": {
            "Q1": {"start_month": 2, "end_month": 4},
            "Q2": {"start_month": 5, "end_month": 7},
            "Q3": {"start_month": 8, "end_month": 10},
            "Q4": {"start_month": 11, "end_month": 1},
        },
    }
    cfg.territories = {
        "South_Europe": {
            "revenue_target": {"fy27": 3_650_000},
            "countries": {
                "Spain":  {"revenue_target": {"fy27": 1_825_000}},
                "Italy":  {"revenue_target": {"fy27": 825_000}},
                "Cyprus": {"revenue_target": {"fy27": 0}},
                "Malta":  {"revenue_target": {"fy27": 0}},
            },
        },
    }
    cfg.partners = {
        "Accenture": {
            "revenue_target": {"fy27": 900_000},
            "countries": {
                "Spain": {"revenue_target": {"fy27": 400_000}},
            },
        },
        "Inetum_Spain": {
            "revenue_target": {"fy27": 500_000},
            "countries": {
                "Spain": {"revenue_target": {"fy27": 500_000}},
            },
        },
        "ZeroPartner": {
            "revenue_target": {"fy27": 0},
        },
    }
    return cfg


class TestTerritoryTargets:
    def setup_method(self):
        self.cfg = make_config()

    def test_territory_target_no_country(self):
        assert self.cfg.get_territory_target("South_Europe", fiscal_year="fy27") == 3_650_000

    def test_territory_target_country_specific(self):
        assert self.cfg.get_territory_target("South_Europe", country="Spain", fiscal_year="fy27") == 1_825_000

    def test_territory_target_italy(self):
        assert self.cfg.get_territory_target("South_Europe", country="Italy", fiscal_year="fy27") == 825_000

    def test_territory_zero_target_not_ignored(self):
        # Cyprus has fy27=0 — must return 0, not fall through to territory-wide
        assert self.cfg.get_territory_target("South_Europe", country="Cyprus", fiscal_year="fy27") == 0

    def test_territory_malta_zero_target_not_ignored(self):
        assert self.cfg.get_territory_target("South_Europe", country="Malta", fiscal_year="fy27") == 0

    def test_unknown_territory_returns_none(self):
        assert self.cfg.get_territory_target("Unknown_Region", fiscal_year="fy27") is None

    def test_missing_fy_returns_none(self):
        result = self.cfg.get_territory_target("South_Europe", country="Spain", fiscal_year="fy99")
        assert result is None

    def test_territory_fallback_when_no_country_config(self):
        # Portugal has no country entry in our test config → falls back to territory
        result = self.cfg.get_territory_target("South_Europe", country="Portugal", fiscal_year="fy27")
        assert result == 3_650_000


class TestPartnerTargets:
    def setup_method(self):
        self.cfg = make_config()

    def test_partner_country_override(self):
        assert self.cfg.get_partner_target("Accenture", country="Spain", fiscal_year="fy27") == 400_000

    def test_partner_global_fallback(self):
        # Italy not in Accenture's country list → global target
        assert self.cfg.get_partner_target("Accenture", country="Italy", fiscal_year="fy27") == 900_000

    def test_partner_no_country(self):
        assert self.cfg.get_partner_target("Accenture", fiscal_year="fy27") == 900_000

    def test_partner_inetum_spain(self):
        assert self.cfg.get_partner_target("Inetum_Spain", country="Spain", fiscal_year="fy27") == 500_000

    def test_unknown_partner_default(self):
        assert self.cfg.get_partner_target("UnknownPartner", fiscal_year="fy27") == 100_000

    def test_zero_partner_target_not_ignored(self):
        # ZeroPartner has revenue_target.fy27=0 — must return 0, not default 100k
        assert self.cfg.get_partner_target("ZeroPartner", fiscal_year="fy27") == 0

    def test_missing_fy_falls_to_default(self):
        result = self.cfg.get_partner_target("Accenture", fiscal_year="fy99")
        assert result == 100_000


class TestFiscalYearKey:
    def test_fy27_key(self):
        # date in FY27 → label "FY27" → key "fy27"
        fy_label = ci._fiscal_year_label(date(2026, 5, 19))
        fy_key = f"fy{fy_label[2:]}"
        assert fy_key == "fy27"

    def test_fy28_key(self):
        fy_label = ci._fiscal_year_label(date(2027, 3, 1))
        fy_key = f"fy{fy_label[2:]}"
        assert fy_key == "fy28"

    def test_fy26_key(self):
        fy_label = ci._fiscal_year_label(date(2025, 5, 1))
        fy_key = f"fy{fy_label[2:]}"
        assert fy_key == "fy26"


class TestFiscalCalendarFromFile:
    """Smoke tests that the real YAML file loads correctly."""

    def test_real_config_loads(self):
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        assert cfg.territories != {}

    def test_real_spain_target(self):
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        result = cfg.get_territory_target("South_Europe", country="Spain", fiscal_year="fy27")
        assert result == 1_825_000

    def test_real_accenture_global(self):
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        result = cfg.get_partner_target("Accenture", fiscal_year="fy27")
        assert result == 900_000

    def test_real_cyprus_zero_not_fallthrough(self):
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        result = cfg.get_territory_target("South_Europe", country="Cyprus", fiscal_year="fy27")
        assert result == 0


class TestNormalizePartnerKey:
    def test_spaces_to_underscores(self):
        assert ci._normalize_partner_key("Inetum Spain") == "inetum_spain"

    def test_already_underscored(self):
        assert ci._normalize_partner_key("Inetum_Spain") == "inetum_spain"

    def test_strips_punctuation(self):
        # "-" and "()" are stripped; multiple spaces collapse to a single underscore
        assert ci._normalize_partner_key("Inetum - Spain (Partner)") == "inetum_spain_partner"

    def test_lowercased(self):
        assert ci._normalize_partner_key("ACCENTURE") == "accenture"

    def test_fuzzy_lookup_spaces(self):
        """'Inetum Spain' should resolve to Inetum_Spain's target via normalisation."""
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        result = cfg.get_partner_target("Inetum Spain", country="Spain", fiscal_year="fy27")
        assert result == 500_000

    def test_fuzzy_lookup_case_insensitive(self):
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        result = cfg.get_partner_target("accenture", fiscal_year="fy27")
        assert result == 900_000

    def test_fuzzy_lookup_still_returns_default_for_unknown(self):
        cfg = ci.ConfigManager("config/sales_targets.yaml")
        result = cfg.get_partner_target("Partner That Does Not Exist", fiscal_year="fy27")
        assert result == 100_000
