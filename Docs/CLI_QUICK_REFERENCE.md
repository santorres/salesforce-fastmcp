# Channel Intelligence CLI - Quick Reference

**Version**: 2.0 | **Updated**: June 16, 2026

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

## All 10 Commands

| Command | Purpose | Example |
|---------|---------|---------|
| **kpi** | Key metrics snapshot | `python3 -m cli.channel_cli kpi` |
| **revenue** | Revenue analysis | `python3 -m cli.channel_cli revenue --breakdown partner` |
| **pipeline** | Open opportunities | `python3 -m cli.channel_cli pipeline --breakdown stage` |
| **risk** | High-risk deals | `python3 -m cli.channel_cli risk` |
| **partner** | Partner scorecard | `python3 -m cli.channel_cli partner "Accenture"` |
| **qbr** | Quarterly business review | `python3 -m cli.channel_cli qbr "Accenture"` |
| **registrations** | Deal registrations trend | `python3 -m cli.channel_cli registrations` |
| **top-partners** | Partner leaderboard | `python3 -m cli.channel_cli top-partners --limit 10` |
| **search** | Search opportunities | `python3 -m cli.channel_cli search "deal name"` |
| **list-opps** | List open opportunities | `python3 -m cli.channel_cli list-opps --partner "Accenture"` |

---

## Common Options

| Option | Commands | Example |
|--------|----------|---------|
| `--period PERIOD` | All | `--period THIS_FISCAL_YEAR` |
| `--json` | All | `--json` |
| `--breakdown TYPE` | revenue, pipeline | `--breakdown country` |
| `--limit N` | top-partners, search, list-opps | `--limit 20` |
| `--channel-manager NAME` | kpi, revenue, risk, registrations | `--channel-manager "John Doe"` |
| `--stage STAGE` | search, list-opps | `--stage "Closed Won"` |
| `--partner NAME` | search, list-opps | `--partner "Accenture"` |
| `--country COUNTRY` | search, list-opps | `--country "Spain"` |
| `--min-amount N` | list-opps | `--min-amount 100000` |
| `--metric METRIC` | top-partners | `--metric pipeline` |
| `--probability-threshold N` | risk | `--probability-threshold 50` |
| `--prior-period PERIOD` | qbr | `--prior-period LAST_QUARTER` |
| `--revenue-target N` | qbr | `--revenue-target 500000` |

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
✅ Use `--json` for data processing and export  
✅ Use `--limit` to speed up large queries  
✅ Check help text: `COMMAND --help`  
✅ Verify period in output: `--json | jq '.period'`  

---

**Status:** ✅ Production Ready | **Security:** ✅ SF CLI Encrypted Auth

