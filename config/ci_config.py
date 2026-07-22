"""Configuration constants and ConfigManager for salesforce-fastmcp.

This module owns:
  - All shared constants (COUNTRIES, PERIODS, etc.)
  - ConfigManager — loads revenue targets and fiscal calendar from YAML
  - get_config() — lazy singleton accessor
  - _normalize_partner_key() — fuzzy partner name → YAML key matching

Dependency direction: ci_config ← ci_fiscal ← channel_intelligence
"""

import os
import re
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOOL_VERSION = "2.1.0"

# ============================================================================
# MCP USAGE MODE (BASIC vs ADVANCED)
# ============================================================================
# Controls which tools are exposed in the MCP server
# BASIC: 48 deterministic domain-specific tools (default, recommended for production)
# ADVANCED: 48 + 12 Salesforce Data Access tools (for power users, testing, evolution)
#
# Set via:
#   1. Environment variable: export MCP_USAGE_MODE=basic|advanced
#   2. Direct config below
#
# For LangSmith integration: metadata will include { "mcp_mode": MCP_USAGE_MODE }
MCP_USAGE_MODE: str = os.getenv("MCP_USAGE_MODE", "basic").lower()

# Validate mode
if MCP_USAGE_MODE not in ["basic", "advanced"]:
    print(f"Warning: Invalid MCP_USAGE_MODE '{MCP_USAGE_MODE}'. Defaulting to 'basic'")
    MCP_USAGE_MODE = "basic"

COUNTRIES: list[str] = ["Italy", "Spain", "Portugal", "Greece", "Cyprus", "Malta"]
COUNTRIES_SQL: str = "('" + "','".join(COUNTRIES) + "')"

COUNTRIES_EE: list[str] = [
    "Poland", "Czech Republic", "Hungary", "Slovakia", "Romania",
    "Bulgaria", "Croatia", "Serbia", "Slovenia", "Turkey"
]

# All countries (SE + EE combined) - used for matching Salesforce data
ALL_COUNTRIES: list[str] = COUNTRIES + COUNTRIES_EE
ALL_COUNTRIES_SQL: str = "('" + "','".join(ALL_COUNTRIES) + "')"

PERIODS: list[str] = [
    "CURRENT", "THIS_FISCAL_YEAR", "CURRENT_FY", "LAST_FISCAL_YEAR",
    "Q1", "Q2", "Q3", "Q4",
    "THIS_QUARTER", "NEXT_QUARTER", "CURRENT_AND_NEXT_QUARTER",
    "LAST_QUARTER", "LAST_30_DAYS", "NEXT_60_DAYS",
    "FY##_Q#",  # Historical year + quarter, e.g. FY26_Q1, FY25_Q2
]

METRICS: list[str] = ["revenue", "pipeline"]
BREAKDOWNS_REVENUE: list[str] = ["total", "country", "quarter", "partner"]
BREAKDOWNS_PIPELINE: list[str] = ["total", "country", "stage", "quarter", "partner"]

DEFAULT_CHANNEL_MANAGER: str = os.getenv("DEFAULT_CHANNEL_MANAGER", "")
ADMIN_KEY: str = os.getenv("ADMIN_KEY", "")
DEFAULT_PARTNER_TARGET: int = 100000

# Region definitions
REGIONS: list[str] = ["SE", "EE", "SE+EE"]

# Sales reps configuration (loaded from YAML, populated below)
SALES_REPS: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Partner key normalisation
# ---------------------------------------------------------------------------

def _normalize_partner_key(name: str) -> str:
    """Convert a natural-language partner name to a YAML dict key.

    Allows fuzzy matching: "Inetum Spain", "Inetum - Spain (Partner)" and
    "Inetum_Spain" all normalise to "inetum_spain".
    """
    cleaned = re.sub(r"[^\w\s]", "", name)   # strip punctuation
    cleaned = cleaned.strip().lower()
    cleaned = re.sub(r"\s+", "_", cleaned)    # spaces → underscores
    return cleaned

# ---------------------------------------------------------------------------
# Config Manager — Load targets from YAML
# ---------------------------------------------------------------------------

class ConfigManager:
    """Load and manage sales targets and fiscal calendar from config/sales_targets.yaml."""

    def __init__(self, config_path: str = "config/sales_targets.yaml"):
        self.config_path = config_path
        self.config = {}
        self.territories = {}
        self.partners = {}
        self.accounts = {}
        self.fiscal_calendar = None
        self.sales_reps = {}
        self._load_config()

    def _load_config(self):
        """Load YAML config, handle missing file gracefully."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or {}
                    self.territories = self.config.get("territories", {})
                    self.partners = self.config.get("partners", {})
                    self.accounts = self.config.get("accounts", {})
                    self.fiscal_calendar = self.config.get("fiscal_calendar", {})
                    self.sales_reps = self.config.get("sales_rep_targets", {})
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")

    def get_territory_target(
        self,
        territory: str,
        country: str | None = None,
        fiscal_year: str = "fy27"
    ) -> int | None:
        """
        Get revenue target for a territory.

        Hierarchy:
        1. Territory + Country combination
        2. Territory-wide target
        3. None if not found
        """
        if territory not in self.territories:
            return None

        terr = self.territories[territory]

        # If country specified, try country-specific target
        if country:
            countries = terr.get("countries", {})
            if country in countries:
                country_config = countries[country]
                target = country_config.get("revenue_target", {}).get(fiscal_year)
                if target is not None:
                    return target

        # Fall back to territory-wide target
        target = terr.get("revenue_target", {}).get(fiscal_year)
        return target

    def get_partner_target(
        self,
        partner_name: str,
        country: str | None = None,
        fiscal_year: str = "fy27"
    ) -> int:
        """
        Get revenue target for a partner.

        Hierarchy:
        1. Partner + Country combination
        2. Partner-wide target
        3. Default (100,000)

        Accepts natural-language partner names — "Inetum Spain" and "Inetum_Spain"
        both resolve to the same YAML entry via _normalize_partner_key().
        """
        # Try exact match first, then normalised key match
        partner = self.partners.get(partner_name)
        if partner is None:
            norm_input = _normalize_partner_key(partner_name)
            for key, val in self.partners.items():
                if _normalize_partner_key(key) == norm_input:
                    partner = val
                    break

        if partner is None:
            return DEFAULT_PARTNER_TARGET

        # If country specified, try country-specific target
        if country:
            countries = partner.get("countries", {})
            if country in countries:
                country_config = countries[country]
                target = country_config.get("revenue_target", {}).get(fiscal_year)
                if target is not None:
                    return target

        # Fall back to partner-wide target
        target = partner.get("revenue_target", {}).get(fiscal_year)
        if target is not None:
            return target

        # Default
        return DEFAULT_PARTNER_TARGET

    def get_account_target(
        self,
        account_name: str,
        fiscal_year: str = "fy27"
    ) -> int | None:
        """Get revenue target for an account (if configured)."""
        if account_name not in self.accounts:
            return None

        account = self.accounts[account_name]
        target = account.get("revenue_target", {}).get(fiscal_year)
        return target

    def get_fiscal_year_start_month(self) -> int:
        """Get fiscal year start month (1-12). Default: February (2)."""
        if not self.fiscal_calendar:
            return 2
        fy_start = self.fiscal_calendar.get("fy_start", "02-01")
        try:
            month = int(fy_start.split("-")[0])
            return month if 1 <= month <= 12 else 2
        except (ValueError, IndexError):
            return 2

    def get_quarter_range(self, quarter: str) -> dict[str, int] | None:
        """Get start/end months for a quarter (Q1-Q4)."""
        if not self.fiscal_calendar:
            return None
        quarters = self.fiscal_calendar.get("quarters", {})
        if quarter not in quarters:
            return None
        q = quarters[quarter]
        return {"start_month": q.get("start_month"), "end_month": q.get("end_month")}

    def get_rep_region(self, rep_name: str) -> str | None:
        """Get the region(s) assigned to a sales rep.
        
        Returns:
            Region string (e.g., 'SE', 'EE', 'SE+EE') or None if not found
        """
        if rep_name not in self.sales_reps:
            return None
        rep = self.sales_reps[rep_name]
        return rep.get("region")

    def get_rep_countries(self, rep_name: str) -> list[str]:
        """Get the list of countries assigned to a sales rep.
        
        Returns:
            List of country names (full names, not ISO codes)
        """
        if rep_name not in self.sales_reps:
            return []
        rep = self.sales_reps[rep_name]
        countries = list(rep.get("countries", {}).keys())
        
        # If multi-region rep (SE+EE), add se_breakdown and ee_breakdown countries
        if rep.get("region") == "SE+EE":
            se_countries = list(rep.get("se_breakdown", {}).keys())
            ee_countries = list(rep.get("ee_breakdown", {}).keys())
            countries = se_countries + ee_countries
        
        return countries


# Lazy-load config on first use
_config_manager: ConfigManager | None = None


def get_config() -> ConfigManager:
    """Get or create the config manager."""
    global _config_manager, SALES_REPS
    if _config_manager is None:
        _config_manager = ConfigManager()
        # Populate the module-level SALES_REPS dict from the config manager
        SALES_REPS.update(_config_manager.sales_reps)
    return _config_manager
