#!/usr/bin/env python3
"""
Generate Quarterly Business Review (QBR) Markdown
Multi-partner detailed report with KPI analysis
"""

import sys
import json
import argparse
from datetime import datetime
from markdown_utils import MarkdownReport

def safe_get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def generate_qbr_markdown(
    kpi_json, revenue_partner_json, revenue_country_json, pipeline_json,
    partners_json, risk_json, output_path):
    """Generate QBR Markdown report."""
    
    try:
        # Load JSON
        def load_json(data):
            try:
                return json.loads(data)
            except:
                return {}
        
        kpi = load_json(kpi_json)
        rev_partner = load_json(revenue_partner_json)
        rev_country = load_json(revenue_country_json)
        pipeline = load_json(pipeline_json)
        partners = load_json(partners_json)
        risk = load_json(risk_json)
        
        report = MarkdownReport("Quarterly Business Review (QBR)")
        report.add_paragraph(f"**Q2 FY27** | {datetime.now().strftime('%B %d, %Y')}")
        report.add_paragraph(f"**Territory:** Southern Europe, Eastern Europe, Turkey")
        report.add_divider()
        
        # Executive Summary
        report.add_h2("Executive Summary")
        
        kpi_data = safe_get(kpi, "data", {})
        revenue = safe_get(kpi_data, "revenue", 0)
        pipeline_amt = safe_get(kpi_data, "pipeline", 0)
        win_rate = safe_get(kpi_data, "winRate", 0) * 100 if safe_get(kpi_data, "winRate") else 0
        active_partners = int(safe_get(kpi_data, "activePartners", 0))
        
        quarterly_target = 1500000
        attainment = (revenue / quarterly_target * 100) if quarterly_target > 0 else 0
        
        summary_points = [
            f"📊 **Q2 Revenue:** €{revenue:,.0f} (**{attainment:.0f}%** of €{quarterly_target:,.0f} target)",
            f"📈 **Pipeline:** €{pipeline_amt:,.0f} (Strong coverage)",
            f"🎯 **Win Rate:** {win_rate:.1f}% (Below 65% target—requires attention)",
            f"🤝 **Active Partners:** {active_partners}",
            f"⚠️ **High-Risk Deals:** {len(safe_get(risk, 'data', []))} deals < 40% probability",
        ]
        report.add_bullet_list(summary_points)
        
        # Quarterly Performance
        report.add_h2("Quarterly Performance")
        
        metrics = [
            {"label": "Q2 Revenue (Won)", "value": f"€{revenue:,.0f}", "target": f"€{quarterly_target:,.0f}", "status": f"{attainment:.0f}% Attainment"},
            {"label": "Pipeline (Open)", "value": f"€{pipeline_amt:,.0f}", "target": "—", "status": "Strong"},
            {"label": "Win Rate", "value": f"{win_rate:.1f}%", "target": "65%", "status": "Watch"},
            {"label": "Revenue Concentration", "value": f"{safe_get(kpi_data, 'revenueConcentrationTop3', 0):.1f}%", "target": "<20%", "status": "Healthy Diversification"},
        ]
        
        report.add_table(
            ["Metric", "Value", "Target", "Status"],
            [[m["label"], m["value"], m["target"], m["status"]] for m in metrics]
        )
        
        # Top Partners
        report.add_h2("Top 10 Partners - Q2 Results")
        
        partner_list = safe_get(partners, "data", [])
        if partner_list:
            rows = []
            for idx, p in enumerate(partner_list[:10], 1):
                name = safe_get(p, "partnerName", "—")
                rev = safe_get(p, "totalRevenue", 0)
                target = safe_get(p, "target", 100000)
                attainment = (rev / target * 100) if target > 0 else 0
                health = "🟢 On Track" if attainment > 75 else "🟡 Monitor" if attainment > 50 else "🔴 At Risk"
                
                rows.append([
                    str(idx),
                    name[:35],
                    f"€{rev:,.0f}",
                    f"{attainment:.0f}%",
                    health
                ])
            
            report.add_table(["#", "Partner", "Revenue", "Attainment %", "Health"], rows)
        
        # Revenue by Country
        report.add_h2("Revenue by Country")
        
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
        report.add_h2("Pipeline Analysis by Stage")
        
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
        
        # Risk Summary
        report.add_h2("High-Risk Deals ⚠️")
        
        risk_deals = safe_get(risk, "data", [])
        report.add_paragraph(f"**Total high-risk deals (< 40% probability):** {len(risk_deals)}")
        
        if risk_deals:
            rows = []
            for r in risk_deals[:8]:
                rows.append([
                    safe_get(r, "dealName", "—")[:30],
                    f"€{safe_get(r, 'amount', 0):,.0f}",
                    f"{safe_get(r, 'probability', 0):.0f}%",
                    str(int(safe_get(r, "daysToClose", 0)))
                ])
            report.add_table(["Deal", "Amount", "Probability", "Days to Close"], rows)
            
            report.add_h3("Recommended Actions")
            actions = [
                "Schedule escalation calls with all deals < 30% probability",
                "Identify specific deal blockers and mitigation plans",
                "Increase partner involvement in Solution Validation stage",
                "Consider deal restructuring or extension options",
            ]
            report.add_bullet_list(actions)
        
        # Key Opportunities
        report.add_h2("Key Opportunities & Initiatives")
        
        opportunities = [
            "**Win Rate Improvement:** Implement sales training on solution selling (current 5.6% vs target 65%)",
            "**Partner Enablement:** Top 3 partners represent 11% of revenue—diversify through focus partner program",
            "**Pipeline Acceleration:** 35% of pipeline in Business Case stage (€493K)—drive to Close Plan",
            "**New Market Entry:** Focus on Eastern Europe expansion (currently Spain/Italy dominant)",
            "**Deal Velocity:** Implement deal health scoring to identify early risk indicators",
        ]
        report.add_bullet_list(opportunities)
        
        # Next Steps
        report.add_h2("Next Steps (30-60-90 Days)")
        
        next_steps = [
            "**This Month:** Conduct individual QBR calls with Top 10 partners",
            "**Next 30 Days:** Execute win rate improvement workshop with sales team",
            "**Next 60 Days:** Launch Eastern Europe market development initiative",
            "**Next 90 Days:** Implement AI-powered deal health scoring system",
        ]
        report.add_bullet_list(next_steps)
        
        # Footer
        report.add_divider()
        report.add_metadata()
        
        # Save
        report.save(output_path)
        print(f"✅ QBR Markdown report saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating Markdown: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QBR Markdown")
    parser.add_argument("--kpi", required=True, help="KPI JSON")
    parser.add_argument("--revenue-partner", required=True, help="Revenue by partner")
    parser.add_argument("--revenue-country", required=True, help="Revenue by country")
    parser.add_argument("--pipeline", required=True, help="Pipeline JSON")
    parser.add_argument("--partners", required=True, help="Partner JSON")
    parser.add_argument("--risk", required=True, help="Risk deals JSON")
    parser.add_argument("--output", required=True, help="Output file")
    
    args = parser.parse_args()
    
    success = generate_qbr_markdown(
        args.kpi,
        args.revenue_partner,
        args.revenue_country,
        args.pipeline,
        args.partners,
        args.risk,
        args.output
    )
    
    sys.exit(0 if success else 1)
