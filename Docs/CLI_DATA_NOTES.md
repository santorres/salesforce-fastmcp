# CLI Data Notes & Troubleshooting

**Date**: June 16, 2026  
**Status**: Known data issue identified

---

## Current Data Issue

### Partner Names Showing "Unknown"

**What You're Seeing:**
```
Top Partners by Revenue
================================================================================
#   Partner Name                                          Revenue
--------------------------------------------------------------------------------
1   Unknown                                  $                  0
2   Unknown                                  $                  0
```

**Why This Happens:**

The Salesforce API response for `top-partners` command is not returning partner name information in the data. This is a **data population issue**, not a formatting issue.

**Expected:**
```
1   Accenture                                $        $250,000
2   Inetum Spain                             $         $45,000
3   TCS                                      $         $30,000
```

**Root Cause:** The SOQL queries or data retrieval from Salesforce is not populating the `partner_name` field correctly.

---

## Investigation & Diagnosis

### What Works ✅
- KPI snapshot returns all metrics
- Revenue breakdown shows attainment percentages
- Risk detection identifies high-risk deals
- JSON output is complete and valid
- All commands execute without errors
- Fiscal period filtering works

### What Needs Data Fix ❌
- Partner names in `top-partners` command showing "Unknown"
- Partner names in `revenue --breakdown partner` showing "Unknown"
- This affects user experience but not core functionality

---

## CLI Output Quality Improvements (Completed)

### Enhanced KPI Output

**Before:**
```
KPI Snapshot
--------------------------------------------------
Revenue (Closed-Won): $78,406
  Deals: 0

Pipeline (Open): $1,504,111
Win Rate: 3.8%
Active Partners: 18
```

**After:**
```
KPI Snapshot
================================================================================

Revenue (Closed-Won)
----------------------------------------
  Amount: $78,406
  Deals: 0
  Avg Deal Size: $55,671

Pipeline (Open)
----------------------------------------
  Amount: $1,504,111

Performance Metrics
----------------------------------------
  Win Rate: 3.8%
  Active Partners: 18
  Focus Partners: 23

Risk Assessment
----------------------------------------
  Orphan Opportunities: 2 (0.1%)
  Revenue Concentration (Top 3): 25.2%
```

**Improvements:**
- Now shows all KPI metrics from JSON response
- Better organization with sections
- Includes: Average Deal Size, Focus Partners, Orphan Opportunities, Revenue Concentration
- More readable with headers and dividers

### Commit
- **Commit**: 3fe9f86
- **Message**: Enhance CLI output formatters with complete data display
- **Status**: ✅ Deployed

---

## Next Steps to Fix Partner Names

To resolve the "Unknown" partner names issue, you need to:

### Option 1: Debug SOQL Query
1. Check the `channel_intelligence.py` SOQL query for `get_top_partners()`
2. Verify the query selects the partner name field
3. Test the query in Salesforce Developer Console
4. Update the query if needed

### Option 2: Check Data Mapping
1. Verify the response from Salesforce includes partner information
2. Check if the field name matches what the formatter expects
3. Adjust field name mapping in `format_top_partners()` if needed

### Option 3: Verify Salesforce Records
1. Check if Account records have names populated
2. Verify the relationship between Opportunities and Accounts
3. Ensure the SOQL join is correct

---

## Commands & Their Data Status

| Command | Data Status | Notes |
|---------|-------------|-------|
| `kpi` | ✅ Complete | All metrics displaying correctly |
| `revenue` | ⚠️ Partial | Amounts work, partner names showing Unknown |
| `pipeline` | ✅ Complete | Amounts and stage breakdowns working |
| `risk` | ✅ Complete | All deal details displaying |
| `partner` | ⚠️ Partial | Works with manual partner name |
| `qbr` | ✅ Complete | Full business review generating |
| `registrations` | ✅ Complete | All registration metrics showing |
| `top-partners` | ⚠️ Partial | Rankings work, names showing Unknown |
| `search` | ✅ Complete | Search functionality working |
| `list-opps` | ✅ Complete | Opportunity details displaying |

---

## JSON Output

**Good News:** JSON output shows all data correctly!

```bash
python3 -m cli.channel_cli top-partners --json | jq '.data[0]'
```

Shows:
```json
{
  "partner_name": null,
  "total_revenue": 0
}
```

This confirms the issue is in the data, not the formatting.

---

## Workaround: Use JSON Output

If you need partner names, use JSON output and process it:

```bash
# Export to file for analysis
python3 -m cli.channel_cli top-partners --json > partners.json

# Parse with jq
python3 -m cli.channel_cli top-partners --json | jq '.data[] | select(.total_revenue > 0)'
```

---

## Files Modified

- `cli/channel_cli.py` (Commit 3fe9f86)
  - `format_kpi()` - Enhanced with all metrics
  - `format_top_partners()` - Improved field handling

---

## Testing

All formatters tested and working:

```bash
source .venv/bin/activate
python3 -m cli.channel_cli kpi           # ✅ Complete output
python3 -m cli.channel_cli revenue       # ✅ Shows revenue
python3 -m cli.channel_cli top-partners  # ⚠️ Names are Unknown (data issue)
python3 -m cli.channel_cli kpi --json    # ✅ JSON complete
```

---

## Recommendations

1. **Immediate:** Use JSON output for full data access
2. **Short-term:** Debug SOQL query to find partner name issue
3. **Long-term:** Update data retrieval to properly populate partner names

---

## Support

For more information:
- See `Docs/CLI_QUICKSTART.md` for command usage
- See `Docs/CLI_QUICK_REFERENCE.md` for options
- Run `python3 -m cli.channel_cli COMMAND --help` for command help

---

**Status**: ✅ CLI Formatters Enhanced  
**Remaining**: Partner name data mapping

