# Salesforce FastMCP Connector

FastMCP server providing Salesforce analytics and CRUD tools, purpose-built for Southern Europe channel management (Italy, Spain, Portugal, Greece, Cyprus, Malta).

**54 tools** across CRUD, navigation, analytics, and channel intelligence. Config-driven revenue targets, full QBR generation, and activity/risk analytics — all without Salesforce custom fields.

---

## Quick Start for Channel Directors

### 📖 Documentation (Pick Your Interface)

**Using Claude Desktop (MCP - Interactive):**
- **[docs/channel-director/PLAYBOOK.md](docs/channel-director/PLAYBOOK.md)** — Complete reference for all 54 MCP tools, organized by daily/weekly/monthly workflows
- **[docs/channel-director/PROMPTS.md](docs/channel-director/PROMPTS.md)** — Copy-paste prompts for Claude Desktop, grouped by topic

**Using CLI (Command-line - Automation):**
- **[cli/docs/PLAYBOOK.md](cli/docs/PLAYBOOK.md)** — Comprehensive CLI guide for automated workflows, scheduled reports, and Hermes Agent integration
  - ✅ 10 commands with real examples
  - ✅ Daily/weekly/monthly workflow templates
  - ✅ Hermes automation setup
  - ✅ Advanced jq piping for custom reporting

**Quick decision:** Use **MCP** for questions ("What's happening with Accenture?"), use **CLI** for automation ("Generate QBRs every month-end")

---

## Codebase Overview

| File | What it does |
|------|-------------|
| `mcp/server.py` | FastMCP server entry point — registers all 54 MCP tools, middleware, HTTP/stdio transport |
| `core/channel_intelligence.py` | All channel analytics tool implementations (revenue, pipeline, partners, hygiene, QBR, etc.) |
| `core/ci_config.py` | Constants, `ConfigManager` (YAML target lookups), partner key normalisation |
| `core/ci_fiscal.py` | Fiscal calendar helpers, period arithmetic, SOQL query builders |
| `core/salesforce_client.py` | Async Salesforce REST API client (httpx-based) |
| `core/prompts.py` | 14 structured MCP prompt templates for common analyses |
| `mcp/proxy.py` | stdio↔HTTP proxy — used by `wrapper.sh` to connect Claude Desktop to the remote server |
| `mcp/wrapper.sh` | Shell script Claude Desktop calls; proxies MCP traffic to the remote server over Tailscale |
| `config/sales_targets.yaml` | Revenue targets by territory, country, and partner — no Salesforce fields needed |

### Test files

| File | What it covers |
|------|---------------|
| `tests/test_fiscal.py` | Fiscal calendar, quarter ranges, period normalisation (44 tests) |
| `tests/test_soql.py` | SOQL escaping, `_clamp_limit`, `_build_opp_where` (22 tests) |
| `tests/test_config.py` | ConfigManager target lookups, zero-target edge cases, partner fuzzy matching (26 tests) |
| `tests/test_analytics.py` | Async analytics tools with mocked Salesforce responses (28 tests) |
| `tests/test_snapshots.py` | Tool count vs README, COUNTRIES consistency, all periods resolve (9 tests) |
| `tests/test_llm_layer.py` | `_detect_period`, routing table, `_coerce_period`, truncation logging (30 tests) |
| `tests/test_integration.py` | **Real Salesforce data** — 59 tests against a live MCP server |

---

## Tools Overview

### Salesforce CRUD (8 tools)
| Tool | Purpose |
|------|---------|
| `salesforce_query` | Execute raw SOQL queries |
| `salesforce_sobjects` | List available Salesforce objects |
| `salesforce_recent` | Fetch recently accessed records |
| `salesforce_search` | Execute SOSL searches |
| `salesforce_describe` | Get object/field metadata |
| `salesforce_create` | Create a record |
| `salesforce_update` | Update a record |
| `salesforce_delete` | Delete a record |

### Navigation & Relationships (4 tools)
| Tool | Purpose |
|------|---------|
| `salesforce_relationships` | Get related records (e.g. Contacts for an Account) |
| `salesforce_lookup` | Search records by name or field |
| `salesforce_hierarchy` | Navigate parent/child relationships |
| `salesforce_find_partner` | Find a partner account by name and return its ID |

### Analytics (3 tools)
| Tool | Purpose |
|------|---------|
| `salesforce_aggregate` | COUNT, SUM, AVG, MAX, MIN aggregations |
| `salesforce_reports` | Access existing Salesforce reports |
| `salesforce_trend_analysis` | Time-based trend analysis |

### Business Intelligence (4 tools)
| Tool | Purpose |
|------|---------|
| `salesforce_pipeline` | Sales pipeline analysis with forecasting |
| `salesforce_case_insights` | Support case metrics |
| `salesforce_lead_funnel` | Lead conversion funnel |
| `salesforce_opportunities_by_partner` | Find opportunities by partner name |

### Southern Europe Channel Intelligence (23 tools)
| Tool | Purpose |
|------|---------|
| `get_revenue` | Closed-Won revenue — total, by country, by partner, by quarter (with targets & attainment %) |
| `get_pipeline` | Open pipeline — total, by stage, by country, by partner |
| `get_top_partners` | Top partners ranked by revenue or pipeline |
| `get_partner_detail` | Full scorecard for a single partner |
| `get_partner_pipeline` | Partner-specific open pipeline with opportunity list |
| `get_partner_scorecard` | Deep-dive: revenue, pipeline, deal count, countries, stages, quarterly trend |
| `get_opportunity_list` | Paginated open opportunity list with filters |
| `search_opportunities` | Search opportunities by name fragment |
| `get_opportunity_detail` | Full detail for a specific opportunity |
| `get_deal_registrations` | Deal registration summary by period |
| `get_deal_registrations_breakdown` | Deal registrations broken down by partner, country, or status |
| `get_deal_registrations_trend` | Deal registration trend across multiple quarters |
| `get_growth` | Growth comparison between two periods (absolute + %) |
| `get_orphan_hygiene` | Open deals missing a partner assignment |
| `get_kpi_snapshot` | Core KPI bundle: revenue, pipeline, win rate, coverage |
| `get_weighted_pipeline` | Pipeline weighted by probability (Amount × Probability%) |
| `get_channel_manager_performance` | Channel manager leaderboard |
| `get_multi_period_trend` | Compare up to 8 fiscal periods side by side |
| `get_win_rate_by_country` | Win rate by country with revenue and deal counts |
| `get_time_to_close_stats` | Avg/median/min/max days from creation to close |
| `route_slash_command` | Slash command router (`/pipeline`, `/revenue`, etc.) |
| `run_exploratory_analysis` | Natural-language intent → canonical tool hint |
| `generate_partner_qbr` | Full QBR document for a partner |
| `list_available_metrics` | List all tools, periods, and runtime config |
| `admin_discover_targets` | Admin-only: discover quota/target fields in the org |

### Activity, Risk & Velocity (9 tools)
| Tool | Purpose |
|------|---------|
| `get_stalled_deals` | Opportunities not modified in X days (default 60) |
| `get_partner_activity_summary` | Partner engagement: open pipeline, deal count, last activity |
| `get_opportunity_recency` | Days since last modification for a specific deal |
| `get_lost_deals` | Lost deal analysis by stage, partner, or country |
| `get_new_vs_existing` | Revenue/pipeline split by Type (New Business vs. Renewal) |
| `get_stage_risk_profile` | Probability distribution and confidence level by stage |
| `get_deal_aging_by_stage` | Deal count and age by stage — pipeline bottleneck detection |
| `get_high_risk_deals` | Low-probability deals closing within 30 days |
| `get_stage_progression_velocity` | Historical stage velocity vs. current deal aging |

---

## Claude Desktop Prompts

These are natural language prompts that work directly in Claude Desktop. Copy and paste any of them.

### Revenue
```
What's our total closed-won revenue for this fiscal year?
Break down FY27 revenue by country
How are we tracking against target in Spain this year?
Compare revenue this fiscal year versus last fiscal year
Show me Q1 revenue
```

### Pipeline
```
What does our pipeline look like this quarter?
Show me the pipeline by stage for this quarter
What's coming up in the next 60 days?
Show pipeline for both this quarter and next quarter combined
```

### Partners
```
Who are our top 10 partners by revenue this fiscal year?
Give me a full scorecard for Accenture
How is Inetum Spain performing this quarter?
Generate a QBR for Accenture for this quarter
Generate QBR for Inetum Spain for Q1 FY27 with a target of 500000
```

### Hygiene & Risk
```
Show me all orphan deals without a partner assigned this quarter
Which deals haven't moved in the last 60 days?
What deals are high risk — low probability and closing soon?
Show me deals we lost this quarter and where we lost them
Which partners are most active?
```

### KPIs & Trends
```
Give me a full KPI snapshot for this fiscal year
Show me revenue trend across Q1, Q2, Q3, Q4
What's our win rate by country this year?
How do deal registrations compare quarter over quarter?
What was revenue in FY26 Q1 versus FY27 Q1?
Show revenue growth from last fiscal year to this one broken down by country
```

---

## Supported Fiscal Periods

Fiscal year runs **Feb – Jan** (FY27 = Feb 2026 – Jan 2027).

| Period | What it means |
|--------|--------------|
| `THIS_QUARTER` | Current fiscal quarter |
| `LAST_QUARTER` | Previous fiscal quarter |
| `NEXT_QUARTER` | Next fiscal quarter |
| `THIS_FISCAL_YEAR` | Full current FY (Feb 1 – Jan 31) |
| `LAST_FISCAL_YEAR` | Prior full fiscal year |
| `Q1` / `Q2` / `Q3` / `Q4` | Named quarter in current FY |
| `FY27_Q1` … `FY27_Q4` | Specific quarter in FY27 |
| `FY26_Q1` … `FY26_Q4` | Same quarters in FY26 |
| `LAST_30_DAYS` | Rolling 30 days back |
| `NEXT_60_DAYS` | Rolling 60 days forward |
| `CURRENT_AND_NEXT_QUARTER` | This quarter + next combined |

The server accepts informal input (`"q1?"`, `"thisQ"`, `"THISQ"`) and normalises it automatically.

---

## Revenue Targets Configuration

Targets live in `config/sales_targets.yaml` — no Salesforce custom fields required.

```yaml
territories:
  South_Europe:
    revenue_target:
      fy27: 3650000
    countries:
      Spain:
        revenue_target:
          fy27: 1825000

partners:
  Accenture:
    revenue_target:
      fy27: 900000
    countries:
      Spain:
        revenue_target:
          fy27: 400000
```

Partner names are matched fuzzily — `"Inetum Spain"`, `"inetum_spain"`, and `"Inetum - Spain (Partner)"` all resolve to the same entry.

---

## Setup

### Prerequisites
- Python 3.10+
- Salesforce Session ID (SID) — from browser cookies or `sf` CLI

### Installation

```bash
git clone git@github.com:santorres/salesforce-fastmcp.git
cd salesforce-fastmcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with SALESFORCE_BASE_URL and SALESFORCE_SID
```

### Running the server

```bash
# HTTP mode — default, used by Claude Desktop via wrapper.sh
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py

# stdio mode — for local Claude Desktop without proxy
MCP_TRANSPORT=stdio python3 server.py
```

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_PORT` | `8000` | HTTP port |
| `MCP_HOST` | `0.0.0.0` | HTTP bind address |
| `MCP_LOG_FILE` | `mcp_requests.log` | Request log path (rotates at 5 MB) |
| `DEFAULT_CHANNEL_MANAGER` | — | Default filter for all tools |

---

## Two-Laptop Setup

The server runs on the laptop with Salesforce auth. Claude Desktop on the other laptop connects via `wrapper.sh` over Tailscale.

```
Claude Desktop (AI laptop)
    └── wrapper.sh (proxy.py)
            └── HTTP → Tailscale → server.py (Salesforce laptop)
                                        └── Salesforce REST API
```

**Server laptop** — start the server:
```bash
source .venv/bin/activate
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py
```

**AI laptop** — Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "salesforceMCP": {
      "command": "/path/to/salesforce-fastmcp/wrapper.sh"
    }
  }
}
```

Set the server address:
```bash
export SALESFORCE_MCP_URL="http://100.x.x.x:8000/mcp"
```

**After every `git pull` on the server laptop, restart `server.py`** — the running process uses the code it loaded at startup.

---

## Running Tests

### Unit tests (no server required, ~0.3s)

```bash
pytest tests/ -m "not integration" -q
# Expected: 149 passed, 9 skipped
```

### Integration tests (requires live server + Salesforce auth)

Start the server on the Salesforce laptop, then run from the same machine:

```bash
INTEGRATION_SERVER_URL=http://localhost:8000/mcp pytest tests/test_integration.py -v
# Expected: 56 passed, 3 skipped
```

Run a subset:
```bash
pytest tests/test_integration.py -v -k "revenue"
pytest tests/test_integration.py -v -k "partner"
pytest tests/test_integration.py -v -k "routing"
```

Integration tests skip automatically when the server is not reachable — they never fail the unit test suite.

### What the integration tests verify

- Revenue, pipeline, KPI snapshot return valid non-negative numbers
- Pipeline contains no Closed Won/Lost stages
- Win rates are between 0 and 100
- Top partners are sorted largest → smallest
- High-risk deals all have probability ≤ threshold
- Multi-period trend Total series is non-empty (Phase 1-A regression guard)
- All 11 canonical periods resolve without error
- Exploratory routing returns correct tool hints

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `INVALID_SESSION_ID` | SID expired — refresh token, update `.env`, restart server |
| `Connection refused` in wrapper | Server not running on the other laptop |
| Tool not found after update | `git pull` on server laptop then restart `server.py` |
| `Missing session ID` (HTTP 400) | Restart Claude Desktop |
| Tests skip with "server not reachable" | Server process stopped — restart it |
