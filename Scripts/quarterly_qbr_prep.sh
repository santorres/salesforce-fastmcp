#!/bin/bash
# Quarterly QBR Preparation Automation
# Runs automatically at quarter-end
# Generates: Excel (12+ partner sheets) + Markdown + JSON reports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/shared/config.sh"
source "${SCRIPT_DIR}/shared/functions.sh"

# Initialize automation
info "Starting Quarterly QBR Preparation..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Collect CLI data
info "Collecting data from CLI..."

cd "${PROJECT_ROOT}"
source "${VENV_PATH}/bin/activate"

# Collect all necessary data
${CLI_CMD} kpi --period THIS_QUARTER --json > "${TEMP_DIR}/kpi.json"
${CLI_CMD} revenue --breakdown partner --period THIS_QUARTER --json > "${TEMP_DIR}/revenue_partner.json"
${CLI_CMD} revenue --breakdown country --period THIS_QUARTER --json > "${TEMP_DIR}/revenue_country.json"
${CLI_CMD} pipeline --breakdown stage --period THIS_QUARTER --json > "${TEMP_DIR}/pipeline.json"
${CLI_CMD} top-partners --limit 20 --period THIS_QUARTER --json > "${TEMP_DIR}/partners.json"
${CLI_CMD} risk --period THIS_QUARTER --json > "${TEMP_DIR}/risk.json"

info "✅ CLI data collection complete"

# Generate Excel
info "Generating QBR Excel report..."

TIMESTAMP=$(get_timestamp)
YEAR=$(date +%Y)

EXCEL_FILE="${QBR_DIR}/qbr_summary_${TIMESTAMP}.xlsx"

python3 "${PYTHON_DIR}/generate_qbr_excel.py" \
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

info "✅ QBR Excel report generated: ${EXCEL_FILE}"

# Generate Markdown
info "Generating QBR Markdown report..."

MARKDOWN_FILE="${QBR_DIR}/qbr_summary_${TIMESTAMP}.md"

python3 "${PYTHON_DIR}/generate_qbr_markdown.py" \
    --kpi "$(cat ${TEMP_DIR}/kpi.json)" \
    --revenue-partner "$(cat ${TEMP_DIR}/revenue_partner.json)" \
    --revenue-country "$(cat ${TEMP_DIR}/revenue_country.json)" \
    --pipeline "$(cat ${TEMP_DIR}/pipeline.json)" \
    --partners "$(cat ${TEMP_DIR}/partners.json)" \
    --risk "$(cat ${TEMP_DIR}/risk.json)" \
    --output "${MARKDOWN_FILE}" 2>&1 || {
    error "Failed to generate Markdown"
    deactivate
    exit 1
}

info "✅ QBR Markdown report generated: ${MARKDOWN_FILE}"

# Archive JSON
JSON_ARCHIVE="${QBR_DIR}/qbr_data_${TIMESTAMP}.json"
python3 << PYTHONEOF
import json
from datetime import datetime

archive = {
    "timestamp": datetime.now().isoformat() + "Z",
    "quarter": "Q2",
    "year": 2026,
    "territory": "Southern Europe, Eastern Europe, Turkey",
    "data": {}
}

files = {
    "kpi": "${TEMP_DIR}/kpi.json",
    "revenue_by_partner": "${TEMP_DIR}/revenue_partner.json",
    "revenue_by_country": "${TEMP_DIR}/revenue_country.json",
    "pipeline_by_stage": "${TEMP_DIR}/pipeline.json",
    "partners": "${TEMP_DIR}/partners.json",
    "risk_deals": "${TEMP_DIR}/risk.json"
}

for key, path in files.items():
    try:
        with open(path) as f:
            archive["data"][key] = json.load(f)
    except:
        archive["data"][key] = None

with open("${JSON_ARCHIVE}", "w") as f:
    json.dump(archive, f, indent=2)

print("✅ JSON archive saved")
PYTHONEOF

info "✅ JSON data archived: ${JSON_ARCHIVE}"

deactivate

# Summary
info ""
info "✅ Quarterly QBR Preparation Complete!"
info ""
info "Reports saved:"
info "  ├─ Excel (Summary + 12 Partner Sheets): ${EXCEL_FILE}"
info "  ├─ Markdown: ${MARKDOWN_FILE}"
info "  └─ JSON Archive: ${JSON_ARCHIVE}"
info ""
info "Next: Review reports and schedule 10-15 partner QBR calls"
info ""

