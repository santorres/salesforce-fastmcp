#!/bin/bash
# Month-End Business Review Automation
# Runs automatically on month-end (last day of month)
# Generates: Excel (10 sheets) + Markdown + JSON reports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/shared/config.sh"
source "${SCRIPT_DIR}/shared/functions.sh"

# Initialize automation
info "Starting Month-End Business Review..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Collect CLI data and generate reports in single venv session
info "Collecting data from CLI..."

cd "${PROJECT_ROOT}"
source "${VENV_PATH}/bin/activate"

# Current period (THIS_QUARTER)
${CLI_CMD} kpi --period THIS_QUARTER --json > "${TEMP_DIR}/kpi.json"
${CLI_CMD} kpi --period THIS_QUARTER --json > "${TEMP_DIR}/current_period.json"
${CLI_CMD} kpi --period LAST_QUARTER --json > "${TEMP_DIR}/prior_period.json"
${CLI_CMD} revenue --breakdown partner --period THIS_QUARTER --json > "${TEMP_DIR}/revenue_partner.json"
${CLI_CMD} revenue --breakdown country --period THIS_QUARTER --json > "${TEMP_DIR}/revenue_country.json"
${CLI_CMD} pipeline --breakdown stage --period THIS_QUARTER --json > "${TEMP_DIR}/pipeline.json"
${CLI_CMD} top-partners --limit 15 --period THIS_QUARTER --json > "${TEMP_DIR}/partners.json"
${CLI_CMD} risk --period THIS_QUARTER --json > "${TEMP_DIR}/risk.json"

# Registrations (use empty if not available)
${CLI_CMD} partners --period THIS_QUARTER --json > "${TEMP_DIR}/registrations.json" 2>/dev/null || echo '{"data":[]}' > "${TEMP_DIR}/registrations.json"

info "✅ CLI data collection complete"

# Generate Excel
info "Generating Excel report..."

TIMESTAMP=$(get_timestamp)
MONTH=$(date +%m)
YEAR=$(date +%Y)

EXCEL_FILE="${MONTHLY_DIR}/month_end_${YEAR}${MONTH}.xlsx"

python3 "${PYTHON_DIR}/generate_month_end_excel.py" \
    --kpi "$(cat ${TEMP_DIR}/kpi.json)" \
    --current-period "$(cat ${TEMP_DIR}/current_period.json)" \
    --prior-period "$(cat ${TEMP_DIR}/prior_period.json)" \
    --revenue-partner "$(cat ${TEMP_DIR}/revenue_partner.json)" \
    --revenue-country "$(cat ${TEMP_DIR}/revenue_country.json)" \
    --pipeline "$(cat ${TEMP_DIR}/pipeline.json)" \
    --partners "$(cat ${TEMP_DIR}/partners.json)" \
    --risk "$(cat ${TEMP_DIR}/risk.json)" \
    --registrations "$(cat ${TEMP_DIR}/registrations.json)" \
    --output "${EXCEL_FILE}" 2>&1 || {
    error "Failed to generate Excel"
    deactivate
    exit 1
}

info "✅ Excel report generated: ${EXCEL_FILE}"

# Generate Markdown
info "Generating Markdown report..."

MARKDOWN_FILE="${MONTHLY_DIR}/month_end_${YEAR}${MONTH}.md"

python3 "${PYTHON_DIR}/generate_month_end_markdown.py" \
    --kpi "$(cat ${TEMP_DIR}/kpi.json)" \
    --current-period "$(cat ${TEMP_DIR}/current_period.json)" \
    --prior-period "$(cat ${TEMP_DIR}/prior_period.json)" \
    --revenue-partner "$(cat ${TEMP_DIR}/revenue_partner.json)" \
    --revenue-country "$(cat ${TEMP_DIR}/revenue_country.json)" \
    --pipeline "$(cat ${TEMP_DIR}/pipeline.json)" \
    --partners "$(cat ${TEMP_DIR}/partners.json)" \
    --risk "$(cat ${TEMP_DIR}/risk.json)" \
    --registrations "$(cat ${TEMP_DIR}/registrations.json)" \
    --output "${MARKDOWN_FILE}" 2>&1 || {
    error "Failed to generate Markdown"
    deactivate
    exit 1
}

info "✅ Markdown report generated: ${MARKDOWN_FILE}"

# Archive JSON
JSON_ARCHIVE="${MONTHLY_DIR}/month_end_data_${YEAR}${MONTH}.json"
python3 << PYTHONEOF
import json
from datetime import datetime

archive = {
    "timestamp": datetime.now().isoformat() + "Z",
    "period": "THIS_QUARTER",
    "month": "${MONTH}",
    "year": "${YEAR}",
    "territory": "Southern Europe, Eastern Europe, Turkey",
    "data": {}
}

files = {
    "kpi": "${TEMP_DIR}/kpi.json",
    "revenue_by_partner": "${TEMP_DIR}/revenue_partner.json",
    "revenue_by_country": "${TEMP_DIR}/revenue_country.json",
    "pipeline_by_stage": "${TEMP_DIR}/pipeline.json",
    "partners": "${TEMP_DIR}/partners.json",
    "risk_deals": "${TEMP_DIR}/risk.json",
    "registrations": "${TEMP_DIR}/registrations.json"
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
info "✅ Month-End Business Review Complete!"
info ""
info "Reports saved:"
info "  ├─ Excel (10 sheets): ${EXCEL_FILE}"
info "  ├─ Markdown: ${MARKDOWN_FILE}"
info "  └─ JSON Archive: ${JSON_ARCHIVE}"
info ""

