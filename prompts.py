"""FastMCP Prompts for Channel Director Playbook.

This module provides reusable prompts for analyzing pipeline, partner engagement,
and leads from a Channel Director perspective covering Southern Europe.

Region: Portugal, Spain, Italy, Greece, Cyprus
Fiscal Year FY27: Feb 1, 2026 – Jan 31, 2027
"""

# =============================================================================
# Configuration Constants
# =============================================================================

COUNTRIES = ["Portugal", "Spain", "Italy", "Greece", "Cyprus"]
COUNTRIES_SQL = "('Spain','Portugal','Italy','Greece','Cyprus')"

# Fiscal Year FY27: Feb 1, 2026 – Jan 31, 2027
FY27_START = "2026-02-01"
FY27_END = "2027-01-31"

# Quarter date ranges for FY27
QUARTERS = {
    "Q1": ("2026-02-01", "2026-04-30"),  # Feb-Apr 2026
    "Q2": ("2026-05-01", "2026-07-31"),  # May-Jul 2026
    "Q3": ("2026-08-01", "2026-10-31"),  # Aug-Oct 2026
    "Q4": ("2026-11-01", "2027-01-31"),  # Nov 2026 - Jan 2027
}

# =============================================================================
# Field Mapping Reference
# =============================================================================
# Partner__c              = Lookup to Account (the actual partner)
# Partner__r.Name         = Partner account name (use in queries)
# Partner_Source_Influence__c = Picklist: Source / Influence / Fulfillment
# Partner__c      = Picklist for partner TYPE (Reseller/Referral) - NOT the partner name
# Primary_Partner_Total__c = Currency field for partner total value
# =============================================================================

# Standard opportunity fields for Channel Director
OPPORTUNITY_FIELDS = """Id, Name, Amount, StageName, Stage_Detail__c, CloseDate, Probability,
Account.Name, Account.BillingCountry, Owner.Name,
Channel_Manager__c, Partner__c, Partner__r.Name, Partner_Source_Influence__c"""

OPPORTUNITY_FIELDS_EXTENDED = """Id, Name, Amount, StageName, Stage_Detail__c, CloseDate, Probability,
Account.Name, Account.BillingCountry, Owner.Name,
Channel_Manager__c, Partner__c, Partner__r.Name, Partner_Source_Influence__c,
Primary_Partner_Total__c, Partner_Reseller_Percentage__c, Type"""


# =============================================================================
# Helper Functions
# =============================================================================


def get_quarter_dates(quarter: str) -> tuple[str, str]:
    """Get start and end dates for a fiscal quarter."""
    return QUARTERS.get(quarter.upper(), QUARTERS["Q1"])


def build_region_filter() -> str:
    """Build the standard region filter clause."""
    return f"Account.BillingCountry IN {COUNTRIES_SQL}"


def format_analysis_section(items: list[str]) -> str:
    """Format analysis bullet points."""
    return "\n".join(f"- {item}" for item in items)


# =============================================================================
# Prompt 1: Quarterly Open Pipeline Analysis
# =============================================================================


def quarterly_pipeline_analysis(quarter: str = "Q1") -> str:
    """Analyze open pipeline for a specific quarter with partner breakdown.

    Shows pipeline by country, partner vs non-partner split, top deals,
    and stage distribution for the Channel Director's region.
    """
    start_date, end_date = get_quarter_dates(quarter)

    return f"""You are assisting a Channel Director covering Portugal, Spain, Italy, Greece, and Cyprus.
Fiscal year FY27 runs from Feb 1, 2026 – Jan 31, 2027.

**Task:** Analyze all OPEN opportunities in {quarter} FY27.

**SOQL Query to execute:**
```sql
SELECT {OPPORTUNITY_FIELDS}
FROM Opportunity
WHERE IsClosed = false
  AND CloseDate >= {start_date}
  AND CloseDate <= {end_date}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
```

**Required Analysis:**
1. **Pipeline by Country** - Total value and count per country
2. **Partner Coverage** - Opportunities WITH partner vs WITHOUT partner (count & value)
3. **Top 5 Deals** - Largest opportunities by Amount
4. **Stage Distribution** - Pipeline value by StageName
5. **Partner Source vs Influence** - Breakdown by Partner_Source_Influence__c

**Output Format:**
Present findings in a structured report with tables where appropriate.
Highlight any country with less than 30% partner coverage as a concern."""


# =============================================================================
# Prompt 2: Closed-Won Partner Contribution
# =============================================================================


def closed_won_partner_analysis(quarter: str = "", full_year: bool = True) -> str:
    """Analyze Closed-Won deals with partner contribution metrics.

    Shows partner revenue contribution, top partners by contract value,
    and Source vs Influence vs Fulfillment breakdown.
    """
    if full_year:
        date_filter = f"CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}"
        period = "FY27"
    else:
        start_date, end_date = get_quarter_dates(quarter)
        date_filter = f"CloseDate >= {start_date} AND CloseDate <= {end_date}"
        period = f"{quarter} FY27"

    return f"""You are assisting a Channel Director covering Southern Europe.

**Task:** Analyze all CLOSED-WON opportunities in {period}.

**SOQL Query to execute:**
```sql
SELECT Id, Name, Amount, CloseDate, Account.Name, Account.BillingCountry,
       Owner.Name, Channel_Manager__c, Partner__c,
       Partner_Source_Influence__c, Primary_Partner_Total_Contract_Value__c
FROM Opportunity
WHERE IsWon = true
  AND {date_filter}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC NULLS LAST
```

**Required Analysis:**
1. **Total Closed-Won Revenue** - Sum of Amount
2. **Partner Contribution Breakdown:**
   - Source (partner originated the deal)
   - Influence (partner helped close)
   - Fulfillment (partner delivers/implements)
3. **Top 10 Partners** - Ranked by Primary_Partner_Total_Contract_Value__c
4. **Partner Share** - % of total revenue involving a partner
5. **Country Performance** - Closed-Won by country with partner %

**Key Insight:** Flag any country where partner contribution is below 40%."""


# =============================================================================
# Prompt 3: Partner Engagement Health Check
# =============================================================================


def partner_engagement_health() -> str:
    """Health check on partner engagement across active opportunities.

    Identifies accounts with opportunities but no partner attached,
    especially those in late stages needing urgent attention.
    """
    return f"""You are assisting a Channel Director focused on partner engagement.

**Task:** Audit partner engagement health across all active opportunities.

**SOQL Query to execute:**
```sql
SELECT Account.Id, Account.Name, Account.BillingCountry, Account.Type,
       Name, Amount, StageName, Stage_Detail__c,
       Partner__c, Partner__c, Partner_Source_Influence__c
FROM Opportunity
WHERE IsClosed = false
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
```

**Required Analysis:**
1. **Partner Engagement by Country:**
   - Count of opportunities WITH partner
   - Count of opportunities WITHOUT partner
   - Partner coverage % per country

2. **High-Value Gaps:**
   - Opportunities > €100K with NO partner attached
   - List: Name, Amount, Stage, Account, Country

3. **Late-Stage Alerts (URGENT):**
   - Opportunities in 'Negotiation', 'Contracts', or 'Submitted to Finance' with NO partner
   - These need immediate partner engagement or explanation

4. **Account Multi-Opportunity Analysis:**
   - Accounts with 3+ active opportunities
   - Flag if ANY of those opportunities lack partner

**Action Items:** Provide specific recommendations for partner attachment."""


# =============================================================================
# Prompt 4: Partner-Sourced Pipeline (Top Deals)
# =============================================================================


def partner_sourced_pipeline(limit: int = 10) -> str:
    """Analyze top partner-sourced opportunities.

    Shows deals where the partner ORIGINATED the opportunity,
    including partner revenue share percentages.
    """
    return f"""You are assisting a Channel Director tracking partner-sourced business.

**Task:** Identify top {limit} PARTNER-SOURCED opportunities (Partner originated the deal).

**SOQL Query to execute:**
```sql
SELECT Id, Name, Amount, StageName, Stage_Detail__c, CloseDate,
       Account.Name, Account.BillingCountry,
       Partner__c, Primary_Partner_Average_Percentage__c, Owner.Name
FROM Opportunity
WHERE IsClosed = false
  AND Partner_Source_Influence__c = 'Source'
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC NULLS LAST
LIMIT {limit}
```

**Also run aggregation query:**
```sql
SELECT Partner_Source_Influence__c, COUNT(Id) opp_count, SUM(Amount) total_value
FROM Opportunity
WHERE IsClosed = false
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
GROUP BY Partner_Source_Influence__c
```

**Required Analysis:**
1. **Top {limit} Sourced Deals** - Table with Amount, Partner, Stage, Close Date
2. **Source vs Influence vs Fulfillment** - Pipeline split (count & value)
3. **Partner Leaderboard** - Which partners source the most pipeline
4. **Average Partner %** - Mean Primary_Partner_Average_Percentage__c for sourced deals
5. **Stage Health** - Are sourced deals progressing or stuck?

**Insight:** Sourced deals indicate strong partner relationships. Highlight top-performing partners."""


# =============================================================================
# Prompt 5: At-Risk Pipeline Analysis
# =============================================================================


def at_risk_pipeline() -> str:
    """Identify at-risk opportunities: late stage but low probability.

    Flags deals in Contracts/Submitted to Finance with <50% probability,
    and analyzes partner attachment on risky deals.
    """
    return f"""You are assisting a Channel Director with pipeline risk assessment.

**Task:** Identify AT-RISK opportunities (late stage + low probability).

**SOQL Query to execute:**
```sql
SELECT Id, Name, Amount, Probability, StageName, Stage_Detail__c,
       CloseDate, Owner.Name, Channel_Manager__c, Partner__c, Partner__c,
       Account.Name, Account.BillingCountry
FROM Opportunity
WHERE IsClosed = false
  AND StageName IN ('Contracts','Submitted to Finance','Negotiation')
  AND Probability < 50
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
```

**Required Analysis:**
1. **Risk Summary:**
   - Total count of at-risk opportunities
   - Total value at risk (sum of Amount)
   - Average probability of at-risk deals

2. **Risk Detail Table:**
   | Opportunity | Amount | Stage | Probability | Partner | Owner | Close Date |

3. **Partner Factor:**
   - How many at-risk deals have a partner attached?
   - Do partnered deals have higher/lower probability on average?

4. **Overdue Analysis:**
   - Deals where CloseDate has already passed but still open

5. **Recommended Actions:**
   - Prioritize by value
   - Suggest partner engagement for unpartnered at-risk deals

**Alert Level:** Use 🔴 for >€500K at risk, 🟡 for €100K-500K, 🟢 for <€100K."""


# =============================================================================
# Prompt 6: New vs Existing Business Analysis
# =============================================================================


def new_vs_existing_business(quarter: str = "") -> str:
    """Analyze pipeline split between new and existing business.

    Shows Type breakdown with partner attachment rates for each category.
    """
    if quarter:
        start_date, end_date = get_quarter_dates(quarter)
        date_filter = f"CloseDate >= {start_date} AND CloseDate <= {end_date}"
        period = f"{quarter} FY27"
    else:
        date_filter = f"CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}"
        period = "FY27"

    return f"""You are assisting a Channel Director analyzing business mix.

**Task:** Analyze NEW vs EXISTING business pipeline for {period}.

**SOQL Query to execute:**
```sql
SELECT Id, Name, Amount, StageName, CloseDate, Type,
       Account.Name, Account.BillingCountry,
       Partner__c, Partner__c, Partner_Source_Influence__c
FROM Opportunity
WHERE IsClosed = false
  AND {date_filter}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Type, Amount DESC
```

**Required Analysis:**
1. **Business Mix Overview:**
   | Type | Count | Total Value | Avg Deal Size |
   - New Business
   - Existing Business
   - Operational Only

2. **Partner Coverage by Type:**
   - % of New Business with partner attached
   - % of Existing Business with partner attached
   - Which type has stronger partner engagement?

3. **Country x Type Matrix:**
   | Country | New Biz | Existing Biz | Partner % |

4. **Partner-Sourced New Business:**
   - Count and value of new business where Partner_Source_Influence__c = 'Source'
   - These are pure partner wins

5. **Strategic Insight:**
   - Is partner channel driving net-new logos or mainly upsell?
   - Recommendations for improving partner sourcing of new business."""


# =============================================================================
# Prompt 7: Lead Conversion & Partner Attribution
# =============================================================================


def lead_conversion_analysis() -> str:
    """Analyze lead funnel with partner attribution tracking.

    Shows conversion rates and identifies leads with partner involvement.
    """
    return f"""You are assisting a Channel Director analyzing lead funnel.

**Task:** Analyze leads created in FY27 with conversion and partner attribution.

**SOQL Query to execute:**
```sql
SELECT Id, Name, Company, Status, Activity_Stage__c, Type__c,
       LeadSource, Lead_Source_Attribution__c, Lead_Source_Detail__c,
       Lead_Source_Sub_Detail__c, Matched_Account_Owner__c, IsConverted,
       ConvertedDate, ConvertedOpportunityId, Country
FROM Lead
WHERE CreatedDate >= {FY27_START} AND CreatedDate <= {FY27_END}
  AND Country IN {COUNTRIES_SQL}
ORDER BY CreatedDate DESC
```

**Required Analysis:**
1. **Funnel Overview:**
   | Status | Count | % of Total |
   - Open leads
   - Converted leads
   - Disqualified leads

2. **Conversion Rate:**
   - Overall conversion rate
   - Conversion rate by country
   - Conversion rate by LeadSource

3. **Partner Attribution:**
   - Leads where Lead_Source_Attribution__c indicates partner
   - Conversion rate of partner-attributed leads vs direct
   - Top lead sources generating converted opportunities

4. **Lead Source Breakdown:**
   | LeadSource | Total | Converted | Conv Rate |

5. **Activity Stage Analysis:**
   - Distribution by Activity_Stage__c
   - Identify bottlenecks in the funnel

6. **Recommendations:**
   - Which lead sources should get more investment?
   - Partner channel lead generation effectiveness."""


# =============================================================================
# Prompt 8: Stalled Opportunities Analysis
# =============================================================================


def stalled_opportunities(days_stalled: int = 60) -> str:
    """Identify opportunities that haven't progressed recently.

    Flags deals with no activity in the specified number of days.
    """
    return f"""You are assisting a Channel Director identifying stalled deals.

**Task:** Find opportunities with NO ACTIVITY in the last {days_stalled} days.

**SOQL Query to execute:**
```sql
SELECT Id, Name, Amount, StageName, Stage_Detail__c, CloseDate,
       Account.Name, Account.BillingCountry, Owner.Name,
       Channel_Manager__c, Partner__c, Partner__c,
       LastModifiedDate, LastActivityDate
FROM Opportunity
WHERE IsClosed = false
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
  AND LastModifiedDate <= LAST_N_DAYS:{days_stalled}
ORDER BY Amount DESC
```

**Required Analysis:**
1. **Stalled Pipeline Summary:**
   - Total count of stalled opportunities
   - Total value of stalled pipeline
   - % of total open pipeline that is stalled

2. **Stalled Deals Table:**
   | Opportunity | Amount | Stage | Last Modified | Partner | Owner |

3. **Partner Impact:**
   - Stalled deals WITH partner vs WITHOUT partner
   - Are partnered deals less likely to stall?

4. **Stage Distribution of Stalled Deals:**
   - Which stages have the most stalled opportunities?
   - Early stage stalls vs late stage stalls

5. **Owner Analysis:**
   - Which owners have the most stalled pipeline?
   - Total stalled value per Owner.Name

6. **Country View:**
   - Stalled pipeline by country

**Action Required:** List top 10 stalled deals by value with recommended next steps."""


# =============================================================================
# Prompt 9: Country-Level Pipeline Dashboard
# =============================================================================


def country_pipeline_dashboard(quarter: str = "") -> str:
    """Generate a country-level pipeline dashboard.

    Shows pipeline per country with partner vs direct breakdown.
    """
    if quarter:
        start_date, end_date = get_quarter_dates(quarter)
        date_filter = f"CloseDate >= {start_date} AND CloseDate <= {end_date}"
        period = f"{quarter} FY27"
    else:
        date_filter = f"CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}"
        period = "FY27"

    return f"""You are assisting a Channel Director with a regional dashboard.

**Task:** Generate country-level pipeline dashboard for {period}.

**Primary SOQL Query:**
```sql
SELECT {OPPORTUNITY_FIELDS_EXTENDED}
FROM Opportunity
WHERE IsClosed = false
  AND {date_filter}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Account.BillingCountry, Amount DESC
```

**Aggregation Query:**
```sql
SELECT Account.BillingCountry, COUNT(Id) opp_count, SUM(Amount) total_pipeline
FROM Opportunity
WHERE IsClosed = false
  AND {date_filter}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
GROUP BY Account.BillingCountry
ORDER BY SUM(Amount) DESC
```

**Required Dashboard Sections:**

1. **Executive Summary:**
   | Country | Pipeline Value | Opp Count | Avg Deal Size |
   (Sorted by pipeline value)

2. **Partner Coverage Matrix:**
   | Country | Partner Pipeline | Direct Pipeline | Partner % |
   🟢 >50% partner | 🟡 30-50% | 🔴 <30%

3. **Stage Health by Country:**
   For each country show pipeline by StageName

4. **Top 3 Deals per Country:**
   List the 3 largest opportunities for each country

5. **Partner Source Analysis:**
   | Country | Sourced by Partner | Influenced | Direct |

6. **Risk Flags:**
   - Countries with declining pipeline vs last quarter
   - Countries with low partner engagement
   - Countries with high concentration in single deals

**Visual:** If possible, present as a regional scorecard."""


# =============================================================================
# Prompt 10: Quarterly Forecast vs Actuals
# =============================================================================


def forecast_vs_actuals(quarter: str = "Q1") -> str:
    """Compare forecast (weighted pipeline) vs actual closed revenue.

    Analyzes forecast accuracy with partner contribution breakdown.
    """
    start_date, end_date = get_quarter_dates(quarter)

    return f"""You are assisting a Channel Director with forecast analysis.

**Task:** Compare FORECAST vs ACTUALS for {quarter} FY27.

**SOQL Query - All opportunities (open + closed):**
```sql
SELECT Id, Name, Amount, Probability, StageName, CloseDate, IsWon, IsClosed,
       Account.Name, Account.BillingCountry,
       Partner__c, Partner__c, Partner_Source_Influence__c
FROM Opportunity
WHERE CloseDate >= {start_date} AND CloseDate <= {end_date}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
```

**Required Analysis:**

1. **Forecast Summary:**
   | Metric | Value |
   | Total Pipeline (open) | SUM(Amount) where IsClosed=false |
   | Weighted Forecast | SUM(Amount × Probability/100) |
   | Closed-Won | SUM(Amount) where IsWon=true |
   | Closed-Lost | SUM(Amount) where IsClosed=true AND IsWon=false |

2. **Forecast Accuracy:**
   - Forecast vs Actual ratio
   - Upside (deals that closed above forecast)
   - Downside (deals that were lost or slipped)

3. **Partner Contribution to Actuals:**
   | Category | Closed-Won Value | % of Total |
   - Partner-Sourced
   - Partner-Influenced
   - Direct (no partner)

4. **Country Forecast Accuracy:**
   | Country | Forecast | Actual | Accuracy % |

5. **Stage Conversion Analysis:**
   - What % of 'Contracts' stage converted to Won?
   - What % of 'Negotiation' stage converted?

6. **Lessons Learned:**
   - Deals that were forecast but lost (why?)
   - Surprise wins (not forecasted but closed)
   - Recommendations for next quarter forecasting."""


# =============================================================================
# BONUS: Partner Performance Scorecard
# =============================================================================


def partner_scorecard(partner_name: str = "") -> str:
    """Generate a performance scorecard for a specific partner or all partners.

    Comprehensive view of partner contribution, pipeline, and engagement.
    """
    partner_filter = f"AND Partner__c = '<PARTNER_ACCOUNT_ID>'" if partner_name else ""
    partner_context = f"partner '{partner_name}'" if partner_name else "ALL partners"

    return f"""You are assisting a Channel Director with partner performance review.

**IMPORTANT - Partner Lookup:**
The Partner__c field is a LOOKUP to Account, not a text field.
{"1. First, use salesforce_find_partner to find the Account ID for: " + partner_name if partner_name else ""}
{"2. Replace <PARTNER_ACCOUNT_ID> in queries with the actual Account ID" if partner_name else ""}
{"3. Use Partner__r.Name to display partner names in results" if partner_name else "Use Partner__r.Name to display partner names in results"}

**Task:** Generate performance scorecard for {partner_context}.

**Query 1 - Open Pipeline:**
```sql
SELECT Partner__c, COUNT(Id) opp_count, SUM(Amount) pipeline_value,
       AVG(Probability) avg_probability
FROM Opportunity
WHERE IsClosed = false
  AND Partner__c != null
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
  {partner_filter}
GROUP BY Partner__c
ORDER BY SUM(Amount) DESC
LIMIT 20
```

**Query 2 - Closed Won:**
```sql
SELECT Partner__c, COUNT(Id) won_count, SUM(Amount) won_value,
       SUM(Primary_Partner_Total_Contract_Value__c) partner_tcv
FROM Opportunity
WHERE IsWon = true
  AND Partner__c != null
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
  {partner_filter}
GROUP BY Partner__c
ORDER BY SUM(Amount) DESC
LIMIT 20
```

**Query 3 - Source vs Influence:**
```sql
SELECT Partner__c, Partner_Source_Influence__c, COUNT(Id) count, SUM(Amount) value
FROM Opportunity
WHERE Partner__c != null
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
  {partner_filter}
GROUP BY Partner__c, Partner_Source_Influence__c
ORDER BY Partner__c, Partner_Source_Influence__c
```

**Required Scorecard:**

1. **Partner Leaderboard:**
   | Rank | Partner | Pipeline | Won Revenue | Win Rate | Sourced % |

2. **Individual Partner Cards (Top 10):**
   For each partner show:
   - Total Pipeline Value
   - Closed-Won Value (FY27)
   - # of Opportunities
   - Avg Deal Size
   - Source vs Influence ratio
   - Countries covered

3. **Partner Tier Analysis:**
   - Tier 1 (>€1M pipeline)
   - Tier 2 (€250K-1M)
   - Tier 3 (<€250K)

4. **Engagement Gaps:**
   - Countries with no partner activity
   - Partners with pipeline but no closed deals
   - Partners with declining engagement vs last quarter

5. **Strategic Recommendations:**
   - Partners to invest more in
   - Partners needing enablement
   - New partner recruitment opportunities by country."""


# =============================================================================
# BONUS: Weekly Channel Director Briefing
# =============================================================================


def weekly_briefing() -> str:
    """Generate a weekly briefing for the Channel Director.

    Quick overview of key metrics and action items.
    """
    return f"""You are assisting a Channel Director with their weekly briefing.

**Task:** Generate a concise WEEKLY BRIEFING covering the most important updates.

**Run the following queries:**

**1. Pipeline Movement (last 7 days):**
```sql
SELECT Id, Name, Amount, StageName, Account.BillingCountry, Partner__c
FROM Opportunity
WHERE IsClosed = false
  AND LastModifiedDate >= LAST_N_DAYS:7
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
LIMIT 20
```

**2. Deals Closed This Week:**
```sql
SELECT Id, Name, Amount, IsWon, CloseDate, Account.BillingCountry, Partner__c
FROM Opportunity
WHERE IsClosed = true
  AND CloseDate >= LAST_N_DAYS:7
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
```

**3. Deals Closing Next Week:**
```sql
SELECT Id, Name, Amount, Probability, StageName, CloseDate,
       Account.Name, Account.BillingCountry, Partner__c
FROM Opportunity
WHERE IsClosed = false
  AND CloseDate >= TODAY
  AND CloseDate <= NEXT_N_DAYS:7
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY CloseDate, Amount DESC
```

**Required Briefing Sections:**

📊 **EXECUTIVE SUMMARY**
- Total open pipeline value
- Closed-Won this week
- Closed-Lost this week
- Net pipeline change

🎯 **THIS WEEK'S WINS**
- List all Closed-Won deals
- Highlight partner contribution

⚠️ **THIS WEEK'S LOSSES**
- List all Closed-Lost deals
- Note if partner was attached

📅 **NEXT WEEK OUTLOOK**
- Deals expected to close
- Total expected value
- Key meetings/actions needed

🚨 **ATTENTION REQUIRED**
- High-value deals needing help
- Stalled opportunities
- Partner engagement gaps

**Keep it brief - this should be readable in 2 minutes.**"""


# =============================================================================
# BONUS: Partner QBR (Quarterly Business Review) Prep
# =============================================================================


def partner_qbr_prep(partner_name: str, quarter: str = "Q1") -> str:
    """Prepare data for a Quarterly Business Review with a specific partner.

    Comprehensive analysis to discuss in QBR meeting.
    """
    start_date, end_date = get_quarter_dates(quarter)

    return f"""You are assisting a Channel Director preparing for a QBR with partner: {partner_name}

**IMPORTANT - Partner Lookup:**
The Partner__c field is a LOOKUP to Account, not a text field.
1. First, use salesforce_find_partner or salesforce_lookup to find the partner's Account ID
2. Then use that ID in queries: WHERE Partner__c = '<account_id>'
3. Use Partner__r.Name to display the partner name in query results

**Task:** Generate QBR preparation report for {quarter} FY27.

**Query 1 - Partner's Pipeline:**
```sql
SELECT Id, Name, Amount, StageName, Stage_Detail__c, CloseDate, Probability,
       Account.Name, Account.BillingCountry, Owner.Name, Partner_Source_Influence__c
FROM Opportunity
WHERE IsClosed = false
  AND Partner__c = '{partner_name}'
  AND CloseDate >= {start_date} AND CloseDate <= {end_date}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY Amount DESC
```

**Query 2 - Partner's Closed Deals (Quarter):**
```sql
SELECT Id, Name, Amount, IsWon, CloseDate, Account.Name, Account.BillingCountry,
       Partner_Source_Influence__c, Primary_Partner_Total_Contract_Value__c
FROM Opportunity
WHERE IsClosed = true
  AND Partner__c = '{partner_name}'
  AND CloseDate >= {start_date} AND CloseDate <= {end_date}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
ORDER BY CloseDate DESC
```

**Query 3 - YTD Performance:**
```sql
SELECT IsWon, COUNT(Id) count, SUM(Amount) value
FROM Opportunity
WHERE IsClosed = true
  AND Partner__c = '{partner_name}'
  AND CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
GROUP BY IsWon
```

**Required QBR Sections:**

📈 **PERFORMANCE SUMMARY**
- {quarter} Pipeline Value
- {quarter} Closed-Won Revenue
- {quarter} Win Rate
- YTD Total Revenue
- Comparison to previous quarter

🎯 **DEAL REVIEW**
- List all deals closed in {quarter} (won & lost)
- Current open pipeline with stages
- Deals at risk (low probability or stalled)

🌍 **GEOGRAPHIC COVERAGE**
- Revenue/Pipeline by country
- Whitespace opportunities (countries with no activity)

💡 **SOURCE VS INFLUENCE**
- Deals sourced by partner vs influenced
- Partner's sourcing rate vs benchmark

⚡ **ACTION ITEMS FOR DISCUSSION**
- Deals needing joint attention
- Enablement needs
- Growth opportunities
- Blockers to address

📊 **NEXT QUARTER TARGETS**
- Suggested pipeline targets
- Focus accounts
- Joint activities needed

**Format for presentation - include talking points for each section.**"""


# =============================================================================
# BONUS: Competitive Deal Analysis
# =============================================================================


def competitive_analysis(competitor: str = "") -> str:
    """Analyze deals where competitors are involved.

    Tracks win/loss rates against specific competitors with partner factor.
    """
    competitor_filter = f"AND Competitor__c LIKE '%{competitor}%'" if competitor else "AND Competitor__c != null"
    competitor_context = f"against {competitor}" if competitor else "with competitor involvement"

    return f"""You are assisting a Channel Director analyzing competitive deals.

**Task:** Analyze opportunities {competitor_context}.

**SOQL Query:**
```sql
SELECT Id, Name, Amount, StageName, IsWon, IsClosed, CloseDate,
       Account.Name, Account.BillingCountry,
       Competitor__c, Loss_Reason__c, Win_Reason__c,
       Partner__c, Partner__c, Partner_Source_Influence__c
FROM Opportunity
WHERE CloseDate >= {FY27_START} AND CloseDate <= {FY27_END}
  AND Account.BillingCountry IN {COUNTRIES_SQL}
  {competitor_filter}
ORDER BY Amount DESC
```

**Required Analysis:**

1. **Competitive Overview:**
   - Total deals with competitor involvement
   - Total value contested
   - Win rate vs competitors

2. **Win/Loss Breakdown:**
   | Outcome | Count | Value | % |
   - Won against competitor
   - Lost to competitor
   - Still open

3. **Partner Impact on Competitive Deals:**
   - Win rate WITH partner vs WITHOUT partner
   - Do partners improve competitive win rate?

4. **Loss Analysis:**
   - Top loss reasons (Loss_Reason__c)
   - Patterns in competitive losses
   - Countries where we struggle most

5. **Win Patterns:**
   - What's working? (Win_Reason__c)
   - Successful strategies against competitors

6. **Recommendations:**
   - Where to engage partners in competitive deals
   - Competitive response strategies
   - Training/enablement needs."""


# =============================================================================
# Export all prompts for registration
# =============================================================================

ALL_PROMPTS = [
    quarterly_pipeline_analysis,
    closed_won_partner_analysis,
    partner_engagement_health,
    partner_sourced_pipeline,
    at_risk_pipeline,
    new_vs_existing_business,
    lead_conversion_analysis,
    stalled_opportunities,
    country_pipeline_dashboard,
    forecast_vs_actuals,
    partner_scorecard,
    weekly_briefing,
    partner_qbr_prep,
    competitive_analysis,
]
