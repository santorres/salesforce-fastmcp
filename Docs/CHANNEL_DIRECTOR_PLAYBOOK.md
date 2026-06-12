# Channel Director Playbook — Complete MCP Tool Reference

Your comprehensive guide to using the Salesforce FastMCP server for reporting, analysis, and decision-making. All 60 tools organized by use case.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Daily Standup](#daily-standup)
3. [Weekly Operations Review](#weekly-operations-review)
4. [Monthly Business Review](#monthly-business-review)
5. [Quarterly Business Review (QBR)](#quarterly-business-review)
6. [Annual Planning & Board Reviews](#annual-planning--board-reviews)
7. [Partner Management](#partner-management)
8. [Pipeline & Forecasting](#pipeline--forecasting)
9. [Risk & Activity Tracking](#risk--activity-tracking)
10. [Revenue & Quota Analysis](#revenue--quota-analysis)
11. [Deal Registrations](#deal-registrations)
12. [Data Exploration & Ad-Hoc](#data-exploration--ad-hoc)
13. [Raw Data Access (CRUD)](#raw-data-access-crud)
14. [Period & Breakdown Reference](#period--breakdown-reference)

---

## Quick Start

**Never used this before?** Start here with 3 essential queries:

```
1. What's our pipeline right now?
   → get_pipeline(period="THIS_QUARTER")

2. How are we tracking to quota?
   → get_revenue(period="THIS_QUARTER")

3. Which partners are we relying on?
   → get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=10)
```

**Need a full partner QBR in 2 minutes?**
```
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER")
→ Returns markdown report: revenue, pipeline, geography, forward looking
```

---

## Daily Standup

**Duration:** 15 minutes  
**Audience:** Your team  
**Purpose:** Health check — pipeline, activity, risks

### Prompts

**1. Pipeline snapshot (2 min)**
```
get_kpi_snapshot(period="THIS_QUARTER")
```
**Returns:** Revenue, pipeline, win rate, coverage % — all in one call.
**What to look for:** Coverage % (pipeline ÷ quota). If <3x, you're behind.

---

**2. Today's deal activity (3 min)**
```
get_partner_activity_summary(period="THIS_QUARTER")
```
**Returns:** Per-partner: pipeline, deal count, last activity date, deals touched this week.
**What to say:** "Accenture touched 5 deals this week, Inetum gone quiet."

---

**3. High-risk deals (5 min)**
```
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=40)
```
**Returns:** Deals <40% probability closing in 30 days. Flag for action.
**What to do:** "Vodafone deal at 35% probability closes in 28 days. Let's intervene."

---

**4. Stalled deals (5 min)**
```
get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
```
**Returns:** Deals untouched 60+ days, grouped by stage.
**What to do:** "8 deals stuck in Prospecting for 90+ days. Time to qualify or close?"

---

## Weekly Operations Review

**Duration:** 45 minutes  
**Audience:** Ops team, Finance  
**Purpose:** Forecast accuracy, bottleneck detection, partner health

### Prompts

**1. Deal aging & bottlenecks (10 min)**
```
get_deal_aging_by_stage(period="THIS_QUARTER", days_threshold=60)
```
**Returns:** By stage: deal count, avg age, deals >60 days.
**Interpretation:**
- Prospecting: 12 deals, avg 67 days old, 8 >60 days → **Bottleneck: qualification issue**
- Negotiation: 7 deals, avg 32 days old, 0 >60 days → **On track**

---

**2. Stage velocity (historical vs current) (10 min)**
```
get_stage_progression_velocity(lookback_period="LAST_FISCAL_YEAR")
```
**Returns:** Historical avg days per stage + current deals aging vs historical.
**Question to ask:** "Current Prospecting deals average 67 days, historically 45. Why slower?"

---

**3. Lost deal analysis (10 min)**
```
get_lost_deals(period="THIS_QUARTER", group_by="stage")
```
**Returns:** Lost count + amount by stage.
**Actionable insight:** "Losing 3 deals in Negotiation worth 275K. Is it competitive? Pricing?"

---

**4. Forecast vs actual (10 min)**
```
get_revenue(period="THIS_QUARTER")
get_pipeline(period="NEXT_60_DAYS")
```
**Combined insight:** Current revenue + pipeline closing in 60 days = realistic forecast?

---

**5. Deal registrations trend (5 min)**
```
get_deal_registrations_trend()
```
**Returns:** Q1/Q2/Q3/Q4 approval rates, close rates.
**Watch for:** Dropping approval rates (registration bottleneck), low close rates (deal quality?).

---

## Monthly Business Review

**Duration:** 2 hours  
**Audience:** Leadership team  
**Purpose:** Detailed performance review, trend analysis, decision-making

### Prompts

**Section 1: Revenue Performance (30 min)**

```
1. Overall revenue + quota
get_revenue(period="THIS_FISCAL_YEAR")

2. By partner (top 10)
get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=10)

3. By country
get_revenue(period="THIS_FISCAL_YEAR", breakdown="country")

4. YoY growth
get_growth(metric="revenue", period_a="THIS_FISCAL_YEAR", period_b="LAST_FISCAL_YEAR")

5. By channel manager (if you have multiple)
get_channel_manager_performance(period="THIS_FISCAL_YEAR", metric="revenue")
```

**Talking points:**
- Revenue: 2.4M vs 2.5M target (96% attainment)
- Top partner Accenture: 450K (on track)
- Spain: 850K (95% of regional target)
- YoY growth: +8% vs last FY
- Channel managers: Santiago leading with 1.2M

---

**Section 2: Pipeline Health (30 min)**

```
1. Pipeline snapshot
get_pipeline(period="THIS_QUARTER")

2. Weighted pipeline (probability-adjusted)
get_weighted_pipeline(period="THIS_QUARTER")

3. Pipeline by stage
get_pipeline(period="THIS_QUARTER", breakdown="stage")

4. Pipeline by partner
get_top_partners(metric="pipeline", period="THIS_QUARTER", limit=10)

5. Days to close analysis
get_time_to_close_stats(period="THIS_FISCAL_YEAR")
```

**Talking points:**
- Open pipeline: 3.5M (140% coverage — healthy)
- Weighted pipeline: 2.1M (accounts for probability)
- Negotiation: 1.2M in 8 deals (strongest stage)
- Prospecting: 1.8M in 15 deals (early-stage, risky)
- Avg close time: 45 days (faster than Q1's 52)

---

**Section 3: Partner Performance (30 min)**

```
1. Top partners by revenue
get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=10)

2. Top partners by pipeline
get_top_partners(metric="pipeline", period="THIS_FISCAL_YEAR", limit=10)

3. Deal registrations by partner
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="partner")

4. Partner activity (who's quiet?)
get_partner_activity_summary(period="THIS_QUARTER")

5. Win rate by partner (use scorecard for deep dive)
get_partner_scorecard(partner_name="Accenture", period="THIS_QUARTER")
```

**Talking points:**
- Accenture revenue: 450K, pipeline 1.2M, 8 registrations, 75% approval rate
- Inetum Spain quiet: only 2 deals touched this month, 450K pipeline
- Deloitte Italy: ramping up, 5 new registrations, high approval rate (80%)

---

**Section 4: Risk & Activity (30 min)**

```
1. Stalled deals
get_stalled_deals(period="THIS_QUARTER", days_threshold=60)

2. High-risk deals (intervention needed)
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=40)

3. Lost deals analysis
get_lost_deals(period="THIS_FISCAL_YEAR", group_by="partner")

4. New vs Existing business mix
get_new_vs_existing(period="THIS_FISCAL_YEAR")

5. Stage risk profile
get_stage_risk_profile(period="THIS_QUARTER")
```

**Talking points:**
- 8 deals stalled in Prospecting for 90+ days
- 3 high-risk deals closing in 30 days at <35% probability
- Lost 570K this FY, mostly in Negotiation stage
- 65% new business, 35% renewal/expansion
- Prospecting stage averaging 28% probability (realistic for early stage)

---

## Quarterly Business Review

**Duration:** 4+ hours  
**Audience:** Board, investors, senior leadership  
**Purpose:** Comprehensive performance review, strategic insights, forecasting

### Pre-QBR (1 week before)

**Prepare comprehensive partner reviews:**
```
# For each major partner
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER", revenue_target=900000)
generate_partner_qbr(partner_name="Inetum Spain", period="THIS_QUARTER", revenue_target=500000)
generate_partner_qbr(partner_name="Deloitte", period="THIS_QUARTER", revenue_target=450000)
```

**Returns:** Markdown report per partner with:
- Revenue + attainment %
- Pipeline + coverage %
- Deal registrations + approval rate
- Win rate + avg deal size
- Geographic breakdown
- Forward-looking: next quarter pipeline, deals closing in 60 days

---

### QBR Agenda

**Opening: Executive Summary (15 min)**

```
get_kpi_snapshot(period="THIS_QUARTER")
```

**Talking points:**
- Revenue: 850K (achieved Q3 quota)
- Pipeline: 3.5M (135% coverage)
- Win rate: 67%
- Registration approvals: 68%

---

**Section 1: Quarterly Performance (45 min)**

```
1. Quarterly revenue + targets
get_revenue(period="THIS_QUARTER")

2. Geographic performance
get_revenue(period="THIS_QUARTER", breakdown="country")

3. Partner contribution
get_top_partners(metric="revenue", period="THIS_QUARTER", limit=15)

4. QoQ growth
get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="LAST_QUARTER")

5. YoY performance
get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="FY26_Q3")
```

---

**Section 2: Partner Scorecards (60 min)**

**Deep dive into top 3-5 partners:**

```
For each partner:
get_partner_scorecard(partner_name="PARTNER", period="THIS_QUARTER")

Alternative (pre-generated):
Use the markdown from generate_partner_qbr() calls
```

**Cover per partner:**
- Revenue vs target (attainment %)
- Pipeline by stage (opportunities listed)
- Registration health (approvals, close rate)
- Win rate (vs your average)
- Activity level (partner engagement)
- Geographic spread
- Forecast for next quarter

---

**Section 3: Pipeline & Forecast (45 min)**

```
1. Current pipeline breakdown
get_pipeline(period="THIS_QUARTER", breakdown="stage")

2. Next quarter forecast
get_pipeline(period="NEXT_QUARTER")

3. Weighted pipeline (probability-adjusted)
get_weighted_pipeline(period="THIS_QUARTER")

4. Deals closing in next 60 days
get_revenue(period="NEXT_60_DAYS")

5. 4-quarter trend (see progress)
get_multi_period_trend(metric="pipeline", periods=["FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"])
```

**Talking points:**
- Prospecting: 1.8M (54 deals) — need qualification pipeline
- Negotiation: 1.2M (8 deals) — strongest stage
- Closing in 60 days: 600K (reasonable confidence)
- Q4 forecast: conservative 700K based on aging

---

**Section 4: Risk Assessment (30 min)**

```
1. Deal aging by stage
get_deal_aging_by_stage(period="THIS_QUARTER", days_threshold=60)

2. High-risk deals
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=35)

3. Stalled deals
get_stalled_deals(period="THIS_QUARTER", days_threshold=90)

4. Lost deal analysis (lessons learned)
get_lost_deals(period="THIS_QUARTER", group_by="stage")

5. Stage velocity (are we moving faster/slower?)
get_stage_progression_velocity(lookback_period="LAST_FISCAL_YEAR")
```

---

**Section 5: Operational Metrics (30 min)**

```
1. Deal registration trend
get_deal_registrations_trend()

2. Win rate by country
get_win_rate_by_country(period="THIS_QUARTER")

3. Time to close stats
get_time_to_close_stats(period="THIS_FISCAL_YEAR")

4. New vs Existing business
get_new_vs_existing(period="THIS_FISCAL_YEAR")

5. Partner activity summary
get_partner_activity_summary(period="THIS_QUARTER")
```

---

## Annual Planning & Board Reviews

**Duration:** Full day(s)  
**Audience:** Board, C-suite, investors  
**Purpose:** Annual strategy, targets, 3-year forecast

### Prompts

**Section 1: Annual Performance**

```
# Full year revenue performance
get_revenue(period="THIS_FISCAL_YEAR")

# YoY growth
get_growth(metric="revenue", period_a="THIS_FISCAL_YEAR", period_b="LAST_FISCAL_YEAR")

# By partner (all year)
get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=20)

# By country (all year)
get_revenue(period="THIS_FISCAL_YEAR", breakdown="country")

# By channel manager
get_channel_manager_performance(period="THIS_FISCAL_YEAR", metric="revenue")
```

---

**Section 2: Annual Trend Analysis**

```
# 8-quarter trend (2 years)
get_multi_period_trend(
  metric="revenue",
  periods=["FY26_Q1","FY26_Q2","FY26_Q3","FY26_Q4",
           "FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"]
)

# Pipeline trend (8 quarters)
get_multi_period_trend(
  metric="pipeline",
  periods=["FY26_Q1","FY26_Q2","FY26_Q3","FY26_Q4",
           "FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"]
)

# Deal registration trend (annual)
get_deal_registrations_trend(periods=["FY26_Q1","FY26_Q2","FY26_Q3","FY26_Q4","FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"])
```

---

**Section 3: Pipeline & Forecast**

```
# Forward-looking: next 2 quarters
get_pipeline(period="NEXT_QUARTER")

# Weighted pipeline
get_weighted_pipeline(period="THIS_FISCAL_YEAR")

# Deals by stage (maturity assessment)
get_pipeline(period="THIS_FISCAL_YEAR", breakdown="stage")

# Time to close (efficiency metric)
get_time_to_close_stats(period="THIS_FISCAL_YEAR")
```

---

**Section 4: Strategic Insights**

```
# New vs Existing revenue mix (strategy balance)
get_new_vs_existing(period="THIS_FISCAL_YEAR")

# Win rate by country (market competitiveness)
get_win_rate_by_country(period="THIS_FISCAL_YEAR")

# Orphan opportunities (partner quality)
get_orphan_hygiene(period="THIS_FISCAL_YEAR", limit=50)

# Lost deal analysis (competitive threats)
get_lost_deals(period="THIS_FISCAL_YEAR", group_by="partner")
```

---

## Partner Management

**For use in 1:1 meetings, partner reviews, scorecard updates**

### Quick Partner Check-In

```
# 5-minute overview
get_partner_detail(partner_name="Accenture", period="THIS_QUARTER")

# What they're doing this month
get_partner_activity_summary(period="THIS_QUARTER")
  → Find "Accenture" in the list, check "deals_modified_this_month"

# Their open pipeline
get_partner_pipeline(partner_name="Accenture", period="THIS_QUARTER")
```

---

### Deep Dive: Partner Scorecard

```
# Comprehensive partner review (30 min prep)
get_partner_scorecard(partner_name="Accenture", period="THIS_QUARTER")

# Returns: revenue, pipeline, win rate, deal count, countries, stages, activity
```

**For QBR meetings, use pre-generated:**
```
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER", revenue_target=900000)
```

---

### Partner Comparison

```
# Who are your top partners?
get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=10)

# Pipeline: which partners have most upside?
get_top_partners(metric="pipeline", period="THIS_QUARTER", limit=10)

# Registration activity: who's ramping?
get_deal_registrations_breakdown(period="THIS_QUARTER", breakdown="partner")

# Activity: who's engaged vs quiet?
get_partner_activity_summary(period="THIS_QUARTER")
```

---

### Partner Diagnostics

```
# Their lost deals (what are we losing to?)
get_lost_deals(period="THIS_FISCAL_YEAR", group_by="partner")

# Their registration health
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="partner")
  → Look for their name: approval rate, close rate

# Their win rate vs yours
get_partner_scorecard(partner_name="PARTNER", period="THIS_QUARTER")
  → Compare to your average (get_kpi_snapshot)
```

---

## Pipeline & Forecasting

**For weekly/monthly forecast accuracy**

### Current State

```
# Today's pipeline snapshot
get_pipeline(period="THIS_QUARTER")

# By stage breakdown
get_pipeline(period="THIS_QUARTER", breakdown="stage")

# Top opportunities
get_opportunity_list(period="THIS_QUARTER", limit=20)

# Probability-weighted pipeline
get_weighted_pipeline(period="THIS_QUARTER")
```

---

### Forecast Confidence

```
# Which deals close in next 60 days?
get_revenue(period="NEXT_60_DAYS")
  → This is your "committed" forecast

# What's the probability distribution of remaining pipeline?
get_stage_risk_profile(period="THIS_QUARTER")
  → Check avg probability per stage. Prospecting too high? Too low?

# Historical velocity: how fast do deals move?
get_stage_progression_velocity(lookback_period="LAST_FISCAL_YEAR")
  → Current deals aging vs historical? Faster or slower?
```

---

### Next Quarter Planning

```
# Next quarter's opening pipeline
get_pipeline(period="NEXT_QUARTER")

# How many deals are we likely to close? (use historical velocity)
get_stage_progression_velocity()

# 60-day forward view
get_revenue(period="NEXT_60_DAYS")

# 4-quarter trend to spot seasonality
get_multi_period_trend(metric="pipeline", periods=["FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"])
```

---

## Risk & Activity Tracking

**Weekly operational reviews**

### Deal Stalling Detection

```
# Which deals haven't moved in 60+ days?
get_stalled_deals(period="THIS_QUARTER", days_threshold=60)

# More severe: 90+ days?
get_stalled_deals(period="THIS_QUARTER", days_threshold=90)

# What stage are they stuck in?
get_deal_aging_by_stage(period="THIS_QUARTER", days_threshold=60)

# Historical: are they moving slower than they used to?
get_stage_progression_velocity()
```

---

### High-Risk Deals (Intervention)

```
# Deals <40% probability closing in 30 days
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=40)

# More aggressive: <50% probability
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=50)

# Flag for weekly check-in
```

---

### Lost Deal Analysis

```
# Why are we losing?
get_lost_deals(period="THIS_QUARTER", group_by="stage")
  → Are we losing early (Prospecting) or late (Negotiation)?

# Which partners losing most?
get_lost_deals(period="THIS_QUARTER", group_by="partner")

# Which countries?
get_lost_deals(period="THIS_QUARTER", group_by="country")

# In aggregate
get_lost_deals(period="THIS_QUARTER")
  → Loss rate %, avg deal size lost
```

---

### Partner Engagement

```
# Who's active? Who's quiet?
get_partner_activity_summary(period="THIS_QUARTER")

# Individual deal activity
get_opportunity_recency(opportunity_id_or_name="Cardiff Marine")
  → Days since last touch, days in current stage

# Weekly activity pulse
get_partner_activity_summary(period="THIS_QUARTER")
  → Look for: deals_modified_this_week > 0
```

---

## Revenue & Quota Analysis

**For exec reporting, attainment tracking**

### Revenue Performance

```
# THIS quarter: attainment check
get_revenue(period="THIS_QUARTER")

# THIS fiscal year: trajectory
get_revenue(period="THIS_FISCAL_YEAR")

# By partner: who's contributing?
get_top_partners(metric="revenue", period="THIS_QUARTER", limit=15)

# By country: geographic mix
get_revenue(period="THIS_QUARTER", breakdown="country")

# Specific: Accenture in Spain?
get_revenue(period="THIS_QUARTER", partner="Accenture", country="Spain")
```

---

### Growth Analysis

```
# QoQ growth
get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="LAST_QUARTER")

# YoY growth
get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="FY26_Q3")

# 8-quarter trend
get_multi_period_trend(metric="revenue", periods=["FY26_Q1","FY26_Q2","FY26_Q3","FY26_Q4","FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"])
```

---

### Target Attainment

```
# Overall territory
get_revenue(period="THIS_QUARTER")
  → Includes "attainmentPct" vs target

# Spain specifically
get_revenue(period="THIS_QUARTER", country="Spain")

# Accenture globally
get_revenue(period="THIS_QUARTER", partner="Accenture")

# Accenture in Spain
get_revenue(period="THIS_QUARTER", partner="Accenture", country="Spain")

# By channel manager (if configured)
get_channel_manager_performance(period="THIS_QUARTER", metric="revenue")
```

---

### Mix Analysis

```
# New Business vs Renewal/Expansion
get_new_vs_existing(period="THIS_QUARTER")

# Over full year
get_new_vs_existing(period="THIS_FISCAL_YEAR")

# By partner
get_new_vs_existing(period="THIS_QUARTER", breakdown="partner")

# By country
get_new_vs_existing(period="THIS_QUARTER", breakdown="country")
```

---

## Deal Registrations

**For partner program metrics, deal flow monitoring**

### Program Health

```
# How many deals are registered?
get_deal_registrations(period="THIS_FISCAL_YEAR")

# Trend: are approvals accelerating?
get_deal_registrations_trend()

# By status breakdown
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="status")
```

---

### Approval Rate Tracking

```
# This quarter's approval rate
get_deal_registrations(period="THIS_QUARTER")

# Trend across the year
get_deal_registrations_trend()

# By partner (who registers cleanly?)
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="partner")

# By country
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="country")
```

---

### Conversion: Approved → Closed

```
# This quarter
get_deal_registrations(period="THIS_QUARTER")
  → Check "close_rate_pct"

# Trend
get_deal_registrations_trend()
  → Look for rising close rates (deal quality improving)

# Forecast: deals approved last quarter, closing now?
# Check individual opportunities:
get_opportunity_list(period="THIS_QUARTER", stage="Closed Won")
```

---

## Data Exploration & Ad-Hoc

**For questions that don't fit standard templates**

### Exploratory Queries

```
# Find an opportunity by name fragment
search_opportunities(query="Telefonica", period="THIS_QUARTER")

# Get full details of an opportunity
get_opportunity_detail(opportunity_name="Telefonica Digital Transformation")

# List all open opportunities (paginated)
get_opportunity_list(period="THIS_QUARTER", limit=50)

# Filter by stage
get_opportunity_list(period="THIS_QUARTER", stage="Negotiation", limit=50)

# Filter by partner
get_opportunity_list(period="THIS_QUARTER", partner_name="Accenture", limit=50)

# Filter by country
get_opportunity_list(period="THIS_QUARTER", country="Spain", limit=50)
```

---

### Ad-Hoc Analysis

```
# "What's our average deal size?"
get_time_to_close_stats(period="THIS_FISCAL_YEAR")
  → Includes avg deal size

# "How long do deals take to close?"
get_time_to_close_stats(period="THIS_FISCAL_YEAR")
  → Avg, median, min, max days

# "What's our total pipeline?"
get_pipeline(period="THIS_QUARTER")

# "What's our coverage ratio?"
get_kpi_snapshot(period="THIS_QUARTER")

# "Which deals are orphaned (no partner)?"
get_orphan_hygiene(period="THIS_QUARTER", limit=50)
```

---

### Natural Language Search

```
# When you don't know which tool to use:
run_exploratory_analysis(intent="Show me deals in negotiation for Accenture")

# The system will find the best matching tool and return results
```

---

## Raw Data Access (CRUD)

**For data corrections, updates, audits**

### Viewing Raw Data

```
# Find a partner by name
salesforce_find_partner(partner_name="Accenture Spain")
  → Returns partner ID + details

# List all Salesforce objects
salesforce_sobjects()

# Search for anything
salesforce_search(query="Cardiff Marine")

# View record metadata
salesforce_describe(sobject="Opportunity")
```

---

### Updating Records (Use with Caution)

```
# Update an opportunity
salesforce_update(sobject="Opportunity", record_id="006...", fields={"StageName": "Negotiation"})

# Create a new record
salesforce_create(sobject="Opportunity", fields={"Name": "...", "AccountId": "...", ...})

# Delete a record
salesforce_delete(sobject="Opportunity", record_id="006...")
```

---

### Direct SOQL Queries (Advanced)

```
# Run any SOQL query
salesforce_query(query="SELECT Name, Amount, StageName FROM Opportunity WHERE AccountId = '001...'")

# Get recent records
salesforce_recent(sobject="Opportunity", limit=10)

# Get aggregate stats
salesforce_aggregate(sobject="Opportunity", metrics=["COUNT(Id)", "SUM(Amount)"], group_by="StageName")
```

---

## Period & Breakdown Reference

### Supported Periods

Use these with any `period=` parameter:

| Period | Meaning | Example Use |
|--------|---------|-------------|
| `THIS_QUARTER` | Current fiscal quarter | Daily standup |
| `THIS_FISCAL_YEAR` | Feb 2026 – Jan 2027 | Monthly reporting |
| `LAST_QUARTER` | Previous fiscal quarter | Comparison |
| `LAST_FISCAL_YEAR` | Prior full fiscal year | YoY analysis |
| `Q1`, `Q2`, `Q3`, `Q4` | Named quarter in current FY | Q1 deep dive |
| `FY27_Q1` | Feb–Apr 2026 | Specific quarter |
| `FY26_Q4` | Nov 2025 – Jan 2026 | YoY comparison |
| `NEXT_QUARTER` | Next fiscal quarter | Forecasting |
| `NEXT_60_DAYS` | Rolling 60 days forward | Committed forecast |
| `LAST_30_DAYS` | Rolling 30 days back | Recent activity |

---

### Supported Breakdowns

Use these with any `breakdown=` parameter:

| Breakdown | Returns | Use Case |
|-----------|---------|----------|
| `total` | Overall aggregate | Executive summary |
| `partner` | Per-partner metrics | Partner scorecards |
| `country` | Per-country (IT/ES/PT/GR/CY/MT) | Geographic analysis |
| `stage` | Prospecting/Validation/Negotiation/Closed | Pipeline health |
| `status` | Deal registration statuses | Program tracking |

---

## Common Reporting Workflows

### Weekly Ops Report (30 min)

```
1. get_pipeline(period="THIS_QUARTER")
2. get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
3. get_high_risk_deals(period="THIS_QUARTER")
4. get_partner_activity_summary(period="THIS_QUARTER")
```

---

### Monthly Business Review (2 hours)

```
1. get_revenue(period="THIS_FISCAL_YEAR")
2. get_pipeline(period="THIS_QUARTER")
3. get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=10)
4. get_deal_registrations_trend()
5. get_partner_scorecard(partner_name="PARTNER", period="THIS_QUARTER") — for each major partner
```

---

### Quarterly Business Review (4 hours)

```
1. get_kpi_snapshot(period="THIS_QUARTER")
2. get_revenue(period="THIS_QUARTER", breakdown="country")
3. generate_partner_qbr(partner_name="PARTNER", period="THIS_QUARTER") — for top 3-5 partners
4. get_pipeline(period="THIS_QUARTER", breakdown="stage")
5. get_deal_registrations_trend()
6. get_high_risk_deals(period="THIS_QUARTER")
7. get_win_rate_by_country(period="THIS_QUARTER")
```

---

### Annual Board Review (Full day)

```
1. get_revenue(period="THIS_FISCAL_YEAR")
2. get_growth(metric="revenue", period_a="THIS_FISCAL_YEAR", period_b="LAST_FISCAL_YEAR")
3. get_multi_period_trend(metric="revenue", periods=["FY26_Q1"..."FY27_Q4"])
4. get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=20)
5. generate_partner_qbr() — for all major partners
6. get_new_vs_existing(period="THIS_FISCAL_YEAR")
7. get_win_rate_by_country(period="THIS_FISCAL_YEAR")
8. get_time_to_close_stats(period="THIS_FISCAL_YEAR")
```

---

## Tips & Tricks

### Partner Name Matching

Partial matches work! These all find the same partner:
- `"Accenture"`
- `"Accenture Spain"`
- `"Accenture - Spain"`
- `"ACCENTURE"` (case-insensitive)

### Filter Combinations

Combine filters for deep dives:
```
# Accenture in Spain for Q2
get_revenue(period="FY27_Q2", partner="Accenture", country="Spain")

# Open pipeline for Deloitte by stage
get_pipeline(period="THIS_QUARTER", partner="Deloitte", breakdown="stage")
```

### Lists & Trends

When you want to compare multiple periods, use:
```
# 8-quarter view (2 years)
get_multi_period_trend(
  metric="revenue",
  periods=["FY26_Q1","FY26_Q2","FY26_Q3","FY26_Q4","FY27_Q1","FY27_Q2","FY27_Q3","FY27_Q4"]
)

# Or for deal registrations (own tool)
get_deal_registrations_trend(periods=["FY26_Q1","FY26_Q2","FY27_Q1","FY27_Q2"])
```

### Limits & Pagination

Most tools accept `limit=` to cap results:
```
get_top_partners(metric="revenue", limit=20)  # Top 20 instead of 10
get_opportunity_list(limit=100)  # More records
```

### Channel Manager Filter

If you manage multiple teams, filter by manager:
```
get_revenue(period="THIS_QUARTER", channel_manager="Santiago")
get_pipeline(period="THIS_QUARTER", channel_manager="Maria")
```

---

## Glossary

| Term | Definition |
|------|-----------|
| **Attainment %** | Revenue closed ÷ quota × 100 |
| **Coverage ratio** | Pipeline ÷ quota. <3x = behind, >4x = healthy |
| **Win rate** | Closed Won ÷ (Closed Won + Closed Lost) × 100 |
| **Approval rate** | Approved registrations ÷ all registered × 100 |
| **Close rate** | Approved deals that became Closed Won ÷ all Approved × 100 |
| **Weighted pipeline** | Pipeline × Probability%. More realistic than raw pipeline |
| **Stalled** | Deal untouched for 60+ days (configurable) |
| **High-risk** | <40% probability AND closing within 30 days |
| **Bottleneck** | Stage with many old deals (e.g., 8 deals >60 days) |

---

## Need Help?

**"What metric should I use for..."**
- **Revenue:** `get_revenue()`
- **Pipeline forecast:** `get_pipeline()` or `get_weighted_pipeline()`
- **Partner health:** `get_partner_scorecard()` or `generate_partner_qbr()`
- **Risk/bottlenecks:** `get_high_risk_deals()` or `get_stalled_deals()`
- **Trends:** `get_multi_period_trend()` or `get_deal_registrations_trend()`
- **Ad-hoc questions:** `run_exploratory_analysis(intent="your question")`

---

**Last updated:** 2026-05-18  
**Total tools available:** 60  
**Southern Europe coverage:** Italy, Spain, Portugal, Greece, Cyprus, Malta
