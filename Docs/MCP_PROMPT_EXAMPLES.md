# MCP Natural Language Prompt Examples

**Purpose:** Real-world examples of how to ask questions naturally using MCP tools. Simply copy the prompts and use them with Claude or any MCP-capable LLM.

**Note:** All prompts are written in natural business language. The LLM will translate them to tool calls automatically.

---

## Channel Intelligence & Revenue Analytics

### KPI & Dashboards

**"Give me a quick executive summary of where we stand right now"**
```
→ Calls: get_kpi_snapshot()
Returns: Total revenue, pipeline, win rate, coverage %, period
```

**"Show me our Q3 revenue"**
```
→ Calls: get_revenue(period="FY27_Q3")
Returns: Total Q3 revenue, deal count, period labels
```

**"Break down this quarter's revenue by partner"**
```
→ Calls: get_revenue(period="THIS_QUARTER", breakdown="partner", limit=20)
Returns: Revenue amounts per partner, ranked by size
```

**"Which countries generated the most revenue this fiscal year?"**
```
→ Calls: get_revenue(period="THIS_FISCAL_YEAR", breakdown="country")
Returns: Revenue by country (Italy, Spain, Portugal, Greece, Cyprus, Malta, EE countries)
```

**"Show me revenue by quarter for the last 4 quarters"**
```
→ Calls: get_revenue(period="THIS_QUARTER", breakdown="quarter")
Returns: Historical quarterly breakdown (Q3, Q2, Q1, Q0 of fiscal year)
```

**"What's our total revenue by partnership type?"**
```
→ Calls: get_revenue(period="THIS_QUARTER", breakdown="total")
Returns: Single total for the period
```

---

### Pipeline Analysis

**"What's our open pipeline for this quarter?"**
```
→ Calls: get_pipeline(period="THIS_QUARTER")
Returns: Total open pipeline amount, deal count
```

**"Break down the pipeline by deal stage"**
```
→ Calls: get_pipeline(period="THIS_QUARTER", breakdown="stage")
Returns: Pipeline amounts per stage (Prospecting, Qualification, etc.)
```

**"Show me pipeline by partner - who are our biggest pipeline contributors?"**
```
→ Calls: get_pipeline(period="THIS_QUARTER", breakdown="partner", limit=15)
Returns: Top 15 partners by open pipeline value
```

**"Which countries have the most opportunity?"**
```
→ Calls: get_pipeline(period="THIS_QUARTER", breakdown="country")
Returns: Pipeline by country, helps identify geographic focus areas
```

**"What's the current pipeline for Eastern Europe?"**
```
→ Calls: get_pipeline(period="THIS_QUARTER", region="EE")
Returns: Total Eastern Europe pipeline with regional breakdown
```

**"Show me Eastern Europe pipeline by country"**
```
→ Calls: get_pipeline(period="THIS_QUARTER", breakdown="country", region="EE")
Returns: Eastern Europe pipeline broken down by country (Poland, Czech Republic, etc.)
```

**"What's the pipeline split by quarter (realistic forecast)?"**
```
→ Calls: get_weighted_pipeline(period="THIS_QUARTER")
Returns: Probability-weighted pipeline (more realistic forecast)
```

**"Show me weighted pipeline by stage - what's actually at risk?"**
```
→ Calls: get_weighted_pipeline(period="THIS_QUARTER", breakdown="stage")
Returns: Probability-adjusted amounts per stage
```

---

### Partner Performance

**"Who are our top 10 partners by revenue this quarter?"**
```
→ Calls: get_top_partners(period="THIS_QUARTER", metric="revenue", limit=10)
Returns: Ranked partners with revenue amounts
```

**"Show me top partners by pipeline value"**
```
→ Calls: get_top_partners(period="THIS_QUARTER", metric="pipeline", limit=10)
Returns: Ranked partners with open opportunities
```

**"Give me a deep dive on Accenture's performance"**
```
→ Calls: get_partner_detail(partner_name="Accenture", period="THIS_QUARTER")
Returns: Revenue, pipeline, metrics, activity summary for Accenture
```

**"What's Accenture's pipeline right now?"**
```
→ Calls: get_partner_pipeline(partner_name="Accenture", period="THIS_QUARTER")
Returns: List of open Accenture deals with names, amounts, stages, close dates
```

**"How is Accenture performing? Give me the full scorecard"**
```
→ Calls: get_partner_scorecard(partner_name="Accenture", period="THIS_QUARTER")
Returns: Comprehensive scorecard with revenue, growth, win rate, activity
```

**"Generate a QBR deck for Accenture"**
```
→ Calls: generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER")
Returns: Formatted markdown QBR report with all key metrics and trends
```

**"Filter to just Accenture deals"**
```
→ Calls: get_partner_pipeline(partner_name="Accenture")
Returns: All Accenture pipeline opportunities with details
```

---

### Growth & Trends

**"How much did we grow quarter-over-quarter?"**
```
→ Calls: get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="LAST_QUARTER")
Returns: Growth %, absolute change, direction indicator
```

**"Are we growing our pipeline?"**
```
→ Calls: get_growth(metric="pipeline", period_a="THIS_QUARTER", period_b="LAST_QUARTER")
Returns: Pipeline growth %, reveals whether we're building future revenue
```

**"Show me revenue trends over the last 8 quarters"**
```
→ Calls: get_multi_period_trend(metric="revenue", periods=["FY27_Q3", "FY27_Q2", "FY27_Q1", "FY27_Q0", "FY26_Q4", "FY26_Q3", "FY26_Q2", "FY26_Q1"])
Returns: Historical trend data for long-term analysis
```

**"What's our pipeline trajectory over the year?"**
```
→ Calls: get_multi_period_trend(metric="pipeline", periods=["FY27_Q3", "FY27_Q2", "FY27_Q1", "FY27_Q0", "FY26_Q4", "FY26_Q3", "FY26_Q2", "FY26_Q1"])
Returns: Historical pipeline data, shows whether pipeline is strengthening or weakening
```

---

### New vs Existing Business

**"What's the split between new business and renewals?"**
```
→ Calls: get_new_vs_existing(period="THIS_QUARTER")
Returns: New revenue vs renewal/expansion revenue amounts
```

**"Show me new vs existing by partner - who's our best expansion partner?"**
```
→ Calls: get_new_vs_existing(period="THIS_QUARTER", breakdown="partner")
Returns: New/renewal/expansion revenue per partner
```

**"By country, who's contributing new business?"**
```
→ Calls: get_new_vs_existing(period="THIS_QUARTER", breakdown="country")
Returns: New vs existing revenue by geography
```

---

## Risk Management & Deal Health

### Stalled & At-Risk Deals

**"Which deals are stalled and need attention?"**
```
→ Calls: get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
Returns: Deals stuck for 60+ days, with last activity dates
```

**"Show me deals that haven't moved in 90 days"**
```
→ Calls: get_stalled_deals(period="THIS_QUARTER", days_threshold=90)
Returns: High-priority stalled deals
```

**"What deals are high-risk and could be lost?"**
```
→ Calls: get_high_risk_deals(period="THIS_QUARTER")
Returns: Deals with low win probability, flagged for intervention
```

**"Show me only deals with less than 40% probability of closing"**
```
→ Calls: get_high_risk_deals(period="THIS_QUARTER", probability_threshold=40)
Returns: Deals below 40% confidence
```

**"Which deals below $50K are high-risk?"**
```
→ Calls: get_high_risk_deals(period="THIS_QUARTER", min_amount=1, max_amount=50000)
Returns: Risky small deals (often overlooked)
```

---

### Deal Aging & Stage Health

**"How long are deals typically in each stage?"**
```
→ Calls: get_stage_progression_velocity()
Returns: Average time spent per stage, helps identify bottlenecks
```

**"What's the age distribution of our deals? How old is the oldest?"**
```
→ Calls: get_deal_aging_by_stage()
Returns: How long deals have been in each stage
```

**"Show me the risk profile for each stage"**
```
→ Calls: get_stage_risk_profile()
Returns: Risk patterns by stage (which stages lose the most deals?)
```

---

### Lost Deals & Analysis

**"Which deals have we lost recently?"**
```
→ Calls: get_lost_deals(period="THIS_QUARTER")
Returns: Lost opportunities with reasons, timing, amounts
```

**"Which partners had the most lost deals?"**
```
→ Calls: get_lost_deals(period="THIS_QUARTER", group_by="partner")
Returns: Lost deals grouped by partner
```

**"Show me lost deals by country to find geographic pain points"**
```
→ Calls: get_lost_deals(period="THIS_QUARTER", group_by="country")
Returns: Lost deals grouped by country
```

---

### Partner Activity & Engagement

**"Are we staying in touch with our partners? Show partner activity"**
```
→ Calls: get_partner_activity_summary(period="THIS_QUARTER")
Returns: Partner engagement metrics, activity levels, quiet partners
```

**"Which partners are quiet? We might be losing them"**
```
→ Calls: get_partner_activity_summary(period="THIS_QUARTER")
Returns: Low-activity partners that need re-engagement
```

**"Show me recent opportunities - what have we touched lately?"**
```
→ Calls: get_opportunity_recency(period="THIS_QUARTER")
Returns: Recently updated deals, shows activity momentum
```

---

## Sales Rep Analytics (Multi-Region Support)

### Sales Rep Performance

**"Show me total revenue by sales rep this quarter"**
```
→ Calls: get_revenue_by_sales_rep(period="THIS_QUARTER")
Returns: Each rep's revenue contribution
```

**"Who's our top sales rep in Southern Europe this quarter?"**
```
→ Calls: get_revenue_by_sales_rep(period="THIS_QUARTER", region="SE")
Returns: SE reps ranked by revenue (Ray Mills, Daniel Gaspar, Bruno, Jacopo, Nuno, Alessia)
```

**"Show me revenue for Alessia Ashkenazi across both regions"**
```
→ Calls: get_revenue_by_sales_rep(rep_name="Alessia Ashkenazi", period="THIS_QUARTER")
Returns: Alessia's combined SE + EE revenue with regional breakdown
```

**"What's the breakdown of Ray Mills' revenue by country?"**
```
→ Calls: get_revenue_by_sales_rep_by_country(rep_name="Ray Mills", period="THIS_QUARTER")
Returns: Ray's revenue in Spain and Greece (his countries)
```

**"Show me Daniel Gaspar's sales by partner"**
```
→ Calls: get_revenue_by_sales_rep_by_partner(rep_name="Daniel Gaspar", period="THIS_QUARTER")
Returns: Daniel's partner breakdown
```

**"Which sales rep is driving growth in Eastern Europe?"**
```
→ Calls: get_revenue_by_sales_rep(period="THIS_QUARTER", region="EE")
Returns: EE reps ranked by revenue (Alessia is the only SE rep with EE territory)
```

---

### Sales Rep Pipeline

**"Show me closed deals by each sales rep"**
```
→ Calls: get_closed_deals_by_sales_rep(period="THIS_QUARTER")
Returns: Closed/won deals grouped by rep (all reps, all regions)
```

**"Show me all closed-won opportunities for Ionatan Ascher in FY27 with deal details"**
```
→ Calls: get_closed_deals_by_sales_rep(period="THIS_FISCAL_YEAR", sales_rep="Ionatan Ascher")
Returns: Ionatan's closed deals with opportunity names, amounts, close dates, partners, countries
```

**"What's Ray Mills' closed deal count vs value?"**
```
→ Calls: get_closed_deals_by_sales_rep(rep_name="Ray Mills", period="THIS_QUARTER")
Returns: Ray's closed deals this quarter
```

**"Show open pipeline deals for each sales rep"**
```
→ Calls: get_pipeline_deals_by_sales_rep(period="THIS_QUARTER")
Returns: Open deals, grouped by rep
```

**"What's Bruno's pipeline in Italy? (his territory)"**
```
→ Calls: get_pipeline_deals_by_sales_rep(rep_name="Bruno Filippelli", period="THIS_QUARTER")
Returns: Bruno's open opportunities in Italy
```

---

### Regional Territory Management

**"Which sales rep covers which regions and countries?"**
```
→ Calls: get_sales_rep_regions()
Returns: Territory mapping for all reps (SE: Ray/Daniel/Bruno/Jacopo/Nuno; EE: Alessia; Ionatan: Spain/Outside)
```

**"Show me all sales reps assigned to Southern Europe"**
```
→ Calls: get_region_sales_reps(region="SE")
Returns: All SE reps: Ray Mills, Daniel Gaspar, Bruno Filippelli, Jacopo Zumerle, Nuno Antunes, Ionatan Ascher, Alessia Ashkenazi
```

**"Who covers Eastern Europe?"**
```
→ Calls: get_region_sales_reps(region="EE")
Returns: EE reps - primarily Alessia Ashkenazi (multi-region rep)
```

**"Show me which countries Alessia covers"**
```
→ Calls: get_sales_rep_regions(rep_name="Alessia Ashkenazi")
Returns: SE (Italy, Greece) + EE (all 10 countries: Poland, Czech Republic, Hungary, Slovakia, Romania, Bulgaria, Croatia, Serbia, Slovenia, Turkey)
```

---

## Deal Registrations & Programs

### Registration Health

**"How's our deal registration program health? Any issues?"**
```
→ Calls: get_deal_registrations(period="THIS_QUARTER")
Returns: Total registered deals, approval status breakdown
```

**"Show me deal registrations by channel manager"**
```
→ Calls: get_deal_registrations_breakdown(period="THIS_QUARTER", breakdown_type="channel_manager")
Returns: Registrations per manager
```

**"What's the trend in registrations? Are we registering more deals?"**
```
→ Calls: get_deal_registrations_trend(periods=["THIS_QUARTER", "LAST_QUARTER"])
Returns: Registration volume trend
```

### Unapproved Registrations (Action Items)

**"Show me all submitted deal registrations this quarter with their details in a table"**
```
→ Calls: get_opportunities_by_registration_status(
    period="THIS_QUARTER",
    registration_status="Submitted",
    limit=50
)
Returns: Table with deal names, amounts, stages, Allbound partners, owners, countries, close dates
Use Case: Identify registrations pending approval for immediate action
```

**"Which deal registrations have not been approved yet? Show me everything"**
```
→ Calls: get_opportunities_by_registration_status(
    period="THIS_FISCAL_YEAR",
    registration_status="Submitted,In Review",
    limit=100
)
Returns: All unapproved registrations (both Submitted AND In Review) with full details
Use Case: Get comprehensive view of pending registrations that need action (approve, reject, etc.)
```

**"Show me submitted registrations by partner this quarter"**
```
→ Calls: get_opportunities_by_registration_status(
    period="THIS_QUARTER",
    registration_status="Submitted",
    limit=50
)
Returns: Table showing which Allbound partners registered which deals, helps identify bottlenecks
Use Case: See which partners have deals pending approval
```

**"I need to review unapproved registrations from FY27_Q1"**
```
→ Calls: get_opportunities_by_registration_status(
    period="FY27_Q1",
    registration_status="Submitted,In Review",
    limit=200
)
Returns: Historical view of unapproved registrations from past quarter
Use Case: Audit or follow up on old pending approvals
```

**"Show me registrations in review status"**
```
→ Calls: get_opportunities_by_registration_status(
    period="THIS_QUARTER",
    registration_status="In Review",
    limit=50
)
Returns: Deals currently being reviewed, with all relevant details
Use Case: Check progress on registrations in the approval pipeline
```

---

## Partner Sourcing & Influence Revenue

### Partner Revenue Attribution

**"What percentage of our revenue was partner-sourced this quarter?"**
```
→ Calls: get_partner_sourced_influenced_revenue(period="THIS_QUARTER")
Returns: Total revenue split by Source/Influence/Fulfillment/Direct with percentages
Use Case: Understand channel contribution to revenue
```

**"Show me the split between partner-sourced, influenced, and direct revenue"**
```
→ Calls: get_partner_sourced_influenced_revenue(period="THIS_QUARTER")
Returns: Breakdown of all four categories with deal counts and percentages
Use Case: Assess partner involvement across deal types
```

**"Which countries source the most revenue through partners?"**
```
→ Calls: get_partner_sourced_influenced_revenue(period="THIS_QUARTER", breakdown="country")
Returns: Per-country sourcing percentages, shows geographic variation
Use Case: Identify countries with strong partner engagement
```

**"Break down partner-sourced vs influenced revenue by partner"**
```
→ Calls: get_partner_sourced_influenced_revenue(period="THIS_QUARTER", breakdown="partner")
Returns: Per-partner sourcing split, top partners list
Use Case: See which partners originate deals vs. support existing ones
```

**"How much of our FY27 revenue came from partner sourcing?"**
```
→ Calls: get_partner_sourced_influenced_revenue(period="THIS_FISCAL_YEAR")
Returns: Full-year sourced/influenced breakdown with trends
Use Case: Assess annual channel performance
```

---

## Win Rate & Performance Metrics

### Win Rate Analysis

**"What's our overall win rate?"**
```
→ Calls: get_win_rate_by_country()
Returns: Win rates by country, identifies strong/weak regions
```

**"Which country has the highest win rate?"**
```
→ Calls: get_win_rate_by_country()
Returns: Country-by-country win rate, helps identify best practices
```

**"How long does it typically take us to close a deal?"**
```
→ Calls: get_time_to_close_stats()
Returns: Average, median, min, max time-to-close, helps forecast accuracy
```

---

## Channel Manager Performance

### Manager Metrics

**"How are my channel managers performing?"**
```
→ Calls: get_channel_manager_performance(period="THIS_QUARTER")
Returns: Performance metrics for each manager
```

**"Show me which channel manager has the best revenue this quarter"**
```
→ Calls: get_channel_manager_performance(period="THIS_QUARTER")
Returns: Ranked managers by revenue
```

---

## Data Exploration & Special Cases

### Opportunity Details

**"Give me the full details on opportunity ID 00658000005gH1AAI"**
```
→ Calls: get_opportunity_detail(opportunity_id="00658000005gH1AAI")
Returns: Complete opportunity record with all fields
```

**"Show me opportunities for Accenture in Spain larger than $100K"**
```
→ Calls: get_opportunity_list(partner_name="Accenture", country="Spain", min_amount=100000, limit=20)
Returns: Filtered list of opportunities matching criteria
```

**"List all opportunities in negotiation stage"**
```
→ Calls: get_opportunity_list(stage="Negotiation", limit=50)
Returns: All deals in Negotiation stage
```

---

### Data Quality

**"How's our data hygiene? Any issues with our opportunity data?"**
```
→ Calls: get_orphan_hygiene()
Returns: Deals without proper partner assignments, missing fields, data quality issues
```

**"Show me opportunities that might have data quality problems"**
```
→ Calls: get_orphan_hygiene()
Returns: Orphaned records, missing associations, incomplete data
```

---

### Exploratory Analysis

**"Tell me something interesting about our deals - what stands out?"**
```
→ Calls: run_exploratory_analysis()
Returns: Interesting patterns, anomalies, trends worth investigating
```

**"What unusual patterns do you see in our pipeline?"**
```
→ Calls: run_exploratory_analysis()
Returns: Statistical anomalies, outliers, unexpected findings
```

---

## Multi-Tool Workflow Examples

### Daily Standup (15 minutes)

**"Give me the executive summary for today's standup"**
```
Sequence:
1. get_kpi_snapshot() → Current status
2. get_high_risk_deals(period="THIS_QUARTER", limit=5) → Top risks
3. get_stalled_deals(period="THIS_QUARTER", days_threshold=60, limit=5) → Stalled deals
4. get_opportunity_recency(period="THIS_QUARTER", limit=10) → Recent activity

Result: Complete standup briefing in 1 minute
```

### Weekly Partner Check-In (30 minutes)

**"Which partners need attention this week?"**
```
Sequence:
1. get_partner_activity_summary() → Quiet partners
2. get_top_partners(period="THIS_QUARTER", metric="revenue") → Top performers
3. For each quiet partner: get_partner_detail(partner_name="X") → Diagnostic

Result: Engagement priorities for the week
```

### Monthly Review (2 hours)

**"Give me a complete monthly business review"**
```
Sequence:
1. get_revenue(period="THIS_MONTH", breakdown="partner")
2. get_pipeline(period="THIS_QUARTER", breakdown="stage")
3. get_growth(metric="revenue", period_a="THIS_MONTH", period_b="LAST_MONTH")
4. get_high_risk_deals(period="THIS_QUARTER")
5. get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
6. For top 3 partners: generate_partner_qbr()

Result: Complete monthly briefing
```

### Quarterly Business Review (4+ hours)

**"Prepare a comprehensive QBR presentation"**
```
Sequence:
1. get_kpi_snapshot()
2. get_multi_period_trend(metric="revenue", periods=[last 8 quarters])
3. get_multi_period_trend(metric="pipeline", periods=[last 8 quarters])
4. get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="LAST_QUARTER")
5. get_top_partners(period="THIS_QUARTER", metric="revenue", limit=10)
6. get_win_rate_by_country() → Performance by region
7. For each top partner: generate_partner_qbr()
8. get_stage_progression_velocity() → Pipeline health
9. get_lost_deals(period="THIS_QUARTER", group_by="partner")

Result: Full QBR deck ready for executive review
```

---

## Regional Territory Scenarios

### Southern Europe (SE) Analysis

**"Show me total SE revenue for this quarter"**
```
Sequence:
1. get_revenue_by_sales_rep(period="THIS_QUARTER", region="SE")
Returns: Combined revenue from all SE reps (Ray Mills, Daniel Gaspar, Bruno, Jacopo, Nuno, Ionatan, Alessia)
```

**"Which SE country is performing best?"**
```
Sequence:
1. get_revenue_by_sales_rep_by_country(period="THIS_QUARTER", region="SE")
Returns: Breakdown by country (Italy, Spain, Portugal, Greece, Cyprus, Malta)
```

**"Show me Alessia's performance in both her SE and EE territories"**
```
Sequence:
1. get_revenue_by_sales_rep(rep_name="Alessia Ashkenazi", region="SE") → SE performance
2. get_revenue_by_sales_rep(rep_name="Alessia Ashkenazi", region="EE") → EE performance
3. Combine for full picture
```

### Eastern Europe (EE) Analysis

**"How are we doing in Eastern Europe?"**
```
Sequence:
1. get_revenue_by_sales_rep(period="THIS_QUARTER", region="EE")
Returns: EE revenue (Alessia is primary EE rep)
```

**"Show me EE pipeline - what's our forecast?"**
```
Sequence:
1. get_pipeline(period="THIS_QUARTER", breakdown="country") → Filter to EE countries
2. get_weighted_pipeline(period="THIS_QUARTER") → Risk-adjusted EE pipeline
```

---

## Diagnostic Workflows

### "Is Partner X at Risk of Churning?"

**Workflow:**
```
1. get_partner_detail(partner_name="Accenture", period="THIS_QUARTER")
   → Check: declining revenue or pipeline?

2. get_partner_activity_summary()
   → Check: recent activity or going quiet?

3. get_lost_deals(group_by="partner")
   → Check: lost deals to Accenture or deals lost by Accenture?

4. generate_partner_qbr(partner_name="Accenture")
   → Full health check with trends

Result: Complete churn risk assessment
```

### "Are We On Track vs Quota?"

**Workflow:**
```
1. get_kpi_snapshot()
   → Current revenue vs target attainment %

2. get_weighted_pipeline(period="THIS_QUARTER")
   → Realistic forecast of remaining pipeline

3. get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="LAST_QUARTER")
   → Momentum vs last quarter

4. get_stage_progression_velocity()
   → Deal age and progression speed

Result: Forecast confidence level and what-if scenarios
```

### "Which Sales Rep Needs Help?"

**Workflow:**
```
1. get_revenue_by_sales_rep(period="THIS_QUARTER")
   → Identify underperformer

2. get_pipeline_deals_by_sales_rep(rep_name="X")
   → Check pipeline quality

3. get_closed_deals_by_sales_rep(rep_name="X")
   → Check closing rate

4. get_high_risk_deals() → Filter by rep
   → Check risk concentration

Result: Specific coaching priorities for underperformer
```

---

## Prompt Templates (Copy & Paste Ready)

### Revenue Questions
- "Show me [METRIC] for [PERIOD] by [BREAKDOWN]"
- "Give me revenue for [PARTNER] in [QUARTER]"
- "Compare [PERIOD_A] vs [PERIOD_B] revenue"
- "Break down [PERIOD] revenue by partner/country/stage"

### Pipeline Questions
- "What's our open pipeline for [PERIOD]?"
- "Show [PERIOD] pipeline by stage/partner/country"
- "Which deals might close in [PERIOD]?"
- "What's the probability-adjusted pipeline for [PERIOD]?"

### Partner Questions
- "Show me [PARTNER]'s [detail/scorecard/QBR]"
- "Generate a QBR for [PARTNER]"
- "Which partners are our top performers?"
- "Show me [PARTNER]'s pipeline"

### Partner Sourcing & Influence Questions
- "What percentage of our revenue was partner-sourced this quarter?"
- "Show me the split between partner-sourced, influenced, and direct revenue"
- "Which countries source the most revenue through partners?"
- "Break down partner-sourced vs influenced revenue by partner"
- "How much of our FY27 revenue came from partner sourcing?"

### Risk Questions
- "Which deals are stalled?"
- "Show me high-risk deals below [PROBABILITY]%"
- "Which partners haven't had recent activity?"
- "Show me lost deals by partner/country"

### Sales Rep Questions
- "Show me [REP_NAME]'s revenue for [PERIOD]"
- "Break down [REP_NAME]'s revenue by country/partner"
- "Show me [REP_NAME]'s pipeline in [REGION]"
- "Which sales rep is top performer?"

### Regional Questions
- "Show me revenue for [SE/EE] this [PERIOD]"
- "Which region is growing faster?"
- "Compare [SE] vs [EE] performance"
- "Show me [REGION] top partners"

---

## Period Reference

Use these in prompts:
- "THIS_QUARTER" = Current fiscal quarter
- "THIS_FISCAL_YEAR" = Current fiscal year (Feb-Jan)
- "LAST_QUARTER" = Previous fiscal quarter
- "THIS_MONTH" = Current calendar month
- "FY27_Q3", "FY27_Q2", etc. = Specific quarters
- "THIS_WEEK" = Current week

---

## Breakdown Options

When asking for details, use these breakdowns:
- `breakdown="partner"` → By partner organization
- `breakdown="country"` → By geographic country
- `breakdown="stage"` → By deal stage (Prospecting, Qualification, etc.)
- `breakdown="quarter"` → By fiscal quarter
- `breakdown="total"` → Overall total only
- `region="SE"` → Southern Europe (Italy, Spain, Portugal, Greece, Cyprus, Malta)
- `region="EE"` → Eastern Europe (Poland, Czech Republic, Hungary, Slovakia, Romania, Bulgaria, Croatia, Serbia, Slovenia, Turkey)

---

## Common Parameters

- `period=` Time range for analysis
- `breakdown=` How to slice the data
- `region=` Geographic territory (SE or EE)
- `rep_name=` Specific sales rep
- `partner_name=` Specific partner
- `country=` Specific country
- `stage=` Deal stage
- `limit=` Number of results (default 20, max 100)
- `min_amount=` Minimum deal amount
- `max_amount=` Maximum deal amount
- `probability_threshold=` Minimum win probability %
- `days_threshold=` Days stalled threshold

---

## Tips for Best Results

1. **Be specific:** "Show me Q3 revenue" is better than "Show me revenue"
2. **Use exact names:** Partner names must match Salesforce exactly
3. **Combine tools:** Get overview first, then drill down
4. **Check multi-region reps:** Alessia Ashkenazi covers both SE and EE
5. **Use realistic forecasts:** Prefer `get_weighted_pipeline()` over raw pipeline for forecasting
6. **Monitor trends:** Use `get_multi_period_trend()` to spot patterns over time
7. **Check data quality:** Run `get_orphan_hygiene()` regularly
8. **Regional filters:** Remember SE covers 6 countries, EE covers 10 countries

