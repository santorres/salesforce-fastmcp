# Scaling Prioritization: Gap Analysis & Solution Design

**Goal:** Build "hallucination-proof" channel director analytics using available Salesforce data + external config
**Status:** Gap audit complete; ready for phased implementation
**Date:** 2026-05-18

---

## Section 1: QUOTA/TARGET MANAGEMENT

### Current State
- ❌ No quota fields in Salesforce (confirmed: not in schema)
- ✅ You cannot create custom fields in Salesforce
- 🟡 User input parameter workaround exists but you prefer structured config

### Proposed Solution: External Config File

**File:** `config/sales_targets.yaml`

```yaml
# Territory-based quotas
territories:
  South_Europe:
    countries:
      - Italy
      - Spain
      - Portugal
      - Greece
      - Cyprus
      - Malta
    revenue_target_fy27: 5000000
    revenue_target_fy26: 4500000
    
  # Add more territories as needed
  # Mediterranean:
  #   countries: [...]
  #   revenue_target_fy27: X

# Partner-based quotas (optional — supplements territory)
partners:
  Accenture:
    countries:
      - Spain
      - Italy
    revenue_target_fy27: 1200000
    revenue_target_fy26: 1000000
    
  Inetum_Spain:
    countries:
      - Spain
    revenue_target_fy27: 800000
    revenue_target_fy26: 700000
    
  # Add more partners as needed

# Account-level targets (if needed)
accounts:
  Telefonica:
    revenue_target_fy27: 300000
  Vodafone:
    revenue_target_fy27: 250000
```

### Implementation Steps

1. **Load config on server startup**
   - `ConfigManager` class in `channel_intelligence.py`
   - Load YAML on init, validate structure
   - Raise friendly errors if missing territories/partners

2. **Expose via tool parameter**
   - `get_revenue(period, territory=None, partner=None, account=None)`
   - If parameter provided, fetch target from config
   - Calculate attainment % automatically

3. **Fallback mechanism**
   - If tool called without target: return revenue + note "no target configured"
   - LLM can still answer "how are we tracking" but notes the missing baseline

### Example Tool Behavior

```python
# Before (current):
get_revenue("THIS_QUARTER", "partner=Inetum Spain")
# Returns: revenue_closed_won: 320000

# After (with config):
get_revenue("THIS_QUARTER", "partner=Inetum Spain")
# Returns: 
#   revenue_closed_won: 320000
#   target: 800000  (from config)
#   attainment_pct: 40.0%
#   gap: 480000
```

### Advantages
- ✅ No Salesforce changes needed
- ✅ Version-controllable (git history of quota changes)
- ✅ Easy to maintain (one file, structured)
- ✅ Team can update without SF admin access
- ✅ Supports multi-level targets (territory + partner + account)

### Maintenance
- Review quarterly when targets change
- Commit to git with context ("Q3 targets updated per leadership")
- Pull on server laptop before restarting MCP

---

## Section 2: ACTIVITY/ENGAGEMENT TRACKING

### Current State: What Salesforce Has

| Field | Available? | Currently Used? | Notes |
|-------|-----------|-----------------|-------|
| `LastModifiedDate` | ✅ YES (standard) | ✅ YES | Ordered by recency in `get_opportunity_list` |
| `LastActivityDate` | ❌ NO (custom field) | ❌ NO | Would need to add to Salesforce |
| `LastReferencedDate` | ✅ YES (standard) | ❌ NO | Tracks last time record was viewed/edited in Salesforce UI |
| Activity records (Task/Event) | ✅ YES (objects) | ❌ NO | Separate object; would need separate query |

### What We Can Do With Available Data

✅ **FULLY IMPLEMENTABLE RIGHT NOW:**

1. **Stalled deals detection** (already partially exists)
   - Use: `CreatedDate` + current date = days since creation
   - Tool: `get_stalled_deals(days_threshold=30, stage_filter=None)`
   - Returns: Opportunities not closed, older than threshold, grouped by stage
   - Example: "Show me deals created more than 30 days ago still in Prospecting"

2. **Recently modified deals** (activity proxy)
   - Use: `LastModifiedDate` + current date = days since last change
   - Tool: `get_recently_active_deals(days=7)`
   - Returns: Opportunities modified in last N days (someone is working them)
   - Proxy for: partner/manager is actively engaging

3. **Partner pipeline by recency**
   - Use: `LastModifiedDate` grouped by Partner__r.Name
   - Tool: `get_partner_activity(partner_name, include_recency=true)`
   - Returns: Pipeline amount + "last deal activity" date
   - Proxy for: "Who's been quiet? Who's active?"

⚠️ **PARTIAL WORKAROUND:**

4. **Deal not modified in X days** (imperfect proxy for "no contact")
   - Use: `LastModifiedDate` < (today - X days) AND IsClosed = false
   - Limitation: System updates (forecast adjustments) count as "activity"
   - Not the same as "no business contact" but close enough

### What We CANNOT Do Without Salesforce Custom Fields

❌ **REQUIRES CUSTOM FIELD: `LastActivityDate__c` or `LastContactDate__c`**
- True "last contact with partner" date (not system updates)
- Partner/Account activity (vs. opportunity-level only)
- Activities/tasks completion rate

### Recommended Phase 1 Implementation

Build these **three tools** using existing data:

```python
# Tool 1: Stalled deals (pipeline at risk)
get_stalled_deals(
    period: str = "THIS_QUARTER",
    days_without_update: int = 30,
    stage_filter: str = None  # e.g. "Prospecting", "Validation"
) → List[Opportunity] with age_days, last_modified_date

# Tool 2: Partner activity summary
get_partner_activity_summary(
    period: str = "THIS_QUARTER"
) → List[Partner] with:
  - open_pipeline_amount
  - deal_count
  - last_deal_modified_date  (proxy for "last we touched this partner")
  - days_since_last_activity
  - deals_modified_this_week
  - deals_modified_this_month

# Tool 3: Individual opportunity recency
get_opportunity_recency(
    opportunity_id: str or name_fragment: str
) → Opportunity with:
  - last_modified_date
  - days_since_modified
  - modification_history (last N modifications)
  - current_stage
  - days_in_current_stage (calculated)
```

### Data Gap Summary

| Question | With Available Data | With Custom Field |
|----------|-------------------|-------------------|
| "Which partners are most active?" | ✅ Proxy via deal modification rate | ✅ Direct via LastContactDate |
| "Who's gone quiet?" (past 60 days) | 🟡 Shows no deal updates but not true contact | ✅ Direct |
| "Why haven't we heard from Partner Y?" | 🟡 Shows last deal change, not contact attempts | ✅ Direct |
| "Activity level by month?" | ✅ Deal modification velocity | ✅ Contact activity velocity |

---

## Section 3: COMPETITIVE INTELLIGENCE

### Current State: What Salesforce Has

| Field | Available? | Currently Used? | Notes |
|-------|-----------|-----------------|-------|
| `Competitor__c` | ❌ NO (defined in prompts, not schema) | ❌ NO | Lookup field exists in prompts but NO data/queries |
| `Loss_Reason__c` | ❌ NO (defined in prompts, not schema) | ❌ NO | Picklist exists in prompts but NO data/queries |
| `Win_Reason__c` | ❌ NO (defined in prompts, not schema) | ❌ NO | Picklist exists in prompts but NO data/queries |
| `Type` | ✅ YES | ✅ YES | "New Business" vs "Renewal" — used in analysis |
| `IsClosed` + `IsWon` | ✅ YES | ✅ YES | Can identify lost deals |

### What We Can Do With Available Data

✅ **IMPLEMENTABLE RIGHT NOW:**

1. **Lost deals analysis** (limited but real)
   - Use: `IsClosed = true` AND `IsWon = false`
   - Tool: `get_lost_deals(period, by_stage=None, by_partner=None)`
   - Returns: Lost opportunity count + amount by stage/partner/country
   - What we learn: "Where are we losing?" (which stages, which partners lose most)
   - What we DON'T learn: "To whom?" (competitor names) or "Why?" (reasons)

2. **New vs. Existing business split**
   - Use: `Type` field (assuming "New Business" vs "Renewal" pattern)
   - Tool: `get_new_vs_existing(period, by_partner=None)`
   - Returns: Revenue/pipeline split by Type
   - What we learn: "Are we growing new logo pipeline or renewing existing?"

3. **Deal size by type**
   - Use: `Type` field
   - Tool: Already have this via `get_time_to_close_stats` (includes avg deal size)
   - Returns: Avg deal size for new vs renewal (proxy for product strategy)

❌ **REQUIRES CUSTOM FIELDS:**
- `Competitor__c` — Identify who we're losing to
- `Loss_Reason__c` — Why we lose (price? product? service?)
- `Product_Line__c` — Which products/solutions are winning
- `Vertical__c` or `Industry__c` — Which market segments are strongest

### Recommended Phase 1 Implementation

Build these **two tools** using existing data:

```python
# Tool 1: Lost deals analysis
get_lost_deals(
    period: str = "THIS_QUARTER",
    group_by: str = None  # "stage", "partner", "country"
) → Lost opportunity summary with:
  - total_lost_count
  - total_lost_amount
  - loss_rate_pct (lost / (lost + won))
  - grouping (by stage, partner, or country)
  - average_deal_size_lost

# Tool 2: New vs Existing business
get_new_vs_existing(
    period: str = "THIS_QUARTER",
    breakdown: str = None  # "partner", "country", "channel_manager"
) → Split with:
  - new_business_revenue
  - existing_business_revenue
  - new_business_pct
  - pipeline_new_vs_existing
  - trend (this quarter vs. last quarter)
```

### Data Gap Summary

| Question | With Available Data | With Custom Fields |
|----------|-------------------|------------------|
| "Who are we losing to?" | ❌ No data | ✅ Direct via Competitor__c |
| "Where do we lose most?" | ✅ By stage/partner | ✅ + Reason why |
| "What's selling best?" | 🟡 New vs existing split only | ✅ By product line + vertical |
| "Loss trends?" | ✅ Count + amount | ✅ + Reasons + Competitors |

---

## Section 4: STAGE VELOCITY & RISK SCORING

### Current State: What Salesforce Has

| Field | Available? | Currently Used? | Notes |
|-------|-----------|-----------------|-------|
| `StageName` | ✅ YES | ✅ YES | All stage queries group by this |
| `Probability` | ✅ YES | ✅ YES | Used for weighted pipeline |
| `CloseDate` | ✅ YES | ✅ YES | Pipeline forecasting, stalled deals |
| `CreatedDate` | ✅ YES | ✅ YES | Time-to-close calculation |
| `Days_In_Stage__c` | ❌ NO | ❌ NO | Custom field doesn't exist |

### What We Can Do With Available Data

✅ **FULLY IMPLEMENTABLE RIGHT NOW:**

1. **Stage distribution** (already have)
   - Use: `StageName` grouping
   - Tool: `get_pipeline(period, by_stage=true)`
   - Returns: $ and count by stage
   - What we learn: "Where is pipeline concentrated?"

2. **Stage risk via probability**
   - Use: `Probability` field + `StageName`
   - Tool: `get_stage_risk_profile(period)`
   - Returns: By stage — avg probability, count, total weighted $
   - What we learn: "Which stages have realistic deals? Which are inflated?"
   - Example: "Prospecting avg prob 25%, Negotiation avg prob 75%"

3. **Deal aging by stage**
   - Use: `CreatedDate` (or `LastModifiedDate`) + `StageName`
   - Tool: `get_deal_aging_by_stage(period, days_old_threshold=45)`
   - Returns: By stage — how many deals are > N days old?
   - What we learn: "Prospecting has 12 deals > 90 days old = bottleneck"

4. **High-risk deals** (multi-criteria)
   - Use: `Probability < X` AND `CloseDate < 30 days` AND `Amount > median`
   - Tool: `get_high_risk_deals(period, probability_threshold=40)`
   - Returns: Opportunities at risk (low probability + imminent close + large)
   - What we learn: "Deal ABC is likely to slip — it's high-value but low-prob and due soon"

5. **Deal velocity by stage** (historical average)
   - Use: For closed-won deals, calculate: (CloseDate - CreatedDate) / days, grouped by final stage
   - Tool: `get_stage_progression_velocity(period, lookback_periods=4)`
   - Returns: Historical average time in each stage (from past quarters)
   - What we learn: "Negotiation stage takes avg 45 days; deals stalled here for 60+ days are at risk"

⚠️ **PARTIAL/CALCULATED:**

6. **Forecast confidence** (weighted pipeline quality)
   - Use: `Probability` + `CloseDate` proximity
   - Tool: Already exists: `get_weighted_pipeline(period)` + Coverage ratio
   - Returns: Weighted $ vs Raw $ = quality indicator
   - What we learn: "Raw pipeline $10M but weighted only $4M = 60% deals are low-probability"

### What We CANNOT Do Without Salesforce Custom Fields

❌ **REQUIRES CUSTOM FIELD: `Days_In_Stage__c`**
- Accurate "how long in current stage?" (requires stage change timestamps)
- Historical stage-to-stage conversion rates (requires audit log of stage changes)
- Predictive risk: "Deals in Prospecting > 90 days have 20% lower close rate" (requires historical tracking)

### Recommended Phase 1 Implementation

Build these **four tools** using existing data:

```python
# Tool 1: Stage risk profile
get_stage_risk_profile(
    period: str = "THIS_QUARTER"
) → By stage:
  - total_pipeline_amount
  - deal_count
  - avg_probability_pct
  - weighted_pipeline
  - min_amount, max_amount, median_amount
  - confidence_level (high = avg_prob > 70%, low = < 40%)

# Tool 2: Deal aging by stage (bottleneck detection)
get_deal_aging_by_stage(
    period: str = "THIS_QUARTER",
    days_threshold: int = 45
) → By stage:
  - total_deals
  - deals_under_threshold
  - deals_over_threshold (aging/bottleneck indicators)
  - avg_age_days
  - oldest_deal_age_days

# Tool 3: High-risk deals (early warning)
get_high_risk_deals(
    period: str = "THIS_QUARTER",
    probability_threshold: int = 40  # e.g. "deals with < 40% prob"
) → Opportunity list with:
  - risk_score (combination of low_prob + close_date_proximity + size)
  - days_until_close
  - stage
  - amount
  - probability
  - recommendation (e.g., "Needs immediate attention: due in 21 days, only 35% prob")

# Tool 4: Historical stage velocity (forecast realism check)
get_stage_progression_velocity(
    period: str = "LAST_FISCAL_YEAR",
    lookback_periods: int = 4
) → By stage (from closed-won deals):
  - avg_days_in_stage
  - median_days_in_stage
  - deal_count (how many won deals passed through this stage)
  - current_deals_in_stage (from THIS_QUARTER)
  - aged_vs_historical (which ones are outliers?)
```

### Data Gap Summary

| Question | With Available Data | With `Days_In_Stage__c` |
|----------|-------------------|------------------------|
| "Where's the bottleneck?" | ✅ Deal count + age by stage | ✅ + exact days in stage |
| "Which deals are at risk?" | ✅ Low prob + imminent close | ✅ + aging detection |
| "Deal velocity realistic?" | ✅ Historical avg from closed deals | ✅ + real-time tracking |
| "Stage conversion rates?" | 🟡 Inferred from deal counts | ✅ Direct tracking |

---

## Implementation Roadmap

### PHASE 1 (Week 1-2): Available Data → Tools

**QUOTA/TARGETS:**
- [ ] Create `config/sales_targets.yaml` structure
- [ ] Add `ConfigManager` class to `channel_intelligence.py`
- [ ] Update `get_revenue()` to accept optional territory/partner + fetch target
- [ ] Add attainment % calculation

**ACTIVITY/ENGAGEMENT:**
- [ ] Tool: `get_stalled_deals()` (days without modification + stage)
- [ ] Tool: `get_partner_activity_summary()` (last deal activity proxy)
- [ ] Tool: `get_opportunity_recency()` (individual deal modifications)

**COMPETITIVE INTELLIGENCE:**
- [ ] Tool: `get_lost_deals()` (count/amount by stage/partner)
- [ ] Tool: `get_new_vs_existing()` (Type field breakdown)

**STAGE VELOCITY & RISK:**
- [ ] Tool: `get_stage_risk_profile()` (probability distribution by stage)
- [ ] Tool: `get_deal_aging_by_stage()` (bottleneck detection)
- [ ] Tool: `get_high_risk_deals()` (multi-criteria risk scoring)
- [ ] Tool: `get_stage_progression_velocity()` (historical velocity from closed deals)

**Total: 9 new tools + config system**

### PHASE 2 (Week 3+): Request Salesforce Custom Fields

Once Phase 1 is live and working:
- [ ] Document custom fields needed: `LastActivityDate__c`, `LastContactDate__c`, `Days_In_Stage__c`
- [ ] Provide Salesforce admin with field specs + import requirements
- [ ] Backfill historical data (where possible)
- [ ] Create tools that use these fields

### PHASE 3 (Later): Advanced Analytics

- Competitive tracking (`Competitor__c`, `Loss_Reason__c`)
- Product performance (`Product_Line__c`, `Vertical__c`)
- Advanced forecasting (stage conversion history)

---

## Decision Points for You

1. **Config file format:** YAML (proposed) or JSON or something else?
2. **Territory structure:** Multi-level (South_Europe → Italy, Spain, etc.) or flat (one target per country)?
3. **Partner-level targets:** Include in Phase 1 or Phase 2?
4. **Stalled deals threshold:** Default 30 days? Or make configurable per stage?
5. **Risk scoring algorithm:** Simple (prob < 40% + closing < 30 days) or complex?

---

## Next Steps

1. Review this document
2. Answer decision points above
3. Prioritize within Phase 1 (all 9 tools or start with subset?)
4. I'll start building — config loader first, then tools in priority order
