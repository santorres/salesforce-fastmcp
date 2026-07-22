# CLI Command Examples & Use Cases

**Purpose:** Real-world examples of CLI commands for every use case. Copy, paste, and run directly.

**Note:** All commands assume you're in the project root: `cd /path/to/salesforce-fastmcp`

---

## Quick Setup

```bash
# Set your credentials
export SALESFORCE_ORG_URL="https://your-instance.salesforce.com"
export SALESFORCE_CLIENT_ID="your-client-id"
export SALESFORCE_CLIENT_SECRET="your-client-secret"
export SALESFORCE_USERNAME="your-username"
export SALESFORCE_PASSWORD="your-password"

# Or use SSO (if configured)
export SALESFORCE_AUTH_METHOD="sso"

# Test the connection
python3 -m cli.channel_cli kpi-snapshot
```

---

## Channel Intelligence & Revenue Analytics

### KPI & Executive Summary

```bash
# Get quick status snapshot
python3 -m cli.channel_cli kpi-snapshot

# Save as JSON for processing
python3 -m cli.channel_cli kpi-snapshot --format json > snapshot.json

# Get KPI for specific fiscal year
python3 -m cli.channel_cli kpi-snapshot --period FY27_Q3
```

### Revenue Queries

```bash
# This quarter's total revenue
python3 -m cli.channel_cli get-revenue

# This quarter's revenue - pretty print as table
python3 -m cli.channel_cli get-revenue --format table

# Revenue by partner this quarter (top 20)
python3 -m cli.channel_cli get-revenue --breakdown partner --limit 20

# Revenue by country this quarter
python3 -m cli.channel_cli get-revenue --breakdown country

# Revenue by fiscal quarter (historical)
python3 -m cli.channel_cli get-revenue --breakdown quarter

# Fiscal year revenue
python3 -m cli.channel_cli get-revenue --period THIS_FISCAL_YEAR

# Specific quarter revenue
python3 -m cli.channel_cli get-revenue --period FY27_Q2

# Top 50 partners by revenue
python3 -m cli.channel_cli get-revenue --breakdown partner --limit 50

# Export revenue to CSV
python3 -m cli.channel_cli get-revenue --breakdown partner --format json | \
  jq -r '.data[] | [.name, .revenue, .deal_count] | @csv' > revenue.csv

# Pipeline Query - similar options
python3 -m cli.channel_cli get-pipeline
python3 -m cli.channel_cli get-pipeline --breakdown stage
python3 -m cli.channel_cli get-pipeline --breakdown partner
python3 -m cli.channel_cli get-pipeline --period THIS_QUARTER --breakdown country
```

### Top Partners

```bash
# Top 10 partners by revenue
python3 -m cli.channel_cli list-top-partners --metric revenue --limit 10

# Top 15 partners by pipeline
python3 -m cli.channel_cli list-top-partners --metric pipeline --limit 15

# Top partners this fiscal year
python3 -m cli.channel_cli list-top-partners --metric revenue --period THIS_FISCAL_YEAR

# Save top partners as JSON
python3 -m cli.channel_cli list-top-partners --metric revenue --format json > top_partners.json

# Process top partners with jq
python3 -m cli.channel_cli list-top-partners --metric revenue --format json | \
  jq '.data | sort_by(.revenue) | reverse | .[0:10]'
```

### Partner Deep Dives

```bash
# Get everything about Accenture
python3 -m cli.channel_cli partner-detail --partner "Accenture"

# Accenture's open pipeline deals
python3 -m cli.channel_cli partner-pipeline --partner "Accenture"

# Accenture's complete scorecard
python3 -m cli.channel_cli partner-scorecard --partner "Accenture"

# Generate Accenture QBR (markdown)
python3 -m cli.channel_cli partner-qbr --partner "Accenture" > accenture_qbr.md

# Accenture's Q3 performance
python3 -m cli.channel_cli partner-detail --partner "Accenture" --period FY27_Q3

# See Accenture's pipeline in JSON
python3 -m cli.channel_cli partner-pipeline --partner "Accenture" --format json

# Get specific Accenture deal details
python3 -m cli.channel_cli partner-pipeline --partner "Accenture" --format json | \
  jq '.data[] | select(.amount > 100000)'
```

### Growth & Trends

```bash
# Quarter-over-quarter revenue growth
python3 -m cli.channel_cli get-growth --metric revenue --period-a THIS_QUARTER --period-b LAST_QUARTER

# Pipeline growth this quarter
python3 -m cli.channel_cli get-growth --metric pipeline --period-a THIS_QUARTER --period-b LAST_QUARTER

# Year-over-year growth comparison
python3 -m cli.channel_cli get-growth --metric revenue --period-a THIS_FISCAL_YEAR --period-b FY26_FISCAL_YEAR

# Multi-period trend - last 8 quarters
python3 -m cli.channel_cli multi-period-trend --metric revenue --periods FY27_Q3,FY27_Q2,FY27_Q1,FY27_Q0,FY26_Q4,FY26_Q3,FY26_Q2,FY26_Q1

# Pipeline trend over time
python3 -m cli.channel_cli multi-period-trend --metric pipeline --periods FY27_Q3,FY27_Q2,FY27_Q1,FY27_Q0

# Export growth trends as CSV for spreadsheet
python3 -m cli.channel_cli multi-period-trend --metric revenue --periods FY27_Q3,FY27_Q2,FY27_Q1,FY27_Q0 --format json | \
  jq -r '.data[] | [.period, .revenue] | @csv' > trends.csv
```

### New vs Existing Business

```bash
# New vs renewal breakdown this quarter
python3 -m cli.channel_cli new-vs-existing

# By partner - who's our best expansion customer?
python3 -m cli.channel_cli new-vs-existing --breakdown partner

# By country - where's new business growing?
python3 -m cli.channel_cli new-vs-existing --breakdown country

# Fiscal year breakdown
python3 -m cli.channel_cli new-vs-existing --period THIS_FISCAL_YEAR
```

### Partner Sourcing & Influence Metrics

```bash
# Show partner-sourced vs influenced revenue this quarter
python3 -m cli.channel_cli partner-metrics

# Break down by country - where do partners source most?
python3 -m cli.channel_cli partner-metrics --breakdown country

# Break down by partner - which partners source vs influence?
python3 -m cli.channel_cli partner-metrics --breakdown partner

# Full fiscal year analysis
python3 -m cli.channel_cli partner-metrics --period THIS_FISCAL_YEAR

# Specific quarter analysis
python3 -m cli.channel_cli partner-metrics --period FY27_Q2

# Get JSON output for processing
python3 -m cli.channel_cli partner-metrics --json

# Filter for high-sourcing regions
python3 -m cli.channel_cli partner-metrics --breakdown country --json | \
  jq '.data[] | select(.sourced.percentage > 50)'

# Export to CSV for reporting
python3 -m cli.channel_cli partner-metrics --breakdown partner --json | \
  jq -r '.data[] | [.partner, .total_revenue, .sourced.percentage, .influenced.percentage] | @csv' > partner_sourcing.csv

# Count deals by type
python3 -m cli.channel_cli partner-metrics --json | \
  jq '.data | to_entries[] | "\(.key): \(.value.deal_count) deals"'

# Find which channel managers have highest sourced revenue
python3 -m cli.channel_cli partner-metrics --channel-manager "John Doe"
```

---

## Risk Management & Deal Health

### Stalled Deals

```bash
# Find stalled deals (60+ days no activity)
python3 -m cli.channel_cli stalled-deals

# Find deals stuck longer (90+ days)
python3 -m cli.channel_cli stalled-deals --days-threshold 90

# Stalled deals for next quarter
python3 -m cli.channel_cli stalled-deals --period FY27_Q4 --days-threshold 60

# Export stalled deals to JSON for manual follow-up
python3 -m cli.channel_cli stalled-deals --format json > stalled.json

# Count stalled deals by partner (who's the blocker?)
python3 -m cli.channel_cli stalled-deals --format json | \
  jq '.data | group_by(.partner) | map({partner: .[0].partner, count: length}) | sort_by(.count) | reverse'

# List stalled Accenture deals
python3 -m cli.channel_cli stalled-deals --format json | \
  jq '.data[] | select(.partner | contains("Accenture"))'
```

### High-Risk Deals

```bash
# All high-risk deals this quarter
python3 -m cli.channel_cli high-risk-deals

# Deals with <40% close probability
python3 -m cli.channel_cli high-risk-deals --probability-threshold 40

# High-risk deals in next quarter
python3 -m cli.channel_cli high-risk-deals --period FY27_Q4

# Only small risky deals (<$50K)
python3 -m cli.channel_cli high-risk-deals --min-amount 1 --max-amount 50000

# Large risky deals (>$500K)
python3 -m cli.channel_cli high-risk-deals --min-amount 500000

# High-risk deals closing soon (next 30 days)
python3 -m cli.channel_cli high-risk-deals --format json | \
  jq '.data[] | select(.days_to_close <= 30)'

# Summary: how many high-risk deals and total amount at risk?
python3 -m cli.channel_cli high-risk-deals --format json | \
  jq '{count: (.data | length), total_at_risk: (.data | map(.amount) | add)}'
```

### Deal Aging

```bash
# See average time in each stage
python3 -m cli.channel_cli stage-progression-velocity

# Show how old deals are in each stage
python3 -m cli.channel_cli deal-aging-by-stage

# Risk profile - which stages lose deals?
python3 -m cli.channel_cli stage-risk-profile
```

### Lost Deals

```bash
# Lost deals this quarter
python3 -m cli.channel_cli lost-deals

# Lost deals by partner (who lost to us most?)
python3 -m cli.channel_cli lost-deals --group-by partner

# Lost deals by country
python3 -m cli.channel_cli lost-deals --group-by country

# Lost deals last fiscal year
python3 -m cli.channel_cli lost-deals --period FY26_FISCAL_YEAR

# Total value lost and deal count
python3 -m cli.channel_cli lost-deals --format json | \
  jq '{lost_count: (.data | length), total_lost_value: (.data | map(.amount) | add)}'
```

### Partner Activity

```bash
# Which partners are we staying in touch with?
python3 -m cli.channel_cli partner-activity

# Identify quiet partners (at churn risk)
python3 -m cli.channel_cli partner-activity --format json | \
  jq '.data[] | select(.activity_score < 30)'

# Active partners this quarter
python3 -m cli.channel_cli partner-activity --format json | \
  jq '.data[] | select(.activity_score > 70)'

# Recent opportunity activity
python3 -m cli.channel_cli opportunity-recency

# Recently touched deals (show momentum)
python3 -m cli.channel_cli opportunity-recency --format json | \
  jq '.data[0:20]'
```

---

## Sales Rep Analytics (Multi-Region Support)

### Sales Rep Revenue

```bash
# Total revenue by each sales rep
python3 -m cli.channel_cli sales-rep-revenue

# Southern Europe (SE) reps this quarter
python3 -m cli.channel_cli sales-rep-revenue --region SE

# Eastern Europe (EE) reps performance
python3 -m cli.channel_cli sales-rep-revenue --region EE

# Specific rep: Ray Mills' revenue
python3 -m cli.channel_cli sales-rep-revenue --rep "Ray Mills"

# Alessia Ashkenazi (multi-region) - total + regional breakdown
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region SE
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region EE

# Revenue by rep by country (see geographic strength)
python3 -m cli.channel_cli sales-rep-revenue-by-country

# Specific rep by country
python3 -m cli.channel_cli sales-rep-revenue-by-country --rep "Ray Mills"

# Revenue by rep by partner (see relationship strength)
python3 -m cli.channel_cli sales-rep-revenue-by-partner

# Specific rep's partner breakdown
python3 -m cli.channel_cli sales-rep-revenue-by-partner --rep "Bruno Filippelli"

# Export rep performance as CSV
python3 -m cli.channel_cli sales-rep-revenue --format json | \
  jq -r '.data[] | [.rep_name, .revenue, .deal_count] | @csv' > rep_performance.csv
```

### Sales Rep Pipeline

```bash
# Closed deals by each rep
python3 -m cli.channel_cli closed-deals-by-rep

# Ray Mills' closed deals
python3 -m cli.channel_cli closed-deals-by-rep --rep "Ray Mills"

# Closed deals in Southern Europe
python3 -m cli.channel_cli closed-deals-by-rep --region SE

# Open pipeline by rep
python3 -m cli.channel_cli pipeline-deals-by-rep

# Daniel Gaspar's open opportunities
python3 -m cli.channel_cli pipeline-deals-by-rep --rep "Daniel Gaspar"

# EE pipeline (Alessia)
python3 -m cli.channel_cli pipeline-deals-by-rep --region EE

# Closed vs pipeline ratio for each rep (closing velocity)
python3 -m cli.channel_cli closed-deals-by-rep --format json | \
  jq '.data as $closed | ... (complex comparison) ...'
```

### Regional Territory Management

```bash
# See territory assignment for all reps
python3 -m cli.channel_cli sales-rep-regions

# Which reps cover SE?
python3 -m cli.channel_cli sales-rep-regions --region SE

# Which reps cover EE?
python3 -m cli.channel_cli sales-rep-regions --region EE

# Get Alessia's full territory coverage
python3 -m cli.channel_cli sales-rep-regions --rep "Alessia Ashkenazi"

# What about regions for other reps?
python3 -m cli.channel_cli sales-rep-regions --rep "Ray Mills"
python3 -m cli.channel_cli sales-rep-regions --rep "Bruno Filippelli"

# Export territory map as JSON
python3 -m cli.channel_cli sales-rep-regions --format json > territories.json
```

### Sales Rep Opportunity Filtering (list-opps)

**Filter and track open opportunities assigned to specific sales reps:**

```bash
# Nuno's opportunities this quarter
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER

# Nuno's opportunities next quarter
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period NEXT_QUARTER

# Both quarters (combined view)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER && \
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period NEXT_QUARTER

# Ray Mills' opportunities (SE rep)
python3 -m cli.channel_cli list-opps --sales-rep "Ray Mills" --period THIS_QUARTER

# Alessia Ashkenazi (multi-region) - all regions
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --period THIS_QUARTER

# Alessia's opportunities - SE only
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --period THIS_QUARTER --region SE

# Alessia's opportunities - EE only
python3 -m cli.channel_cli list-opps --sales-rep "Alessia Ashkenazi" --period THIS_QUARTER --region EE

# Bruno Filippelli's opportunities (Italy rep)
python3 -m cli.channel_cli list-opps --sales-rep "Bruno Filippelli" --period THIS_QUARTER

# Sales rep's opportunities as JSON (for processing/export)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --json

# Sales rep's opportunities by stage
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --stage "Business Case"

# Sales rep's high-value opportunities (>100K)
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --min-amount 100000

# Sales rep's large deals in Negotiation
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --stage Negotiation --min-amount 50000

# Sales rep's opportunities in specific country
python3 -m cli.channel_cli list-opps --sales-rep Nuno --country Portugal --period THIS_QUARTER

# Sales rep's opportunities by region
python3 -m cli.channel_cli list-opps --sales-rep Nuno --region SE --period THIS_QUARTER

# Export sales rep's opportunities as CSV
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --json | \
  jq -r '.data[] | [.name, .account, .stage, .amount, .closeDate] | @csv' > nuno_opps.csv

# Get statistics on sales rep's pipeline
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --json | \
  jq '{total_opps: (.data|length), total_value: (.data|map(.amount)|add), avg_value: ((.data|map(.amount)|add)/(.data|length)), by_stage: (.data|group_by(.stage)|map({stage: .[0].stage, count: length, value: (map(.amount)|add)}))}'

# Compare two sales reps' pipeline
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_QUARTER --json > nuno.json && \
python3 -m cli.channel_cli list-opps --sales-rep "Ray Mills" --period THIS_QUARTER --json > ray.json && \
jq -n --slurpfile nuno nuno.json --slurpfile ray ray.json '{nuno: ($nuno[0].data|length), ray: ($ray[0].data|length), nuno_value: ($nuno[0].data|map(.amount)|add), ray_value: ($ray[0].data|map(.amount)|add)}'

# List all sales rep opportunities this fiscal year
python3 -m cli.channel_cli list-opps --sales-rep Nuno --period THIS_FISCAL_YEAR --limit 100

# Combine sales rep filter with partner filter
python3 -m cli.channel_cli list-opps --sales-rep Nuno --partner "Accenture" --period THIS_QUARTER

# Sales rep's opportunities with a specific partner in a specific stage
python3 -m cli.channel_cli list-opps --sales-rep "Bruno Filippelli" --partner "Inetum" --stage Validation --period THIS_QUARTER
```

---

## Deal Registration & Programs

### Registration Health

```bash
# Overall deal registration health
python3 -m cli.channel_cli deal-registrations

# Registrations by channel manager
python3 -m cli.channel_cli deal-registrations-breakdown

# Registration trend (are we registering more?)
python3 -m cli.channel_cli deal-registrations-trend

# Fiscal year registrations
python3 -m cli.channel_cli deal-registrations --period THIS_FISCAL_YEAR
```

### Unapproved Registrations (Action Items)

```bash
# Show all unapproved registrations this quarter (Submitted + In Review)
python3 -m cli.channel_cli opportunities-by-status

# Show only submitted registrations (not yet reviewed)
python3 -m cli.channel_cli opportunities-by-status --status Submitted

# Show only in-review registrations
python3 -m cli.channel_cli opportunities-by-status --status "In Review"

# Show all unapproved registrations from entire fiscal year
python3 -m cli.channel_cli opportunities-by-status --status "Submitted,In Review" --period THIS_FISCAL_YEAR

# Show submitted registrations from specific quarter (FY27_Q1)
python3 -m cli.channel_cli opportunities-by-status --status Submitted --period FY27_Q1

# Get unapproved registrations as JSON for processing
python3 -m cli.channel_cli opportunities-by-status --json | jq '.data.opportunities'

# Limit results to specific count
python3 -m cli.channel_cli opportunities-by-status --limit 20

# Filter by channel manager
python3 -m cli.channel_cli opportunities-by-status --status Submitted --channel-manager "John Smith"

# Show approved registrations instead (for comparison)
python3 -m cli.channel_cli opportunities-by-status --status Approved

# Export unapproved registrations to CSV
python3 -m cli.channel_cli opportunities-by-status --json | \
  jq -r '.data.opportunities[] | [.name, .amount, .stageName, .allboundPartner, .ownerName, .country, .registrationStatus] | @csv' > unapproved_registrations.csv

# Count unapproved registrations by status
python3 -m cli.channel_cli opportunities-by-status --json | \
  jq '.data.opportunities | group_by(.registrationStatus) | map({status: .[0].registrationStatus, count: length})'

# Find unapproved registrations by specific Allbound partner
python3 -m cli.channel_cli opportunities-by-status --json | \
  jq '.data.opportunities | group_by(.allboundPartner) | map({partner: .[0].allboundPartner, count: length, total_amount: (map(.amount) | add)})'
```

---

## Win Rate & Performance

### Win Rates

```bash
# Win rate by country
python3 -m cli.channel_cli win-rate-by-country

# Find best-performing regions
python3 -m cli.channel_cli win-rate-by-country --format json | \
  jq '.data | sort_by(.win_rate) | reverse'

# Time to close analysis
python3 -m cli.channel_cli time-to-close-stats
```

### Channel Manager Performance

```bash
# How are managers performing?
python3 -m cli.channel_cli channel-manager-performance

# Specific manager's metrics
python3 -m cli.channel_cli channel-manager-performance --channel-manager "John Smith"

# Fiscal year performance
python3 -m cli.channel_cli channel-manager-performance --period THIS_FISCAL_YEAR
```

---

## Data Quality & Exploration

### Data Quality

```bash
# Check for data issues (orphaned records, etc.)
python3 -m cli.channel_cli orphan-hygiene

# Export data quality report
python3 -m cli.channel_cli orphan-hygiene --format json > data_quality.json
```

### Opportunity Search

```bash
# Get details on a specific opportunity
python3 -m cli.channel_cli opportunity-detail --opportunity-id 00658000005gH1AAI

# Search for Accenture opportunities
python3 -m cli.channel_cli list-opps --partner "Accenture"

# Opportunities in Negotiation stage
python3 -m cli.channel_cli list-opps --stage Negotiation

# Large opportunities (>$100K)
python3 -m cli.channel_cli list-opps --min-amount 100000

# Small opportunities (<$50K)
python3 -m cli.channel_cli list-opps --min-amount 1 --max-amount 50000

# Accenture deals in Spain over $100K
python3 -m cli.channel_cli list-opps --partner "Accenture" --country Spain --min-amount 100000

# Complex multi-filter query
python3 -m cli.channel_cli list-opps \
  --partner "Inetum - Spain (Partner)" \
  --stage "Qualification" \
  --min-amount 50000 \
  --max-amount 500000 \
  --limit 50

# Export for spreadsheet analysis
python3 -m cli.channel_cli list-opps --partner "Accenture" --format json > accenture_opps.json
```

### Exploratory Analysis

```bash
# Discover interesting patterns in your data
python3 -m cli.channel_cli exploratory-analysis

# What anomalies exist?
python3 -m cli.channel_cli exploratory-analysis --format json
```

---

## Advanced Filter Combinations

### Complex Multi-Filter Queries

```bash
# Southern Europe, specific partner, specific stage, large deals
python3 -m cli.channel_cli list-opps \
  --region SE \
  --partner "Accenture" \
  --stage "Negotiation" \
  --min-amount 100000 \
  --period THIS_QUARTER

# Eastern Europe, multiple countries, high amount
python3 -m cli.channel_cli list-opps \
  --region EE \
  --country "Poland" \
  --min-amount 200000

# All deals for a specific rep in their territory
python3 -m cli.channel_cli list-opps \
  --rep "Ray Mills" \
  --stage "Proposal" \
  --min-amount 50000

# Opportunities by multiple criteria
python3 -m cli.channel_cli list-opps \
  --partner "Accenture" \
  --country "Spain" \
  --stage "Negotiation" \
  --min-amount 100000 \
  --max-amount 1000000 \
  --limit 100

# Filter for reps in SE to show their Negotiation stage deals
python3 -m cli.channel_cli list-opps \
  --region SE \
  --stage "Negotiation" \
  --min-amount 50000 \
  --format json | jq '.data | group_by(.sales_rep)'

# Sales rep + partner + stage combination (Nuno's Accenture deals in Negotiation)
python3 -m cli.channel_cli list-opps \
  --sales-rep Nuno \
  --partner "Accenture" \
  --stage "Negotiation" \
  --period THIS_QUARTER

# Sales rep + region + high-value (Alessia's SE opportunities over 200K)
python3 -m cli.channel_cli list-opps \
  --sales-rep "Alessia Ashkenazi" \
  --region SE \
  --min-amount 200000 \
  --period THIS_QUARTER

# Sales rep + country + stage (Nuno's Portugal Validation deals)
python3 -m cli.channel_cli list-opps \
  --sales-rep Nuno \
  --country Portugal \
  --stage Validation \
  --period THIS_QUARTER

# Sales rep's next quarter high-priority deals
python3 -m cli.channel_cli list-opps \
  --sales-rep Nuno \
  --period NEXT_QUARTER \
  --stage "Business Case" \
  --min-amount 50000
```

---

## Export & Data Processing

### JSON Export

```bash
# Export revenue data as JSON
python3 -m cli.channel_cli get-revenue --format json > revenue.json

# Export pipeline as JSON
python3 -m cli.channel_cli get-pipeline --breakdown partner --format json > pipeline.json

# Export all stalled deals
python3 -m cli.channel_cli stalled-deals --format json > stalled_deals.json
```

### CSV Export (using jq)

```bash
# Revenue by partner as CSV
python3 -m cli.channel_cli get-revenue --breakdown partner --format json | \
  jq -r '.data[] | [.partner_name, .revenue, .deal_count] | @csv' > revenue.csv

# Stalled deals as CSV
python3 -m cli.channel_cli stalled-deals --format json | \
  jq -r '.data[] | [.deal_name, .partner, .amount, .last_activity_days] | @csv' > stalled.csv

# High-risk deals as CSV
python3 -m cli.channel_cli high-risk-deals --format json | \
  jq -r '.data[] | [.deal_name, .partner, .amount, .probability, .close_date] | @csv' > risks.csv
```

### jq Filtering Examples

```bash
# Get just the total revenue from a query
python3 -m cli.channel_cli get-revenue --format json | jq '.summary.total_revenue'

# List partner names only
python3 -m cli.channel_cli list-top-partners --metric revenue --format json | \
  jq -r '.data[].partner_name'

# Filter to partners with revenue > $500K
python3 -m cli.channel_cli get-revenue --breakdown partner --format json | \
  jq '.data[] | select(.revenue > 500000)'

# Sort deals by amount (largest first)
python3 -m cli.channel_cli partner-pipeline --partner "Accenture" --format json | \
  jq '.data | sort_by(.amount) | reverse'

# Count deals by stage
python3 -m cli.channel_cli partner-pipeline --partner "Accenture" --format json | \
  jq '.data | group_by(.stage) | map({stage: .[0].stage, count: length})'

# Get average deal size
python3 -m cli.channel_cli get-pipeline --breakdown total --format json | \
  jq '.summary.average_deal_size'

# Complex filter: deals >$100K in Negotiation for Accenture
python3 -m cli.channel_cli partner-pipeline --partner "Accenture" --format json | \
  jq '.data[] | select(.stage == "Negotiation" and .amount > 100000)'
```

### Piping to Other Tools

```bash
# Save data and send slack notification
python3 -m cli.channel_cli high-risk-deals --format json > risks.json
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"High-risk deals: $(jq '.data | length' risks.json) deals at risk\"}" \
  $SLACK_WEBHOOK

# Export and email
python3 -m cli.channel_cli stalled-deals --format json | \
  jq -r '.data[] | [.deal_name, .partner, .amount] | @csv' | \
  mail -s "Stalled Deals Report" team@example.com

# Create markdown report
python3 -m cli.channel_cli kpi-snapshot --format json | jq -r '.data | to_entries[] | "- \(.key): \(.value)"' > report.md
```

---

## Scheduled Reports & Automation

### Daily Standup Report

```bash
#!/bin/bash
# daily_standup.sh - Run each morning

python3 -m cli.channel_cli kpi-snapshot
echo "---"
python3 -m cli.channel_cli high-risk-deals --format json | \
  jq '.data | length' | xargs -I {} echo "High-risk deals: {}"
echo "---"
python3 -m cli.channel_cli stalled-deals --format json | \
  jq '.data | length' | xargs -I {} echo "Stalled deals: {}"
```

### Weekly Report

```bash
#!/bin/bash
# weekly_report.sh

echo "=== WEEKLY BUSINESS REVIEW ===" > weekly.txt
echo "Generated: $(date)" >> weekly.txt
echo "" >> weekly.txt

echo "=== Revenue ===" >> weekly.txt
python3 -m cli.channel_cli get-revenue --breakdown partner --format json | \
  jq '.data | sort_by(.revenue) | reverse | .[0:5]' >> weekly.txt

echo "=== Pipeline by Stage ===" >> weekly.txt
python3 -m cli.channel_cli get-pipeline --breakdown stage --format json >> weekly.txt

echo "=== Stalled Deals ===" >> weekly.txt
python3 -m cli.channel_cli stalled-deals --format json | \
  jq '.data | length' >> weekly.txt

mail -s "Weekly Report $(date +%Y-%m-%d)" team@example.com < weekly.txt
```

### Monthly Deep Dive

```bash
#!/bin/bash
# monthly_deep_dive.sh

REPORT="monthly_$(date +%B).md"

cat > $REPORT << EOF
# Monthly Business Review - $(date +%B)

## Executive Summary
EOF

python3 -m cli.channel_cli kpi-snapshot --format json | jq '.data' >> $REPORT

echo "## Revenue by Partner" >> $REPORT
python3 -m cli.channel_cli get-revenue --breakdown partner --limit 10 --format json | jq '.data' >> $REPORT

echo "## Pipeline Analysis" >> $REPORT
python3 -m cli.channel_cli get-pipeline --breakdown stage --format json | jq '.data' >> $REPORT

echo "## Risk Dashboard" >> $REPORT
python3 -m cli.channel_cli high-risk-deals --format json | jq '{count: (.data|length), total_at_risk: (.data|map(.amount)|add)}' >> $REPORT

echo "## Stalled Deals" >> $REPORT
python3 -m cli.channel_cli stalled-deals --format json | jq '.data' >> $REPORT

echo "Report saved to: $REPORT"
```

---

## Troubleshooting & Common Scenarios

### "No results for partner X"

```bash
# List top partners to find exact name
python3 -m cli.channel_cli list-top-partners --metric revenue --format json | \
  jq '.data[].partner_name' | grep -i "accenture"

# Use exact name
python3 -m cli.channel_cli partner-detail --partner "Accenture"  # Use exact match

# Alternative: if still no results, check for typos or company name variations
python3 -m cli.channel_cli get-revenue --breakdown partner --format json | \
  jq '.data[] | .partner_name' | grep -i accenture
```

### "Period not found or invalid"

```bash
# Use these valid periods:
# Current: THIS_QUARTER, THIS_FISCAL_YEAR, THIS_MONTH
# Previous: LAST_QUARTER, LAST_MONTH
# Specific: FY27_Q3, FY27_Q2, FY26_Q4, etc.

# Examples:
python3 -m cli.channel_cli get-revenue --period THIS_QUARTER
python3 -m cli.channel_cli get-revenue --period FY27_Q3  # Specific quarter
python3 -m cli.channel_cli get-revenue --period THIS_FISCAL_YEAR
```

### "Region not recognized"

```bash
# Use only: SE (Southern Europe) or EE (Eastern Europe)

python3 -m cli.channel_cli sales-rep-revenue --region SE  # Correct
python3 -m cli.channel_cli sales-rep-revenue --region south_europe  # Will fail

# SE = Italy, Spain, Portugal, Greece, Cyprus, Malta
# EE = Poland, Czech Republic, Hungary, Slovakia, Romania, Bulgaria, Croatia, Serbia, Slovenia, Turkey
```

### "Too many results - limit output"

```bash
# Use --limit flag (default 20, max 100)
python3 -m cli.channel_cli get-revenue --breakdown partner --limit 10

# Or pipe through head
python3 -m cli.channel_cli get-revenue --breakdown partner --format json | \
  jq '.data | .[0:5]'
```

### "Want formatted output"

```bash
# Use --format flag
--format table    # Pretty table (default for terminal)
--format json     # Machine-readable JSON (for piping/scripts)

python3 -m cli.channel_cli kpi-snapshot --format table
python3 -m cli.channel_cli get-revenue --format json | jq '.'
```

---

## Regional Territory Examples

### Southern Europe (SE) Focus

```bash
# SE team revenue
python3 -m cli.channel_cli sales-rep-revenue --region SE

# SE team by country
python3 -m cli.channel_cli sales-rep-revenue-by-country --region SE

# SE pipeline health
python3 -m cli.channel_cli get-pipeline --period THIS_QUARTER | grep -A 10 "SE"

# Each SE rep's performance
python3 -m cli.channel_cli sales-rep-revenue --rep "Ray Mills"
python3 -m cli.channel_cli sales-rep-revenue --rep "Daniel Gaspar"
python3 -m cli.channel_cli sales-rep-revenue --rep "Bruno Filippelli"
python3 -m cli.channel_cli sales-rep-revenue --rep "Jacopo Zumerle"
python3 -m cli.channel_cli sales-rep-revenue --rep "Nuno Antunes"

# SE opportunities by stage
python3 -m cli.channel_cli list-opps --region SE --stage Negotiation --min-amount 50000
```

### Eastern Europe (EE) Focus

```bash
# EE team revenue (Alessia is primary)
python3 -m cli.channel_cli sales-rep-revenue --region EE

# Alessia's EE territory
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region EE

# EE pipeline forecast
python3 -m cli.channel_cli get-pipeline --period THIS_QUARTER | grep -A 10 "EE"

# EE opportunities
python3 -m cli.channel_cli list-opps --region EE --format json | \
  jq '.data | group_by(.country)'
```

### Multi-Region Rep (Alessia)

```bash
# Alessia's SE performance
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region SE

# Alessia's EE performance
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region EE

# Alessia's combined (all regions)
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi"

# Alessia's pipeline across territories
python3 -m cli.channel_cli pipeline-deals-by-rep --rep "Alessia Ashkenazi"

# Compare Alessia's SE vs EE performance
echo "=== Alessia SE ===" && \
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region SE && \
echo "=== Alessia EE ===" && \
python3 -m cli.channel_cli sales-rep-revenue --rep "Alessia Ashkenazi" --region EE
```

---

## Quick Reference - Common Commands

```bash
# Daily essentials
python3 -m cli.channel_cli kpi-snapshot                    # Status check
python3 -m cli.channel_cli high-risk-deals                 # Risk check
python3 -m cli.channel_cli stalled-deals                   # Activity check

# Weekly reviews
python3 -m cli.channel_cli get-revenue --breakdown partner # Revenue by partner
python3 -m cli.channel_cli get-pipeline --breakdown stage  # Pipeline by stage
python3 -m cli.channel_cli partner-activity                # Partner engagement

# Monthly deep dive
python3 -m cli.channel_cli generate_partner_qbr --partner "Accenture"
python3 -m cli.channel_cli lost-deals
python3 -m cli.channel_cli new-vs-existing

# Quarterly review
python3 -m cli.channel_cli multi-period-trend --metric revenue --periods FY27_Q3,FY27_Q2,FY27_Q1,FY27_Q0
python3 -m cli.channel_cli win-rate-by-country
python3 -m cli.channel_cli stage-progression-velocity

# Sales rep tracking
python3 -m cli.channel_cli sales-rep-revenue              # All reps' revenue
python3 -m cli.channel_cli sales-rep-revenue --rep "Name"  # Specific rep
python3 -m cli.channel_cli sales-rep-regions              # Territory mapping
```

---

## Copy-Paste Command Templates

```bash
# Revenue by partner
python3 -m cli.channel_cli get-revenue --breakdown partner --limit 20

# Partner details
python3 -m cli.channel_cli partner-detail --partner "NAME"

# Generate QBR
python3 -m cli.channel_cli partner-qbr --partner "NAME"

# High-risk deals
python3 -m cli.channel_cli high-risk-deals --probability-threshold 40

# Stalled deals (60+ days)
python3 -m cli.channel_cli stalled-deals --days-threshold 60

# Sales rep revenue
python3 -m cli.channel_cli sales-rep-revenue --region SE

# Regional comparison
python3 -m cli.channel_cli sales-rep-revenue --region SE
python3 -m cli.channel_cli sales-rep-revenue --region EE

# Export to JSON
python3 -m cli.channel_cli [COMMAND] --format json > output.json

# Export to CSV
python3 -m cli.channel_cli [COMMAND] --format json | \
  jq -r '.data[] | [.field1, .field2] | @csv' > output.csv
```

