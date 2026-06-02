# Channel Intelligence CLI

Direct command-line access to Salesforce analytics — no MCP, no LLM. Perfect for debug, automation, and scheduled reports.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Get daily standup KPI
python cli/channel_cli.py kpi

# Check revenue for this fiscal year
python cli/channel_cli.py revenue --period THIS_FISCAL_YEAR

# Partner deep-dive
python cli/channel_cli.py partner "Inetum Spain" --period FY27_Q1

# Generate full QBR (outputs markdown)
python cli/channel_cli.py qbr Accenture

# High-risk deals (closing soon, low probability)
python cli/channel_cli.py risk

# Top 10 partners by revenue
python cli/channel_cli.py top-partners --limit 10

# Export as JSON for scripting
python cli/channel_cli.py revenue --json | jq '.data'
```

## Available Commands

### `kpi`
Daily standup metrics: revenue, pipeline, win rate, coverage ratio.

```bash
python cli/channel_cli.py kpi [--period PERIOD] [--json] [--channel-manager MANAGER]
```

**Output:** Key metrics summary
- Closed revenue
- Deal count
- Attainment %
- Pipeline
- Win rate
- Coverage ratio

---

### `revenue`
Closed-won revenue with attainment %, optionally broken down by partner/country/stage.

```bash
python cli/channel_cli.py revenue \
  [--period PERIOD] \
  [--breakdown partner|country|stage|total] \
  [--json] \
  [--channel-manager MANAGER]
```

**Examples:**
```bash
# Revenue this quarter
python cli/channel_cli.py revenue

# Revenue by partner, this fiscal year
python cli/channel_cli.py revenue --period THIS_FISCAL_YEAR --breakdown partner

# JSON export for analysis
python cli/channel_cli.py revenue --json
```

---

### `pipeline`
Open pipeline amount and count, optionally by partner/country/stage.

```bash
python cli/channel_cli.py pipeline \
  [--period PERIOD] \
  [--breakdown partner|country|stage|total] \
  [--json] \
  [--channel-manager MANAGER]
```

**Examples:**
```bash
# Pipeline breakdown by stage
python cli/channel_cli.py pipeline --breakdown stage

# Pipeline by country
python cli/channel_cli.py pipeline --breakdown country
```

---

### `partner`
Full partner scorecard: revenue, pipeline, win rate, activity metrics.

```bash
python cli/channel_cli.py partner PARTNER_NAME [--period PERIOD] [--json]
```

**Examples:**
```bash
# Inetum Spain scorecard
python cli/channel_cli.py partner "Inetum Spain"

# Historical view: last quarter
python cli/channel_cli.py partner "Accenture" --period LAST_QUARTER
```

---

### `qbr`
Full Quarterly Business Review — markdown document with business performance, pipeline health, geography, forward-looking.

```bash
python cli/channel_cli.py qbr PARTNER_NAME \
  [--period PERIOD] \
  [--prior-period PERIOD] \
  [--revenue-target AMOUNT] \
  [--json]
```

**Examples:**
```bash
# QBR for Accenture, this quarter
python cli/channel_cli.py qbr Accenture

# QBR with custom quota
python cli/channel_cli.py qbr "NTT Spain" --revenue-target 500000

# Export as JSON (for programmatic processing)
python cli/channel_cli.py qbr Accenture --json > qbr_accenture.json
```

---

### `risk`
High-risk deals: low probability (<40% default) closing within 30 days.

```bash
python cli/channel_cli.py risk \
  [--period PERIOD] \
  [--probability-threshold PERCENT] \
  [--json] \
  [--channel-manager MANAGER]
```

**Examples:**
```bash
# High-risk alerts
python cli/channel_cli.py risk

# Find deals <50% probability, closing soon
python cli/channel_cli.py risk --probability-threshold 50

# Export to JSON for integration
python cli/channel_cli.py risk --json | jq '.data[] | select(.days_to_close < 7)'
```

---

### `registrations`
Deal registration trend across quarters: count, amount, approval rate, close rate.

```bash
python cli/channel_cli.py registrations [--period PERIOD] [--json] [--channel-manager MANAGER]
```

**Examples:**
```bash
# Show trend across all 4 quarters of current FY
python cli/channel_cli.py registrations

# JSON for graphing
python cli/channel_cli.py registrations --json
```

---

### `top-partners`
Partner leaderboard ranked by revenue or pipeline.

```bash
python cli/channel_cli.py top-partners \
  [--period PERIOD] \
  [--metric revenue|pipeline] \
  [--limit LIMIT] \
  [--json]
```

**Examples:**
```bash
# Top 10 by revenue (default)
python cli/channel_cli.py top-partners

# Top 5 by pipeline, this fiscal year
python cli/channel_cli.py top-partners --limit 5 --metric pipeline --period THIS_FISCAL_YEAR

# Export for reports
python cli/channel_cli.py top-partners --json
```

---

## Common Options

All commands support:

- `--period TEXT` — Fiscal period (default: `THIS_QUARTER`)
  - Examples: `THIS_QUARTER`, `THIS_FISCAL_YEAR`, `LAST_QUARTER`, `FY27_Q1`, `FY26_Q2`, `LAST_30_DAYS`, `NEXT_60_DAYS`

- `--json` — Output raw JSON instead of pretty formatting
  - Use with `jq` for advanced filtering and transformation

- `--channel-manager TEXT` — Filter by channel manager name

---

## Fiscal Periods

All commands accept any valid period identifier:

| Period | Meaning |
|--------|---------|
| `THIS_QUARTER` | Current fiscal quarter |
| `THIS_FISCAL_YEAR` | Feb 2026 – Jan 2027 |
| `LAST_QUARTER` | Previous quarter |
| `LAST_FISCAL_YEAR` | Prior full fiscal year |
| `Q1`, `Q2`, `Q3`, `Q4` | Named quarter in current FY |
| `FY27_Q1` | Feb–Apr 2026 |
| `FY26_Q1` | Feb–Apr 2025 |
| `LAST_30_DAYS` | Rolling 30 days back |
| `NEXT_60_DAYS` | Rolling 60 days forward |

---

## Output Formats

### Pretty Print (Default)

Human-readable tables and summaries:

```bash
$ python cli/channel_cli.py kpi

KPI Snapshot
--------------------------------------------------
Revenue (Closed-Won): $550,000
  Deals: 6
  Attainment: 73.3%

Pipeline (Open): $2,100,000
  Deals: 18

Coverage Ratio: 3.8x
Win Rate: 66.7%
```

### JSON Export

Machine-readable output for scripting, piping to `jq`, or integration:

```bash
$ python cli/channel_cli.py revenue --json

{
  "tool": "get_revenue",
  "period": {
    "fiscalLabel": "FY27_Q2",
    "startDate": "2026-05-01",
    "endDate": "2026-07-31"
  },
  "data": {
    "closed_won_amount": 550000,
    "count": 6,
    "attainment_pct": 73.3
  }
}
```

---

## Use Cases

### Daily Standup (5 min)

```bash
python cli/channel_cli.py kpi
python cli/channel_cli.py risk
```

### Weekly Ops Review (30 min)

```bash
python cli/channel_cli.py revenue --period THIS_QUARTER
python cli/channel_cli.py pipeline --breakdown stage
python cli/channel_cli.py risk --json
python cli/channel_cli.py registrations
```

### Monthly Business Review (1 hour)

```bash
python cli/channel_cli.py revenue --period THIS_FISCAL_YEAR --breakdown partner
python cli/channel_cli.py top-partners --limit 10
python cli/channel_cli.py pipeline --breakdown country
```

### Partner Review (30 min)

```bash
python cli/channel_cli.py partner "Accenture"
python cli/channel_cli.py qbr "Accenture"
```

### Automated Weekly Report

```bash
#!/bin/bash
# save as weekly_report.sh

REPORT_FILE="weekly_report_$(date +%Y%m%d).txt"

{
  echo "Weekly Channel Report — $(date)"
  echo "======================================"
  echo ""
  
  echo "KPI Snapshot"
  python cli/channel_cli.py kpi
  echo ""
  
  echo "High-Risk Deals"
  python cli/channel_cli.py risk
  echo ""
  
  echo "Top Partners"
  python cli/channel_cli.py top-partners --limit 5
} > $REPORT_FILE

# Email or upload
mail -s "Weekly Report" christophe@company.com < $REPORT_FILE
```

### Integration with Cron

```bash
# /etc/cron.d/channel_reports

# Every Friday at 8am: generate QBR for all key partners
0 8 * * 5 santiago cd /Users/santiago/Projects/salesforce-fastmcp && \
  python cli/channel_cli.py qbr "Accenture" --json > /tmp/qbr_accenture.json && \
  python cli/channel_cli.py qbr "Inetum Spain" --json > /tmp/qbr_inetum.json

# Every day at 9am: email morning risk summary
0 9 * * * santiago cd /Users/santiago/Projects/salesforce-fastmcp && \
  python cli/channel_cli.py risk --json | jq '.data[] | select(.days_to_close < 7)' | \
  mail -s "Morning Risk Alert" channel-ops@company.com
```

---

## Debug Tips

### See what parameters are being used

All errors print the context and function name. Example:

```bash
$ python cli/channel_cli.py partner "InvalidPartner"
Error (partner (InvalidPartner)): Partner not found
```

### Export to JSON for inspection

```bash
# Full response structure
python cli/channel_cli.py revenue --json | jq '.'

# Just the data
python cli/channel_cli.py revenue --json | jq '.data'

# Count of partners in breakdown
python cli/channel_cli.py revenue --breakdown partner --json | jq '.data | length'
```

### Combine with grep/awk for field extraction

```bash
# Find deals closing in next 10 days
python cli/channel_cli.py risk --json | jq '.data[] | select(.days_to_close < 10) | .opportunity_name'

# Sum pipeline by stage
python cli/channel_cli.py pipeline --breakdown stage --json | \
  jq '.data | map(select(.stage == "Negotiation")) | map(.total_amount) | add'
```

---

## Environment Setup

The CLI uses the same `.env` configuration as the MCP server:

```bash
# .env
SALESFORCE_BASE_URL=https://your-instance.salesforce.com
SALESFORCE_SID=your_session_id_here
```

If these are not set, you'll get a clear error:

```
Error: Missing required environment variables: SALESFORCE_BASE_URL and SALESFORCE_ACCESS_TOKEN (or SALESFORCE_SID)
```

Refresh your SID if it expires:

```bash
node Scripts/extract-sid.js
# Update .env with new SALESFORCE_SID
```

---

## Comparison: CLI vs MCP

| Aspect | CLI | MCP |
|--------|-----|-----|
| **Setup** | Direct Python, `.env` only | MCP integration required |
| **Best for** | Automation, debug, scripting | Natural language questions |
| **Response time** | Instant | Through LLM |
| **Tool confusion** | N/A (exact function call) | Possible (54 tools exposed) |
| **Output format** | Pretty or JSON | LLM-formatted text |
| **Cron/automation** | Excellent | Not ideal |
| **Ad-hoc questions** | Good | Excellent |

Use **CLI** for: cron jobs, weekly reports, debugging, integration
Use **MCP** for: interactive exploration, natural language questions, ad-hoc analysis
