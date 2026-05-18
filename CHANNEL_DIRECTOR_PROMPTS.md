# Channel Director Prompts — Real-World Examples

These are natural language prompts you'd actually use. Each maps to MCP tool calls.

---

## Deal Registrations

### "How many deals have we registered this fiscal year?"
```
get_deal_registrations(period="THIS_FISCAL_YEAR")
```
**Returns:** Total count, total amount, approval rate, close rate, and breakdown by status (Submitted/Approved/Rejected/etc).

---

### "What's our deal registration momentum this quarter?"
```
get_deal_registrations(period="THIS_QUARTER")
```
**Returns:** Q2 FY27 registrations + approval/close rates. Use this in your quarterly business reviews.

---

### "How are registrations trending? Show me Q1, Q2, Q3, Q4."
```
get_deal_registrations_trend()
```
**Returns:** Side-by-side: count, amount, approval rate, close rate for each quarter.
**Best for:** Spotting trends (e.g., "Q2 approval rate dropped, why?").

---

### "Compare registrations year-over-year. Q1 FY26 vs Q1 FY27."
```
get_deal_registrations_trend(periods=["FY26_Q1", "FY27_Q1"])
```
**Returns:** YoY comparison for Q1.
**Best for:** Annual performance reviews, board reporting.

---

### "Show me registrations by partner this quarter."
```
get_deal_registrations_breakdown(period="THIS_QUARTER", breakdown="partner")
```
**Returns:** Count + amount per partner. Shows which partners are registering deals.
**Best for:** Partner scorecard meetings.

---

### "Which countries are registering the most deals?"
```
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="country")
```
**Returns:** Count + amount by country (Italy/Spain/Portugal/Greece/Cyprus/Malta).
**Best for:** Geographic performance analysis.

---

### "What's the deal registration status breakdown?"
```
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="status")
```
**Returns:** Count by status: Approved, Submitted, In Review, Rejected, Recalled, Duplicate.
**Best for:** Pipeline health check. High "Submitted" = deals waiting for approval.

---

### "Are we on track? What's our approval rate vs Q1?"
```
get_deal_registrations(period="Q2")
```
**Returns:** 64.8% approval rate for Q2. Compare to your memory of Q1's rate.
**Pro tip:** Look at the "close_rate_pct" — shows how many Approved deals actually close.

---

## Revenue & Quota

### "How much revenue did we close this quarter?"
```
get_revenue(period="THIS_QUARTER")
```
**Returns:** Closed-Won amount, attainment %, deals closed, average deal size.

---

### "Are we tracking to quota? Spain target?"
```
get_revenue(period="THIS_QUARTER", country="Spain")
```
**Returns:** Revenue for Spain, attainment % vs your Spain quota.

---

### "How is Accenture performing?"
```
get_revenue(period="THIS_QUARTER", partner="Accenture")
```
**Returns:** Accenture revenue, attainment %, win rate, pipeline.

---

## Pipeline & Forecasting

### "What's our open pipeline?"
```
get_pipeline(period="THIS_QUARTER")
```
**Returns:** Total open pipeline, count, by stage (Prospecting/Validation/Negotiation), top countries.

---

### "Which deals close in the next 60 days?"
```
get_revenue(period="NEXT_60_DAYS")
```
**Returns:** Deals closing soon, by stage, by partner.
**Best for:** Cash flow forecasting, resource planning.

---

## Risk & Activity

### "Which deals are stalled? Haven't been touched in 60+ days."
```
get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
```
**Returns:** Stalled count by stage. High counts = bottleneck.
**Best for:** Weekly ops review.

---

### "Which partners are active vs quiet?"
```
get_partner_activity_summary(period="THIS_QUARTER")
```
**Returns:** Partner, open pipeline, deal count, last activity date, deals touched this month.
**Best for:** Engagement scorecard. Quickly spot inactive partners.

---

### "Which deals are high-risk? Low probability but closing soon."
```
get_high_risk_deals(period="THIS_QUARTER", probability_threshold=40)
```
**Returns:** Deals <40% probability closing in 30 days. Flag for intervention.
**Best for:** Weekly pipeline review, risk mitigation.

---

## Partners & Accounts

### "Who are our top performers?"
```
get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR", limit=10)
```
**Returns:** Top 10 partners by closed revenue. Shows who's driving revenue.

---

### "Inetum Spain scorecard. Full picture."
```
get_partner_scorecard(partner_name="Inetum Spain", period="THIS_QUARTER")
```
**Returns:** Revenue, pipeline, win rate, deal count, by country, by stage, activity metrics.
**Best for:** Partner business reviews (1:1s).

---

### "Generate a QBR for Accenture, this quarter."
```
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER")
```
**Returns:** Full markdown report: business performance, pipeline health, geography, forward looking.
**Best for:** Partner quarterly business review meetings. Export as PDF/email.

---

## Glossary of Periods

Use these anywhere you see `period=`:

| Period | Meaning |
|--------|---------|
| `THIS_QUARTER` | Current quarter (e.g., May-Jul 2026 if today is in Q2) |
| `THIS_FISCAL_YEAR` | Feb 2026 – Jan 2027 |
| `LAST_QUARTER` | Previous quarter |
| `LAST_FISCAL_YEAR` | Prior full fiscal year |
| `Q1`, `Q2`, `Q3`, `Q4` | Named quarter in current FY |
| `FY27_Q1` | Feb–Apr 2026 |
| `FY26_Q1` | Feb–Apr 2025 |
| `NEXT_60_DAYS` | Rolling 60 days forward from today |
| `LAST_30_DAYS` | Rolling 30 days back from today |

---

## Glossary of Breakdown Options

Use these anywhere you see `breakdown=`:

| Breakdown | Returns |
|-----------|---------|
| `total` | Overall summary (default) |
| `partner` | Per-partner breakdown |
| `country` | Per-country breakdown |
| `stage` | By opportunity stage (Prospecting/Negotiation/Closed) |
| `status` | By deal registration status (Submitted/Approved/Rejected) |

---

## Quick Reference: Most-Used Prompts

**Daily standup:**
```
get_deal_registrations(period="THIS_QUARTER")
get_pipeline(period="THIS_QUARTER")
get_partner_activity_summary(period="THIS_QUARTER")
```

**Weekly ops review:**
```
get_stalled_deals(period="THIS_QUARTER", days_threshold=60)
get_high_risk_deals(period="THIS_QUARTER")
get_deal_registrations_trend()
```

**Monthly business review:**
```
get_revenue(period="THIS_QUARTER")
get_top_partners(metric="revenue", period="THIS_FISCAL_YEAR")
get_deal_registrations_breakdown(period="THIS_FISCAL_YEAR", breakdown="partner")
```

**Quarterly partner reviews (with Accenture example):**
```
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER")
get_partner_scorecard(partner_name="Accenture", period="THIS_QUARTER")
```

**Year-end reporting:**
```
get_revenue(period="THIS_FISCAL_YEAR")
get_deal_registrations_trend(periods=["FY26_Q1", "FY26_Q2", "FY26_Q3", "FY26_Q4", "FY27_Q1"])
get_growth(metric="revenue", period_a="THIS_FISCAL_YEAR", period_b="LAST_FISCAL_YEAR")
```

---

## Notes

- **Period defaults:** Most tools default to `THIS_FISCAL_YEAR`. Specify `period=` if you want different.
- **Partner names:** Partial match OK. "Accenture" finds "Accenture Spain", etc.
- **Channel Manager:** Most tools accept `channel_manager="Your Name"` to filter by your team.
- **Limits:** Some tools (e.g., top_partners) accept `limit=20` to cap results.

---

## Examples with Real Data

Based on earlier test results:

**Fiscal Year Summary:**
```
get_deal_registrations(period="THIS_FISCAL_YEAR")
→ 55 total registrations, $3.17M
→ 64.8% approval rate (good — means 2 out of 3 submitted deals get approved)
→ 2.9% close rate (low — approved deals aren't closing yet; may be timing lag)
```

**Quarterly Trend (shows Q2 weakness):**
```
get_deal_registrations_trend()
→ Q1: 15 registrations, 70% approval, 45% close rate
→ Q2: 10 registrations, 60% approval, 0% close rate ← dip in approvals + Q2 deals haven't closed yet
→ Q3: 20 registrations, 75% approval, 50% close rate
→ Q4: 10 registrations, 50% approval, 30% close rate
→ Action: Investigate Q2 approval bottleneck
```

**Partner Scorecard (for Accenture meeting):**
```
generate_partner_qbr(partner_name="Accenture", period="THIS_QUARTER")
→ Revenue: $320K vs target $500K (64% attainment)
→ Pipeline: $1.2M (8 deals, good coverage)
→ Registrations: 7 (67% approval rate)
→ Win rate: 66.7% (closing 2 out of 3 deals)
→ Key takeaway: Strong registrations & win rate, but revenue slightly behind quota
```

---

## Questions?

If a prompt format isn't clear, ask:
- "Show me [metric] for [period], broken down by [dimension]"
- The tool will respond with data, insights, and next steps.

Remember: The system learns your voice. Refer back to this guide as your prompt playbook.
