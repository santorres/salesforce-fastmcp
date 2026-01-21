# Channel Director Prompts Playbook

This document describes the **14 FastMCP prompts** available in the Salesforce Connector for Channel Director workflows.

**Role:** Channel Director (Portugal, Spain, Italy, Greece, Cyprus)
**Fiscal Year FY27:** Feb 1, 2026 – Jan 31, 2027

---

## Quick Reference

| # | Prompt Name | Purpose | Key Parameters |
|---|-------------|---------|----------------|
| 1 | `quarterly_pipeline` | Open pipeline by quarter | `quarter` |
| 2 | `closed_won_partners` | Partner contribution to revenue | `quarter`, `full_year` |
| 3 | `partner_health` | Partner engagement gaps | - |
| 4 | `partner_sourced` | Top partner-sourced deals | `limit` |
| 5 | `at_risk_pipeline` | Late stage + low probability | - |
| 6 | `new_vs_existing` | Business type mix | `quarter` |
| 7 | `lead_conversion` | Lead funnel analysis | - |
| 8 | `stalled_deals` | Inactive opportunities | `days_stalled` |
| 9 | `country_dashboard` | Regional scorecard | `quarter` |
| 10 | `forecast_vs_actuals` | Forecast accuracy | `quarter` |
| 11 | `partner_scorecard` | Partner performance | `partner_name` |
| 12 | `weekly_briefing` | Weekly overview | - |
| 13 | `partner_qbr` | QBR preparation | `partner_name`, `quarter` |
| 14 | `competitive_analysis` | Win/loss vs competitors | `competitor` |

---

## Configuration

### Fiscal Year FY27

| Quarter | Start Date | End Date |
|---------|------------|----------|
| Q1 | Feb 1, 2026 | Apr 30, 2026 |
| Q2 | May 1, 2026 | Jul 31, 2026 |
| Q3 | Aug 1, 2026 | Oct 31, 2026 |
| Q4 | Nov 1, 2026 | Jan 31, 2027 |

### Region Coverage

- Portugal
- Spain
- Italy
- Greece
- Cyprus

### Key Salesforce Fields

**Opportunity Partner Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `Partner__c` | Lookup (Account) | **Primary partner account** - use Account ID to filter |
| `Partner__r.Name` | Reference | Partner account name (use in SELECT) |
| `Partner_Source_Influence__c` | Picklist | Deal type: Source / Influence / Fulfillment |
| `Primary_Partner__c` | Picklist | Partner TYPE (Reseller/Referral) - NOT the partner name |
| `Primary_Partner_Total__c` | Currency | Partner's total contract value |
| `Partner_Reseller_Percentage__c` | Percent | Partner Year 1 revenue share % |
| `Channel_Manager__c` | Lookup | Assigned channel manager |
| `Stage_Detail__c` | Text | Custom stage detail field |

**Important:** `Partner__c` is a **lookup field**, not a text field. To query by partner:
1. First find the partner's Account ID using `salesforce_find_partner` tool
2. Then filter: `WHERE Partner__c = '<account_id>'`
3. Display name with: `Partner__r.Name` in SELECT clause

**Lead Fields:**
- `Lead_Source_Attribution__c` - Partner attribution on leads
- `Lead_Source_Detail__c` - Detailed lead source
- `Lead_Source_Sub_Detail__c` - Sub-detail for lead source
- `Activity_Stage__c` - Lead activity stage
- `Type__c` - Lead type

---

## Prompt Details

### 1. Quarterly Pipeline Analysis

**Prompt:** `quarterly_pipeline`
**Tags:** `pipeline`, `quarterly`, `channel-director`

**Purpose:** Analyze all open opportunities for a specific fiscal quarter with full partner and country breakdown.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quarter` | string | `"Q1"` | Fiscal quarter (Q1, Q2, Q3, Q4) |

**Analysis Includes:**
- Pipeline by country (value & count)
- Partner vs non-partner coverage
- Top 5 deals by value
- Stage distribution
- Partner Source vs Influence breakdown

**Example Usage:**
```
"Run the quarterly_pipeline prompt for Q2"
"Show me Q3 pipeline analysis"
```

---

### 2. Closed-Won Partner Contribution

**Prompt:** `closed_won_partners`
**Tags:** `revenue`, `partners`, `channel-director`

**Purpose:** Analyze closed-won revenue with partner contribution breakdown (Source vs Influence vs Fulfillment).

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quarter` | string | `""` | Specific quarter or empty for full year |
| `full_year` | boolean | `true` | Analyze full FY27 |

**Analysis Includes:**
- Total closed-won revenue
- Partner contribution by type (Source/Influence/Fulfillment)
- Top 10 partners by contract value
- Partner share of total revenue
- Country performance with partner %

**Example Usage:**
```
"Show closed-won partner analysis for the full year"
"What's the partner contribution for Q1?"
```

---

### 3. Partner Engagement Health Check

**Prompt:** `partner_health`
**Tags:** `partners`, `engagement`, `channel-director`

**Purpose:** Audit partner engagement health across all active opportunities, identifying gaps and late-stage alerts.

**Parameters:** None

**Analysis Includes:**
- Partner engagement % by country
- High-value opportunities (>€100K) with NO partner
- Late-stage alerts (Negotiation/Contracts without partner)
- Accounts with multiple opportunities lacking partner coverage

**Example Usage:**
```
"Run partner health check"
"Show me partner engagement gaps"
```

---

### 4. Partner-Sourced Pipeline

**Prompt:** `partner_sourced`
**Tags:** `partners`, `sourcing`, `channel-director`

**Purpose:** Identify top partner-sourced opportunities where the partner originated the deal.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | `10` | Number of top deals to show |

**Analysis Includes:**
- Top N sourced deals (Amount, Partner, Stage, Close Date)
- Source vs Influence vs Fulfillment pipeline split
- Partner leaderboard by sourced pipeline
- Average partner revenue share %
- Stage health of sourced deals

**Example Usage:**
```
"Show top 20 partner-sourced deals"
"Which partners source the most pipeline?"
```

---

### 5. At-Risk Pipeline Analysis

**Prompt:** `at_risk_pipeline`
**Tags:** `risk`, `pipeline`, `channel-director`

**Purpose:** Identify at-risk opportunities that are in late stages but have low probability.

**Parameters:** None

**Criteria:**
- Stage: Contracts, Submitted to Finance, or Negotiation
- Probability < 50%

**Analysis Includes:**
- Risk summary (count, value, avg probability)
- Risk detail table with all flagged deals
- Partner factor analysis (do partners improve outcomes?)
- Overdue deals (past close date)
- Action recommendations by priority

**Alert Levels:**
- 🔴 >€500K at risk
- 🟡 €100K-500K at risk
- 🟢 <€100K at risk

**Example Usage:**
```
"Show me at-risk pipeline"
"What deals are in trouble?"
```

---

### 6. New vs Existing Business

**Prompt:** `new_vs_existing`
**Tags:** `pipeline`, `business-type`, `channel-director`

**Purpose:** Analyze pipeline split between new business, existing business, and operational deals.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quarter` | string | `""` | Specific quarter or empty for full year |

**Analysis Includes:**
- Business mix overview (count, value, avg deal size)
- Partner coverage by business type
- Country × Type matrix
- Partner-sourced new business (pure partner wins)
- Strategic insights on partner channel effectiveness

**Example Usage:**
```
"Break down new vs existing business"
"Is our partner channel driving new logos?"
```

---

### 7. Lead Conversion Analysis

**Prompt:** `lead_conversion`
**Tags:** `leads`, `conversion`, `channel-director`

**Purpose:** Analyze the lead funnel with conversion rates and partner attribution tracking.

**Parameters:** None

**Analysis Includes:**
- Funnel overview (open/converted/disqualified)
- Conversion rates by country and lead source
- Partner attribution analysis
- Lead source breakdown with conversion rates
- Activity stage distribution and bottlenecks

**Example Usage:**
```
"Analyze lead conversion funnel"
"Which lead sources convert best?"
```

---

### 8. Stalled Opportunities

**Prompt:** `stalled_deals`
**Tags:** `risk`, `pipeline`, `channel-director`

**Purpose:** Identify opportunities that haven't had any activity in a specified number of days.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days_stalled` | integer | `60` | Days without activity to flag as stalled |

**Analysis Includes:**
- Stalled pipeline summary (count, value, % of total)
- Stalled deals table with last modified date
- Partner impact (do partnered deals stall less?)
- Stage distribution of stalled deals
- Owner analysis (who has most stalled pipeline?)
- Country view

**Example Usage:**
```
"Find opportunities stalled for 30 days"
"Show me deals with no activity in 90 days"
```

---

### 9. Country-Level Dashboard

**Prompt:** `country_dashboard`
**Tags:** `dashboard`, `regional`, `channel-director`

**Purpose:** Generate a comprehensive country-level pipeline dashboard.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quarter` | string | `""` | Specific quarter or empty for full year |

**Analysis Includes:**
- Executive summary by country (value, count, avg deal size)
- Partner coverage matrix with color coding:
  - 🟢 >50% partner coverage
  - 🟡 30-50% partner coverage
  - 🔴 <30% partner coverage
- Stage health by country
- Top 3 deals per country
- Partner source analysis by country
- Risk flags (declining pipeline, low engagement, concentration risk)

**Example Usage:**
```
"Generate country dashboard for Q2"
"Show me regional pipeline scorecard"
```

---

### 10. Forecast vs Actuals

**Prompt:** `forecast_vs_actuals`
**Tags:** `forecast`, `quarterly`, `channel-director`

**Purpose:** Compare weighted pipeline forecast against actual closed revenue for a quarter.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quarter` | string | `"Q1"` | Fiscal quarter (Q1, Q2, Q3, Q4) |

**Analysis Includes:**
- Forecast summary (pipeline, weighted forecast, closed-won, closed-lost)
- Forecast accuracy calculation
- Partner contribution to actuals (Sourced/Influenced/Direct)
- Country forecast accuracy
- Stage conversion analysis
- Lessons learned (surprise wins, unexpected losses)

**Example Usage:**
```
"Compare Q1 forecast vs actuals"
"How accurate was our Q3 forecast?"
```

---

### 11. Partner Performance Scorecard

**Prompt:** `partner_scorecard`
**Tags:** `partners`, `performance`, `channel-director`

**Purpose:** Generate a performance scorecard for a specific partner or all partners.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `partner_name` | string | `""` | Specific partner or empty for all |

**Analysis Includes:**
- Partner leaderboard (pipeline, won revenue, win rate, sourced %)
- Individual partner cards (top 10):
  - Pipeline value
  - Closed-won value
  - Number of opportunities
  - Avg deal size
  - Source vs Influence ratio
  - Countries covered
- Partner tier analysis:
  - Tier 1: >€1M pipeline
  - Tier 2: €250K-1M
  - Tier 3: <€250K
- Engagement gaps
- Strategic recommendations

**Example Usage:**
```
"Show partner scorecard for Acme Partners"
"Generate partner leaderboard"
```

---

### 12. Weekly Briefing

**Prompt:** `weekly_briefing`
**Tags:** `briefing`, `weekly`, `channel-director`

**Purpose:** Generate a concise weekly briefing covering key metrics and action items.

**Parameters:** None

**Sections:**
- 📊 Executive Summary (pipeline value, closed-won/lost, net change)
- 🎯 This Week's Wins (with partner contribution)
- ⚠️ This Week's Losses (with partner notes)
- 📅 Next Week Outlook (deals closing, expected value)
- 🚨 Attention Required (high-value deals, stalled opps, partner gaps)

**Design:** Readable in 2 minutes

**Example Usage:**
```
"Generate my weekly briefing"
"What happened this week?"
```

---

### 13. Partner QBR Preparation

**Prompt:** `partner_qbr`
**Tags:** `partners`, `qbr`, `channel-director`

**Purpose:** Prepare comprehensive data for a Quarterly Business Review with a specific partner.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `partner_name` | string | **required** | Partner name for QBR |
| `quarter` | string | `"Q1"` | Fiscal quarter |

**Sections:**
- 📈 Performance Summary (quarterly & YTD)
- 🎯 Deal Review (closed deals, open pipeline, at-risk)
- 🌍 Geographic Coverage (by country, whitespace)
- 💡 Source vs Influence Analysis
- ⚡ Action Items for Discussion
- 📊 Next Quarter Targets

**Example Usage:**
```
"Prepare QBR data for TechCorp for Q2"
"I have a QBR with GlobalPartners next week, prepare the data"
```

---

### 14. Competitive Analysis

**Prompt:** `competitive_analysis`
**Tags:** `competitive`, `win-loss`, `channel-director`

**Purpose:** Analyze deals where competitors are involved, with win/loss patterns.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `competitor` | string | `""` | Specific competitor or empty for all |

**Analysis Includes:**
- Competitive overview (deals, value, win rate)
- Win/Loss breakdown
- Partner impact on competitive deals
- Loss analysis (top reasons, patterns)
- Win patterns (successful strategies)
- Recommendations

**Example Usage:**
```
"Analyze competitive deals against CompetitorX"
"How do we perform in competitive situations?"
```

---

## Tags Reference

Use tags to filter prompts by category:

| Tag | Prompts |
|-----|---------|
| `pipeline` | quarterly_pipeline, at_risk_pipeline, new_vs_existing, stalled_deals |
| `partners` | closed_won_partners, partner_health, partner_sourced, partner_scorecard, partner_qbr |
| `quarterly` | quarterly_pipeline, forecast_vs_actuals |
| `risk` | at_risk_pipeline, stalled_deals |
| `channel-director` | All prompts |
| `revenue` | closed_won_partners |
| `engagement` | partner_health |
| `sourcing` | partner_sourced |
| `business-type` | new_vs_existing |
| `leads` | lead_conversion |
| `conversion` | lead_conversion |
| `dashboard` | country_dashboard |
| `regional` | country_dashboard |
| `forecast` | forecast_vs_actuals |
| `performance` | partner_scorecard |
| `briefing` | weekly_briefing |
| `weekly` | weekly_briefing |
| `qbr` | partner_qbr |
| `competitive` | competitive_analysis |
| `win-loss` | competitive_analysis |

---

## Workflow Recommendations

### Daily
- `weekly_briefing` - Start each day with quick overview

### Weekly
- `weekly_briefing` - Full weekly review
- `at_risk_pipeline` - Check deals needing attention
- `stalled_deals` - Follow up on inactive opportunities

### Monthly
- `country_dashboard` - Regional performance review
- `partner_health` - Partner engagement audit
- `partner_scorecard` - Partner performance tracking

### Quarterly
- `quarterly_pipeline` - Quarter opening/closing review
- `forecast_vs_actuals` - Forecast accuracy analysis
- `partner_qbr` - Partner QBR preparation
- `closed_won_partners` - Revenue attribution review

### Ad-Hoc
- `partner_sourced` - When evaluating partner contributions
- `competitive_analysis` - Before competitive deals or strategy sessions
- `lead_conversion` - Marketing/demand gen reviews
- `new_vs_existing` - Business mix analysis

---

---

## Helper Tools

Two additional tools were added to support the prompts:

### salesforce_find_partner

**Purpose:** Find a partner account by name and return its ID for use in queries.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search_term` | string | Partner name to search (e.g., "Adaptit") |

**Returns:**
- Account ID, name, country, type, partner status
- Ready-to-use filter: `Partner__c = '<id>'`

**Example:**
```
salesforce_find_partner("Adaptit")
→ Returns: Account ID 001Pb00001zmRLgIAM for "ADAPTIT S.A. (Partner)"
```

### salesforce_describe_fields

**Purpose:** Get field metadata with optional filtering (avoids token limits on large objects).

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `object_name` | string | Salesforce object (e.g., "Opportunity") |
| `field_filter` | string | Filter fields by name pattern (e.g., "partner") |
| `field_types` | list | Filter by types (e.g., ["reference", "picklist"]) |

**Example:**
```
salesforce_describe_fields("Opportunity", field_filter="partner")
→ Returns only fields with "partner" in the name
```

**Why this helps:** The full `salesforce_describe` for Opportunity returns ~1M characters, exceeding token limits. This filtered version returns only what you need.

---

## Customization

To modify the region, fiscal year, or field mappings, edit the constants in `prompts.py`:

```python
# Change countries
COUNTRIES = ["Portugal", "Spain", "Italy", "Greece", "Cyprus"]
COUNTRIES_SQL = "('Spain','Portugal','Italy','Greece','Cyprus')"

# Change fiscal year
FY27_START = "2026-02-01"
FY27_END = "2027-01-31"

# Change quarters
QUARTERS = {
    "Q1": ("2026-02-01", "2026-04-30"),
    "Q2": ("2026-05-01", "2026-07-31"),
    "Q3": ("2026-08-01", "2026-10-31"),
    "Q4": ("2026-11-01", "2027-01-31"),
}
```
