# MCP Tools Reference - Tool Registry

**Version:** 2.2 | **Updated:** June 21, 2026 | **Multi-Region Support:** ✅ | **Mode-based Tool Loading:** ✅

Complete reference for MCP (Model Context Protocol) tools in the Salesforce FastMCP server with BASIC and ADVANCED mode support.

## 🔧 Tool Availability by Mode

| Mode | Tools | Description |
|------|-------|-------------|
| **BASIC** (default) | 48 | Domain-specific analytics & intelligence tools only (deterministic, no raw SOQL) |
| **ADVANCED** | 60 | BASIC + 12 Salesforce Data Access tools (raw SOQL, metadata access) |

**Default:** `BASIC` mode (recommended for production)  
**How to enable ADVANCED:**
```bash
export MCP_USAGE_MODE=advanced
# or set in config/ci_config.py: MCP_USAGE_MODE = "advanced"
```

**LangSmith Integration Ready:** When you add LangSmith observability, it will log which mode was active and which tools were called, enabling data-driven decisions on tool usage patterns.

---

## Quick Navigation

### BASIC Mode (50 tools - Always Available)
- [Channel Intelligence (21 tools)](#channel-intelligence-21-tools)
- [Risk Management (10 tools)](#risk-management-10-tools)
- [Sales Rep Analytics (7 tools) ⭐ Multi-Region Support](#sales-rep-analytics-7-tools--new)
- [Deal Registrations (5 tools)](#deal-registrations-5-tools)
- [Win Rate & Performance (3 tools)](#win-rate--performance-3-tools)
- [Utility & Config (4 tools)](#utility--config-4-tools)

### ADVANCED Mode (Additional 12 tools - Opt-in)
- [Salesforce Data Access (12 tools) 🔓 ADVANCED ONLY](#salesforce-data-access-12-tools--advanced-mode-only)

---

## Channel Intelligence (21 tools)

Core revenue, pipeline, and partner analytics.

### `get_kpi_snapshot`
**Purpose:** Get KPI snapshot  
**Returns:** Revenue, pipeline, win rate, coverage %  
**Use case:** Daily standup, executive summary  
**Parameters:** `period`, `channel_manager`

### `get_revenue`
**Purpose:** Revenue by period with optional breakdown  
**Returns:** Total revenue, deal count, breakdown by partner/country/quarter  
**Use case:** Revenue tracking, attainment analysis  
**Parameters:** `period`, `breakdown` (partner/country/quarter/total), `limit`

### `get_pipeline`
**Purpose:** Open pipeline by period with optional breakdown and region filtering  
**Returns:** Pipeline amount, deal count, breakdown, region (if filtered)  
**Use case:** Forecast, pipeline health, regional analysis  
**Parameters:** `period`, `breakdown` (stage/country/partner/total), `limit`, `region` (SE/EE/all - optional), `country` (optional), `partner_name` (optional)

### `get_top_partners`
**Purpose:** Top N partners ranked by revenue or pipeline  
**Returns:** Partner name, amount, deal count, rank  
**Use case:** Partner performance, partner meetings  
**Parameters:** `period`, `metric` (revenue/pipeline), `limit`

### `get_partner_detail`
**Purpose:** Partner scorecard with revenue, pipeline, forecast  
**Returns:** Full partner metrics and activity  
**Use case:** Partner reviews, account planning  
**Parameters:** `partner_name`, `period`, `channel_manager`

### `get_partner_pipeline`
**Purpose:** Partner's open pipeline deals  
**Returns:** Deal names, amounts, stages, close dates  
**Use case:** Partner pipeline review  
**Parameters:** `partner_name`, `period`, `limit`, `channel_manager`

### `get_partner_scorecard`
**Purpose:** Full partner scorecard with metrics and trends  
**Returns:** Revenue, pipeline, growth, win rate, activity  
**Use case:** Quarterly partner reviews  
**Parameters:** `partner_name`, `period`, `channel_manager`

### `generate_partner_qbr`
**Purpose:** Generate complete partner QBR markdown report  
**Returns:** Formatted markdown report with all metrics  
**Use case:** QBR preparation  
**Parameters:** `partner_name`, `period`

### `get_growth`
**Purpose:** Period-over-period growth comparison  
**Returns:** Revenue/pipeline growth %, absolute change  
**Use case:** Growth analysis, trend tracking  
**Parameters:** `metric` (revenue/pipeline), `period_a`, `period_b`

### `get_multi_period_trend`
**Purpose:** Multi-period trend (8-quarter historical analysis)  
**Returns:** Historical data for multiple periods  
**Use case:** Long-term trend analysis, trajectory assessment  
**Parameters:** `metric` (revenue/pipeline), `periods` (list of periods)

### `get_new_vs_existing`
**Purpose:** New business vs renewal/expansion breakdown  
**Returns:** New revenue, renewal revenue, expansion revenue  
**Use case:** Mix analysis, revenue composition  
**Parameters:** `period`, `breakdown` (partner/country/total)

### `get_partner_sourced_influenced_revenue` ⭐ NEW
**Purpose:** Partner sourcing attribution — revenue by deal type (Source/Influence/Fulfillment/Direct)  
**Returns:** Revenue breakdown with percentages: sourced %, influenced %, fulfillment %, direct %  
**Use case:** Partner contribution analysis, channel performance assessment  
**Parameters:** `period`, `breakdown` (country/partner/total), `channel_manager` (optional)  
**Example:** "What percentage of revenue was partner-sourced this quarter?"

### `get_weighted_pipeline`
**Purpose:** Pipeline weighted by probability for realistic forecast  
**Returns:** Weighted pipeline amount, probability distribution  
**Use case:** Realistic forecasting, risk-adjusted pipeline  
**Parameters:** `period`, `breakdown` (optional)

### `get_channel_manager_performance`
**Purpose:** Performance metrics by channel manager  
**Returns:** Manager performance, territory metrics  
**Use case:** Team management, manager accountability  
**Parameters:** `period`, `metric` (revenue/pipeline)

### `get_opportunity_recency`
**Purpose:** Track deal activity - recently touched deals  
**Returns:** Deals by last activity date  
**Use case:** Activity tracking, engagement monitoring  
**Parameters:** `period`, `limit`

### `get_partner_activity_summary`
**Purpose:** Per-partner: pipeline, deals, last activity date  
**Returns:** Partner metrics with activity timestamp  
**Use case:** Partner engagement assessment  
**Parameters:** `period`

### `search_opportunities`
**Purpose:** Search opportunities by keyword/deal name  
**Returns:** Matching opportunities with details  
**Use case:** Deal lookup, keyword search  
**Parameters:** `query`, `period`, `stage` (optional)

### `salesforce_opportunities_by_partner`
**Purpose:** Opportunities grouped by partner  
**Returns:** Opportunities with partner grouping  
**Use case:** Partner drill-down  
**Parameters:** `period`, `limit`

### `salesforce_pipeline`
**Purpose:** Pipeline opportunities for forecasting  
**Returns:** Pipeline deals grouped  
**Use case:** Forecasting, pipeline visualization  
**Parameters:** `period`, `limit`

### `salesforce_lead_funnel`
**Purpose:** Lead-to-opportunity conversion funnel  
**Returns:** Funnel metrics  
**Use case:** Lead quality analysis  
**Parameters:** `period`

### `salesforce_trend_analysis`
**Purpose:** Historical trend analysis across periods  
**Returns:** Trend data and metrics  
**Use case:** Historical analysis, trend visualization  
**Parameters:** `periods` (list)

---

## Risk Management (10 tools)

Deal health, aging, stalling, and risk detection.

### `get_high_risk_deals`
**Purpose:** High-risk deals (<40% probability, closing in 30 days)  
**Returns:** High-risk deal list with details  
**Use case:** Risk mitigation, deal intervention  
**Parameters:** `period`, `probability_threshold`, `days_to_close`

### `get_stalled_deals`
**Purpose:** Stalled deals (untouched 60+ days by stage)  
**Returns:** Stalled deal list grouped by stage  
**Use case:** Pipeline hygiene, deal qualification  
**Parameters:** `period`, `days_threshold`

### `get_deal_aging_by_stage`
**Purpose:** Deal aging (avg days per stage and distribution)  
**Returns:** Aging metrics by stage, distribution  
**Use case:** Bottleneck detection, velocity assessment  
**Parameters:** `period`, `days_threshold`

### `get_stage_progression_velocity`
**Purpose:** Historical velocity (avg days/stage vs current)  
**Returns:** Historical velocity vs current deals aging  
**Use case:** Velocity benchmarking, slowdown detection  
**Parameters:** `lookback_period`

### `get_stage_risk_profile`
**Purpose:** Risk profile by stage (count, value, composition)  
**Returns:** Risk metrics by stage  
**Use case:** Stage-specific risk assessment  
**Parameters:** `period`

### `get_time_to_close_stats`
**Purpose:** Time-to-close statistics by stage/partner  
**Returns:** Close time metrics  
**Use case:** Close cycle analysis  
**Parameters:** `period`

### `get_lost_deals`
**Purpose:** Lost deals (count, amount, stage, reason)  
**Returns:** Lost deal analysis  
**Use case:** Win/loss analysis, competitive intelligence  
**Parameters:** `period`, `group_by` (stage/partner/reason)

### `get_opportunity_detail`
**Purpose:** Single opportunity full details  
**Returns:** Complete opportunity record  
**Use case:** Deal deep-dive  
**Parameters:** `opportunity_id`

### `get_opportunity_list`
**Purpose:** List opportunities with filtering  
**Returns:** Opportunity list with optional filters  
**Use case:** Opportunity browsing  
**Parameters:** `period`, `partner`, `country`, `stage`, `min_amount`, `limit`

### `get_orphan_hygiene`
**Purpose:** Deals with missing partner assignments  
**Returns:** Orphan deal list  
**Use case:** Data quality, deal assignment  
**Parameters:** `period`

---

## Sales Rep Analytics (7 tools) ⭐ NEW

Sales rep performance with **NEW multi-region filtering for SE/EE territories**.

### `get_revenue_by_sales_rep`
**Purpose:** Revenue aggregated by sales rep  
**NEW:** Regional filtering support  
**Returns:** Revenue by rep, deal count, avg deal size  
**Use case:** Rep performance, territory management  
**Parameters:** `period`, `metric` (revenue/pipeline), `limit`, **`region` (SE/EE/all)** ⭐

### `get_revenue_by_sales_rep_by_country`
**Purpose:** Revenue by rep, breakdown by country  
**Returns:** Per-rep, per-country revenue  
**Use case:** Geographic performance per rep  
**Parameters:** `period`, `country`, `metric`, `limit`

### `get_revenue_by_sales_rep_by_partner`
**Purpose:** Revenue by rep, breakdown by partner  
**Returns:** Per-rep, per-partner revenue  
**Use case:** Partner-rep alignment  
**Parameters:** `period`, `partner`, `metric`, `limit`

### `get_closed_deals_by_sales_rep`
**Purpose:** Closed deals by rep with deal details  
**NEW:** Regional filtering support  
**Returns:** Closed deals grouped by rep  
**Use case:** Rep productivity, deal tracking  
**Parameters:** `period`, `sales_rep`, **`region` (SE/EE/all)** ⭐, `limit`

### `get_pipeline_deals_by_sales_rep`
**Purpose:** Pipeline deals by rep with forecast  
**NEW:** Regional filtering support  
**Returns:** Pipeline deals grouped by rep with probability  
**Use case:** Rep pipeline, forecast accuracy  
**Parameters:** `period`, `sales_rep`, **`region` (SE/EE/all)** ⭐, `limit`

### `get_sales_rep_regions` ⭐ NEW
**Purpose:** Get regions and countries for a specific sales rep  
**Returns:** Region(s), country list, multi-region flag  
**Use case:** Understanding rep territory scope  
**Parameters:** `rep_name`

**Example return:**
```json
{
  "rep_name": "Alessia Ashkenazi",
  "region": "SE+EE",
  "countries": ["Italy", "Greece", "Poland", "Czech Republic", "..."],
  "is_multi_region": true,
  "region_abbreviation": "[SE+EE]"
}
```

### `get_region_sales_reps` ⭐ NEW
**Purpose:** Get all sales reps assigned to a region  
**Returns:** List of reps in region with their territories  
**Use case:** Regional team management, territory planning  
**Parameters:** `region` (SE/EE)

**Example return:**
```json
{
  "region": "SE",
  "region_name": "Southern Europe",
  "abbreviation": "[SE]",
  "sales_reps": [
    {"rep_name": "Ray Mills", "countries": ["Spain", "Greece"], ...},
    {"rep_name": "Bruno Filippelli", "countries": ["Italy"], ...},
    ...
  ],
  "rep_count": 7
}
```

---

## Deal Registrations (5 tools)

Partner program tracking and deal registration metrics.

### `get_deal_registrations`
**Purpose:** Registered deals by status  
**Returns:** Deal count, amount by status (approved/rejected/all)  
**Use case:** Program health, deal flow  
**Parameters:** `period`

### `get_deal_registrations_trend`
**Purpose:** Q-over-Q trends (approval rates, close rates)  
**Returns:** Trend metrics across quarters  
**Use case:** Program acceleration, approval rate tracking  
**Parameters:** `periods` (optional)

### `get_deal_registrations_breakdown`
**Purpose:** Breakdown by status/partner/stage  
**Returns:** Registrations with segmentation  
**Use case:** Granular program analysis  
**Parameters:** `period`, `breakdown` (status/partner/stage)

### `get_opportunities_by_registration_status` ⭐ NEW
**Purpose:** Get opportunities by registration status with Allbound partner details  
**Returns:** Table with deal names, amounts, stages, partners, owners, countries, close dates  
**Use case:** Identify and action unapproved registrations (Submitted, In Review, Approved, Rejected)  
**Parameters:** `period`, `registration_status` (single or comma-separated: Submitted/In Review/Approved/Rejected), `limit`, `channel_manager`  
**Key Features:**
- Multi-status support: `registration_status="Submitted,In Review"` for all unapproved
- Includes Allbound_Partner__c (the partner who registered the deal)
- Markdown table formatting with deal details
- Configurable time period and result limit
**Example Prompts:**
- "Show me all submitted deal registrations this quarter with their details in a table"
- "Which deal registrations have not been approved yet?"
- "Show me unapproved registrations (Submitted + In Review) from FY27_Q1"

### `admin_discover_targets`
**Purpose:** Discover available targeting segments  
**Returns:** Available targeting dimensions  
**Use case:** Program targeting options  
**Parameters:** None

---

## Win Rate & Performance (3 tools)

Performance tracking and win/loss analysis.

### `get_win_rate_by_country`
**Purpose:** Win rate by country (closed-won vs closed-lost)  
**Returns:** Win % by country  
**Use case:** Geographic performance, competitive strength  
**Parameters:** `period`

### `salesforce_reports`
**Purpose:** Access Salesforce reports by name  
**Returns:** Report data  
**Use case:** Standard report access  
**Parameters:** `report_name`, `filters` (optional)

### `run_exploratory_analysis`
**Purpose:** Natural language exploratory analysis  
**Returns:** Analysis results  
**Use case:** Ad-hoc questions, data exploration  
**Parameters:** `intent` (natural language question)

---

## Salesforce Data Access (12 tools) 🔓 ADVANCED MODE ONLY

Raw SOQL queries, describes, and direct data access. These tools are only available when MCP_USAGE_MODE is set to "advanced".

**⚠️ DESIGN NOTE:** These tools are preserved for backward compatibility and advanced use cases. In ADVANCED mode, they allow raw SOQL execution which can introduce LLM hallucination risk. In BASIC mode, all use cases are covered by domain-specific deterministic tools above.

**Why split into modes?**
- BASIC mode forces healthy tool design (no escape hatches)
- ADVANCED mode enables power users and observability testing
- LangSmith integration will track SOQL tool usage patterns to inform future decisions
- Easy to scale: add new domains as tools in BASIC, not raw SOQL workarounds

### `salesforce_query`
**Purpose:** Run SOQL queries directly  
**Returns:** Query results  
**Use case:** Advanced queries, custom analysis  
**Parameters:** `query` (SOQL string)

### `salesforce_search`
**Purpose:** Search records with SOQL-like syntax  
**Returns:** Search results  
**Use case:** Record search  
**Parameters:** `query`

### `salesforce_describe`
**Purpose:** Describe sObject structure and relationships  
**Returns:** sObject metadata  
**Use case:** Understanding data structure  
**Parameters:** `sobject_name`

### `salesforce_describe_fields`
**Purpose:** Describe fields for a specific sObject  
**Returns:** Field metadata  
**Use case:** Field-level data structure  
**Parameters:** `sobject_name`

### `salesforce_sobjects`
**Purpose:** List all available sObjects  
**Returns:** sObject list  
**Use case:** Data discovery  
**Parameters:** None

### `salesforce_lookup`
**Purpose:** Look up records by ID or name  
**Returns:** Record details  
**Use case:** Record retrieval  
**Parameters:** `sobject_name`, `lookup_value`

### `salesforce_aggregate`
**Purpose:** Aggregate data (SUM/COUNT/AVG by group)  
**Returns:** Aggregated results  
**Use case:** Aggregate analysis  
**Parameters:** `sobject_name`, `aggregate_field`, `group_by_field`

### `salesforce_relationships`
**Purpose:** Explore sObject relationships  
**Returns:** Relationship map  
**Use case:** Data relationship discovery  
**Parameters:** `sobject_name`

### `salesforce_recent`
**Purpose:** Recently modified records  
**Returns:** Recent records  
**Use case:** Activity tracking  
**Parameters:** `sobject_name`, `limit`

### `salesforce_hierarchy`
**Purpose:** Hierarchy relationships (Account→Contacts, etc)  
**Returns:** Hierarchy structure  
**Use case:** Organizational structure  
**Parameters:** `parent_sobject`, `child_sobject`

### `salesforce_find_partner`
**Purpose:** Find partner records by criteria  
**Returns:** Partner list  
**Use case:** Partner lookup  
**Parameters:** `search_criteria`

### `salesforce_case_insights`
**Purpose:** Case and support ticket insights  
**Returns:** Case metrics  
**Use case:** Support analysis  
**Parameters:** `period`

---

## Utility & Config (4 tools)

System initialization and configuration.

### `list_available_metrics`
**Purpose:** List all available metrics for analysis  
**Returns:** Metrics list with descriptions  
**Use case:** Discover available metrics  
**Parameters:** None

### `get_authenticated_user`
**Purpose:** Get current authenticated user info  
**Returns:** User details (name, org, profile)  
**Use case:** Verify authentication  
**Parameters:** None

### `route_slash_command`
**Purpose:** Route slash commands to handlers  
**Returns:** Command execution result  
**Use case:** Slash command routing  
**Parameters:** `command`, `args`

### `initialize_client`
**Purpose:** Initialize Salesforce client connection  
**Returns:** Connection status  
**Use case:** Client setup  
**Parameters:** `credentials` (optional)

---

## Summary Statistics

### BASIC Mode (50 tools - Default, Production-Ready)
| Category | Count | Description |
|----------|-------|-------------|
| Channel Intelligence | 21 | Core revenue/pipeline/partner analytics + sourcing attribution |
| Risk Management | 10 | Deal health, aging, stalling detection |
| Sales Rep Analytics | 7 | Rep performance with multi-region support |
| Deal Registrations | 5 | Program tracking, metrics, and unapproved registration details |
| Win Rate & Performance | 3 | Performance analysis |
| Utility & Config | 4 | System initialization and auth |
| **BASIC TOTAL** | **50** | **Deterministic domain-specific tools** |

### ADVANCED Mode (Additional 12 tools - Opt-in)
| Category | Count | Description |
|----------|-------|-------------|
| Salesforce Data Access | 12 | Raw SOQL queries and direct data exploration |
| **ADVANCED TOTAL** | **62** | **50 BASIC + 12 ADVANCED tools** |

### Architecture Notes
- **BASIC mode** (default): All tools are deterministic, domain-specific, and designed to prevent LLM hallucination/drift
- **ADVANCED mode** (opt-in): Adds 12 raw Salesforce Data Access tools for power users and testing
- **Tool registration is dynamic:** Set `MCP_USAGE_MODE=advanced` to enable ADVANCED tools; no code changes needed
- **Backward compatibility:** All existing commands and integrations work unchanged in BASIC mode
- **LangSmith-ready:** Observability logging will track which mode was used and which tools were invoked

---

## Multi-Region Support (NEW in v2.1)

Five tools now support **regional filtering for SE/EE territories**:

### Enhanced with `--region SE|EE|all` parameter:
- `get_revenue_by_sales_rep`
- `get_closed_deals_by_sales_rep`
- `get_pipeline_deals_by_sales_rep`

### New utility tools:
- `get_sales_rep_regions` - Get regions for a specific rep
- `get_region_sales_reps` - Get all reps in a region

### Regions:
- **SE (Southern Europe)**: Italy, Spain, Portugal, Greece, Cyprus, Malta (7 reps)
- **EE (Eastern Europe)**: Poland, Czech Republic, Hungary, Slovakia, Romania, Bulgaria, Croatia, Serbia, Slovenia, Turkey (1 multi-region rep)

---

## Common Parameters

| Parameter | Type | Used In | Description |
|-----------|------|---------|-------------|
| `period` | string | Most tools | Time period (THIS_QUARTER, THIS_FISCAL_YEAR, FY27_Q1, etc.) |
| `metric` | string | Some tools | revenue or pipeline |
| `breakdown` | string | Some tools | partner, country, stage, quarter, etc. |
| `limit` | integer | Some tools | Max records to return (10-500) |
| `partner` | string | Some tools | Partner name or partial match |
| `country` | string | Some tools | Country name (IT, ES, PT, GR, CY, MT) |
| `region` | string | Sales rep tools | SE, EE, or all |
| `period_a`, `period_b` | string | Growth tools | Two periods for comparison |
| `channel_manager` | string | Some tools | Filter by channel manager name |

---

## Usage Examples

### Channel Intelligence
```
get_revenue(period="THIS_QUARTER", breakdown="partner")
get_top_partners(period="THIS_FISCAL_YEAR", metric="revenue", limit=10)
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER")
```

### Risk Management
```
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=40)
get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
get_deal_aging_by_stage(period="THIS_QUARTER")
```

### Sales Rep Analytics with Regions
```
get_revenue_by_sales_rep(period="THIS_QUARTER", region="SE")
get_closed_deals_by_sales_rep(period="THIS_QUARTER", region="EE")
get_sales_rep_regions(rep_name="Alessia Ashkenazi")
get_region_sales_reps(region="SE")
```

### Data Access
```
salesforce_query(query="SELECT Id, Name FROM Opportunity WHERE Amount > 100000")
salesforce_describe(sobject_name="Opportunity")
salesforce_lookup(sobject_name="Account", lookup_value="Accenture")
```

---

## 🎯 Natural Language Examples (How to Ask Questions)

Instead of tool signatures, use natural business language. The LLM translates to tools automatically.

### "I want to..." → Use this tool

**Revenue & Status**
- "Give me our Q3 revenue" → `get_revenue(period="FY27_Q3")`
- "Break down revenue by partner" → `get_revenue(breakdown="partner")`
- "Who are our top 10 partners?" → `get_top_partners(period="THIS_QUARTER", metric="revenue", limit=10)`
- "How much did we grow this quarter?" → `get_growth(metric="revenue", period_a="THIS_QUARTER", period_b="LAST_QUARTER")`
- "Show me 8 quarters of trends" → `get_multi_period_trend(metric="revenue", periods=[...])`

**Pipeline & Forecast**
- "What's our open pipeline?" → `get_pipeline(period="THIS_QUARTER")`
- "Show pipeline by stage" → `get_pipeline(breakdown="stage")`
- "What's our realistic forecast?" → `get_weighted_pipeline(period="THIS_QUARTER")`
- "Which countries have the most opportunity?" → `get_pipeline(breakdown="country")`

**Partner Details**
- "Give me Accenture's full scorecard" → `get_partner_scorecard(partner_name="Accenture")`
- "What's Accenture's pipeline?" → `get_partner_pipeline(partner_name="Accenture")`
- "Generate Accenture's QBR" → `generate_partner_qbr(partner_name="Accenture")`
- "Is Accenture active? Show engagement" → `get_partner_activity_summary()`

**Risk & Health**
- "Which deals are stalled?" → `get_stalled_deals(period="THIS_QUARTER")`
- "Show me high-risk deals (< 40% probability)" → `get_high_risk_deals(probability_threshold=40)`
- "How old are deals in each stage?" → `get_deal_aging_by_stage()`
- "Which deals have we lost?" → `get_lost_deals(period="THIS_QUARTER")`
- "Which partners went quiet?" → `get_partner_activity_summary()`

**Sales Reps (Multi-Region)**
- "Show me rep revenue in Southern Europe" → `get_revenue_by_sales_rep(region="SE")`
- "What's Alessia's performance across both regions?" → `get_revenue_by_sales_rep(rep_name="Alessia Ashkenazi")`
- "Show me Ray Mills' revenue by country" → `get_revenue_by_sales_rep_by_country(rep_name="Ray Mills")`
- "Which reps cover Eastern Europe?" → `get_region_sales_reps(region="EE")`
- "What's Alessia's full territory?" → `get_sales_rep_regions(rep_name="Alessia Ashkenazi")`

**Deal Details**
- "Tell me about opportunity ID 00658000005gH1AAI" → `get_opportunity_detail(opportunity_id="00658000005gH1AAI")`
- "Find Accenture deals > $100K" → `get_opportunity_list(partner_name="Accenture", min_amount=100000)`
- "Show me Negotiation stage deals" → `get_opportunity_list(stage="Negotiation")`

**Data Quality**
- "Are there data quality issues?" → `get_orphan_hygiene()`
- "What unusual patterns exist?" → `run_exploratory_analysis()`

### Multi-Tool Workflows

**"Is Partner X at Risk?"**
```
1. get_partner_detail(partner_name="Accenture", period="THIS_QUARTER")
   → Check declining revenue or pipeline?
2. get_partner_activity_summary()
   → Check recent activity or going quiet?
3. get_lost_deals(group_by="partner")
   → Check lost deal patterns?
4. generate_partner_qbr(partner_name="Accenture")
   → Full health check
```

**"Are We On Track vs Quota?"**
```
1. get_kpi_snapshot()
   → Attainment %?
2. get_weighted_pipeline(period="THIS_QUARTER")
   → Realistic forecast?
3. get_stage_progression_velocity()
   → Deal progression speed?
```

**"Daily Executive Briefing"**
```
1. get_kpi_snapshot() → Current status
2. get_high_risk_deals(limit=5) → Top risks
3. get_stalled_deals(limit=5) → Attention needed
4. get_opportunity_recency(limit=10) → Recent activity
```

---

## Notes

- All tools are async and support timeout handling
- Most tools return JSON-structured responses
- All financial amounts are in EUR (or local currency per Salesforce org)
- Fiscal calendar: FY27 (Feb 1, 2026 - Jan 31, 2027)
- All tools support optional `channel_manager` parameter for filtering by team
- New multi-region tools support SE, EE, or all regions (default=all)

---

**Last Updated:** June 21, 2026  
**Version:** 2.1  
**Status:** ✅ Production Ready
