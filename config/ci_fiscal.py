"""Fiscal-year and SOQL helper functions for salesforce-fastmcp.

This module owns all date/period arithmetic and SOQL query-building utilities.

Dependency direction: ci_config ← ci_fiscal ← channel_intelligence
"""

import re
from datetime import date, timedelta
from typing import Any

from .ci_config import get_config, COUNTRIES_SQL

# ---------------------------------------------------------------------------
# Fiscal-year / date utilities
# ---------------------------------------------------------------------------

def _start_of_fiscal_year(d: date) -> date:
    """FY start date based on config (default Feb 1). If month < FY start, FY started the previous year."""
    cfg = get_config()
    fy_start_month = cfg.get_fiscal_year_start_month()
    year = d.year if d.month >= fy_start_month else d.year - 1
    return date(year, fy_start_month, 1)


def _end_of_fiscal_year(d: date) -> date:
    fy_start = _start_of_fiscal_year(d)
    # End month is the calendar month before FY start (wraps Dec→Jan)
    end_month = fy_start.month - 1 or 12
    # End year is always one calendar year after FY start year
    end_year = fy_start.year + 1
    last_day = 31 if end_month in (1, 3, 5, 7, 8, 10, 12) else (30 if end_month != 2 else 28)
    return date(end_year, end_month, last_day)


def _fiscal_year_number(d: date) -> int:
    return _start_of_fiscal_year(d).year + 1


def _fiscal_year_label(d: date) -> str:
    fy = _fiscal_year_number(d) % 100
    return f"FY{fy:02d}"


def _fiscal_quarter_range(d: date) -> dict[str, Any]:
    """Get fiscal quarter range based on config (default: Feb-Jan FY). Falls back to hardcoded if config unavailable."""
    m, y = d.month, d.year
    cfg = get_config()

    # Try to get quarter definitions from config
    quarters_config = cfg.fiscal_calendar.get("quarters", {}) if cfg.fiscal_calendar else {}

    if not quarters_config:
        # Fallback to hardcoded defaults
        if 2 <= m <= 4:
            return {"start": date(y, 2, 1), "end": date(y, 4, 30), "quarter": "Q1"}
        if 5 <= m <= 7:
            return {"start": date(y, 5, 1), "end": date(y, 7, 31), "quarter": "Q2"}
        if 8 <= m <= 10:
            return {"start": date(y, 8, 1), "end": date(y, 10, 31), "quarter": "Q3"}
        if m >= 11:
            return {"start": date(y, 11, 1), "end": date(y + 1, 1, 31), "quarter": "Q4"}
        return {"start": date(y - 1, 11, 1), "end": date(y, 1, 31), "quarter": "Q4"}

    # Use config-based quarter definitions
    def _get_last_day_of_month(month: int, year: int) -> int:
        if month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        elif month in (4, 6, 9, 11):
            return 30
        elif month == 2:
            return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
        return 31

    # Match month to quarter based on config
    for q_name in ["Q1", "Q2", "Q3", "Q4"]:
        if q_name not in quarters_config:
            continue
        q = quarters_config[q_name]
        start_m = q.get("start_month")
        end_m = q.get("end_month")

        if start_m and end_m:
            # Handle Q4 which spans year boundary (Nov-Jan)
            if end_m < start_m:
                if start_m <= m or m <= end_m:
                    start_year = y if m >= start_m else y - 1
                    end_year = y if m <= end_m else y + 1
                    return {
                        "start": date(start_year, start_m, 1),
                        "end": date(end_year, end_m, _get_last_day_of_month(end_m, end_year)),
                        "quarter": q_name,
                    }
            else:
                if start_m <= m <= end_m:
                    return {
                        "start": date(y, start_m, 1),
                        "end": date(y, end_m, _get_last_day_of_month(end_m, y)),
                        "quarter": q_name,
                    }

    # Fallback if month doesn't match any quarter (shouldn't happen)
    return {"start": date(y, 2, 1), "end": date(y, 4, 30), "quarter": "Q1"}


def _fiscal_quarter_from_date_str(date_str: str) -> str:
    """Return Q1–Q4 for a YYYY-MM-DD string."""
    d = date.fromisoformat(date_str[:10])
    return _fiscal_quarter_range(d)["quarter"]


def _get_period_range(period: str, now: date | None = None) -> dict[str, Any]:
    today = now or date.today()
    match period:
        case "CURRENT":
            q = _fiscal_quarter_range(today)
            fy = _fiscal_year_label(q["start"])
            return {**q, "label": f"CURRENT_{q['quarter']}", "fiscal_label": f"{fy}_{q['quarter']}"}
        case "THIS_FISCAL_YEAR" | "CURRENT_FY":
            start = _start_of_fiscal_year(today)
            end = _end_of_fiscal_year(today)
            return {"start": start, "end": end, "label": period, "fiscal_label": _fiscal_year_label(start)}
        case "LAST_FISCAL_YEAR":
            this_fy_start = _start_of_fiscal_year(today)
            last_fy_start = date(this_fy_start.year - 1, 2, 1)
            last_fy_end = date(this_fy_start.year, 1, 31)
            return {"start": last_fy_start, "end": last_fy_end, "label": "LAST_FISCAL_YEAR",
                    "fiscal_label": _fiscal_year_label(last_fy_start)}
        case "THIS_QUARTER":
            q = _fiscal_quarter_range(today)
            fy = _fiscal_year_label(q["start"])
            return {**q, "label": f"THIS_{q['quarter']}", "fiscal_label": f"{fy}_{q['quarter']}"}
        case "Q1":
            fy_start = _start_of_fiscal_year(today)
            start = date(fy_start.year, 2, 1)
            end = date(fy_start.year, 4, 30)
            return {"start": start, "end": end, "label": "Q1", "fiscal_label": f"{_fiscal_year_label(start)}_Q1"}
        case "Q2":
            fy_start = _start_of_fiscal_year(today)
            start = date(fy_start.year, 5, 1)
            end = date(fy_start.year, 7, 31)
            return {"start": start, "end": end, "label": "Q2", "fiscal_label": f"{_fiscal_year_label(start)}_Q2"}
        case "Q3":
            fy_start = _start_of_fiscal_year(today)
            start = date(fy_start.year, 8, 1)
            end = date(fy_start.year, 10, 31)
            return {"start": start, "end": end, "label": "Q3", "fiscal_label": f"{_fiscal_year_label(start)}_Q3"}
        case "Q4":
            fy_start = _start_of_fiscal_year(today)
            start = date(fy_start.year, 11, 1)
            end = date(fy_start.year + 1, 1, 31)
            return {"start": start, "end": end, "label": "Q4", "fiscal_label": f"{_fiscal_year_label(start)}_Q4"}
        case "NEXT_QUARTER":
            this_q = _fiscal_quarter_range(today)
            next_start = this_q["end"] + timedelta(days=1)
            next_q = _fiscal_quarter_range(next_start)
            fy = _fiscal_year_label(next_q["start"])
            return {**next_q, "label": f"NEXT_{next_q['quarter']}", "fiscal_label": f"{fy}_{next_q['quarter']}"}
        case "CURRENT_AND_NEXT_QUARTER":
            this_q = _fiscal_quarter_range(today)
            next_start = this_q["end"] + timedelta(days=1)
            next_q = _fiscal_quarter_range(next_start)
            fy = _fiscal_year_label(this_q["start"])
            return {
                "start": this_q["start"],
                "end": next_q["end"],
                "label": f"CURRENT_AND_NEXT_{this_q['quarter']}_{next_q['quarter']}",
                "fiscal_label": f"{fy}_{this_q['quarter']}+{next_q['quarter']}",
            }
        case "LAST_QUARTER":
            this_q = _fiscal_quarter_range(today)
            prev_end = this_q["start"] - timedelta(days=1)
            prev_q = _fiscal_quarter_range(prev_end)
            fy = _fiscal_year_label(prev_q["start"])
            return {**prev_q, "label": f"LAST_{prev_q['quarter']}", "fiscal_label": f"{fy}_{prev_q['quarter']}"}
        case "LAST_30_DAYS":
            start = today - timedelta(days=29)
            fy = _fiscal_year_label(today)
            return {"start": start, "end": today, "label": "LAST_30_DAYS", "fiscal_label": f"{fy}_ROLLING_30D"}
        case "NEXT_60_DAYS":
            end = today + timedelta(days=60)
            fy = _fiscal_year_label(today)
            return {"start": today, "end": end, "label": "NEXT_60_DAYS", "fiscal_label": f"{fy}_ROLLING_60D"}
        case _:
            # Try to match historical FY##_Q# pattern (e.g. FY26_Q1, FY25_Q3)
            m = re.match(r"^FY(\d{2})_Q([1-4])$", period)
            if m:
                fy_short = int(m.group(1))
                quarter_num = int(m.group(2))
                fy_year = 2000 + fy_short - 1
                q_name = f"Q{quarter_num}"

                if quarter_num == 1:
                    start, end = date(fy_year, 2, 1), date(fy_year, 4, 30)
                elif quarter_num == 2:
                    start, end = date(fy_year, 5, 1), date(fy_year, 7, 31)
                elif quarter_num == 3:
                    start, end = date(fy_year, 8, 1), date(fy_year, 10, 31)
                else:  # Q4
                    start, end = date(fy_year, 11, 1), date(fy_year + 1, 1, 31)

                return {
                    "start": start,
                    "end": end,
                    "label": period,
                    "fiscal_label": f"FY{fy_short:02d}_{q_name}",
                }
            raise ValueError(f"Unsupported period: {period}")


# ---------------------------------------------------------------------------
# SOQL helpers
# ---------------------------------------------------------------------------

def _escape_soql(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _clamp_limit(value: Any, default: int = 10, max_val: int = 50) -> int:
    n = default if value is None else int(value)
    if n < 1:
        raise ValueError("limit must be a positive number")
    return min(n, max_val)


def _normalize_period(value: str) -> str:
    cleaned = (
        str(value).strip().upper()
        .replace("?", "").replace(".", "").replace(",", "").replace("!", "")
        .replace(" ", "_").replace("-", "_")
    )
    aliases: dict[str, str] = {
        "CURRENTFY": "CURRENT_FY",
        "THISFY": "THIS_FISCAL_YEAR",
        "CURRENTQ": "THIS_QUARTER",
        "THISQ": "THIS_QUARTER",
        "NEXTQ": "NEXT_QUARTER",
        "LASTQ": "LAST_QUARTER",
        "CURRENT_AND_NEXT_Q": "CURRENT_AND_NEXT_QUARTER",
        "CURRENT_NEXT_QUARTER": "CURRENT_AND_NEXT_QUARTER",
    }
    if cleaned in aliases:
        return aliases[cleaned]
    # Handle FY##_Q# pattern (and variations like FY26Q1, FY26_QUARTER1)
    m = re.match(r"^FY(\d{2})_?Q([1-4])$", cleaned)
    if m:
        return f"FY{m.group(1)}_Q{m.group(2)}"
    m = re.match(r"^FY(\d{2})_QUARTER_?([1-4])$", cleaned)
    if m:
        return f"FY{m.group(1)}_Q{m.group(2)}"
    m = re.match(r"^Q([1-4])_FY(\d{2})$", cleaned)
    if m:
        return f"FY{m.group(2)}_Q{m.group(1)}"
    m = re.match(r"^QUARTER_?([1-4])$", cleaned)
    if m:
        return f"Q{m.group(1)}"
    return cleaned


def _assert_enum(value: str, allowed: list[str], name: str) -> None:
    if value in allowed:
        return
    if "period" in name.lower() and re.match(r"^FY\d{2}_Q[1-4]$", value):
        return
    raise ValueError(f"Invalid {name}. Allowed: {', '.join(allowed)}")


def _summarize_period(period: str) -> dict[str, Any]:
    r = _get_period_range(period)
    return {
        "period": period,
        "startDate": r["start"].isoformat(),
        "endDate": r["end"].isoformat(),
        "label": r["label"],
        "fiscalLabel": r["fiscal_label"],
    }


def _build_opp_where(
    *,
    closed_mode: str | None,
    range_: dict[str, Any],
    channel_manager: str,
    extra_conditions: list[str] | None = None,
) -> str:
    clauses = [
        f"Account.BillingCountry IN {COUNTRIES_SQL}",
        f"CloseDate >= {range_['start'].isoformat()}",
        f"CloseDate <= {range_['end'].isoformat()}",
    ]
    if closed_mode == "open":
        clauses.append("IsClosed = false")
    elif closed_mode == "won":
        # Use StageName rather than IsWon=true — IsWon is set by Salesforce only when the
        # stage transitions through the standard close flow. Custom stage names or data
        # migrations can leave IsWon=false on deals that are genuinely Closed Won. The
        # stage name is the authoritative signal for this org.
        clauses.append("StageName = 'Closed Won'")
    elif closed_mode == "closed":
        clauses.append("IsClosed = true")
    if channel_manager:
        clauses.append(f"Channel_Manager__c = '{_escape_soql(channel_manager)}'")
    for cond in (extra_conditions or []):
        if cond:
            clauses.append(cond)
    return " AND ".join(clauses)


def _num(row: dict | None, key: str, fallback: str = "") -> float:
    if not row:
        return 0.0
    for k in (key, fallback):
        if not k:
            continue
        v = row.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str) and v.strip():
            try:
                return float(v)
            except ValueError:
                pass
    return 0.0
