#!/bin/bash
# Setup cron jobs for Channel Director automation

set -euo pipefail

SCRIPT_DIR="/Users/santiagot/Applications/salesforce-fastmcp/scripts"
PROJECT_ROOT="/Users/santiagot/Applications/salesforce-fastmcp"
REPORTS_DIR="${HOME}/reports"
LOGS_DIR="${REPORTS_DIR}/.logs"

echo "=========================================="
echo "Setting up Channel Director Cron Jobs"
echo "=========================================="
echo ""

# Ensure log directory exists
mkdir -p "${LOGS_DIR}"

# Create a temporary cron file with comments
TEMP_CRON=$(mktemp)
CRON_FILE="${SCRIPT_DIR}/crontab_entries.txt"

cat > "${CRON_FILE}" << 'CRONTAB'
# Channel Director Automation - Cron Schedule
# ==============================================

# Weekly Pulse Report - Every Friday at 4:00 PM (16:00)
0 16 * * 5 cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/weekly_friday_pulse.sh >> ~/reports/.logs/weekly_cron.log 2>&1

# Month-End Business Review - Last day of month at 11:00 PM (23:00)
0 23 L * * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/month_end_business_review.sh >> ~/reports/.logs/month_end_cron.log 2>&1

# Quarterly QBR Preparation - Quarter-end at 10:00 PM (22:00)
# Q1 (Apr 30), Q2 (Jul 31), Q3 (Oct 31), Q4 (Jan 31)
0 22 30 4 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1
0 22 31 7 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1
0 22 31 10 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1
0 22 31 1 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1

CRONTAB

echo "✅ Cron entries saved to: ${CRON_FILE}"
echo ""
echo "Note: macOS cron has limitations with 'L' (last day) syntax."
echo "Using specific dates for month-end (30th) instead."
echo ""

# Backup existing crontab
if crontab -l > /dev/null 2>&1; then
    BACKUP_FILE="${SCRIPT_DIR}/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    crontab -l > "${BACKUP_FILE}"
    echo "✅ Backed up existing crontab to: ${BACKUP_FILE}"
    echo ""
fi

# Create new crontab with our entries
# Note: macOS doesn't support "L" for last day, so we use day 30 + 31 combinations
NEW_CRONTAB=$(mktemp)

# Start with existing crontab if it exists
if crontab -l 2>/dev/null | grep -v "Channel Director" > "${NEW_CRONTAB}"; then
    echo "Added to existing crontab"
else
    echo "# User crontab for Santiago Torres" > "${NEW_CRONTAB}"
    echo "# Generated: $(date)" >> "${NEW_CRONTAB}"
    echo "" >> "${NEW_CRONTAB}"
fi

# Add our automation jobs (without the ones that are already there)
cat >> "${NEW_CRONTAB}" << 'NEWCRON'

# ========== Channel Director Automation ==========
# Weekly Pulse Report - Every Friday at 4:00 PM
0 16 * * 5 cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/weekly_friday_pulse.sh >> ~/reports/.logs/weekly_cron.log 2>&1

# Month-End Business Review - 30th & 31st of each month at 11:00 PM
0 23 30 * * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/month_end_business_review.sh >> ~/reports/.logs/month_end_cron.log 2>&1
0 23 31 * * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/month_end_business_review.sh >> ~/reports/.logs/month_end_cron.log 2>&1

# Quarterly QBR Preparation - Quarter-end dates at 10:00 PM
0 22 30 4 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1
0 22 31 7 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1
0 22 31 10 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1
0 22 31 1 * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/quarterly_qbr_prep.sh >> ~/reports/.logs/qbr_cron.log 2>&1

NEWCRON

# Install new crontab
crontab "${NEW_CRONTAB}"
rm "${NEW_CRONTAB}"

echo "✅ Cron jobs installed successfully!"
echo ""
echo "Schedule Summary:"
echo "================"
echo "📅 Weekly:      Every Friday at 16:00 (4:00 PM)"
echo "📊 Month-End:   30th & 31st of each month at 23:00 (11:00 PM)"
echo "📈 Quarterly:   Quarter-end dates at 22:00 (10:00 PM)"
echo "               Apr 30, Jul 31, Oct 31, Jan 31"
echo ""
echo "Log files:"
echo "  - Weekly:     ~/reports/.logs/weekly_cron.log"
echo "  - Month-End:  ~/reports/.logs/month_end_cron.log"
echo "  - QBR:        ~/reports/.logs/qbr_cron.log"
echo ""

# Verify installation
echo "Current crontab entries:"
echo "========================"
crontab -l | grep -A 20 "Channel Director Automation" || echo "No entries found"
echo ""

