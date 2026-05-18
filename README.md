# Salesforce FastMCP Connector

FastMCP server providing Salesforce analytics and CRUD tools, purpose-built for Southern Europe channel management (Italy, Spain, Portugal, Greece, Cyprus, Malta).

**Total: 60 tools** across CRUD, navigation, analytics, BI, and specialized channel intelligence. Includes Phase 1 activity/risk/velocity analytics with config-based revenue targets.

## 📖 Quick Start for Channel Directors

**New to the MCP?** Start here:
- **[CHANNEL_DIRECTOR_PLAYBOOK.md](CHANNEL_DIRECTOR_PLAYBOOK.md)** — Complete reference for all 60 tools with real-world examples, organized by use case (daily standup, weekly ops, monthly review, QBR, partner management, etc.)
- Real prompt examples: `get_revenue()`, `get_pipeline()`, `generate_partner_qbr()`
- Copy-paste ready workflows for reporting

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
| `salesforce_opportunities_by_partner` | Find opportunities by partner name (handles lookup syntax) |

### Southern Europe Channel Intelligence (21 tools)
| Tool | Purpose |
|------|---------|
| `get_revenue` | Closed-Won revenue — total, by country, by partner, by quarter (now with targets & attainment %) |
| `get_pipeline` | Open pipeline — total, by stage, by country, by partner |
| `get_top_partners` | Top partners ranked by revenue or pipeline |
| `get_partner_detail` | Full scorecard for a single partner |
| `get_partner_pipeline` | Partner-specific open pipeline with opportunity list |
| `get_partner_scorecard` | Deep-dive: revenue, pipeline, deal count, countries, stages |
| `get_opportunity_list` | Paginated open opportunity list with filters |
| `search_opportunities` | Search opportunities by name fragment |
| `get_opportunity_detail` | Full detail for a specific opportunity |
| `get_deal_registrations` | Deal registration count by period |
| `get_deal_registrations_breakdown` | Deal registrations broken down by partner or country |
| `get_growth` | Growth comparison between two periods (absolute + %) |
| `get_orphan_hygiene` | Open deals missing a partner assignment |
| `get_kpi_snapshot` | Core KPI bundle: revenue, pipeline, win rate, coverage |
| `get_weighted_pipeline` | Pipeline weighted by probability (Amount × Probability%) |
| `get_channel_manager_performance` | Channel manager leaderboard |
| `get_multi_period_trend` | Compare up to 8 fiscal periods side by side |
| `get_win_rate_by_country` | Win rate by country with revenue and deal counts |
| `get_time_to_close_stats` | Avg/median/min/max days from creation to close |
| `route_slash_command` | Slash command router (`/pipeline`, `/revenue`, etc.) |
| `run_exploratory_analysis` | Natural-language intent mapping to canonical tools |
| `generate_partner_qbr` | **Full QBR document for a partner (see below)** |
| `list_available_metrics` | List all tools, periods, and runtime config |

### Phase 1: Activity, Risk & Velocity Tools (9 tools)
| Tool | Purpose |
|------|---------|
| `get_stalled_deals` | Find opportunities not modified in X days (default 60) — bottleneck detection |
| `get_partner_activity_summary` | Partner engagement summary: open pipeline, deal count, last activity date |
| `get_opportunity_recency` | Individual deal modification history and days since activity |
| `get_lost_deals` | Lost deal analysis: count, amount, grouped by stage/partner/country |
| `get_new_vs_existing` | Revenue/pipeline split by Type (New Business vs. Renewal/Expansion) |
| `get_stage_risk_profile` | Probability distribution and confidence level by stage |
| `get_deal_aging_by_stage` | Deal count and age by stage — identifies pipeline bottlenecks |
| `get_high_risk_deals` | Alerts on low-probability deals closing within 30 days (early intervention) |
| `get_stage_progression_velocity` | Historical stage velocity from closed-won deals vs. current aging |

---

## Revenue Targets Configuration

Revenue targets are defined in `config/sales_targets.yaml` (no Salesforce custom fields needed).

### Features

- **Multi-level targets**: Territory → Countries → specific overrides
- **Partner targets**: Global + country-specific with 100k default
- **Account targets**: Optional enterprise-level targets
- **Version-controlled**: Git history of all quota changes

### Example

```yaml
territories:
  South_Europe:
    revenue_target:
      fy27: 2000000
    countries:
      Spain:
        revenue_target:
          fy27: 700000

partners:
  Accenture:
    revenue_target:
      fy27: 900000
    countries:
      Spain:
        revenue_target:
          fy27: 400000
```

### Usage in Tools

```
get_revenue(period="THIS_QUARTER", territory="South_Europe")
→ Returns revenue + target + attainment %

get_revenue(period="THIS_QUARTER", partner="Accenture", country="Spain")
→ Returns revenue + target + attainment %
```

---

## QBR Tool

`generate_partner_qbr` fetches all relevant partner metrics in parallel and returns a formatted markdown document covering four sections.

### What it includes

| Section | Data |
|---------|------|
| **Business Performance** | Closed-Won revenue, YoY growth %, attainment % vs target, deals won/lost, win rate, avg deal size, avg time to close, deal registrations |
| **Pipeline Health** | Open pipeline amount and count, by stage breakdown, top open opportunities table |
| **Geography** | Revenue and pipeline split by country |
| **Forward Looking** | Next quarter pipeline, deals closing in 60 days |

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `partner_name` | Yes | — | Partner name (partial match, e.g. `"Inetum Spain"`) |
| `period` | No | `THIS_QUARTER` | Review period: `THIS_QUARTER`, `LAST_QUARTER`, `FY27_Q1`, `FY26_Q4`, etc. |
| `prior_period` | No | auto | Comparison period — auto-calculated as same quarter 1 FY back |
| `revenue_target` | No | — | Quota/target amount — enables attainment % and coverage % |
| `top_opps_limit` | No | `10` | Number of open opportunities to list (max 20) |
| `channel_manager` | No | env default | Filter by `Channel_Manager__c` |

### Example prompts

```
Generate QBR for Inetum Spain for Q1 FY27
```
```
Generate a partner QBR for Accenture, this quarter
```
```
QBR for NTT Spain, period FY27_Q1, revenue target 500000
```
```
Generate QBR for Deloitte Italy for last quarter with a target of 800000
```

### Example output structure

```markdown
# QBR: Inetum Spain
**Period:** FY27_Q1 (Feb 2026 – Apr 2026)
**Prepared:** 2026-05-17

---
## Business Performance

### Revenue
- Closed-Won: 320,000
- vs FY26_Q1: +14.3% (280,000 → 320,000)
- Attainment: 64.0% of 500,000 target

### Deals
- Won: 4 | Lost: 2 | Win Rate: 66.7%
- Avg Deal Size: 80,000
- Avg Time to Close: 45 days
- Deal Registrations: 7

---
## Pipeline Health
- Open Pipeline: 1,240,000 (11 deals)
- By Stage: Negotiation 480,000 | Validation 390,000 | Prospecting 370,000

### Top Open Opportunities
| Opportunity | Amount | Stage | Close Date |
|-------------|--------|-------|------------|
| Telefonica Digital Transformation | 250,000 | Negotiation | 2026-06-30 |
| ...

---
## Geography
| Country | Revenue | Pipeline |
|---------|---------|----------|
| Spain   | 320,000 | 1,240,000 |

---
## Forward Looking
- Next Quarter Pipeline: 890,000 (8 deals)
- Closing in 60 days: 3 deals, 480,000
```

---

## Phase 1 Tools: Activity & Risk Analytics

The 9 Phase 1 tools provide activity tracking, risk detection, and stage velocity analysis without requiring Salesforce custom fields. They use **LastModifiedDate** as a proxy for engagement and include simple but effective risk scoring.

### Key Features

- **Activity Tracking**: Identify stalled deals (aging) and partner engagement level
- **Risk Detection**: High-risk alerts on low-probability deals closing soon
- **Stage Analysis**: Bottleneck detection, risk profile, and historical velocity
- **Loss Analysis**: Understand where deals are being lost (by stage, partner, country)
- **New vs Existing**: Split revenue and pipeline by business type

### Documentation

- **[CHANNEL_DIRECTOR_PLAYBOOK.md](CHANNEL_DIRECTOR_PLAYBOOK.md)** — **Start here** — Complete MCP reference for channel directors: daily standup, weekly ops, monthly review, QBR workflows, partner management, real-world examples for all 60 tools
- **[PHASE_1_IMPLEMENTATION.md](PHASE_1_IMPLEMENTATION.md)** — Full usage guide with examples for all 9 activity/risk/velocity tools
- **[CHANNEL_DIRECTOR_CAPABILITY_MAP.md](CHANNEL_DIRECTOR_CAPABILITY_MAP.md)** — Assessment of 60+ channel director questions vs tool coverage
- **[SCALING_PRIORITIZATION.md](SCALING_PRIORITIZATION.md)** — Gap analysis, roadmap for Phase 2+ custom fields

### Example Queries

```
"Which partners are most active?"
→ get_partner_activity_summary()

"Which deals are at high risk of slipping?"
→ get_high_risk_deals(probability_threshold=40)

"Where's our biggest pipeline bottleneck?"
→ get_deal_aging_by_stage(days_threshold=60)

"Are we on quota this quarter?"
→ get_revenue(period="THIS_QUARTER", territory="South_Europe")

"What's our historical stage velocity?"
→ get_stage_progression_velocity()
```

---

## Supported Fiscal Periods

The fiscal year runs **Feb – Jan** (FY27 = Feb 2026 – Jan 2027).

| Period | Dates |
|--------|-------|
| `THIS_QUARTER` / `CURRENT` | Current fiscal quarter |
| `LAST_QUARTER` | Previous fiscal quarter |
| `NEXT_QUARTER` | Next fiscal quarter |
| `THIS_FISCAL_YEAR` | Feb 1 – Jan 31 of current FY |
| `LAST_FISCAL_YEAR` | Prior full fiscal year |
| `Q1` / `Q2` / `Q3` / `Q4` | Named quarter in current FY |
| `FY27_Q1` | Feb – Apr 2026 |
| `FY27_Q2` | May – Jul 2026 |
| `FY27_Q3` | Aug – Oct 2026 |
| `FY27_Q4` | Nov 2026 – Jan 2027 |
| `FY26_Q1` … `FY26_Q4` | Same quarters in prior FY |
| `LAST_30_DAYS` | Rolling 30 days back |
| `NEXT_60_DAYS` | Rolling 60 days forward |

---

## Setup

### Prerequisites
- Python 3.10+
- Salesforce Session ID (SID) — obtained from browser cookies

### Installation

```bash
git clone git@github.com:santorres/salesforce-fastmcp.git
cd salesforce-fastmcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with SALESFORCE_BASE_URL and SALESFORCE_SID
```

### Getting a Salesforce Session ID

1. Log into Salesforce in Chrome
2. Run: `node Scripts/extract-sid.js`
3. Test it: `node Scripts/test-token.js <sid>`
4. Paste into `.env` as `SALESFORCE_SID`

Session IDs expire after ~24 hours of inactivity. Repeat when you get `INVALID_SESSION_ID` errors.

---

## Running the Server

```bash
# HTTP mode (for remote/two-laptop setup) — default
python3 server.py

# Explicit configuration
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py

# stdio mode (for local Claude Desktop without proxy)
MCP_TRANSPORT=stdio python3 server.py
```

Request logs are written to `mcp_requests.log` (and stderr), rotating at 5 MB.

---

## Two-Laptop Setup

Run the server on the Salesforce-authenticated laptop and connect from the AI laptop via Tailscale.

### Server laptop

```bash
# Get fresh SID, update .env, then:
python3 server.py
# Server runs on port 8000
```

### AI laptop (Claude Desktop)

`~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "salesforce": {
      "command": "/path/to/salesforce-fastmcp/wrapper.sh"
    }
  }
}
```

`wrapper.sh` converts Claude Desktop's stdio to HTTP and handles MCP session management. Server IP is configured via:
```bash
export SALESFORCE_MCP_URL="http://100.x.x.x:8000/mcp"
```

### AI laptop (Claude Code)

```bash
claude mcp add salesforce "/path/to/salesforce-fastmcp/wrapper.sh"
```

### Pulling updates on the server laptop

```bash
git pull origin main
# Then restart the server
```

---

## Working with Lookup Fields

Salesforce lookup fields store record IDs, not names. Use relationship syntax:

```sql
-- WRONG:
WHERE Partner__c = 'Inetum - Spain (Partner)'

-- CORRECT:
WHERE Partner__r.Name = 'Inetum - Spain (Partner)'
-- or partial match:
WHERE Partner__r.Name LIKE '%Inetum%'
```

Use `salesforce_find_partner` to look up a partner's ID before writing raw SOQL.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `INVALID_SESSION_ID` | SID expired — run `extract-sid.js`, update `.env`, restart server |
| `Connection refused` in wrapper | Server not running on the other laptop |
| `Missing session ID` (HTTP 400) | proxy.py session tracking issue — restart Claude Desktop |
| Tool not found after update | Pull latest on server laptop and restart `server.py` |
