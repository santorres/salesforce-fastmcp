# Channel Director Questions → MCP Capability Map

**Status:** Assessment of 60+ channel director questions vs. current tool availability
**Date:** 2026-05-18
**Scale readiness:** ~70% of questions fully answerable; 20% partially; 10% require new tools

---

## Executive Summary

Your MCP has **strong pipeline, revenue, and partner analytics**. It can answer most "what happened" and "how are we tracking" questions with high accuracy. 

**Main gaps:**
1. **Territory/quota management** — no quota targets stored; can't calculate attainment %
2. **Account/customer segmentation** — no product line, vertical, or customer type fields
3. **Activity/engagement tracking** — no last-contact-date or activity log visibility
4. **Competitive intelligence** — no loss reasons, competitor tracking, or product performance by vertical
5. **Stage velocity & risk scoring** — no historical stage-to-stage conversion rates or deal aging metrics

---

## Category-by-Category Breakdown

### 🟢 PIPELINE & FORECAST HEALTH (4/6 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| How's our pipeline looking for Q3? Are we on track? | `get_pipeline`, `get_kpi_snapshot`, `get_weighted_pipeline` | ✅ FULL | Instant snapshot; shows coverage ratio vs. raw pipeline |
| Which deals are at risk of slipping? | `get_opportunity_list`, `salesforce_query` | 🟡 PARTIAL | Can list by stage + close date, but no "risk score" field; would need manual interpretation |
| What's our win rate this quarter vs. last quarter? | `get_revenue` (calc), `get_multi_period_trend` | ✅ FULL | Can calculate from closed-won count; multi-period trend shows trajectory |
| Why is Partner X's pipeline down 30%? | `get_growth` (by partner) | ✅ FULL | Direct period-over-period comparison |
| Can you show me deals closing in the next 30 days? | `get_opportunity_list` (filter by CloseDate) | ✅ FULL | Built-in close date filtering |

**Gap:** Risk-scoring by stage (needs: historical close rates by stage, probability field usage)

---

### 🟡 TERRITORY PERFORMANCE (1/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| How am I performing against my quota? | `get_revenue` + manual quota input | 🟡 PARTIAL | Revenue works; quota must be provided as parameter (not stored in SF) |
| Which territories are underperforming and why? | `get_revenue`, `get_pipeline` (by Country) | 🟡 PARTIAL | "Territory" != country; no Territory object in SF config; can only group by BillingCountry |
| How does my region stack up against other regions? | `get_revenue`, `get_pipeline` (by Country) | ✅ FULL | Country-level comparison works well |
| Why is Territory B only at 40% of target? | Requires quota targets | ❌ MISSING | No quota/target field in schema; manual workaround only |
| Which accounts should I focus on next week? | — | ❌ MISSING | No account scoring, priority, or engagement metrics |

**Gap:** Territory object (multi-country?) | Quota targets | Account prioritization engine

---

### 🟢 PARTNER HEALTH & ACTIVITY (2/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Which partners are most active? Who's gone quiet? | `get_top_partners` (by revenue/pipeline) | 🟡 PARTIAL | Can rank by revenue/pipeline; no last-activity date; would need custom "stalled partner" query |
| How much revenue is each partner bringing in? | `get_revenue` (by partner), `get_top_partners` | ✅ FULL | Direct read; `get_top_partners` shows top 10/bottom 10 |
| Which partners are growing vs. stagnant? | `get_growth`, `get_multi_period_trend` (by partner) | ✅ FULL | Period-over-period comparison |
| Why haven't we heard from Partner Y in 2 months? | — | ❌ MISSING | No activity log / last-contact-date visibility |
| Who should I invest time in right now? | — | ❌ MISSING | No engagement scoring or recommendation engine |

**Gap:** Partner activity tracking | Partner health score | Engagement recommendations

---

### 🟢 OPERATIONAL EFFICIENCY (2/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| What's our average deal size? Is it trending up or down? | `get_time_to_close_stats`, `get_multi_period_trend` | ✅ FULL | Avg size in stats; trend over periods visible |
| How long are deals taking to close? | `get_time_to_close_stats` | ✅ FULL | Avg/median/min/max; days from creation → close date |
| What's our biggest bottleneck in the sales process? | `get_pipeline` (by Stage), `salesforce_aggregate` | 🟡 PARTIAL | Can show $ by stage; no stage-velocity (days-in-stage) or conversion rate |
| Where are we losing deals in the pipeline? | `salesforce_query` (lost deals by stage) | 🟡 PARTIAL | Can query lost opportunities, but no built-in funnel analysis; need custom SOQL |
| What's the cost per win vs. our target? | — | ❌ MISSING | Salesforce has no cost data; would need external system (ERP/finance) |

**Gap:** Stage velocity metrics | Detailed loss analysis | Cost data integration

---

### 🔴 COMPETITIVE & MARKET INTEL (0/3 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Who are we losing to and why? | — | ❌ MISSING | No competitor field / loss reason in schema |
| What products/solutions are selling best? | — | ❌ MISSING | No product line field in opportunity schema |
| Where should I invest my team's effort? | — | ❌ MISSING | Requires product/vertical segmentation + opportunity scoring |

**Gap:** Competitive tracking | Loss reasons | Product/solution taxonomy | Vertical segmentation

---

### 🟢 QUANTITATIVE SNAPSHOTS (4/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Total pipeline by territory | `get_pipeline` (by Country) | ✅ FULL | Country-level; "territory" would need clarification |
| Revenue by territory YTD vs. quota | `get_revenue` + quota input | 🟡 PARTIAL | Revenue works; quota is manual parameter |
| Avg deal size, deal velocity, win rate by territory | `get_time_to_close_stats`, multi-period trend | ✅ FULL | Works by country |
| Pipeline by stage distribution | `get_pipeline` (by Stage) | ✅ FULL | Built-in aggregation |
| Partner contribution to revenue (top 10, bottom 10, inactive) | `get_top_partners`, `get_orphan_hygiene` | ✅ FULL | Top/bottom works; inactive = no open pipeline + no recent closures (custom query needed) |

---

### 🟢 TREND ANALYSIS (5/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Pipeline growth/decline MoM & QoQ | `get_multi_period_trend` | ✅ FULL | Up to 8 periods side-by-side |
| Win rate trends | Calculated from `get_revenue` / deal count | ✅ FULL | Can trend over periods |
| Avg deal cycle time trends | `get_time_to_close_stats` (per period) | ✅ FULL | Avg days to close, trended |
| Revenue by partner over time | `get_multi_period_trend` (by partner) | ✅ FULL | Partner-level trending |
| Quota attainment trends | Revenue trend + quota input | 🟡 PARTIAL | Revenue trends; quota is external |

---

### 🟡 RISK & OPPORTUNITY IDENTIFICATION (2/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Deals over X days old in each stage | `get_opportunity_list`, custom calc | 🟡 PARTIAL | Can list with creation date; need to compute age yourself |
| Opportunities with no activity in last 30 days | `get_opportunity_list` (LastActivityDate filter) | 🟡 PARTIAL | Tool exists (`get_orphan_hygiene` for deals w/o partner); not generalized for activity |
| Deals at high-risk stages | `salesforce_query` | 🟡 PARTIAL | Can filter by stage, but no "risk" indicator; need to infer from historical data |
| Partners with zero activity in 60+ days | — | ❌ MISSING | Would need LastActivityDate by partner |
| Deals significantly over/under avg deal size | `get_opportunity_list`, manual calc | 🟡 PARTIAL | Can list and compare to average; not built-in flagging |

**Gap:** Activity logging / last-activity-date visibility | Deal aging metrics | Risk scoring by stage

---

### 🟡 SEGMENTATION & DEEP DIVES (2/5 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Revenue by product line, customer type, vertical | — | ❌ MISSING | No product/vertical fields in schema |
| Win/loss analysis | `salesforce_query` (custom) | 🟡 PARTIAL | Can query won vs. lost; no automated trend analysis |
| Territory health score | `get_kpi_snapshot` (multi-metric) | 🟡 PARTIAL | Can build from revenue + pipeline + win rate; not a single KPI |
| Partner performance segmentation (A/B/C tiers) | `get_top_partners`, `get_multi_period_trend` | ✅ FULL | Can rank by revenue; A/B/C tier calculation is straightforward |
| Geographic or account-based breakdowns | `get_revenue`, `get_pipeline` (by Country/Account) | ✅ FULL | Country works perfectly; account-level less developed |

---

### 🟢 FORECASTING INPUTS (2/4 fully supported)

| Question | Tool(s) | Status | Notes |
|----------|---------|--------|-------|
| Weighted pipeline | `get_weighted_pipeline` | ✅ FULL | Amount × Probability; coverage ratio included |
| Deal velocity by stage | — | ❌ MISSING | Would need: how many deals move from stage A → B per week? |
| Historical close rates by stage | — | ❌ MISSING | Requires historical tracking of stage-to-stage conversion |
| Deals marked closing this quarter — realistic or inflated? | `get_opportunity_list`, compare to weighted | ✅ FULL | List close dates vs. weighted pipeline |

**Gap:** Stage-to-stage velocity metrics | Historical conversion rates by stage

---

## Summary: Tool Gaps

### 🔴 Critical gaps (blocking multiple questions):

1. **Quota/Target management**
   - No quota field in Salesforce schema
   - Workaround: Accept as input parameter
   - Fix: Add `Territory_Quota__c`, `Account_Target__c` custom field

2. **Activity/Engagement tracking**
   - No last-contact-date or activity log
   - Impacts: "Who's gone quiet?", "why haven't we heard from Partner Y?"
   - Fix: Track `LastActivityDate__c`, `DaysWithoutActivity__c` in Partner/Account object

3. **Competitive intelligence**
   - No loss reason, competitor field, or product line in opportunities
   - Impacts: 3/3 competitive questions
   - Fix: Add `Loss_Reason__c`, `Competitor__c`, `Product_Line__c` to Opportunity

4. **Stage velocity & risk**
   - No stage-duration, conversion rates, or risk scoring
   - Impacts: bottleneck analysis, deal aging, risk identification
   - Fix: Add `Days_In_Stage__c`, calculate historical conversion rates, implement risk scoring

### 🟡 Medium gaps (elegant workarounds exist):

5. **Territory management**
   - No Territory object; only country-level aggregation
   - Workaround: Use country, or map countries to sales territories in a lookup
   - Fix: Define Territory object or add `Territory__c` lookup field

6. **Account/partner prioritization**
   - No account scoring or engagement metrics
   - Workaround: LLM can suggest based on growth + pipeline + activity
   - Fix: Add `Account_Priority_Score__c`, `Health_Status__c`

7. **Product/vertical segmentation**
   - No product line in schema
   - Workaround: Use account type or industry
   - Fix: Add `Product_Line__c`, `Vertical__c`, `Industry__c`

---

## Recommendations for Scaling to "Hallucination-Proof"

### Phase 1: Quick wins (1-2 weeks)
- ✅ Already done: Revenue, pipeline, win rate, partner leaderboards, multi-period trends
- Add: `get_partner_activity` tool → Last activity, days quiet, engagement health
- Add: `get_stalled_deals` tool → Deals by age + stage, with aging days
- Add: Custom quota/target input to `get_revenue` for attainment %

### Phase 2: Core data enrichment (2-3 weeks)
- Add Salesforce custom fields: `Loss_Reason__c`, `LastActivityDate__c`, `Days_In_Stage__c`
- Add: `get_risk_deals` tool → High-risk stage detection, aging, probability < threshold
- Add: `get_stage_velocity` tool → How many deals move per week by stage
- Add: Territory/region mapping (whether object or calculation)

### Phase 3: Intelligence layer (3-4 weeks)
- Add: `get_partner_health_score` → Composite metric (revenue + growth + activity + pipeline)
- Add: `get_territory_health_score` → Quota attainment + pipeline coverage + win rate
- Add: `get_competitive_lost_deals` → Loss reasons, competitor tracking
- Add: `get_product_performance` → Revenue by product/vertical, if data exists

### Phase 4: Forecasting & recommendations (ongoing)
- Add: `forecast_next_quarter` → Weighted pipeline + historical close rates by stage
- Add: `get_partner_recommendations` → Who to invest in (growth + activity + pipeline)
- Add: `get_account_recommendations` → Which accounts to prioritize

---

## How to Make Each Question "Hallucination-Proof"

For **every** question you want to ask reliably:

1. **Does a tool exist to answer it directly?**
   - If yes: Use it. No hallucination risk.
   - If no: Go to step 2.

2. **Can the answer be calculated from existing tools + known Salesforce fields?**
   - If yes: Write a custom MCP tool that combines them. Returns structured data.
   - If no: Go to step 3.

3. **Is the data not in Salesforce at all?**
   - If data is external (cost, competitor names): Mark as "not available in this MCP"
   - If data *should* be in SF but isn't: Add custom field, then create tool.

4. **Is the data too ambiguous for an LLM to infer?**
   - Example: "Which partners should I invest in?" — needs explicit scoring.
   - Fix: Create a tool with a scoring algorithm, return ranked list + reasoning.

---

## Recommended Next Steps

1. **Pick your top 10 questions** from the list above
2. **For each, confirm:** Which status category (✅/🟡/❌)?
3. **For 🟡 & ❌ questions:**
   - Clarify what data is missing
   - Decide: Add SF custom field? Or create a tool that calculates it?
4. **Build Phase 1 tools** (activity, stalled deals, quota attainment)
5. **Test with real prompts** — does LLM ask follow-ups, or does it have enough data?

Want me to start building the Phase 1 tools?
