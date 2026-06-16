# Channel Intelligence CLI - Quick Start Guide

**Version**: 2.0 (with auth_provider security integration)  
**Last Updated**: June 16, 2026

---

## Prerequisites

Before running the CLI, ensure you have:

1. **Python 3.8+** installed
2. **Salesforce CLI** (optional but recommended for secure authentication)
3. **Virtual environment activated** (recommended)

### Check Your Python Version

```bash
python3 --version
# Expected output: Python 3.8.x or higher
```

---

## Authentication Setup

The CLI now uses secure authentication via either **Salesforce CLI** or **.env file**.

### Option 1: Salesforce CLI (Recommended - Secure)

**Install Salesforce CLI:**
```bash
# macOS (using Homebrew)
brew install salesforce-cli

# Or download from:
# https://developer.salesforce.com/tools/salesforcecli
```

**Authenticate:**
```bash
sf org login web
# This opens a browser for authentication
# Follow the prompts to log in to your Salesforce org
```

**Verify authentication:**
```bash
sf org list
# Should show your authenticated org(s)
```

### Option 2: Environment Variables (Fallback)

If you can't use Salesforce CLI, set environment variables:

```bash
# Get your Salesforce instance URL and access token
# Then set them:
export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=your_access_token_here
```

Or create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env

# Edit .env with your credentials
# Uncomment and fill in:
# SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
# SALESFORCE_ACCESS_TOKEN=your_access_token_here
```

---

## Installation & Setup

### Step 1: Navigate to Project Directory

```bash
cd /Users/santiagot/Applications/salesforce-fastmcp
```

### Step 2: Create Virtual Environment (if needed)

```bash
# Create virtual environment
python3 -m venv .venv

# Or use existing one (already created)
```

### Step 3: Activate Virtual Environment

```bash
# Activate the virtual environment
source .venv/bin/activate

# Your prompt should now show: (.venv) $
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Verify Installation

```bash
# Test the CLI is working
python3 -m cli.channel_cli --help

# Expected output: Shows CLI help with all available commands
```

---

## Running the CLI

### Basic Command Structure

```bash
python3 -m cli.channel_cli COMMAND [OPTIONS]
```

### Get Help

```bash
# Show all available commands
python3 -m cli.channel_cli --help

# Show help for a specific command
python3 -m cli.channel_cli kpi --help
python3 -m cli.channel_cli revenue --help
```

---

## Test Commands & Examples

### 1. KPI Snapshot (Key Performance Indicators)

**What it does**: Shows revenue, pipeline, win rate, coverage ratio, and active partners

```bash
# Basic KPI for current quarter
python3 -m cli.channel_cli kpi

# KPI for a specific period
python3 -m cli.channel_cli kpi --period THIS_FISCAL_YEAR

# KPI filtered by channel manager
python3 -m cli.channel_cli kpi --channel-manager "Manager Name"

# KPI as JSON output
python3 -m cli.channel_cli kpi --json

# KPI as JSON piped to jq for filtering
python3 -m cli.channel_cli kpi --json | jq '.data'
```

**Expected Output:**
```
KPI Snapshot
--------------------------------------------------
Revenue (Closed-Won): $78,406
  Deals: 2

Pipeline (Open): $1,504,111

Coverage Ratio: 2.1x

Win Rate: 3.8%

Active Partners: 18
```

---

### 2. Revenue Analysis

**What it does**: Shows closed-won revenue, attainment %, and deal count

```bash
# Basic revenue for current quarter
python3 -m cli.channel_cli revenue

# Revenue for specific period
python3 -m cli.channel_cli revenue --period THIS_FISCAL_YEAR

# Revenue breakdown by partner
python3 -m cli.channel_cli revenue --breakdown partner

# Revenue breakdown by country
python3 -m cli.channel_cli revenue --breakdown country

# Revenue breakdown by quarter
python3 -m cli.channel_cli revenue --breakdown quarter

# Revenue breakdown by stage
python3 -m cli.channel_cli revenue --breakdown stage

# Filter by channel manager
python3 -m cli.channel_cli revenue --channel-manager "Manager Name"

# JSON output
python3 -m cli.channel_cli revenue --json
```

**Expected Output:**
```
Revenue Summary
--------------------------------------------------
Closed-Won: $78,406
Deals: 2.0
Attainment: 12.3%
```

---

### 3. Pipeline Analysis

**What it does**: Shows open pipeline opportunities

```bash
# Basic pipeline for current quarter
python3 -m cli.channel_cli pipeline

# Pipeline for specific period
python3 -m cli.channel_cli pipeline --period THIS_FISCAL_YEAR

# Pipeline breakdown by partner
python3 -m cli.channel_cli pipeline --breakdown partner

# Pipeline breakdown by stage
python3 -m cli.channel_cli pipeline --breakdown stage

# Pipeline breakdown by country
python3 -m cli.channel_cli pipeline --breakdown country

# JSON output
python3 -m cli.channel_cli pipeline --json
```

**Expected Output:**
```
Pipeline Summary
--------------------------------------------------
Open Pipeline: $1,504,111
Deal Count: 23.0

By Stage:
  Prospecting: $500,000
  Validation: $750,000
  Closed Lost: $254,111
```

---

### 4. Risk Analysis (High-Risk Deals)

**What it does**: Shows deals with low probability closing soon

```bash
# High-risk deals (default: probability < 40%, closing < 30 days)
python3 -m cli.channel_cli risk

# Custom probability threshold
python3 -m cli.channel_cli risk --probability-threshold 50

# Filter by channel manager
python3 -m cli.channel_cli risk --channel-manager "Manager Name"

# JSON output
python3 -m cli.channel_cli risk --json
```

**Expected Output:**
```
High-Risk Deals (probability < 40%, closing within 30 days)
================================================================================
No high-risk deals found. ✓
```

---

### 5. Partner Scorecard

**What it does**: Detailed view of a specific partner's performance

```bash
# Partner scorecard (exact name match required)
python3 -m cli.channel_cli partner "Partner Name"

# Example with real partner
python3 -m cli.channel_cli partner "Inetum Spain"

# Specific period
python3 -m cli.channel_cli partner "Accenture" --period THIS_FISCAL_YEAR

# JSON output
python3 -m cli.channel_cli partner "Inetum Spain" --json
```

**Expected Output:**
```
Partner Scorecard: Inetum Spain
============================================================

Revenue
----------------------------------------
  Closed-Won: $45,000
  Deals: 1

Pipeline
----------------------------------------
  Open: $200,000

Avg Deal Size: $45,000

Top Countries: Spain, Portugal

Open by Stage:
  Prospecting: 2 deals
  Validation: 1 deal
```

---

### 6. QBR (Quarterly Business Review)

**What it does**: Generates a comprehensive business review for a partner

```bash
# Basic QBR for current quarter
python3 -m cli.channel_cli qbr "Partner Name"

# Example
python3 -m cli.channel_cli qbr "Accenture"

# With prior period for comparison
python3 -m cli.channel_cli qbr "Accenture" --period THIS_QUARTER --prior-period LAST_QUARTER

# With revenue target
python3 -m cli.channel_cli qbr "Accenture" --revenue-target 500000

# Specific fiscal period
python3 -m cli.channel_cli qbr "Inetum Spain" --period FY27_Q2

# JSON output (for parsing)
python3 -m cli.channel_cli qbr "Accenture" --json
```

**Expected Output:**
```
QBR Report for Accenture
[Comprehensive markdown report with trends, metrics, and forward-looking analysis]
```

---

### 7. Deal Registrations Trend

**What it does**: Shows deal registrations trend over time

```bash
# Deal registrations for current period
python3 -m cli.channel_cli registrations

# Filter by channel manager
python3 -m cli.channel_cli registrations --channel-manager "Manager Name"

# JSON output
python3 -m cli.channel_cli registrations --json
```

**Expected Output:**
```
Deal Registrations Trend
================================================================================
Quarter       Count    Amount        Approval %  Close %
────────────────────────────────────────────────────────
THIS_Q2          5   $450,000       80.0%      40.0%
LAST_Q1          4   $320,000       75.0%      50.0%
```

---

### 8. Top Partners Leaderboard

**What it does**: Ranks partners by revenue or pipeline

```bash
# Top 10 partners by revenue (default)
python3 -m cli.channel_cli top-partners

# Top 20 partners
python3 -m cli.channel_cli top-partners --limit 20

# Top partners by pipeline (not revenue)
python3 -m cli.channel_cli top-partners --metric pipeline

# Specific period
python3 -m cli.channel_cli top-partners --period THIS_FISCAL_YEAR

# JSON output
python3 -m cli.channel_cli top-partners --json
```

**Expected Output:**
```
Top Partners by Revenue
============================================================
#   Partner Name                   Revenue
────────────────────────────────────────────
1   Accenture                    $250,000
2   Inetum Spain                 $45,000
3   TCS                          $30,000
4   Infosys                      $20,000
5   Wipro                        $15,000
```

---

### 9. Search Opportunities

**What it does**: Search for opportunities by name

```bash
# Search for opportunities
python3 -m cli.channel_cli search "opportunity name"

# Search with stage filter (show only closed-won)
python3 -m cli.channel_cli search "deal name" --stage "Closed Won"

# Filter by partner
python3 -m cli.channel_cli search "deal" --partner "Accenture"

# Filter by country
python3 -m cli.channel_cli search "deal" --country "Spain"

# Limit results
python3 -m cli.channel_cli search "deal" --limit 50

# JSON output
python3 -m cli.channel_cli search "security" --json
```

**Expected Output:**
```
Opportunities (0 found)
==================================================================================================================================
No opportunities found.
```

---

### 10. List Open Opportunities

**What it does**: List all open opportunities with filters

```bash
# List all open opportunities (default: current quarter)
python3 -m cli.channel_cli list-opps

# Filter by partner
python3 -m cli.channel_cli list-opps --partner "Accenture"

# Filter by stage
python3 -m cli.channel_cli list-opps --stage "Prospecting"

# Minimum amount filter
python3 -m cli.channel_cli list-opps --min-amount 100000

# Limit results
python3 -m cli.channel_cli list-opps --limit 50

# Filter by channel manager
python3 -m cli.channel_cli list-opps --channel-manager "Manager Name"

# Combine filters
python3 -m cli.channel_cli list-opps --partner "Accenture" --stage "Validation" --min-amount 50000

# JSON output
python3 -m cli.channel_cli list-opps --json
```

**Expected Output:**
```
Opportunities (2 found)
==================================================================================================================================
Name                                     Amount      Stage               Close Date    Partner               Prob %
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Test Deal 1                            $100,000     Prospecting         2026-09-15    Accenture             25.0%
Test Deal 2                            $250,000     Validation          2026-08-30    Accenture             50.0%
```

---

## Useful Fiscal Periods

Use these period values with `--period` flag:

```
THIS_QUARTER           # Current quarter (default)
LAST_QUARTER
NEXT_QUARTER

THIS_FISCAL_YEAR       # Current fiscal year
LAST_FISCAL_YEAR
NEXT_FISCAL_YEAR

FY27_Q1                # Specific fiscal quarter
FY27_Q2
FY27_Q3
FY27_Q4

THIS_MONTH
LAST_MONTH
```

---

## JSON Output & Piping

All commands support `--json` flag for structured output:

```bash
# Basic JSON output
python3 -m cli.channel_cli kpi --json

# Pretty print with jq
python3 -m cli.channel_cli kpi --json | jq '.'

# Extract specific fields
python3 -m cli.channel_cli kpi --json | jq '.data.revenue'

# Filter with jq
python3 -m cli.channel_cli revenue --breakdown partner --json | jq '.data[] | select(.totalRevenue > 100000)'

# Count items
python3 -m cli.channel_cli top-partners --json | jq '.data | length'

# Sort and filter
python3 -m cli.channel_cli top-partners --json | jq '.data | sort_by(.total_revenue) | reverse | .[0:5]'
```

---

## Test Workflow

### Complete Testing Sequence

Run these commands in order to test all features:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Get help
python3 -m cli.channel_cli --help

# 3. Test KPI
python3 -m cli.channel_cli kpi

# 4. Test Revenue
python3 -m cli.channel_cli revenue --breakdown partner

# 5. Test Pipeline
python3 -m cli.channel_cli pipeline

# 6. Test Risk
python3 -m cli.channel_cli risk

# 7. Test Top Partners
python3 -m cli.channel_cli top-partners

# 8. Test JSON output
python3 -m cli.channel_cli kpi --json | jq '.data'

# 9. Deactivate virtual environment
deactivate
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'click'"

**Solution**: Activate virtual environment
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Failed to initialize authentication"

**Solution**: Ensure one of the following:
```bash
# Option 1: Install and login with Salesforce CLI
brew install salesforce-cli
sf org login web

# Option 2: Set environment variables
export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=your_token_here

# Option 3: Create .env file
cp .env.example .env
# Edit .env with your credentials
```

### "No module named 'salesforce_client'"

**Solution**: Make sure you're running from the project root directory
```bash
cd /Users/santiagot/Applications/salesforce-fastmcp
source .venv/bin/activate
python3 -m cli.channel_cli kpi
```

### "Invalid period: INVALID_PERIOD"

**Solution**: Use valid fiscal period. See "Useful Fiscal Periods" section above

### Partner name not found

**Solution**: Use exact partner name (case-sensitive). List available partners first:
```bash
python3 -m cli.channel_cli top-partners --json | jq '.data[].partner_name'
```

---

## Common Workflows

### Workflow 1: Daily KPI Check

```bash
source .venv/bin/activate

echo "=== TODAY'S KPI ==="
python3 -m cli.channel_cli kpi

echo "=== TOP PARTNERS ==="
python3 -m cli.channel_cli top-partners --limit 5

echo "=== HIGH RISK DEALS ==="
python3 -m cli.channel_cli risk

deactivate
```

### Workflow 2: Partner Analysis

```bash
source .venv/bin/activate

PARTNER="Accenture"

echo "=== Partner Scorecard ==="
python3 -m cli.channel_cli partner "$PARTNER"

echo "=== Partner QBR ==="
python3 -m cli.channel_cli qbr "$PARTNER"

echo "=== Open Opportunities ==="
python3 -m cli.channel_cli list-opps --partner "$PARTNER"

deactivate
```

### Workflow 3: Revenue Analysis

```bash
source .venv/bin/activate

echo "=== Revenue by Partner ==="
python3 -m cli.channel_cli revenue --breakdown partner

echo "=== Revenue by Country ==="
python3 -m cli.channel_cli revenue --breakdown country

echo "=== Pipeline by Stage ==="
python3 -m cli.channel_cli pipeline --breakdown stage

deactivate
```

### Workflow 4: Export Data to JSON

```bash
source .venv/bin/activate

# Export all KPI data
python3 -m cli.channel_cli kpi --json > kpi_data.json

# Export top partners
python3 -m cli.channel_cli top-partners --json > partners_data.json

# Export opportunities
python3 -m cli.channel_cli list-opps --json > opportunities.json

deactivate
```

---

## Advanced Examples

### Using with Shell Scripts

```bash
#!/bin/bash
# analyze.sh - Automated analysis script

cd /Users/santiagot/Applications/salesforce-fastmcp
source .venv/bin/activate

# Get revenue and extract specific metric
REVENUE=$(python3 -m cli.channel_cli revenue --json | jq '.data.totalRevenue')
echo "Total Revenue: $REVENUE"

# List high-value partners
python3 -m cli.channel_cli top-partners --json | \
  jq '.data[] | select(.total_revenue > 100000) | {name: .partner_name, revenue: .total_revenue}'

deactivate
```

### Using with Cron (Scheduled Execution)

```bash
# Add to crontab
# Daily at 9 AM - Generate KPI report
0 9 * * * cd /Users/santiagot/Applications/salesforce-fastmcp && \
  source .venv/bin/activate && \
  python3 -m cli.channel_cli kpi --json > /tmp/daily_kpi_$(date +\%Y\%m\%d).json && \
  deactivate
```

---

## Performance Tips

1. **Use JSON output for large datasets**
   ```bash
   # Faster to parse than pretty-printed output
   python3 -m cli.channel_cli list-opps --limit 1000 --json
   ```

2. **Filter early when possible**
   ```bash
   # Do this (filter in CLI)
   python3 -m cli.channel_cli list-opps --partner "Accenture"
   
   # Not this (filter after retrieval)
   python3 -m cli.channel_cli list-opps --json | jq '.data[] | select(.partner == "Accenture")'
   ```

3. **Use specific periods**
   ```bash
   # Faster (smaller result set)
   python3 -m cli.channel_cli revenue --period THIS_QUARTER
   
   # Slower (larger result set)
   python3 -m cli.channel_cli revenue --period THIS_FISCAL_YEAR
   ```

---

## Resources

- **Security Assessment**: `Docs/CLI_SECURITY_ASSESSMENT.md`
- **Implementation Guide**: `Docs/AUTH_PROVIDER_CLI_IMPLEMENTATION.md`
- **Authentication Guide**: `Docs/AUTHENTICATION_QUICKSTART.md`
- **Corporate Deployment**: `.github/CORPORATE_DEPLOYMENT_GUIDE.md`

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review authentication setup
3. Verify virtual environment is activated
4. Check that credentials are valid (try Salesforce CLI login)

---

**Status**: ✅ CLI is production-ready with secure authentication
**Last Updated**: June 16, 2026
**Version**: 2.0 (auth_provider integration)

