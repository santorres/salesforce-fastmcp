#!/usr/bin/env python3
"""
Generate Weekly Excel Report
Combines KPI, revenue, pipeline, and risk data into a professional Excel report
"""

import sys
import json
import argparse
from datetime import datetime
from excel_utils import ExcelReport, load_json_data, format_currency, format_percentage, safe_get

def generate_weekly_excel(kpi_json, revenue_partner_json, revenue_country_json, 
                         pipeline_json, partners_json, risk_json, output_path):
    """Generate weekly Excel report with 5 sheets."""
    
    try:
        # Parse all JSON inputs
        kpi_data = load_json_data(kpi_json)
        rev_partner = load_json_data(revenue_partner_json)
        rev_country = load_json_data(revenue_country_json)
        pipeline = load_json_data(pipeline_json)
        partners = load_json_data(partners_json)
        risk = load_json_data(risk_json)
        
        if not kpi_data:
            print("❌ Failed to parse KPI data")
            return False
        
        # Create Excel workbook
        report = ExcelReport()
        
        # ========== SHEET 1: SUMMARY ==========
        report.add_sheet("Summary")
        report.add_title("Weekly Pulse Report", 
                        f"Week of {datetime.now().strftime('%B %d, %Y')}")
        
        # Report metadata
        report.add_metric("Report Date", datetime.now().strftime("%A, %B %d, %Y"))
        report.add_metric("Period", "THIS_QUARTER (Q2 FY27)")
        report.add_metric("Territory", "Southern Europe, Eastern Europe, Turkey")
        
        report.add_blank_rows(1)
        
        # Key metrics
        kpi_obj = safe_get(kpi_data, "data", {})
        coverage_ratio = safe_get(kpi_obj, "coverageRatio")
        coverage_str = f"{coverage_ratio:.2f}x" if coverage_ratio is not None else "—"
        
        metrics = [
            ["Revenue (Closed Won)", format_currency(safe_get(kpi_obj, "revenue")), 
             format_currency(1500000), "On Track"],
            ["Pipeline (Open)", format_currency(safe_get(kpi_obj, "pipeline")), 
             "—", "Strong"],
            ["Win Rate", format_percentage(safe_get(kpi_obj, "winRate")), 
             "65%", "Watch"],
            ["Coverage Ratio", coverage_str, 
             "1.5x+", "Excellent"],
            ["Active Partners", str(int(safe_get(kpi_obj, "activePartners", 0))), 
             "—", "—"],
            ["Focus Partners", str(int(safe_get(kpi_obj, "focusPartners", 0))), 
             "—", "—"],
        ]
        
        headers = ["Metric", "Value", "Target", "Status"]
        report.add_table(headers, metrics)
        
        report.add_blank_rows(1)
        report.add_metric("High-Risk Deals", str(len(safe_get(risk, "data", []))))
        
        # ========== SHEET 2: REVENUE BY PARTNER ==========
        report.add_sheet("Revenue by Partner")
        report.add_title("Revenue by Partner", "THIS_QUARTER")
        
        partner_data = safe_get(rev_partner, "data", [])
        if partner_data:
            headers = ["Partner", "Revenue", "Deals", "Attainment %"]
            table_data = []
            for p in partner_data[:10]:
                table_data.append([
                    safe_get(p, "partnerName", "—"),
                    format_currency(safe_get(p, "totalRevenue")),
                    str(int(safe_get(p, "dealCount", 0))),
                    f"{safe_get(p, 'attainmentPct', 0):.1f}%"
                ])
            report.add_table(headers, table_data)
        
        # ========== SHEET 3: REVENUE BY COUNTRY ==========
        report.add_sheet("Revenue by Country")
        report.add_title("Revenue by Country", "THIS_QUARTER")
        
        country_data = safe_get(rev_country, "data", [])
        if country_data:
            total_rev = sum([c.get("totalRevenue", 0) for c in country_data])
            headers = ["Country", "Revenue", "% of Total", "Deals"]
            table_data = []
            for c in country_data:
                country_rev = c.get("totalRevenue", 0)
                pct = (country_rev / total_rev * 100) if total_rev > 0 else 0
                table_data.append([
                    c.get("country", "—"),
                    format_currency(country_rev),
                    f"{pct:.1f}%",
                    str(int(c.get("dealCount", 0)))
                ])
            report.add_table(headers, table_data)
        
        # ========== SHEET 4: PIPELINE BY STAGE ==========
        report.add_sheet("Pipeline by Stage")
        report.add_title("Pipeline by Stage", "THIS_QUARTER")
        
        pipeline_data = safe_get(pipeline, "data", [])
        if pipeline_data:
            total_pipe = sum([s.get("totalPipeline", 0) for s in pipeline_data])
            headers = ["Stage", "Deals", "Amount", "% of Total"]
            table_data = []
            for s in pipeline_data:
                amount = s.get("totalPipeline", 0)
                pct = (amount / total_pipe * 100) if total_pipe > 0 else 0
                table_data.append([
                    s.get("stage", "—"),
                    str(int(s.get("dealCount", 0))),
                    format_currency(amount),
                    f"{pct:.1f}%"
                ])
            report.add_table(headers, table_data)
        
        # ========== SHEET 5: TOP PARTNERS & RISK ==========
        report.add_sheet("Partners & Risk")
        report.add_title("Top Partners & Risk Summary", "THIS_QUARTER")
        
        # Top 5 partners
        partner_list = safe_get(partners, "data", [])
        if partner_list:
            report.add_metric("Top Partners", "")
            headers = ["Rank", "Partner", "Revenue", "Deals", "Attainment %"]
            table_data = []
            for idx, p in enumerate(partner_list[:5], 1):
                table_data.append([
                    str(idx),
                    safe_get(p, "partnerName", "—"),
                    format_currency(safe_get(p, "totalRevenue")),
                    str(int(safe_get(p, "dealCount", 0))),
                    f"{safe_get(p, 'attainmentPct', 0):.1f}%"
                ])
            report.add_table(headers, table_data)
        
        # Risk deals
        report.add_blank_rows(1)
        risk_deals = safe_get(risk, "data", [])
        report.add_metric("High-Risk Deals", str(len(risk_deals)))
        
        if risk_deals:
            headers = ["Deal", "Amount", "Probability", "Days to Close"]
            table_data = []
            for r in risk_deals[:5]:
                table_data.append([
                    safe_get(r, "dealName", "—"),
                    format_currency(safe_get(r, "amount")),
                    f"{safe_get(r, 'probability', 0):.0f}%",
                    str(int(safe_get(r, "daysToClose", 0)))
                ])
            report.add_table(headers, table_data)
        
        # Save workbook
        report.save(output_path)
        print(f"✅ Excel report saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate weekly Excel report")
    parser.add_argument("--kpi", required=True, help="KPI JSON data")
    parser.add_argument("--revenue-partner", required=True, help="Revenue by partner JSON")
    parser.add_argument("--revenue-country", required=True, help="Revenue by country JSON")
    parser.add_argument("--pipeline", required=True, help="Pipeline JSON data")
    parser.add_argument("--partners", required=True, help="Top partners JSON data")
    parser.add_argument("--risk", required=True, help="Risk deals JSON data")
    parser.add_argument("--output", required=True, help="Output Excel file path")
    
    args = parser.parse_args()
    
    success = generate_weekly_excel(
        args.kpi,
        args.revenue_partner,
        args.revenue_country,
        args.pipeline,
        args.partners,
        args.risk,
        args.output
    )
    
    sys.exit(0 if success else 1)
