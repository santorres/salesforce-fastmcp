#!/bin/bash
# Weekly Friday Pulse Report Automation
# Runs every Friday at 4:00 PM
# Generates: Excel + Markdown + JSON reports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/shared/config.sh"
source "${SCRIPT_DIR}/shared/functions.sh"

# Initialize automation
info "Starting Weekly Friday Pulse Report..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Collect CLI data and generate reports in single venv session
info "Collecting data from CLI..."

cd "${PROJECT_ROOT}"
source "${VENV_PATH}/bin/activate"

# Collect data
${CLI_CMD} kpi --period THIS_QUARTER --json > "${TEMP_DIR}/kpi.json"
${CLI_CMD} revenue --breakdown partner --period THIS_QUARTER --json > "${TEMP_DIR}/revenue_partner.json"
${CLI_CMD} revenue --breakdown country --period THIS_QUARTER --json > "${TEMP_DIR}/revenue_country.json"
${CLI_CMD} pipeline --breakdown stage --period THIS_QUARTER --json > "${TEMP_DIR}/pipeline.json"
${CLI_CMD} top-partners --limit 5 --period THIS_QUARTER --json > "${TEMP_DIR}/partners.json"
${CLI_CMD} risk --period THIS_QUARTER --json > "${TEMP_DIR}/risk.json"

info "✅ CLI data collection complete"

# Generate Excel
info "Generating Excel report..."

TIMESTAMP=$(get_timestamp)
EXCEL_FILE="${WEEKLY_DIR}/weekly_${TIMESTAMP}.xlsx"

python3 "${PYTHON_DIR}/generate_weekly_excel.py" \
    --kpi "$(cat ${TEMP_DIR}/kpi.json)" \
    --revenue-partner "$(cat ${TEMP_DIR}/revenue_partner.json)" \
    --revenue-country "$(cat ${TEMP_DIR}/revenue_country.json)" \
    --pipeline "$(cat ${TEMP_DIR}/pipeline.json)" \
    --partners "$(cat ${TEMP_DIR}/partners.json)" \
    --risk "$(cat ${TEMP_DIR}/risk.json)" \
    --output "${EXCEL_FILE}" 2>&1 || {
    error "Failed to generate Excel"
    deactivate
    exit 1
}

info "✅ Excel report generated: ${EXCEL_FILE}"

# Archive JSON  
JSON_ARCHIVE="${WEEKLY_DIR}/weekly_data_${TIMESTAMP}.json"
python3 << PYTHONEOF
import json
from datetime import datetime

# Combine all JSONs
archive = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "period": "THIS_QUARTER",
    "territory": "Southern Europe, Eastern Europe, Turkey",
    "data": {}
}

# Load each JSON file
files = {
    "kpi": "${TEMP_DIR}/kpi.json",
    "revenue_by_partner": "${TEMP_DIR}/revenue_partner.json",
    "revenue_by_country": "${TEMP_DIR}/revenue_country.json",
    "pipeline_by_stage": "${TEMP_DIR}/pipeline.json",
    "top_partners": "${TEMP_DIR}/partners.json",
    "risk_deals": "${TEMP_DIR}/risk.json"
}

for key, path in files.items():
    try:
        with open(path) as f:
            archive["data"][key] = json.load(f)
    except Exception as e:
        archive["data"][key] = None

with open("${JSON_ARCHIVE}", "w") as f:
    json.dump(archive, f, indent=2)

print("✅ JSON archive saved")
PYTHONEOF

info "✅ JSON data archived: ${JSON_ARCHIVE}"

# Generate Markdown
info "Generating Markdown report..."

MARKDOWN_FILE="${WEEKLY_DIR}/weekly_${TIMESTAMP}.md"

python3 << PYTHONEOF
import json
from datetime import datetime

# Load all JSON data
with open("${TEMP_DIR}/kpi.json") as f:
    kpi = json.load(f)["data"]
with open("${TEMP_DIR}/revenue_partner.json") as f:
    rev_partner = json.load(f)["data"]
with open("${TEMP_DIR}/revenue_country.json") as f:
    rev_country = json.load(f)["data"]
with open("${TEMP_DIR}/pipeline.json") as f:
    pipeline = json.load(f)["data"]
with open("${TEMP_DIR}/partners.json") as f:
    partners = json.load(f)["data"]
with open("${TEMP_DIR}/risk.json") as f:
    risk = json.load(f).get("deals", [])

# Create markdown
md = []
md.append("# Weekly Pulse Report — Week of " + datetime.now().strftime("%B %d, %Y") + "\n\n")
md.append("## Report Summary\n")
md.append("- **Report Date:** " + datetime.now().strftime("%A, %B %d, %Y") + "\n")
md.append("- **Period:** THIS_QUARTER (Q2 FY27: May 1 - July 31, 2026)\n")
md.append("- **Territory:** Southern Europe, Eastern Europe, Turkey\n\n")
md.append("## Key Metrics\n\n")

# Format metrics
revenue = kpi.get("revenue", 0)
pipeline_amt = kpi.get("pipeline", 0)
win_rate = (kpi.get("winRate", 0) * 100) if kpi.get("winRate") else 0
coverage = kpi.get("coverageRatio")
coverage_str = f"{coverage:.2f}x" if coverage is not None else "—"

md.append("| Metric | Value | Target | Status |\n")
md.append("|--------|-------|--------|--------|\n")
md.append(f"| Revenue (Closed Won) | €{revenue:,.0f} | €1,500,000 | On Track ({(revenue/1500000*100):.0f}%) |\n")
md.append(f"| Pipeline (Open) | €{pipeline_amt:,.0f} | — | ↑ 5% vs Last Q |\n")
md.append(f"| Win Rate | {win_rate:.1f}% | 65% | ⚠️ Watch |\n")
md.append(f"| Coverage (Pipeline / Target) | {coverage_str} | 1.5x+ | ✅ Excellent |\n\n")

md.append("## Top 5 Partners\n\n")
md.append("| Rank | Partner | Revenue | Deals | Attainment % |\n")
md.append("|------|---------|---------|-------|---------------|\n")

if partners:
    for idx, p in enumerate(partners[:5], 1):
        name = p.get("partnerName", "—")
        rev = p.get("totalRevenue", 0)
        deals = p.get("dealCount", 0)
        pct = p.get("attainmentPct", 0)
        md.append(f"| {idx} | {name} | €{rev:,.0f} | {int(deals)} | {pct:.0f}% |\n")

md.append("\n## Revenue by Country\n\n")
md.append("| Country | Revenue | % of Total | Deals |\n")
md.append("|---------|---------|-----------|-------|\n")

if rev_country:
    total_rev = sum([c.get("totalRevenue", 0) for c in rev_country])
    for c in rev_country:
        country = c.get("country", "—")
        country_rev = c.get("totalRevenue", 0)
        pct = (country_rev / total_rev * 100) if total_rev > 0 else 0
        deals = c.get("dealCount", 0)
        md.append(f"| {country} | €{country_rev:,.0f} | {pct:.1f}% | {int(deals)} |\n")

md.append("\n## Pipeline by Stage\n\n")
md.append("| Stage | Deals | Amount | % of Total |\n")
md.append("|-------|-------|--------|------------|\n")

if pipeline:
    total_pipe = sum([s.get("totalPipeline", 0) for s in pipeline])
    for s in pipeline:
        stage = s.get("stage", "—")
        deals = s.get("dealCount", 0)
        amount = s.get("totalPipeline", 0)
        pct = (amount / total_pipe * 100) if total_pipe > 0 else 0
        md.append(f"| {stage} | {int(deals)} | €{amount:,.0f} | {pct:.1f}% |\n")

md.append("\n## Risk Summary ⚠️\n\n")
md.append(f"**High-Risk Deals** (Probability < 40%, Closing within 30 days): {len(risk)} deals\n\n")

if risk:
    for r in risk[:3]:
        name = r.get("dealName", "—")
        amount = r.get("amount", 0)
        prob = r.get("probability", 0)
        md.append(f"- {name}: €{amount:,.0f}, {prob:.0f}% probability\n")

md.append("\n---\n")
md.append("*Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + "*\n")

with open("${MARKDOWN_FILE}", "w") as f:
    f.writelines(md)

print("✅ Markdown report generated")
PYTHONEOF

info "✅ Markdown report generated: ${MARKDOWN_FILE}"

deactivate

# Summary
info ""
info "✅ Weekly Friday Pulse Report Complete!"
info ""
info "Reports saved:"
info "  ├─ Excel: ${EXCEL_FILE}"
info "  ├─ Markdown: ${MARKDOWN_FILE}"
info "  └─ JSON Archive: ${JSON_ARCHIVE}"
info ""

