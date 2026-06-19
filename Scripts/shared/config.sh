#!/bin/bash
# Shared Configuration for Channel Director Automation Scripts
# Source this file at the beginning of each automation script

# ═══════════════════════════════════════════════════════════════════════════
# PROJECT PATHS
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ROOT="/Users/santiagot/Applications/salesforce-fastmcp"
VENV_PATH="${PROJECT_ROOT}/.venv"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"
SHARED_DIR="${SCRIPT_DIR}/shared"
PYTHON_DIR="${SCRIPT_DIR}/python"
REPORTS_DIR="${HOME}/reports"

# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT DIRECTORIES (Created automatically)
# ═══════════════════════════════════════════════════════════════════════════

WEEKLY_DIR="${REPORTS_DIR}/weekly/2026"
MONTHLY_DIR="${REPORTS_DIR}/monthly/2026"
QBR_DIR="${REPORTS_DIR}/qbr"
LOGS_DIR="${REPORTS_DIR}/.logs"

# ═══════════════════════════════════════════════════════════════════════════
# CHANNEL DIRECTOR CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

TERRITORY="Southern Europe, Eastern Europe, Turkey"
REGION_CODES="EU_SOUTH,EU_EAST,TR"
CURRENCY="EUR"
TIMEZONE="Europe/Madrid"
DIRECTOR_NAME="Santiago Torres"
DIRECTOR_EMAIL="Santiago.Torres@semperis.com"

# ═══════════════════════════════════════════════════════════════════════════
# REPORTING DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════

# Default period for all reports
DEFAULT_PERIOD="THIS_QUARTER"

# Number of top partners to include in reports
TOP_PARTNERS_LIMIT=10
TOP_PARTNERS_WEEKLY_LIMIT=5

# Risk threshold (deals with probability < this are considered high-risk)
RISK_PROBABILITY_THRESHOLD=40
RISK_DAYS_THRESHOLD=30

# ═══════════════════════════════════════════════════════════════════════════
# CLI COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

# CLI base command (will be executed with full path to venv)
CLI_CMD="python3 -m cli.channel_cli"

# ═══════════════════════════════════════════════════════════════════════════
# FILE NAMING CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Weekly report naming: weekly_YYYYMMDD
# Month-end naming: month_end_YYYYMM
# QBR naming: qbr_summary_YYYYMMDD

# Extensions
EXCEL_EXT="xlsx"
MARKDOWN_EXT="md"
JSON_EXT="json"
LOG_EXT="log"

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

# Log level: DEBUG, INFO, WARN, ERROR
LOG_LEVEL="INFO"

# Log format: Include timestamp in logs
LOG_FORMAT="[%Y-%m-%d %H:%M:%S]"

# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════

# Exit on error
set -o pipefail

# ═══════════════════════════════════════════════════════════════════════════
# EXPORT VARIABLES FOR CHILD PROCESSES
# ═══════════════════════════════════════════════════════════════════════════

export PROJECT_ROOT
export VENV_PATH
export SCRIPT_DIR
export SHARED_DIR
export PYTHON_DIR
export REPORTS_DIR
export WEEKLY_DIR
export MONTHLY_DIR
export QBR_DIR
export LOGS_DIR
export TIMEZONE
export CURRENCY
export CLI_CMD

# ═══════════════════════════════════════════════════════════════════════════
# END OF CONFIG
# ═══════════════════════════════════════════════════════════════════════════
