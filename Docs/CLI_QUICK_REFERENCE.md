# Channel Intelligence CLI - Quick Reference

**One-page reference for all CLI commands**

---

## Setup (First Time Only)

```bash
# 1. Navigate to project
cd /Users/santiagot/Applications/salesforce-fastmcp

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install dependencies (if needed)
pip install -r requirements.txt

# 4. Authenticate (choose one)

# Option A: Salesforce CLI (recommended)
sf org login web

# Option B: Environment variables
export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=your_token_here

# Option C: .env file
cp .env.example .env
# Edit .env with your credentials
```

---

## Quick Command Reference

```bash
# Activate environment (every session)
source .venv/bin/activate

# All commands use this format:
python3 -m cli.channel_cli COMMAND [OPTIONS]

# Deactivate (when done)
deactivate
```

---

## All Available Commands

| Command | Purpose | Quick Example |
|---------|---------|---------------|
| **kpi** | Key performance indicators | `python3 -m cli.channel_cli kpi` |
| **revenue** | Closed-won revenue | `python3 -m cli.channel_cli revenue --breakdown partner` |
| **pipeline** | Open opportunities | `python3 -m cli.channel_cli pipeline` |
| **risk** | High-risk deals | `python3 -m cli.channel_cli risk` |
| **partner** | Partner scorecard | `python3 -m cli.channel_cli partner "Accenture"` |
| **qbr** | Quarterly business review | `python3 -m cli.channel_cli qbr "Accenture"` |
| **registrations** | Deal registrations trend | `python3 -m cli.channel_cli registrations` |
| **top-partners** | Partner leaderboard | `python3 -m cli.channel_cli top-partners --limit 10` |
| **search** | Search opportunities | `python3 -m cli.channel_cli search "deal name"` |
| **list-opps** | List open opportunities | `python3 -m cli.channel_cli list-opps --partner "Accenture"` |

---

## Common Options

| Option | Used With | Example |
|--------|-----------|---------|
| `--period PERIOD` | All | `--period THIS_FISCAL_YEAR` |
| `--json` | All | `--json` |
| `--breakdown TYPE` | revenue, pipeline | `--breakdown partner` |
| `--limit N` | top-partners, search, list-opps | `--limit 20` |
| `--channel-manager NAME` | kpi, revenue, risk | `--channel-manager "John Doe"` |
| `--probability-threshold N` | risk | `--probability-threshold 50` |
| `--stage STAGE` | search, list-opps | `--stage "Closed Won"` |
| `--partner NAME` | search, list-opps | `--partner "Accenture"` |
| `--country COUNTRY` | search, list-opps | `--country "Spain"` |
| `--min-amount N` | list-opps | `--min-amount 100000` |
| `--metric METRIC` | top-partners | `--metric pipeline` |
| `--prior-period PERIOD` | qbr | `--prior-period LAST_QUARTER` |
| `--revenue-target N` | qbr | `--revenue-target 500000` |

---

## Command Examples

### 1. KPI Snapshot
```bash
python3 -m cli.channel_cli kpi                              # Current quarter
python3 -m cli.channel_cli kpi --period THIS_FISCAL_YEAR    # Full year
python3 -m cli.channel_cli kpi --json                       # JSON format
```

### 2. Revenue
```bash
python3 -m cli.channel_cli revenue                          # Total
python3 -m cli.channel_cli revenue --breakdown partner      # By partner
python3 -m cli.channel_cli revenue --breakdown country      # By country
python3 -m cli.channel_cli revenue --breakdown quarter      # By quarter
```

### 3. Pipeline
```bash
python3 -m cli.channel_cli pipeline                         # Total
python3 -m cli.channel_cli pipeline --breakdown partner     # By partner
python3 -m cli.channel_cli pipeline --breakdown stage       # By stage
python3 -m cli.channel_cli pipeline --breakdown country     # By country
```

### 4. Risk
```bash
python3 -m cli.channel_cli risk                             # Default threshold (40%)
python3 -m cli.channel_cli risk --probability-threshold 50  # Custom threshold
python3 -m cli.channel_cli risk --json                      # JSON format
```

### 5. Partner Scorecard
```bash
python3 -m cli.channel_cli partner "Accenture"              # Partner details
python3 -m cli.channel_cli partner "Accenture" --period FY27_Q2  # Specific period
```

### 6. QBR
```bash
python3 -m cli.channel_cli qbr "Accenture"                  # Basic QBR
python3 -m cli.channel_cli qbr "Accenture" --revenue-target 500000  # With target
python3 -m cli.channel_cli qbr "Accenture" --json           # JSON format
```

### 7. Registrations
```bash
python3 -m cli.channel_cli registrations                     # All registrations
python3 -m cli.channel_cli registrations --json             # JSON format
```

### 8. Top Partners
```bash
python3 -m cli.channel_cli top-partners                      # Top 10 by revenue
python3 -m cli.channel_cli top-partners --limit 20          # Top 20
python3 -m cli.channel_cli top-partners --metric pipeline   # Top by pipeline
python3 -m cli.channel_cli top-partners --period THIS_FISCAL_YEAR  # Full year
```

### 9. Search
```bash
python3 -m cli.channel_cli search "deal name"               # Search
python3 -m cli.channel_cli search "deal" --stage "Closed Won"  # With stage filter
python3 -m cli.channel_cli search "deal" --partner "Accenture"  # With partner filter
python3 -m cli.channel_cli search "deal" --limit 50         # Limit results
```

### 10. List Opportunities
```bash
python3 -m cli.channel_cli list-opps                        # All open opps
python3 -m cli.channel_cli list-opps --partner "Accenture"  # For partner
python3 -m cli.channel_cli list-opps --stage "Prospecting"  # By stage
python3 -m cli.channel_cli list-opps --min-amount 100000    # Min amount
python3 -m cli.channel_cli list-opps --limit 50             # Limit
```

---

## Fiscal Periods

Use with `--period` option:

| Period | Meaning |
|--------|---------|
| `THIS_QUARTER` | Current quarter (default) |
| `LAST_QUARTER` | Previous quarter |
| `NEXT_QUARTER` | Next quarter |
| `THIS_FISCAL_YEAR` | Current fiscal year |
| `LAST_FISCAL_YEAR` | Last fiscal year |
| `NEXT_FISCAL_YEAR` | Next fiscal year |
| `FY27_Q1` | Fiscal 2027, Q1 |
| `FY27_Q2` | Fiscal 2027, Q2 |
| `FY27_Q3` | Fiscal 2027, Q3 |
| `FY27_Q4` | Fiscal 2027, Q4 |
| `THIS_MONTH` | Current month |
| `LAST_MONTH` | Previous month |

---

## JSON Processing with jq

```bash
# Pretty print JSON
python3 -m cli.channel_cli kpi --json | jq '.'

# Extract specific field
python3 -m cli.channel_cli kpi --json | jq '.data.revenue'

# Filter array
python3 -m cli.channel_cli revenue --breakdown partner --json | jq '.data[] | select(.totalRevenue > 100000)'

# Count items
python3 -m cli.channel_cli top-partners --json | jq '.data | length'

# Sort by field
python3 -m cli.channel_cli top-partners --json | jq '.data | sort_by(.total_revenue) | reverse'

# Extract specific fields
python3 -m cli.channel_cli top-partners --json | jq '.data[] | {name: .partner_name, revenue: .total_revenue}'

# Multiple filters
python3 -m cli.channel_cli list-opps --json | jq '.data[] | select(.amount > 50000 and .stage == "Validation")'

# Export to CSV (basic)
python3 -m cli.channel_cli top-partners --json | jq -r '.data[] | [.partner_name, .total_revenue] | @csv'
```

---

## Common Workflows

### Daily Check
```bash
source .venv/bin/activate
python3 -m cli.channel_cli kpi
python3 -m cli.channel_cli top-partners --limit 5
python3 -m cli.channel_cli risk
deactivate
```

### Partner Deep Dive
```bash
source .venv/bin/activate
PARTNER="Accenture"
python3 -m cli.channel_cli partner "$PARTNER"
python3 -m cli.channel_cli qbr "$PARTNER"
python3 -m cli.channel_cli list-opps --partner "$PARTNER"
deactivate
```

### Revenue Analysis
```bash
source .venv/bin/activate
python3 -m cli.channel_cli revenue --breakdown partner
python3 -m cli.channel_cli revenue --breakdown country
python3 -m cli.channel_cli pipeline --breakdown stage
deactivate
```

### Export Data
```bash
source .venv/bin/activate
python3 -m cli.channel_cli kpi --json > kpi.json
python3 -m cli.channel_cli top-partners --json > partners.json
python3 -m cli.channel_cli list-opps --json > opportunities.json
deactivate
```

---

## Help Commands

```bash
# General help
python3 -m cli.channel_cli --help

# Command-specific help
python3 -m cli.channel_cli kpi --help
python3 -m cli.channel_cli revenue --help
python3 -m cli.channel_cli pipeline --help
python3 -m cli.channel_cli partner --help
python3 -m cli.channel_cli qbr --help
python3 -m cli.channel_cli risk --help
python3 -m cli.channel_cli registrations --help
python3 -m cli.channel_cli top-partners --help
python3 -m cli.channel_cli search --help
python3 -m cli.channel_cli list-opps --help
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: click` | Run: `source .venv/bin/activate && pip install -r requirements.txt` |
| `Failed to initialize authentication` | Install SF CLI: `sf org login web` OR set `.env` |
| `No module named 'salesforce_client'` | Run from project root: `cd /Users/santiagot/Applications/salesforce-fastmcp` |
| `Partner not found` | Use exact name: `python3 -m cli.channel_cli top-partners --json \| jq '.data[].partner_name'` |
| `Invalid period` | Use valid period (see Fiscal Periods section) |

---

## Tips

✅ Always activate virtual environment: `source .venv/bin/activate`  
✅ Use `--json` for data processing and export  
✅ Use exact partner names (case-sensitive)  
✅ Use `--limit` to speed up large queries  
✅ Use `--period` to narrow down results  
✅ Use pipes with `jq` for advanced filtering  

---

**Updated**: June 16, 2026  
**Version**: 2.0 (with auth_provider security)

