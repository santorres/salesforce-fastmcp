# Channel Intelligence CLI - Quick Reference

**Version**: 2.1 | **Updated**: June 21, 2026 | **Multi-Region Support**: SE/EE Territory Management

---

## 30-Second Setup

```bash
cd /Users/santiagot/Applications/salesforce-fastmcp
source .venv/bin/activate
python3 -m cli.channel_cli kpi
```

**First time setup:**
1. Install Salesforce CLI: `brew install salesforce-cli`
2. Login: `sf org login web`
3. Or set env vars:
   ```bash
   export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
   export SALESFORCE_ACCESS_TOKEN=your_token_here
   ```

---

## All 16 Commands

| Command | Purpose | Example |
|---------|---------|---------|
| **kpi** | Key metrics snapshot | `python3 -m cli.channel_cli kpi` |
| **revenue** | Revenue analysis | `python3 -m cli.channel_cli revenue --breakdown partner` |
| **pipeline** | Open opportunities | `python3 -m cli.channel_cli pipeline --breakdown stage` |
| **risk** | High-risk deals | `python3 -m cli.channel_cli risk` |
| **partner** | Partner scorecard | `python3 -m cli.channel_cli partner "Accenture"` |
| **qbr** | Quarterly business review | `python3 -m cli.channel_cli qbr "Accenture"` |
| **registrations** | Deal registrations trend | `python3 -m cli.channel_cli registrations` |
| **opportunities-by-status** | Unapproved registrations with details | `python3 -m cli.channel_cli opportunities-by-status` |
| **partner-metrics** ⭐ NEW | Partner sourcing breakdown | `python3 -m cli.channel_cli partner-metrics` |
| **top-partners** | Partner leaderboard | `python3 -m cli.channel_cli top-partners --limit 10` |
| **search** | Search opportunities | `python3 -m cli.channel_cli search "deal name"` |
| **list-opps** | List open opportunities | `python3 -m cli.channel_cli list-opps --partner "Accenture"` |
| **sales-rep-revenue** | Sales rep performance | `python3 -m cli.channel_cli sales-rep-revenue --region SE` |
| **closed-deals-by-rep** | Closed deals by sales rep | `python3 -m cli.channel_cli closed-deals-by-rep --region SE` |
| **pipeline-deals-by-rep** | Pipeline deals by sales rep | `python3 -m cli.channel_cli pipeline-deals-by-rep --region EE` |
| **sales-rep-by-country** | Sales rep metrics by country | `python3 -m cli.channel_cli sales-rep-by-country --country Italy` |

---

## Common Options

| Option | Commands | Example |
|--------|----------|---------|
| `--period PERIOD` | All | `--period THIS_FISCAL_YEAR` |
| `--json` | All | `--json` |
| `--status STATUS` | opportunities-by-status | `--status Submitted` or `--status "Submitted,In Review"` |
| `--breakdown TYPE` | revenue, pipeline, partner-metrics | `--breakdown country` or `--breakdown partner` |
| `--region REGION` | sales-rep-revenue, closed-deals-by-rep, pipeline-deals-by-rep | `--region SE` or `--region EE` |
| `--limit N` | top-partners, search, list-opps, sales-rep-*, opportunities-by-status | `--limit 20` |
| `--channel-manager NAME` | kpi, revenue, risk, registrations, opportunities-by-status, partner-metrics | `--channel-manager "John Doe"` |
| `--stage STAGE` | search, list-opps | `--stage "Closed Won"` |
| `--partner NAME` | search, list-opps, sales-rep-by-partner | `--partner "Accenture"` |
| `--country COUNTRY` | search, list-opps, sales-rep-by-country | `--country "Spain"` |
| `--sales-rep NAME` | list-opps | `--sales-rep "Nuno"` |
| `--min-amount N` | list-opps | `--min-amount 100000` |
| `--metric METRIC` | top-partners, sales-rep-revenue | `--metric pipeline` |
| `--probability-threshold N` | risk | `--probability-threshold 50` |
| `--prior-period PERIOD` | qbr | `--prior-period LAST_QUARTER` |
| `--revenue-target N` | qbr | `--revenue-target 500000` |
| `--rep NAME` | closed-deals-by-rep, pipeline-deals-by-rep | `--rep "Alessia Ashkenazi"` |

---

## Real Examples

### Daily Operations

```bash
# Get today's KPI
python3 -m cli.channel_cli kpi

# Top 5 partners this quarter
python3 -m cli.channel_cli top-partners --limit 5

# High-risk deals
python3 -m cli.channel_cli risk

# Revenue by partner
python3 -m cli.channel_cli revenue --breakdown partner
```

### Analysis & Reports

```bash
# Full fiscal year KPI
python3 -m cli.channel_cli kpi --period THIS_FISCAL_YEAR

# Partner deep dive
python3 -m cli.channel_cli partner "Accenture"
python3 -m cli.channel_cli qbr "Accenture"

# Revenue by country
python3 -m cli.channel_cli revenue --breakdown country

# Pipeline by stage
python3 -m cli.channel_cli pipeline --breakdown stage

# All registrations
python3 -m cli.channel_cli registrations
```

### Data Export

```bash
# Export to JSON
python3 -m cli.channel_cli kpi --json > kpi.json
python3 -m cli.channel_cli top-partners --json > partners.json

# Process with jq
python3 -m cli.channel_cli top-partners --json | jq '.data[] | {name: .partnerName, revenue: .totalRevenue}'
```

### Filtering & Searching

```bash
# Find negotiation deals this quarter
python3 -m cli.channel_cli list-opps --stage Negotiation --period THIS_QUARTER

# Large opportunities only
python3 -m cli.channel_cli list-opps --min-amount 500000

# Specific partner's open opps
python3 -m cli.channel_cli list-opps --partner "TCS" --stage Validation

# Search for deals
python3 -m cli.channel_cli search "cloud" --stage "Closed Won"

# Sales rep's opportunities (THIS_QUARTER only)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER

# Sales rep's opportunities (NEXT_QUARTER)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period NEXT_QUARTER

# Sales rep's pipeline deals by region
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --region SE --period THIS_QUARTER
```

### Sales Rep Analytics (Multi-Region SE/EE)

```bash
# Revenue by sales rep (all regions combined)
python3 -m cli.channel_cli sales-rep-revenue

# Revenue by sales rep - Southern Europe only
python3 -m cli.channel_cli sales-rep-revenue --region SE

# Revenue by sales rep - Eastern Europe only
python3 -m cli.channel_cli sales-rep-revenue --region EE

# Pipeline by sales rep - specific region
python3 -m cli.channel_cli sales-rep-revenue --region SE --metric pipeline

# Closed deals by sales rep - SE only
python3 -m cli.channel_cli closed-deals-by-rep --region SE

# Open pipeline deals by sales rep - EE only
python3 -m cli.channel_cli pipeline-deals-by-rep --region EE

# Sales rep performance by country
python3 -m cli.channel_cli sales-rep-by-country --country Italy

# Specific sales rep's deals (all regions)
python3 -m cli.channel_cli closed-deals-by-rep --rep "Alessia Ashkenazi"

# Alessia's deals - SE only
python3 -m cli.channel_cli pipeline-deals-by-rep --rep "Alessia Ashkenazi" --region SE

# Alessia's deals - EE only
python3 -m cli.channel_cli pipeline-deals-by-rep --rep "Alessia Ashkenazi" --region EE
```

### Sales Rep Opportunity Filtering (list-opps)

**Filter open opportunities by sales rep with time period:**

```bash
# Nuno's opportunities this quarter
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER

# Nuno's opportunities next quarter
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period NEXT_QUARTER

# Both quarters (run both commands)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER && \
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period NEXT_QUARTER

# As JSON (for filtering/export)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --json

# With additional stage filter
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --stage "Business Case"

# By region (all countries in SE/EE + sales rep)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --region SE

# Alessia's opportunities (all regions)
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --period THIS_QUARTER

# Alessia's SE only
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --period THIS_QUARTER --region SE

# Alessia's EE only
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --period THIS_QUARTER --region EE

# High-value opportunities for sales rep
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --min-amount 100000

# Sales rep's opportunities in specific country
python3 -m cli.channel_cli list-opps --sales-rep Nuno --country Portugal --period THIS_QUARTER

# Combine multiple filters
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --stage Negotiation --min-amount 50000
```

---

## Multi-Region Territory Support

**New in v2.1:** Sales rep analytics now support regional filtering for Southern Europe (SE) and Eastern Europe (EE).

### Territories

| Region | Code | Countries | Reps |
|--------|------|-----------|------|
| **Southern Europe** | `SE` | Italy, Spain, Portugal, Greece, Cyprus, Malta | 7 (including Alessia) |
| **Eastern Europe** | `EE` | Poland, Czech Republic, Hungary, Slovakia, Romania, Bulgaria, Croatia, Serbia, Slovenia, Turkey | 1 (Alessia Ashkenazi) |

### Sales Reps by Region

**Southern Europe (SE):**
- Ray Mills (Spain, Greece)
- Daniel Gaspar (Spain)
- Bruno Filippelli (Italy)
- Jacopo Zumerle (Italy)
- Nuno Antunes (Portugal)
- Ionatan Ascher (Spain)
- Alessia Ashkenazi (Italy, Greece) ⭐ Multi-region

**Eastern Europe (EE):**
- Alessia Ashkenazi (All 10 EE countries) ⭐ Multi-region

**Note:** Alessia is the only multi-region rep, covering both SE (Italy + Greece) and all EE countries. Use `--region` flag to isolate her performance by region.

### Regional Filter Examples

```bash
# Default: Show all regions combined with region labels [SE]/[EE]
python3 -m cli.channel_cli sales-rep-revenue
# Output: Ray Mills [SE], Alessia Ashkenazi [SE+EE], etc.

# SE only: Filter to Southern Europe reps
python3 -m cli.channel_cli sales-rep-revenue --region SE
# Output: Ray Mills, Alessia Ashkenazi, Bruno Filippelli, etc. (Alessia shows [SE] label)

# EE only: Filter to Eastern Europe (only Alessia)
python3 -m cli.channel_cli sales-rep-revenue --region EE
# Output: Alessia Ashkenazi [EE]

# All: Explicit "all regions" (same as default)
python3 -m cli.channel_cli sales-rep-revenue --region all
```

---

## Periods

Use with `--period` flag:

| Relative | Specific |
|----------|----------|
| `THIS_QUARTER` (default) | `FY27_Q1`, `FY27_Q2`, `FY27_Q3`, `FY27_Q4` |
| `LAST_QUARTER` | |
| `NEXT_QUARTER` | |
| `THIS_FISCAL_YEAR` | |
| `LAST_FISCAL_YEAR` | |
| `NEXT_FISCAL_YEAR` | |
| `THIS_MONTH` | |
| `LAST_MONTH` | |

**Current Fiscal Year (FY27):** Feb 1, 2026 - Jan 31, 2027  
**Current Quarter (FY27_Q2):** May 1 - July 31, 2026

---

## Defaults

**Most commands default to THIS_QUARTER:**
- kpi, revenue, pipeline, risk, partner, qbr, registrations, search, list-opps

**Use explicit `--period` for other timeframes:**
```bash
python3 -m cli.channel_cli kpi --period THIS_FISCAL_YEAR
python3 -m cli.channel_cli top-partners --period FY27_Q1
```

---

## Help & Troubleshooting

**Get help:**
```bash
python3 -m cli.channel_cli --help                    # All commands
python3 -m cli.channel_cli kpi --help                # Specific command
```

**Common Issues:**

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError: click" | `source .venv/bin/activate && pip install -r requirements.txt` |
| "Failed to initialize authentication" | Run `sf org login web` OR set env vars |
| "No results found" | Check period with `--json` flag to verify dates |
| "Partner not found" | Use exact name: `python3 -m cli.channel_cli top-partners --json \| jq '.data[].partnerName'` |

**Verify what period was used:**
```bash
python3 -m cli.channel_cli kpi --json | jq '.period'
```

---

## Output Formats

**Pretty-printed tables (default):**
```bash
python3 -m cli.channel_cli top-partners
```

**Structured JSON (for processing):**
```bash
python3 -m cli.channel_cli top-partners --json
```

**Pipe to jq for advanced filtering:**
```bash
python3 -m cli.channel_cli top-partners --json | jq '.data | sort_by(.totalRevenue) | reverse | .[0:5]'
```

---

## Quick Workflows

### Daily Check (2 minutes)
```bash
source .venv/bin/activate
python3 -m cli.channel_cli kpi
python3 -m cli.channel_cli top-partners --limit 5
python3 -m cli.channel_cli risk
deactivate
```

### Month-End Report (5 minutes)
```bash
source .venv/bin/activate
python3 -m cli.channel_cli revenue --breakdown partner
python3 -m cli.channel_cli revenue --breakdown country
python3 -m cli.channel_cli pipeline --breakdown stage
python3 -m cli.channel_cli registrations
deactivate
```

### Quarter-End Crunch (10 minutes)
```bash
source .venv/bin/activate
python3 -m cli.channel_cli kpi --period THIS_QUARTER
python3 -m cli.channel_cli list-opps --stage Negotiation --period THIS_QUARTER
python3 -m cli.channel_cli risk --period THIS_QUARTER
python3 -m cli.channel_cli top-partners --limit 10 --period THIS_QUARTER
deactivate
```

---

## Authentication Details

**Salesforce CLI (Recommended):**
- Secure: Credentials stored in OS keychain
- Automatic: No manual token management
- Refresh: SF CLI handles token refresh automatically

**Environment Variables (Fallback):**
- Set in terminal: `export SALESFORCE_BASE_URL=...`
- Or in .env file: Copy `.env.example` to `.env` and edit
- Still works if SF CLI not available

**Priority:** SF CLI > Environment Variables > Error message

---

## Session Setup

Every session, activate the environment:
```bash
source .venv/bin/activate
```

When done:
```bash
deactivate
```

---

## Advanced Filtering Examples

Combine multiple filters for powerful queries:

```bash
# Complex filter: Southern Europe, specific partner, specific stage
python3 -m cli.channel_cli list-opps \
  --region SE \
  --partner "Accenture" \
  --stage "Negotiation" \
  --min-amount 100000 \
  --period THIS_QUARTER

# Large deals by rep in EE
python3 -m cli.channel_cli list-opps \
  --region EE \
  --min-amount 500000 \
  --limit 50

# High-risk deals (< 40% probability) over next 30 days
python3 -m cli.channel_cli high-risk-deals \
  --probability-threshold 40 \
  --period FY27_Q4

# Stalled Accenture deals (90+ days)
python3 -m cli.channel_cli stalled-deals \
  --days-threshold 90 \
  --format json | \
  jq '.data[] | select(.partner | contains("Accenture"))'

# Export opportunities with complex filters as CSV
python3 -m cli.channel_cli list-opps \
  --partner "Inetum" \
  --stage "Qualification" \
  --min-amount 50000 \
  --max-amount 500000 \
  --format json | \
  jq -r '.data[] | [.name, .partner, .amount, .stage] | @csv' > deals.csv

# SE team opportunities by stage (group by stage)
python3 -m cli.channel_cli list-opps \
  --region SE \
  --format json | \
  jq '.data | group_by(.stage) | map({stage: .[0].stage, count: length, total: (map(.amount) | add)})'

# Southern Europe - Ray Mills' high-value negotiations
python3 -m cli.channel_cli list-opps \
  --rep "Ray Mills" \
  --stage "Negotiation" \
  --min-amount 200000 \
  --format json
```

### Using jq for Advanced Processing

```bash
# Filter to opportunities closing in next 30 days and over $100K
python3 -m cli.channel_cli list-opps --format json | \
  jq '.data[] | select(.days_to_close <= 30 and .amount > 100000)'

# Get deal statistics (count, avg size, total)
python3 -m cli.channel_cli list-opps --partner "Accenture" --format json | \
  jq '{count: (.data|length), avg_size: ((.data|map(.amount)|add)/(.data|length)), total: (.data|map(.amount)|add)}'

# Find partners with deals in both Qualification and Proposal
python3 -m cli.channel_cli list-opps --format json | \
  jq '.data | group_by(.partner) | map(select(map(.stage) | contains(["Qualification", "Proposal"])) | {partner: .[0].partner, stages: [.[].stage]|unique})'

# Sort opportunities by close date
python3 -m cli.channel_cli get-pipeline --breakdown total --format json | \
  jq '.data | sort_by(.close_date)'

# Get revenue by partner and stage
python3 -m cli.channel_cli list-opps --format json | \
  jq '[.data[] | {partner: .partner, stage: .stage, amount: .amount}] | group_by(.partner) | map({partner: .[0].partner, by_stage: (group_by(.stage) | map({stage: .[0].stage, revenue: (map(.amount)|add)}))})'
```

---

## Real Data (Current Org)

**Top Partners (FY27):**
1. SorintSEC (Partner) - $579,771
2. GetConsulting (Partner) - $221,839
3. ANADAT Technology SP (Partner) - $194,562

**Revenue (This Quarter):**
- Ayesa (Partner): $53,369
- iCubed s.r.l. (Partner): $25,037

**Registrations (FY27):**
- Q1: 50 deals, $2.2M (73.5% approval rate)
- Q2: 22 deals, $156K (81.8% approval rate)

---

## Tips

✅ Always use `--period` for explicit control  
✅ Use `--region SE|EE|all` to isolate regional performance  
✅ Use `--json` for data processing and export  
✅ Use `--limit` to speed up large queries  
✅ Check help text: `COMMAND --help`  
✅ Verify period in output: `--json | jq '.period'`  
✅ For Alessia (multi-region rep): Use `--region SE` or `--region EE` to see her breakdown by region  
✅ Regional labels in output: `[SE]` = Southern Europe, `[EE]` = Eastern Europe, `[SE+EE]` = both regions  

---

**Status:** ✅ Production Ready | **Security:** ✅ SF CLI Encrypted Auth | **Multi-Region:** ✅ SE/EE Territory Management

