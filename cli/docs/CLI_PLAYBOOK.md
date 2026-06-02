# Channel Intelligence CLI Playbook
## For Channel Directors: Direct Salesforce Access & Automation

---

## Table of Contents

1. [What is the CLI?](#what-is-the-cli)
2. [When to Use CLI vs MCP](#when-to-use-cli-vs-mcp)
3. [Getting Started](#getting-started)
4. [Command Reference](#command-reference)
5. [Real-World Workflows](#real-world-workflows)
6. [Hermes Automation](#hermes-automation)
7. [Advanced Piping with jq](#advanced-piping-with-jq)
8. [Troubleshooting](#troubleshooting)

---

## What is the CLI?

The **Channel Intelligence CLI** is a direct, command-line interface to your Salesforce analytics. Unlike the MCP (which uses an LLM), the CLI:

✅ Runs instantly (no LLM latency)
✅ Works in scripts and cron jobs
✅ Returns consistent, predictable results
✅ Can be automated 24/7
✅ Supports JSON output for piping/integration
✅ No rate limits or token costs

**Perfect for:** automated reports, scheduled dashboards, alert workflows

---

## When to Use CLI vs MCP

| Situation | Use CLI | Use MCP |
|-----------|---------|---------|
| "Run this daily at 8am" | ✅ | ❌ |
| "What's happening with Accenture?" | ❌ | ✅ |
| "Send me weekly risk alerts" | ✅ | ❌ |
| "Show me something unusual" | ❌ | ✅ |
| "Generate QBR for all partners" | ✅ | ❌ |
| "Which deals are at risk?" | ✅✅ | ✅ |
| "Feed data to Slack every morning" | ✅ | ❌ |
| "I have a question about the data" | ❌ | ✅ |

**Rule of thumb:** CLI = automation & workflows. MCP = exploration & discovery.

---

## Getting Started

### Prerequisites

```bash
# Navigate to project directory
cd /Users/santiagot/Applications/salesforce-fastmcp

# Ensure .env has valid credentials
cat .env
# Should show:
# SALESFORCE_BASE_URL=https://...
# SALESFORCE_SID=your_session_id
```

### Refresh Your Session ID (if expired)

```bash
node Scripts/extract-sid.js
# Paste new SID into .env
```

### Test Connection

```bash
python cli/channel_cli.py kpi
# Should show KPI snapshot. If error: "Missing required environment variables"
# → .env is missing SALESFORCE_BASE_URL or SALESFORCE_SID
```

---

## Command Reference

### Help

```bash
# List all commands
python cli/channel_cli.py --help

# Help for specific command
python cli/channel_cli.py kpi --help
python cli/channel_cli.py revenue --help
python cli/channel_cli.py risk --help
```

---

### 1. KPI (Daily Standup)

**What it does:** Get your morning snapshot in 30 seconds.

```bash
# Basic KPI
python cli/channel_cli.py kpi

# Returns:
# - Revenue (closed-won this quarter)
# - Pipeline (open opportunities)
# - Coverage ratio (pipeline vs quota)
# - Win rate
# - Active partners
```

**Examples:**

```bash
# This quarter (default)
python cli/channel_cli.py kpi

# This fiscal year
python cli/channel_cli.py kpi --period THIS_FISCAL_YEAR

# Last quarter
python cli/channel_cli.py kpi --period LAST_QUARTER

# Last 30 days
python cli/channel_cli.py kpi --period LAST_30_DAYS

# As JSON (for scripting/automation)
python cli/channel_cli.py kpi --json

# Pretty-print then pipe to file
python cli/channel_cli.py kpi > daily_kpi.txt
```

**Use case:** Email this every morning at 8am to leadership

---

### 2. Revenue (Quota Tracking)

**What it does:** See closed-won revenue with attainment %.

```bash
# Basic (this quarter)
python cli/channel_cli.py revenue

# Breakdown by country
python cli/channel_cli.py revenue --breakdown country

# Breakdown by partner
python cli/channel_cli.py revenue --breakdown partner

# Breakdown by quarter (compare Q1, Q2, Q3, Q4)
python cli/channel_cli.py revenue --breakdown quarter

# This fiscal year
python cli/channel_cli.py revenue --period THIS_FISCAL_YEAR

# Last quarter
python cli/channel_cli.py revenue --period LAST_QUARTER

# JSON output
python cli/channel_cli.py revenue --json
```

**Real examples:**

```bash
# "How much did we close this quarter?"
python cli/channel_cli.py revenue

# Output:
# Revenue Summary
# ├─ Closed-Won: $1,308,444
# ├─ Deals: 12
# └─ Attainment: 87.2%

# "Which countries are performing best?"
python cli/channel_cli.py revenue --breakdown country

# "How is Accenture doing?" (see Partner Scorecard instead)
# "How much did we close this FY?"
python cli/channel_cli.py revenue --period THIS_FISCAL_YEAR
```

---

### 3. Pipeline (Forecast Health)

**What it does:** Track open opportunities by stage/partner/country.

```bash
# Total pipeline
python cli/channel_cli.py pipeline

# By stage (Prospecting, Validation, Negotiation)
python cli/channel_cli.py pipeline --breakdown stage

# By partner
python cli/channel_cli.py pipeline --breakdown partner

# By country
python cli/channel_cli.py pipeline --breakdown country

# By quarter (future close dates)
python cli/channel_cli.py pipeline --breakdown quarter

# This fiscal year
python cli/channel_cli.py pipeline --period THIS_FISCAL_YEAR
```

**Real examples:**

```bash
# "Where's our bottleneck?"
python cli/channel_cli.py pipeline --breakdown stage
# Shows: Prospecting $X, Validation $Y, Negotiation $Z
# → Largest amount = bottleneck

# "Which partner has the most open pipeline?"
python cli/channel_cli.py pipeline --breakdown partner

# "Which countries will close next quarter?"
python cli/channel_cli.py pipeline --breakdown quarter
```

---

### 4. Partner (Deep Dive Scorecard)

**What it does:** Full partner health in one view.

```bash
# Partner scorecard
python cli/channel_cli.py partner "Accenture"

# Partial name match (auto-searches)
python cli/channel_cli.py partner "Inetum"

# Specific period
python cli/channel_cli.py partner "Accenture" --period FY27_Q1

# As JSON
python cli/channel_cli.py partner "Accenture" --json
```

**Output includes:**
- Revenue (closed-won)
- Pipeline (open)
- Average deal size
- Top countries
- Open deals by stage

**Real examples:**

```bash
# "How is Accenture performing?"
python cli/channel_cli.py partner "Accenture"

# "Inetum scorecard for my 1:1"
python cli/channel_cli.py partner "Inetum Spain"

# "How did Accenture do last quarter?"
python cli/channel_cli.py partner "Accenture" --period LAST_QUARTER

# "Export scorecard for email"
python cli/channel_cli.py partner "Accenture" > accenture_scorecard.txt
```

---

### 5. QBR (Quarterly Business Review)

**What it does:** Full markdown QBR document (ready to email or print).

```bash
# Generate QBR (this quarter)
python cli/channel_cli.py qbr "Accenture"

# Specific period
python cli/channel_cli.py qbr "Accenture" --period FY27_Q1

# With revenue target
python cli/channel_cli.py qbr "Accenture" --revenue-target 500000

# Export to file
python cli/channel_cli.py qbr "Accenture" > qbr_accenture.md

# As JSON (for programmatic processing)
python cli/channel_cli.py qbr "Accenture" --json
```

**QBR includes:**
- Business performance (revenue, growth, win rate, deal registrations)
- Pipeline health (open pipeline, by stage, top opportunities)
- Geography (revenue & pipeline by country)
- Forward-looking (next quarter pipeline, closing in 60 days)

**Real examples:**

```bash
# "Generate QBR for partner meeting"
python cli/channel_cli.py qbr "Accenture" > accenture_qbr.md

# "QBR with custom target"
python cli/channel_cli.py qbr "NTT Spain" --revenue-target 300000

# "Generate all partner QBRs for month-end"
for partner in "Accenture" "Inetum" "NTT"; do
  python cli/channel_cli.py qbr "$partner" > qbr_${partner}.md
done
```

---

### 6. Risk (High-Risk Alerts)

**What it does:** Flag deals with low probability closing soon.

```bash
# High-risk deals (default threshold: 40% probability)
python cli/channel_cli.py risk

# Custom probability threshold
python cli/channel_cli.py risk --probability-threshold 30

# Specific period
python cli/channel_cli.py risk --period THIS_FISCAL_YEAR

# As JSON (for jq filtering)
python cli/channel_cli.py risk --json

# By channel manager
python cli/channel_cli.py risk --channel-manager "Santiago"
```

**Output includes:**
- Deal name
- Amount & close date
- Probability & stage
- Risk score
- Recommended action

**Real examples:**

```bash
# "What deals need attention?"
python cli/channel_cli.py risk

# "Deals closing in <14 days (urgent)"
python cli/channel_cli.py risk --json | jq '.deals[] | select(.daysUntilClose < 14)'

# "Which deals <50% probability?"
python cli/channel_cli.py risk --probability-threshold 50
```

---

### 7. Registrations (Deal Registration Trend)

**What it does:** Track deal registration health across quarters.

```bash
# Show trend (all 4 quarters of current FY)
python cli/channel_cli.py registrations

# Specific period
python cli/channel_cli.py registrations --period THIS_FISCAL_YEAR

# By channel manager
python cli/channel_cli.py registrations --channel-manager "Santiago"

# As JSON
python cli/channel_cli.py registrations --json
```

**Output shows:**
- Count, amount, approval rate, close rate per quarter
- Trend analysis (Q1 vs Q2 vs Q3 vs Q4)

**Real examples:**

```bash
# "How are registrations trending?"
python cli/channel_cli.py registrations

# "Q2 approval rate dipped. Why?"
python cli/channel_cli.py registrations --json | jq '.data[] | select(.quarter == "Q2")'
```

---

### 8. Top Partners (Leaderboard)

**What it does:** Rank partners by revenue or pipeline.

```bash
# Top 10 by revenue (default)
python cli/channel_cli.py top-partners

# Top 5
python cli/channel_cli.py top-partners --limit 5

# Top 10 by pipeline
python cli/channel_cli.py top-partners --metric pipeline

# This fiscal year
python cli/channel_cli.py top-partners --period THIS_FISCAL_YEAR

# As JSON
python cli/channel_cli.py top-partners --json
```

**Real examples:**

```bash
# "Who's our top performer?"
python cli/channel_cli.py top-partners --limit 5

# "Top partners by pipeline (forecast)"
python cli/channel_cli.py top-partners --metric pipeline

# "Top 10 for annual board review"
python cli/channel_cli.py top-partners --limit 10 --period THIS_FISCAL_YEAR
```

---

### 9. Search (Find Specific Deals)

**What it does:** Search for closed opportunities by name/stage.

```bash
# Search for all closed-won deals (% matches anything)
python cli/channel_cli.py search "%" --stage "Closed Won" --limit 50

# Search by name fragment
python cli/channel_cli.py search "telefonica" --stage "Closed Won"

# Last quarter only
python cli/channel_cli.py search "%" --period LAST_QUARTER --stage "Closed Won"

# By partner
python cli/channel_cli.py search "%" --partner "Accenture" --stage "Closed Won"

# Closed-lost deals (to understand where deals fail)
python cli/channel_cli.py search "%" --stage "Closed Lost" --limit 50

# As JSON
python cli/channel_cli.py search "%" --stage "Closed Won" --json
```

**Real examples:**

```bash
# "Which deals closed last quarter?"
python cli/channel_cli.py search "%" --period LAST_QUARTER --stage "Closed Won" --limit 50

# "What Accenture deals did we close?"
python cli/channel_cli.py search "%" --partner "Accenture" --stage "Closed Won"

# "Why did we lose deals? (analysis)"
python cli/channel_cli.py search "%" --stage "Closed Lost" --limit 50 --json | \
  jq -r '.data[] | "\(.name): \(.partner) in \(.country)"'
```

---

### 10. List Open Opportunities (Pipeline Deep Dive)

**What it does:** List all open opportunities with filters.

```bash
# All open deals
python cli/channel_cli.py list-opps

# Specific stage
python cli/channel_cli.py list-opps --stage "Negotiation"

# By partner
python cli/channel_cli.py list-opps --partner "Accenture"

# Large deals (>$100k)
python cli/channel_cli.py list-opps --min-amount 100000

# Combination filters
python cli/channel_cli.py list-opps --partner "Accenture" --country Spain

# As JSON
python cli/channel_cli.py list-opps --json
```

**Real examples:**

```bash
# "What's in Negotiation stage?"
python cli/channel_cli.py list-opps --stage "Negotiation"

# "Accenture pipeline in Spain"
python cli/channel_cli.py list-opps --partner "Accenture" --country Spain

# "Deals >$500k (forecast impact)"
python cli/channel_cli.py list-opps --min-amount 500000 --json | jq '.data[]'
```

---

## Real-World Workflows

### Workflow 1: Daily Standup (5 minutes)

**Goal:** Get your daily briefing at 8am before the standup.

```bash
#!/bin/bash
# File: daily_standup.sh

echo "=== DAILY STANDUP ($(date)) ===" > standup.txt
echo "" >> standup.txt

echo "KPI:" >> standup.txt
python cli/channel_cli.py kpi >> standup.txt

echo "" >> standup.txt
echo "HIGH-RISK DEALS:" >> standup.txt
python cli/channel_cli.py risk --period THIS_QUARTER >> standup.txt

echo "" >> standup.txt
echo "STALLED DEALS:" >> standup.txt
python cli/channel_cli.py search "%" --stage "Prospecting" --limit 50 | grep -i "stalled" >> standup.txt

# Send to Slack (requires integration)
# curl -X POST -H 'Content-type: application/json' \
#   --data @standup.txt \
#   $SLACK_WEBHOOK_URL
```

**Hermes schedule:**
```
"Every weekday at 8:00 AM, run daily_standup.sh and post to #standup-briefing"
```

---

### Workflow 2: Weekly Risk Report (Monday 9am)

**Goal:** Flag escalations before the week starts.

```bash
#!/bin/bash
# File: weekly_risk.sh

echo "WEEKLY RISK REPORT - $(date +%Y-%m-%d)" > risk_report.txt
python cli/channel_cli.py risk --period THIS_QUARTER --json | \
  jq '.deals[] | select(.daysUntilClose < 30) | 
    "\(.name): \(.probability)% prob, closes in \(.daysUntilClose) days"' >> risk_report.txt

# Urgent alerts (< 14 days)
echo "" >> risk_report.txt
echo "⚠️ URGENT (< 14 days):" >> risk_report.txt
python cli/channel_cli.py risk --period THIS_QUARTER --json | \
  jq '.deals[] | select(.daysUntilClose < 14)' >> risk_report.txt
```

---

### Workflow 3: Monthly Revenue Review (1st of month)

**Goal:** See if you're tracking to quota.

```bash
#!/bin/bash
# File: monthly_review.sh

MONTH=$(date +%B)
echo "=== MONTHLY REVENUE REVIEW - $MONTH ===" > monthly_report.txt

echo "TOTAL REVENUE:" >> monthly_report.txt
python cli/channel_cli.py revenue --period THIS_QUARTER >> monthly_report.txt

echo "" >> monthly_report.txt
echo "BY COUNTRY:" >> monthly_report.txt
python cli/channel_cli.py revenue --breakdown country >> monthly_report.txt

echo "" >> monthly_report.txt
echo "BY PARTNER:" >> monthly_report.txt
python cli/channel_cli.py revenue --breakdown partner >> monthly_report.txt

echo "" >> monthly_report.txt
echo "TOP PERFORMERS:" >> monthly_report.txt
python cli/channel_cli.py top-partners --limit 5 >> monthly_report.txt
```

---

### Workflow 4: Auto-Generate Partner QBRs (Month-end)

**Goal:** Generate QBRs for all key partners in one command.

```bash
#!/bin/bash
# File: generate_qbrs.sh

PARTNERS=("Accenture" "Inetum Spain" "NTT" "SorintSEC" "ANADAT")
QUARTER=$(date +%Y-%m-%d)

mkdir -p qbrs/$QUARTER

for partner in "${PARTNERS[@]}"; do
  echo "Generating QBR for $partner..."
  python cli/channel_cli.py qbr "$partner" \
    --revenue-target 500000 \
    > "qbrs/$QUARTER/qbr_${partner}.md"
done

echo "✓ All QBRs generated in qbrs/$QUARTER/"
# Upload to Google Drive / SharePoint
```

---

### Workflow 5: Deal Closure Forecast

**Goal:** See which deals are closing next week.

```bash
python cli/channel_cli.py list-opps --stage "Negotiation" --json | \
  jq '.data[] | select(.closeDate < (today | todate + 7 days)) | 
    {name, amount, closeDate, partner}'
```

---

## Hermes Automation

### Example: Daily KPI to Slack

**Hermes configuration:**

```yaml
skill: daily_kpi_slack
schedule: "Every weekday at 8:00 AM"
command: |
  python cli/channel_cli.py kpi --json | \
    jq '{revenue: .data.revenue, pipeline: .data.pipeline, coverage: .data.coverageRatio}' | \
    post-to-slack --channel "#sales-metrics"
```

### Example: Weekly Risk Alert with Escalation

```yaml
skill: weekly_risk_alert
schedule: "Every Monday at 9:00 AM"
command: |
  deals=$(python cli/channel_cli.py risk --json | jq '[.deals[] | select(.daysUntilClose < 14)]')
  if [ $(echo $deals | jq 'length') -gt 0 ]; then
    post-to-slack --channel "#risk-escalation" --priority "high"
    send-email "urgent-risks@company.com" "Risk Escalation: $deals"
  fi
```

### Example: Monthly Report Distribution

```yaml
skill: monthly_reports
schedule: "First day of month at 10:00 AM"
command: |
  python cli/channel_cli.py revenue --period THIS_MONTH --json > revenue.json
  python cli/channel_cli.py top-partners --limit 10 --json > partners.json
  
  # Generate report
  python scripts/generate_report.py revenue.json partners.json > report.html
  
  # Distribute
  send-email "leadership@company.com" --attachment report.html
  upload-to-gdrive "Monthly Reports" report.html
```

---

## Advanced Piping with jq

### Filter Deals by Amount

```bash
# Deals > $100k
python cli/channel_cli.py list-opps --json | \
  jq '.data[] | select(.amount > 100000)'

# Deals < $50k
python cli/channel_cli.py search "%" --stage "Closed Won" --json | \
  jq '.data[] | select(.amount < 50000)'
```

### Count & Sum by Country

```bash
python cli/channel_cli.py list-opps --json | \
  jq 'group_by(.country) | 
      map({
        country: .[0].country, 
        count: length, 
        total: map(.amount) | add
      })'
```

### Find Deals Closing in Next N Days

```bash
# Closing in next 30 days
python cli/channel_cli.py list-opps --json | \
  jq '.data[] | select(.closeDate < now + 30 days)'

# Closing in next 7 days (urgent)
python cli/channel_cli.py risk --json | \
  jq '.deals[] | select(.daysUntilClose < 7)'
```

### Partner Performance Summary

```bash
python cli/channel_cli.py revenue --breakdown partner --json | \
  jq '.data[] | "\(.partner): $\(.totalRevenue) (\(.dealCount) deals)"'
```

### Export to CSV

```bash
python cli/channel_cli.py list-opps --json | \
  jq -r '.data[] | [.name, .amount, .stage, .partner, .closeDate] | @csv' \
  > opportunities.csv
```

---

## Troubleshooting

### "Missing required environment variables"

**Fix:** Your `.env` file is missing Salesforce credentials.

```bash
# Update .env
cat > .env << EOF
SALESFORCE_BASE_URL=https://your-instance.salesforce.com
SALESFORCE_SID=$(node Scripts/extract-sid.js)
EOF
```

### "Invalid period. Allowed: CURRENT, THIS_FISCAL_YEAR, ..."

**Fix:** Period name is wrong. Valid values:

```
THIS_QUARTER, LAST_QUARTER, NEXT_QUARTER
THIS_FISCAL_YEAR, LAST_FISCAL_YEAR
Q1, Q2, Q3, Q4 (current FY only)
FY27_Q1, FY26_Q2 (specific quarter)
LAST_30_DAYS, NEXT_60_DAYS
CURRENT, CURRENT_AND_NEXT_QUARTER
```

### "No opportunities found" (but you know they exist)

**Reason:** You're searching in Southern Europe territory only (scope of the MCP).

**Fix:** Verify with sf CLI:

```bash
sf data query --query "SELECT COUNT(Id) FROM Opportunity WHERE IsClosed = false" \
  -o santiagot@semperis.com
```

### "jq: error Cannot iterate over null"

**Fix:** Use correct field names from the CLI output:

```bash
# ❌ Wrong
python cli/channel_cli.py risk --json | jq '.data[]'

# ✅ Correct (deals, not data)
python cli/channel_cli.py risk --json | jq '.deals[]'
```

### "Inconsistent counts (CLI shows 6, revenue shows 12)"

**Reason:** Revenue command counts globally; search/list are scoped to Southern Europe.

**Expected behavior:** Some deals are outside your territory.

---

## Keyboard Shortcuts & Tips

### Run Last Command Faster

```bash
# Re-run last command
!!

# Re-run and pipe to jq
!! | jq '.data[]'
```

### Save Recurring Commands as Aliases

```bash
# Add to ~/.zshrc or ~/.bashrc
alias cli-kpi='python cli/channel_cli.py kpi'
alias cli-risk='python cli/channel_cli.py risk --period THIS_QUARTER'
alias cli-top='python cli/channel_cli.py top-partners --limit 10'

# Then just use:
cli-kpi
cli-risk
cli-top
```

### Quick Debugging

```bash
# See response structure
python cli/channel_cli.py kpi --json | jq 'keys'

# Check specific field
python cli/channel_cli.py partner "Accenture" --json | jq '.data.revenue'

# Pretty-print JSON
python cli/channel_cli.py revenue --json | jq '.'
```

---

## Next Steps

1. **Try each command once** (take 20 minutes to familiarize yourself)
2. **Build your first workflow** (pick one from Real-World Workflows)
3. **Set up Hermes automation** (start with Daily KPI to Slack)
4. **Create aliases** for your most-used commands
5. **Share playbooks** with your team

---

## Questions?

If a command isn't working as expected:

1. Check the help: `python cli/channel_cli.py <command> --help`
2. Test with `--json` to see raw response: `python cli/channel_cli.py <command> --json`
3. Verify credentials: `cat .env`
4. Check period names: must be one of the valid values above

---

**Last Updated:** 2026-05-25
**Version:** 1.0 (CLI with 10 commands + Hermes integration)
