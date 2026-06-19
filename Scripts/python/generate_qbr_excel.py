#!/usr/bin/env python3
"""
Generate Quarterly Business Review (QBR) Excel Report
Summary sheet + individual partner detail sheets (Top 10-15 partners)
"""

import sys
import json
import argparse
from datetime import datetime
from excel_utils import ExcelReport, load_json_data, format_currency, format_percentage, safe_get

def generate_qbr_excel(
    kpi_json, revenue_partner_json, revenue_country_json, pipeline_json,
    partners_json, risk_json, output_path):
    """Generate QBR Excel with summary + partner detail sheets."""
    
    try:
        # Parse JSON
        kpi = load_json_data(kpi_json)
        rev_partner = load_json_data(revenue_partner_json)
        rev_country = load_json_data(revenue_country_json)
        pipeline = load_json_data(pipeline_json)
        partners = load_json_data(partners_json)
        risk = load_json_data(risk_json)
        
        if not kpi:
            print("❌ Failed to parse KPI data")
            return False
        
        report = ExcelReport()
        kpi_data = safe_get(kpi, "data", {})
        
        # ========== SHEET 1: EXECUTIVE SUMMARY ==========
        report.add_sheet("QBR Summary")
        report.add_title("Quarterly Business Review (QBR)",
                        f"Q2 FY27 - {datetime.now().strftime('%B %d, %Y')}")
        
        report.add_metric("Review Date", datetime.now().strftime("%A, %B %d, %Y"))
        report.add_metric("Quarter", "Q2 FY27 (May 1 - July 31, 2026)")
        report.add_metric("Territory", "Southern Europe, Eastern Europe, Turkey")
        
        report.add_blank_rows(1)
        
        # Key metrics
        revenue = safe_get(kpi_data, "revenue", 0)
        pipeline = safe_get(kpi_data, "pipeline", 0)
        win_rate = safe_get(kpi_data, "winRate", 0) * 100 if safe_get(kpi_data, "winRate") else 0
        active_partners = int(safe_get(kpi_data, "activePartners", 0))
        focus_partners = int(safe_get(kpi_data, "focusPartners", 0))
        
        quarterly_target = 1500000
        attainment_pct = (revenue / quarterly_target * 100) if quarterly_target > 0 else 0
        
        metrics = [
            ["Q2 Revenue (Won)", format_currency(revenue), format_currency(quarterly_target),
             f"{attainment_pct:.1f}%"],
            ["Open Pipeline", format_currency(pipeline), "—", "Strong"],
            ["Win Rate", f"{win_rate:.1f}%", "65%", "Watch"],
            ["Active Partners", str(active_partners), "—", "—"],
            ["Focus Partners", str(focus_partners), "—", "—"],
            ["High-Risk Deals", str(len(safe_get(risk, "data", []))), "<5", "Monitor"],
        ]
        
        headers = ["Metric", "Value", "Target", "Status/Attainment"]
        report.add_table(headers, metrics)
        
        report.add_blank_rows(1)
        report.add_metric("Revenue Concentration (Top 3)", f"{safe_get(kpi_data, 'revenueConcentrationTop3', 0):.1f}%")
        
        # ========== SHEET 2: TOP PARTNERS SUMMARY ==========
        report.add_sheet("Top 10 Partners")
        report.add_title("Top 10 Partners - Q2 Performance", "Revenue | Target | Attainment")
        
        partner_list = safe_get(partners, "data", [])
        if partner_list:
            headers = ["Rank", "Partner", "Revenue", "Target", "Attainment %", "QoQ Growth"]
            table_data = []
            for idx, p in enumerate(partner_list[:10], 1):
                name = safe_get(p, "partnerName", "—")
                rev = safe_get(p, "totalRevenue", 0)
                target = safe_get(p, "target", 100000)
                attainment = safe_get(p, "attainmentPct", 0)
                growth = safe_get(p, "qoqGrowth", 0)
                
                table_data.append([
                    str(idx),
                    name[:40],
                    format_currency(rev),
                    format_currency(target),
                    f"{attainment:.0f}%",
                    f"{growth:+.1f}%"
                ])
            report.add_table(headers, table_data)
        
        # ========== SHEETS 3+: INDIVIDUAL PARTNER DETAIL ==========
        for idx, partner in enumerate(partner_list[:12], 1):  # Up to 12 partners
            if idx <= 12:
                partner_name = safe_get(partner, "partnerName", f"Partner {idx}")
                partner_id = safe_get(partner, "partnerId", "")
                
                # Create sheet (no colons allowed in Excel sheet names)
                sheet_name = f"P{idx} - {partner_name[:20]}"
                report.add_sheet(sheet_name)
                report.add_title(f"Partner Detail: {partner_name[:50]}", "Q2 FY27 Analysis")
                
                # Partner metrics
                partner_revenue = safe_get(partner, "totalRevenue", 0)
                partner_target = safe_get(partner, "target", 100000)
                partner_deals = safe_get(partner, "dealCount", 0)
                partner_pipeline = safe_get(partner, "pipeline", 0)
                partner_win_rate = safe_get(partner, "winRate", 0) * 100 if safe_get(partner, "winRate") else 0
                
                partner_attainment = (partner_revenue / partner_target * 100) if partner_target > 0 else 0
                
                metrics = [
                    ["Q2 Revenue", format_currency(partner_revenue), format_currency(partner_target),
                     f"{partner_attainment:.0f}%"],
                    ["Pipeline", format_currency(partner_pipeline), "—", "—"],
                    ["Closed Deals", str(int(partner_deals)), "—", "—"],
                    ["Win Rate", f"{partner_win_rate:.1f}%", "—", "—"],
                    ["Health", "🟢 Good" if partner_attainment > 75 else "🟡 Fair", "—", "—"],
                ]
                
                report.add_table(["Metric", "Value", "Target", "Status"], metrics)
                
                report.add_blank_rows(1)
                
                # Partner actions (simulated)
                report.add_metric("Key Actions", "")
                actions = [
                    f"Schedule QBR call",
                    f"Review deal pipeline (${partner_pipeline:,.0f})",
                    f"Discuss growth opportunities",
                ]
                for action in actions[:3]:
                    report.add_metric("—", action)
        
        # Save workbook
        report.save(output_path)
        print(f"✅ QBR Excel report saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QBR Excel report")
    parser.add_argument("--kpi", required=True, help="KPI JSON data")
    parser.add_argument("--revenue-partner", required=True, help="Revenue by partner")
    parser.add_argument("--revenue-country", required=True, help="Revenue by country")
    parser.add_argument("--pipeline", required=True, help="Pipeline JSON")
    parser.add_argument("--partners", required=True, help="Partner data JSON")
    parser.add_argument("--risk", required=True, help="Risk deals JSON")
    parser.add_argument("--output", required=True, help="Output file path")
    
    args = parser.parse_args()
    
    success = generate_qbr_excel(
        args.kpi,
        args.revenue_partner,
        args.revenue_country,
        args.pipeline,
        args.partners,
        args.risk,
        args.output
    )
    
    sys.exit(0 if success else 1)
