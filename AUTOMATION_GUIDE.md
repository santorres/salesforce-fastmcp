# Channel Director Automation Guide

Complete automation system for Santiago Torres' weekly, monthly, and quarterly reporting.

## Overview

Three automated reporting workflows generate professional Excel + Markdown reports for:
- **Weekly Friday Pulse** - Snapshot of current quarter performance
- **Month-End Business Review** - Comprehensive monthly analysis with YoY/Q comparisons
- **Quarterly QBR Prep** - Multi-partner quarterly business review with individual partner sheets

## Scheduled Execution

All workflows run automatically on your MacBook via cron jobs:

### Weekly (Every Friday at 4:00 PM)
```
0 16 * * 5  cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/weekly_friday_pulse.sh
```
**Outputs**: `~/reports/weekly/2026/weekly_YYYYMMDD.{xlsx,md,json}`

### Month-End (30th & 31st of each month at 11:00 PM)
```
0 23 30 * * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/month_end_business_review.sh
0 23 31 * * cd /Users/santiagot/Applications/salesforce-fastmcp && bash scripts/month_end_business_review.sh
```
**Outputs**: `~/reports/monthly/2026/month_end_YYYYMM.{xlsx,md,json}`

### Quarterly (Quarter-end dates at 10:00 PM)
```
0 22 30 4 *  → April 30 (Q1 end)
0 22 31 7 *  → July 31 (Q2 end)
0 22 31 10 * → October 31 (Q3 end)
0 22 31 1 *  → January 31 (Q4 end)
```
**Outputs**: `~/reports/qbr/qbr_summary_YYYYMMDD.{xlsx,md,json}`

## Report Formats

### Excel Reports

**Weekly (5 sheets)**
1. Summary - KPIs, metrics, targets
2. Revenue by Partner - Top 10 partners with attainment
3. Revenue by Country - Geographic breakdown
4. Pipeline by Stage - Sales funnel analysis
5. Top Partners & Risk - 5 partners + high-risk deals

**Month-End (10 sheets)**
1. Summary - Q/FY/YoY metrics
2. Revenue - Monthly detail with growth
3. Revenue - Country breakdown with YTD
4. Revenue - 3-quarter trend analysis
5. Pipeline - Monthly detail with growth
6. Pipeline - Forecast & coverage analysis
7. Partner Health - Top 10 with health scoring
8. Registrations - New partners this month
9. Aging - Pipeline aging analysis by days
10. Risk - High-risk deals with blockers

**QBR (13+ sheets)**
1. QBR Summary - Quarterly performance
2. Top 10 Partners - Revenue, target, attainment, QoQ growth
3-14. Partner Detail Sheets - Individual metrics for Top 12 partners

### Markdown Reports

Professional formatted documents with:
- Executive summary with key metrics
- Revenue analysis by partner and country
- Pipeline analysis by stage
- Partner health scoring (Green/Yellow/Red)
- New registrations summary
- Risk & alerts (high-risk deals)
- Action items and next steps
- Metadata and timestamps

### JSON Archives

Complete raw data from CLI for:
- Historical analysis
- Data science / trending
- Integration with other tools

## File Structure

```
~/reports/
├── .logs/                          # Automation logs
│   ├── weekly_cron.log
│   ├── month_end_cron.log
│   └── qbr_cron.log
├── weekly/2026/                    # Weekly reports
│   ├── weekly_20260619.xlsx
│   ├── weekly_20260619.md
│   └── weekly_20260619.json
├── monthly/2026/                   # Monthly reports
│   ├── month_end_202606.xlsx
│   ├── month_end_202606.md
│   └── month_end_202606.json
└── qbr/                            # Quarterly reports
    ├── qbr_summary_20260617.xlsx
    ├── qbr_summary_20260617.md
    └── qbr_summary_20260617.json
```

## Manual Execution

Run any workflow manually:

```bash
# Weekly
bash ~/Applications/salesforce-fastmcp/scripts/weekly_friday_pulse.sh

# Month-End
bash ~/Applications/salesforce-fastmcp/scripts/month_end_business_review.sh

# QBR
bash ~/Applications/salesforce-fastmcp/scripts/quarterly_qbr_prep.sh
```

## Logging & Troubleshooting

All executions logged to:
- `~/reports/.logs/weekly_cron.log` - Weekly runs
- `~/reports/.logs/month_end_cron.log` - Month-end runs
- `~/reports/.logs/qbr_cron.log` - QBR runs

View recent logs:
```bash
tail -f ~/reports/.logs/weekly_cron.log
```

## Data Sources

All reports pull from Salesforce via the CLI:
- `python3 -m cli.channel_cli kpi` - KPIs
- `python3 -m cli.channel_cli revenue` - Revenue analysis
- `python3 -m cli.channel_cli pipeline` - Pipeline analysis
- `python3 -m cli.channel_cli top-partners` - Partner metrics
- `python3 -m cli.channel_cli risk` - Risk deals

Territory filter applied automatically:
- **Southern Europe** (Spain, Italy)
- **Eastern Europe** (Poland, Czech Republic, Hungary)
- **Turkey**

## Configuration

Edit `/Users/santiagot/Applications/salesforce-fastmcp/scripts/shared/config.sh` to customize:

```bash
# Territory
TERRITORY="Southern Europe, Eastern Europe, Turkey"

# Reporting
TOP_PARTNERS_LIMIT=10
RISK_PROBABILITY_THRESHOLD=40
RISK_DAYS_THRESHOLD=30

# Storage
WEEKLY_DIR="${REPORTS_DIR}/weekly/2026"
MONTHLY_DIR="${REPORTS_DIR}/monthly/2026"
QBR_DIR="${REPORTS_DIR}/qbr"
```

## Cron Job Management

### View current cron jobs
```bash
crontab -l | grep "Channel Director"
```

### Edit cron schedule
```bash
crontab -e
```

### Backup crontab
```bash
crontab -l > ~/crontab_backup.txt
```

### Restore crontab
```bash
crontab ~/crontab_backup.txt
```

## Requirements

- macOS with cron support
- Python 3.11+ with venv
- Salesforce Fastmcp CLI installed
- 1.5 GB free space for reports (~3-5 MB per report)
- Laptop must be on during scheduled times

## Time Zone

All cron times in **Europe/Madrid (UTC+2 in summer, UTC+1 in winter)**

## Performance

Typical execution times:
- **Weekly**: 5-10 minutes (CLI data + Excel + Markdown)
- **Month-End**: 15-25 minutes (larger dataset)
- **QBR**: 20-30 minutes (12+ partner sheets)

## Support

For issues:
1. Check cron logs: `tail ~/reports/.logs/*.log`
2. Run script manually to see full error output
3. Verify CLI connectivity: `python3 -m cli.channel_cli kpi`
4. Ensure reports directory exists: `ls ~/reports/`

---

**Last Updated**: June 18, 2026
**Automation Version**: 1.0
**Maintained By**: Santiago Torres
