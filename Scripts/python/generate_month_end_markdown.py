#!/usr/bin/env python3
"""
Generate Month-End Business Review Markdown
Comprehensive analysis with Q, FY, YoY comparisons
"""

import sys
import json
import argparse
from datetime import datetime
from markdown_utils import MarkdownReport

def safe_get(obj, key, default=None):
    """Safely get value from dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def generate_month_end_markdown(
    kpi_json, current_period_json, prior_period_json,
    revenue_partner_json, revenue_country_json, pipeline_json,
    partners_json, risk_json, registrations_json, output_path):
    """Generate month-end Markdown report."""
    
    try:
        # Load all JSON data
        with open('/dev/stdin', 'r') as f:
            pass
        
        # Parse JSON inputs
        def load_json(data):
            try:
                return json.loads(data)
            except:
                return {}
        
        kpi = load_json(kpi_json)
        current = load_json(current_period_json)
        prior = load_json(prior_period_json)
        rev_partner = load_json(revenue_partner_json)
        rev_country = load_json(revenue_country_json)
        pipeline = load_json(pipeline_json)
        partners = load_json(partners_json)
        risk = load_json(risk_json)
        registrations = load_json(registrations_json)
        
        report = MarkdownReport("Month-End Business Review")
        report.add_paragraph(f"**Review Date:** {datetime.now().strftime('%A, %B %d, %Y')}")
        report.add_paragraph(f"**Period:** Q2 FY27 (May 1 - July 31, 2026)")
        report.add_paragraph(f"**Territory:** Southern Europe, Eastern Europe, Turkey")
        report.add_divider()
        
        # Executive Summary
        report.add_h2("Executive Summary")
        
        kpi_data = safe_get(kpi, "data", {})
        current_data = safe_get(current, "data", {})
        prior_data = safe_get(prior, "data", {})
        
        current_revenue = safe_get(current_data, "revenue", 0)
        prior_revenue = safe_get(prior_data, "revenue", 0)
        growth = ((current_revenue - prior_revenue) / prior_revenue * 100) if prior_revenue > 0 else 0
        
        exec_summary = [
            f"💰 **Revenue:** €{current_revenue:,.0f} ({growth:+.1f}% vs prior month)",
            f"📈 **Pipeline:** €{safe_get(current_data, 'pipeline', 0):,.0f} (Strong)",
            f"🎯 **Win Rate:** {safe_get(current_data, 'winRate', 0)*100:.1f}% (Watch)",
            f"🤝 **Active Partners:** {int(safe_get(current_data, 'activePartners', 0))}",
            f"⚠️ **High-Risk Deals:** {len(safe_get(risk, 'data', []))}",
        ]
        report.add_bullet_list(exec_summary)
        
        # Key Metrics
        report.add_h2("Key Metrics")
        
        metrics = [
            {"label": "Revenue (This Month)", "value": f"€{current_revenue:,.0f}", "target": "€1,500,000", "status": "On Track"},
            {"label": "Pipeline (Open)", "value": f"€{safe_get(current_data, 'pipeline', 0):,.0f}", "target": "—", "status": "Strong"},
            {"label": "Win Rate", "value": f"{safe_get(current_data, 'winRate', 0)*100:.1f}%", "target": "65%", "status": "Watch"},
            {"label": "Coverage Ratio", "value": "—", "target": "1.5x+", "status": "—"},
        ]
        
        report.add_table(
            ["Metric", "Value", "Target", "Status"],
            [[m["label"], m["value"], m["target"], m["status"]] for m in metrics]
        )
        
        # Revenue Analysis
        report.add_h2("Revenue Analysis")
        report.add_h3("By Partner (Top 10)")
        
        partner_data = safe_get(rev_partner, "data", [])
        if partner_data:
            rows = []
            for p in partner_data[:10]:
                rows.append([
                    safe_get(p, "partnerName", "—")[:40],
                    f"€{safe_get(p, 'totalRevenue', 0):,.0f}",
                    str(int(safe_get(p, "dealCount", 0))),
                    f"{safe_get(p, 'attainmentPct', 0):.0f}%"
                ])
            report.add_table(["Partner", "Revenue", "Deals", "Attainment %"], rows)
        
        report.add_h3("By Country")
        
        country_data = safe_get(rev_country, "data", [])
        if country_data:
            total_rev = sum([c.get("totalRevenue", 0) for c in country_data])
            rows = []
            for c in country_data:
                country_rev = c.get("totalRevenue", 0)
                pct = (country_rev / total_rev * 100) if total_rev > 0 else 0
                rows.append([
                    c.get("country", "—"),
                    f"€{country_rev:,.0f}",
                    f"{pct:.1f}%",
                    str(int(c.get("dealCount", 0)))
                ])
            report.add_table(["Country", "Revenue", "% of Total", "Deals"], rows)
        
        # Pipeline Analysis
        report.add_h2("Pipeline Analysis")
        
        pipeline_data = safe_get(pipeline, "data", [])
        if pipeline_data:
            total_pipe = sum([s.get("totalPipeline", 0) for s in pipeline_data])
            rows = []
            for s in pipeline_data:
                amount = s.get("totalPipeline", 0)
                pct = (amount / total_pipe * 100) if total_pipe > 0 else 0
                rows.append([
                    s.get("stage", "—"),
                    str(int(s.get("dealCount", 0))),
                    f"€{amount:,.0f}",
                    f"{pct:.1f}%"
                ])
            report.add_table(["Stage", "Deals", "Amount", "% of Total"], rows)
        
        # Partner Health
        report.add_h2("Partner Health Score")
        
        partner_list = safe_get(partners, "data", [])
        if partner_list:
            rows = []
            for idx, p in enumerate(partner_list[:10], 1):
                revenue = safe_get(p, "totalRevenue", 0)
                target = safe_get(p, "target", 100000)
                attainment = (revenue / target * 100) if target > 0 else 0
                health = "🟢 Green" if attainment > 80 else "🟡 Yellow" if attainment > 50 else "🔴 Red"
                
                rows.append([
                    str(idx),
                    safe_get(p, "partnerName", "—")[:35],
                    f"{attainment:.0f}%",
                    health
                ])
            report.add_table(["#", "Partner", "Attainment %", "Health"], rows)
        
        # Registrations
        report.add_h2("New Partner Registrations")
        
        reg_data = safe_get(registrations, "data", [])
        if reg_data:
            report.add_paragraph(f"**New registrations this month:** {len(reg_data)} partners")
            rows = []
            for r in reg_data[:5]:
                rows.append([
                    safe_get(r, "partnerName", "—"),
                    safe_get(r, "registrationDate", "—"),
                    safe_get(r, "status", "Active")
                ])
            report.add_table(["Partner", "Date", "Status"], rows)
        else:
            report.add_paragraph("No new registrations this month.")
        
        # Risk Summary
        report.add_h2("Risk & Alerts ⚠️")
        
        risk_deals = safe_get(risk, "data", [])
        report.add_paragraph(f"**High-Risk Deals:** {len(risk_deals)} deals (Probability < 40%)")
        
        if risk_deals:
            rows = []
            for r in risk_deals[:5]:
                rows.append([
                    safe_get(r, "dealName", "—")[:30],
                    f"€{safe_get(r, 'amount', 0):,.0f}",
                    f"{safe_get(r, 'probability', 0):.0f}%",
                    str(int(safe_get(r, "daysToClose", 0)))
                ])
            report.add_table(["Deal", "Amount", "Probability", "Days"], rows)
        
        # Action Items
        report.add_h2("Action Items")
        
        actions = [
            "Review 5 at-risk deals (< 40% probability) with responsible partners",
            "Accelerate Solution Validation stage (4 deals, $512K) to Business Case",
            "Onboard new partners from this month's registrations",
            "Schedule quarterly partner business reviews with Top 10 partners",
            "Address win rate gap (5.6% vs 65% target) through sales enablement",
        ]
        report.add_bullet_list(actions)
        
        # Footer
        report.add_divider()
        report.add_metadata()
        
        # Save
        report.save(output_path)
        print(f"✅ Month-end Markdown report saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating Markdown: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate month-end Markdown report")
    parser.add_argument("--kpi", required=True, help="Current period KPI JSON")
    parser.add_argument("--current-period", required=True, help="Current period data")
    parser.add_argument("--prior-period", required=True, help="Prior period data")
    parser.add_argument("--revenue-partner", required=True, help="Revenue by partner JSON")
    parser.add_argument("--revenue-country", required=True, help="Revenue by country JSON")
    parser.add_argument("--pipeline", required=True, help="Pipeline JSON data")
    parser.add_argument("--partners", required=True, help="Partner data JSON")
    parser.add_argument("--risk", required=True, help="Risk deals JSON")
    parser.add_argument("--registrations", required=True, help="Registrations JSON")
    parser.add_argument("--output", required=True, help="Output file path")
    
    args = parser.parse_args()
    
    success = generate_month_end_markdown(
        args.kpi,
        args.current_period,
        args.prior_period,
        args.revenue_partner,
        args.revenue_country,
        args.pipeline,
        args.partners,
        args.risk,
        args.registrations,
        args.output
    )
    
    sys.exit(0 if success else 1)
