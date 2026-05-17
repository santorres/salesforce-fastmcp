"""Southern Europe Channel Intelligence — ported from LocalPartner server.js.

Provides deterministic analytics tools scoped to Italy, Spain, Portugal, Greece,
Cyprus, and Malta.  All functions accept a SalesforceClient instance as their
first argument so they can share the authenticated session managed by server.py.
"""

import asyncio
import os
import re
from datetime import date, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOOL_VERSION = "2.0.0"

COUNTRIES: list[str] = ["Italy", "Spain", "Portugal", "Greece", "Cyprus", "Malta"]
COUNTRIES_SQL: str = "('" + "','".join(COUNTRIES) + "')"

PERIODS: list[str] = [
    "CURRENT", "THIS_FISCAL_YEAR", "CURRENT_FY", "LAST_FISCAL_YEAR",
    "Q1", "Q2", "Q3", "Q4",
    "THIS_QUARTER", "NEXT_QUARTER", "CURRENT_AND_NEXT_QUARTER",
    "LAST_QUARTER", "LAST_30_DAYS", "NEXT_60_DAYS",
    "FY##_Q#",  # Historical year + quarter, e.g. FY26_Q1, FY25_Q2
]

METRICS: list[str] = ["revenue", "pipeline"]
BREAKDOWNS_REVENUE: list[str] = ["total", "country", "quarter", "partner"]
BREAKDOWNS_PIPELINE: list[str] = ["total", "country", "stage", "quarter", "partner"]

DEFAULT_CHANNEL_MANAGER: str = os.getenv("DEFAULT_CHANNEL_MANAGER", "")
ADMIN_KEY: str = os.getenv("ADMIN_KEY", "")

# ---------------------------------------------------------------------------
# Fiscal-year / date utilities
# ---------------------------------------------------------------------------

def _start_of_fiscal_year(d: date) -> date:
    """FY starts Feb 1.  If month < February the FY started the previous year."""
    year = d.year if d.month >= 2 else d.year - 1
    return date(year, 2, 1)


def _end_of_fiscal_year(d: date) -> date:
    fy_start = _start_of_fiscal_year(d)
    return date(fy_start.year + 1, 1, 31)


def _fiscal_year_number(d: date) -> int:
    return _start_of_fiscal_year(d).year + 1


def _fiscal_year_label(d: date) -> str:
    fy = _fiscal_year_number(d) % 100
    return f"FY{fy:02d}"


def _fiscal_quarter_range(d: date) -> dict[str, Any]:
    m, y = d.month, d.year
    if 2 <= m <= 4:
        return {"start": date(y, 2, 1), "end": date(y, 4, 30), "quarter": "Q1"}
    if 5 <= m <= 7:
        return {"start": date(y, 5, 1), "end": date(y, 7, 31), "quarter": "Q2"}
    if 8 <= m <= 10:
        return {"start": date(y, 8, 1), "end": date(y, 10, 31), "quarter": "Q3"}
    if m >= 11:
        return {"start": date(y, 11, 1), "end": date(y + 1, 1, 31), "quarter": "Q4"}
    # January — belongs to Q4 of the previous fiscal year
    return {"start": date(y - 1, 11, 1), "end": date(y, 1, 31), "quarter": "Q4"}


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
                fy_year = 2000 + fy_short
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
    if value not in allowed:
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

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def get_revenue(
    sf,
    period: str,
    breakdown: str = "total",
    limit: int = 10,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
    partner_name: str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    _assert_enum(breakdown, BREAKDOWNS_REVENUE, "breakdown")
    safe_limit = _clamp_limit(limit, 10, 50)
    range_ = _get_period_range(period)

    extra: list[str] = []
    if partner_name:
        extra.append(f"Partner__r.Name LIKE '%{_escape_soql(str(partner_name))}%'")
    if country:
        extra.append(f"Account.BillingCountry = '{_escape_soql(str(country))}'")

    where = _build_opp_where(closed_mode="won", range_=range_, channel_manager=channel_manager, extra_conditions=extra)

    if breakdown == "total":
        res = await sf.query(f"SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE {where}")
        return {
            "tool": "get_revenue", "period": _summarize_period(period),
            "breakdown": breakdown, "channelManager": channel_manager or None,
            "data": {
                "totalRevenue": _num(res["records"][0], "totalRevenue", "expr0"),
                "dealCount": _num(res["records"][0], "dealCount", "expr1"),
            },
        }

    if breakdown == "country":
        res = await sf.query(
            f"SELECT Account.BillingCountry country, SUM(Amount) totalRevenue, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        return {
            "tool": "get_revenue", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": [{"country": r.get("country"), "totalRevenue": _num(r, "totalRevenue", "expr0"), "dealCount": _num(r, "dealCount", "expr1")} for r in res["records"]],
        }

    if breakdown == "partner":
        res = await sf.query(
            f"SELECT Partner__c partnerId, Partner__r.Name partnerName, SUM(Amount) totalRevenue, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} AND Partner__c != null "
            f"GROUP BY Partner__c, Partner__r.Name ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        return {
            "tool": "get_revenue", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": [{"partnerId": r.get("partnerId"), "partnerName": r.get("partnerName"),
                      "totalRevenue": _num(r, "totalRevenue", "expr0"), "dealCount": _num(r, "dealCount", "expr1")} for r in res["records"]],
        }

    # quarter breakdown — aggregate client-side
    res = await sf.query(f"SELECT CloseDate, Amount FROM Opportunity WHERE {where}")
    by_q: dict[str, float] = {}
    for r in res["records"]:
        q = _fiscal_quarter_from_date_str(r["CloseDate"])
        by_q[q] = by_q.get(q, 0.0) + (r.get("Amount") or 0)
    return {
        "tool": "get_revenue", "period": _summarize_period(period),
        "breakdown": breakdown, "channelManager": channel_manager or None,
        "data": [{"quarter": q, "totalRevenue": by_q.get(q, 0.0)} for q in ["Q1", "Q2", "Q3", "Q4"]],
    }


async def get_pipeline(
    sf,
    period: str,
    breakdown: str = "total",
    limit: int = 10,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
    partner_name: str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    _assert_enum(breakdown, BREAKDOWNS_PIPELINE, "breakdown")
    safe_limit = _clamp_limit(limit, 10, 50)
    range_ = _get_period_range(period)

    extra: list[str] = ["StageName NOT IN ('Closed Won', 'Closed Lost')"]
    if partner_name:
        extra.append(f"Partner__r.Name LIKE '%{_escape_soql(str(partner_name))}%'")
    if country:
        extra.append(f"Account.BillingCountry = '{_escape_soql(str(country))}'")

    where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager, extra_conditions=extra)

    if breakdown == "total":
        res = await sf.query(f"SELECT SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE {where}")
        return {
            "tool": "get_pipeline", "period": _summarize_period(period),
            "breakdown": breakdown, "channelManager": channel_manager or None,
            "data": {
                "totalPipeline": _num(res["records"][0], "totalPipeline", "expr0"),
                "dealCount": _num(res["records"][0], "dealCount", "expr1"),
            },
        }

    if breakdown == "country":
        res = await sf.query(
            f"SELECT Account.BillingCountry country, SUM(Amount) totalPipeline, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        return {
            "tool": "get_pipeline", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": [{"country": r.get("country"), "totalPipeline": _num(r, "totalPipeline", "expr0"), "dealCount": _num(r, "dealCount", "expr1")} for r in res["records"]],
        }

    if breakdown == "stage":
        res = await sf.query(
            f"SELECT StageName stage, SUM(Amount) totalPipeline, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} GROUP BY StageName ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        return {
            "tool": "get_pipeline", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": [{"stage": r.get("stage"), "totalPipeline": _num(r, "totalPipeline", "expr0"), "dealCount": _num(r, "dealCount", "expr1")} for r in res["records"]],
        }

    if breakdown == "partner":
        res = await sf.query(
            f"SELECT Partner__c partnerId, Partner__r.Name partnerName, SUM(Amount) totalPipeline, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} AND Partner__c != null "
            f"GROUP BY Partner__c, Partner__r.Name ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        return {
            "tool": "get_pipeline", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": [{"partnerId": r.get("partnerId"), "partnerName": r.get("partnerName"),
                      "totalPipeline": _num(r, "totalPipeline", "expr0"), "dealCount": _num(r, "dealCount", "expr1")} for r in res["records"]],
        }

    # quarter breakdown
    res = await sf.query(f"SELECT CloseDate, Amount FROM Opportunity WHERE {where}")
    by_q: dict[str, float] = {}
    for r in res["records"]:
        q = _fiscal_quarter_from_date_str(r["CloseDate"])
        by_q[q] = by_q.get(q, 0.0) + (r.get("Amount") or 0)
    return {
        "tool": "get_pipeline", "period": _summarize_period(period),
        "breakdown": breakdown, "channelManager": channel_manager or None,
        "data": [{"quarter": q, "totalPipeline": by_q.get(q, 0.0)} for q in ["Q1", "Q2", "Q3", "Q4"]],
    }


async def get_top_partners(
    sf,
    metric: str,
    period: str,
    limit: int = 10,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(metric, METRICS, "metric")
    _assert_enum(period, PERIODS, "period")
    safe_limit = _clamp_limit(limit, 10, 50)
    range_ = _get_period_range(period)

    if metric == "revenue":
        revenue = await get_revenue(sf, period, breakdown="partner", limit=safe_limit, channel_manager=channel_manager)
        diagnostics = None
        if not isinstance(revenue["data"], list) or not revenue["data"]:
            where_won = _build_opp_where(closed_mode="won", range_=range_, channel_manager=channel_manager)
            total_won_res, partnered_won_res = await asyncio.gather(
                sf.query(f"SELECT COUNT(Id) totalWon FROM Opportunity WHERE {where_won}"),
                sf.query(f"SELECT COUNT(Id) partneredWon FROM Opportunity WHERE {where_won} AND Partner__c != null"),
            )
            total_won = _num(total_won_res["records"][0], "totalWon", "expr0")
            partnered_won = _num(partnered_won_res["records"][0], "partneredWon", "expr0")
            reason = ("Closed Won opportunities exist, but none have Partner__c populated."
                      if total_won > 0 and partnered_won == 0
                      else "No Closed Won opportunities matched the current filters.")
            diagnostics = {"noData": True, "reason": reason,
                           "counters": {"totalClosedWon": total_won, "partneredClosedWon": partnered_won},
                           "filters": {"period": _summarize_period(period), "channelManager": channel_manager or None, "metric": metric}}
        return {"tool": "get_top_partners", "metric": metric, "period": revenue["period"],
                "limit": safe_limit, "data": revenue["data"], "diagnostics": diagnostics}

    pipeline = await get_pipeline(sf, period, breakdown="partner", limit=safe_limit, channel_manager=channel_manager)
    diagnostics = None
    if not isinstance(pipeline["data"], list) or not pipeline["data"]:
        where_open = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager,
                                       extra_conditions=["StageName NOT IN ('Closed Won', 'Closed Lost')"])
        total_open_res, partnered_open_res = await asyncio.gather(
            sf.query(f"SELECT COUNT(Id) totalOpen FROM Opportunity WHERE {where_open}"),
            sf.query(f"SELECT COUNT(Id) partneredOpen FROM Opportunity WHERE {where_open} AND Partner__c != null"),
        )
        total_open = _num(total_open_res["records"][0], "totalOpen", "expr0")
        partnered_open = _num(partnered_open_res["records"][0], "partneredOpen", "expr0")
        reason = ("Open opportunities exist, but none have Partner__c populated."
                  if total_open > 0 and partnered_open == 0
                  else "No open opportunities matched the current filters.")
        diagnostics = {"noData": True, "reason": reason,
                       "counters": {"totalOpen": total_open, "partneredOpen": partnered_open},
                       "filters": {"period": _summarize_period(period), "channelManager": channel_manager or None, "metric": metric}}
    return {"tool": "get_top_partners", "metric": metric, "period": pipeline["period"],
            "limit": safe_limit, "data": pipeline["data"], "diagnostics": diagnostics}


async def get_partner_detail(
    sf,
    partner_name: str,
    period: str,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
    open_opp_limit: int = 20,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    safe_partner = str(partner_name).strip()
    escaped = _escape_soql(safe_partner)
    safe_opp_limit = _clamp_limit(open_opp_limit, 20, 50)
    range_ = _get_period_range(period)

    account_res = await sf.query(
        f"SELECT Id, Name FROM Account WHERE Name LIKE '%{escaped}%' ORDER BY Name LIMIT 25"
    )
    candidates = [{"id": r["Id"], "name": r["Name"]} for r in account_res.get("records", [])]
    partner_ids = [c["id"] for c in candidates if c["id"]]

    if partner_ids:
        ids_sql = ",".join(f"'{_escape_soql(pid)}'" for pid in partner_ids)
        partner_cond = f"Partner__c IN ({ids_sql})"
    else:
        partner_cond = f"(Partner__r.Name = '{escaped}' OR Partner__r.Name LIKE '%{escaped}%')"

    async def collect_metrics(mgr: str) -> dict[str, Any]:
        base = _build_opp_where(closed_mode=None, range_=range_, channel_manager=mgr,
                                extra_conditions=[partner_cond])
        (rev_res, pipe_res, total_closed_res, won_closed_res, open_opps_res) = await asyncio.gather(
            sf.query(f"SELECT SUM(Amount) totalRevenue, COUNT(Id) wonCount FROM Opportunity WHERE {base} AND StageName = 'Closed Won'"),
            sf.query(f"SELECT SUM(Amount) totalPipeline, COUNT(Id) openCount FROM Opportunity WHERE {base} AND IsClosed = false AND StageName NOT IN ('Closed Won','Closed Lost')"),
            sf.query(f"SELECT COUNT(Id) totalClosed FROM Opportunity WHERE {base} AND IsClosed = true"),
            sf.query(f"SELECT COUNT(Id) wonClosed FROM Opportunity WHERE {base} AND IsClosed = true AND IsWon = true"),
            sf.query(f"SELECT Id, Name, Amount, CloseDate, StageName, Owner.Name FROM Opportunity "
                     f"WHERE {base} AND IsClosed = false AND StageName NOT IN ('Closed Won','Closed Lost') "
                     f"ORDER BY Amount DESC NULLS LAST LIMIT {safe_opp_limit}"),
        )
        total_closed = _num(total_closed_res["records"][0], "totalClosed", "expr0")
        won_closed = _num(won_closed_res["records"][0], "wonClosed", "expr0")
        return {
            "revenue": _num(rev_res["records"][0], "totalRevenue", "expr0"),
            "pipeline": _num(pipe_res["records"][0], "totalPipeline", "expr0"),
            "openDeals": _num(pipe_res["records"][0], "openCount", "expr1"),
            "closedWonCount": _num(rev_res["records"][0], "wonCount", "expr1"),
            "winRate": (won_closed / total_closed) if total_closed > 0 else 0,
            "openOpportunities": [
                {"id": r["Id"], "name": r["Name"], "value": r.get("Amount") or 0,
                 "closeDate": r.get("CloseDate"), "stageName": r.get("StageName"),
                 "ownerName": (r.get("Owner") or {}).get("Name")}
                for r in open_opps_res.get("records", [])
            ],
        }

    scoped = await collect_metrics(channel_manager)
    unscoped = None
    if (channel_manager and scoped["revenue"] == 0 and scoped["pipeline"] == 0
            and scoped["openDeals"] == 0 and scoped["closedWonCount"] == 0):
        unscoped = await collect_metrics("")

    return {
        "tool": "get_partner_detail",
        "partnerName": safe_partner,
        "period": _summarize_period(period),
        "channelManagerApplied": bool(channel_manager),
        "channelManager": channel_manager or None,
        "scopeNote": (
            "Metrics are computed from Opportunity records for the partner, filtered by deal-level Channel_Manager__c."
            if channel_manager else
            "Metrics are computed from Opportunity records for the partner with no channel-manager filter."
        ),
        "matchedPartners": candidates[:10],
        "data": scoped,
        "diagnostics": {
            "scopedNoData": True,
            "note": "No data found with channelManager filter; unscoped metrics included for comparison.",
            "unscopedData": unscoped,
        } if unscoped else None,
    }


async def get_partner_pipeline(
    sf,
    partner_name: str,
    period: str,
    open_opp_limit: int = 20,
    channel_manager: str = "",
) -> dict[str, Any]:
    detail = await get_partner_detail(sf, partner_name, period, channel_manager, open_opp_limit)
    opps = detail["data"].get("openOpportunities", [])
    pipeline = detail["data"].get("pipeline", 0)
    open_deals = detail["data"].get("openDeals", 0)

    lines = [
        f"Partner: {detail['partnerName']}",
        f"Period: {detail['period'].get('fiscalLabel', '')} ({detail['period']['startDate']} to {detail['period']['endDate']})",
        f"Pipeline: {int(pipeline):,}",
        f"Open deals: {int(open_deals):,}",
        f"Scope: {detail['scopeNote']}",
        "Open opportunities:",
    ]
    if not opps:
        lines.append("1. none")
    else:
        for i, opp in enumerate(opps, 1):
            lines.append(
                f"{i}. {opp.get('name', 'Unnamed')} (Id: {opp.get('id', '-')}): "
                f"{int(opp.get('value', 0)):,}, {opp.get('closeDate', '-')}, "
                f"Owner: {opp.get('ownerName', '-')}, Stage: {opp.get('stageName', '-')}"
            )

    return {
        "tool": "get_partner_pipeline",
        "partnerName": detail["partnerName"],
        "period": detail["period"],
        "channelManagerApplied": detail["channelManagerApplied"],
        "channelManager": detail["channelManager"],
        "scopeNote": detail["scopeNote"],
        "answer_markdown": "\n".join(lines),
        "matchedPartners": detail["matchedPartners"],
        "data": {"pipeline": pipeline, "openDeals": open_deals, "openOpportunities": opps},
        "diagnostics": detail.get("diagnostics"),
    }


async def search_opportunities(
    sf,
    query: str,
    partner_name: str | None = None,
    period: str = "THIS_FISCAL_YEAR",
    limit: int = 10,
    channel_manager: str = "",
) -> dict[str, Any]:
    safe_query = str(query).strip()[:180]
    safe_limit = _clamp_limit(limit, 10, 50)
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)

    conditions = [
        f"Account.BillingCountry IN {COUNTRIES_SQL}",
        f"Name LIKE '%{_escape_soql(safe_query)}%'",
        f"CloseDate >= {range_['start'].isoformat()}",
        f"CloseDate <= {range_['end'].isoformat()}",
    ]
    if channel_manager:
        conditions.append(f"Channel_Manager__c = '{_escape_soql(channel_manager)}'")
    if partner_name:
        safe_partner = str(partner_name).strip()
        escaped_partner = _escape_soql(safe_partner)
        acct_res = await sf.query(f"SELECT Id FROM Account WHERE Name LIKE '%{escaped_partner}%' ORDER BY Name LIMIT 25")
        pids = [r["Id"] for r in acct_res.get("records", [])]
        if pids:
            ids_sql = ",".join(f"'{_escape_soql(pid)}'" for pid in pids)
            conditions.append(f"Partner__c IN ({ids_sql})")
        else:
            conditions.append(f"(Partner__r.Name = '{escaped_partner}' OR Partner__r.Name LIKE '%{escaped_partner}%')")

    soql = (
        f"SELECT Id, Name, Amount, CloseDate, StageName, IsClosed, Partner__r.Name, Account.Name, Account.BillingCountry "
        f"FROM Opportunity WHERE {' AND '.join(conditions)} ORDER BY CloseDate ASC, Amount DESC NULLS LAST LIMIT {safe_limit}"
    )
    res = await sf.query(soql)
    return {
        "tool": "search_opportunities", "query": safe_query, "period": _summarize_period(period),
        "limit": safe_limit, "channelManager": channel_manager or None,
        "data": [
            {"id": r["Id"], "name": r["Name"], "amount": r.get("Amount") or 0,
             "closeDate": r.get("CloseDate"), "stageName": r.get("StageName"),
             "isClosed": bool(r.get("IsClosed")),
             "partnerName": (r.get("Partner__r") or {}).get("Name"),
             "accountName": (r.get("Account") or {}).get("Name"),
             "country": (r.get("Account") or {}).get("BillingCountry")}
            for r in res.get("records", [])
        ],
    }


async def get_opportunity_detail(
    sf,
    opportunity_id: str | None = None,
    opportunity_name: str | None = None,
    partner_name: str | None = None,
    period: str | None = None,
    channel_manager: str = "",
) -> dict[str, Any]:
    conditions = [f"Account.BillingCountry IN {COUNTRIES_SQL}"]

    if period:
        period = _normalize_period(period)
        _assert_enum(period, PERIODS, "period")
        range_ = _get_period_range(period)
        conditions.append(f"CloseDate >= {range_['start'].isoformat()}")
        conditions.append(f"CloseDate <= {range_['end'].isoformat()}")

    if channel_manager:
        conditions.append(f"Channel_Manager__c = '{_escape_soql(channel_manager)}'")

    if partner_name:
        escaped = _escape_soql(str(partner_name).strip())
        acct_res = await sf.query(f"SELECT Id FROM Account WHERE Name LIKE '%{escaped}%' ORDER BY Name LIMIT 25")
        pids = [r["Id"] for r in acct_res.get("records", [])]
        if pids:
            ids_sql = ",".join(f"'{_escape_soql(pid)}'" for pid in pids)
            conditions.append(f"Partner__c IN ({ids_sql})")
        else:
            conditions.append(f"(Partner__r.Name = '{escaped}' OR Partner__r.Name LIKE '%{escaped}%')")

    if opportunity_id:
        safe_id = str(opportunity_id).strip()[:24]
        if not re.match(r"^[a-zA-Z0-9]{15,18}$", safe_id):
            raise ValueError("opportunityId must be a valid Salesforce Id (15/18 alphanumeric chars).")
        conditions.append(f"Id = '{_escape_soql(safe_id)}'")
    elif opportunity_name:
        safe_name = str(opportunity_name).strip()[:220]
        conditions.append(f"Name LIKE '%{_escape_soql(safe_name)}%'")
    else:
        raise ValueError("Either opportunityId or opportunityName is required.")

    soql = (
        "SELECT Id, Name, Amount, CloseDate, StageName, Probability, IsClosed, IsWon, "
        "Account.Name, Account.BillingCountry, Owner.Name, Partner__r.Name, Partner_Source_Influence__c, "
        "Channel_Manager__c, CreatedDate, LastModifiedDate, Description "
        f"FROM Opportunity WHERE {' AND '.join(conditions)} ORDER BY LastModifiedDate DESC LIMIT 5"
    )
    res = await sf.query(soql)
    records = [
        {"id": r["Id"], "name": r["Name"], "amount": r.get("Amount") or 0,
         "closeDate": r.get("CloseDate"), "stageName": r.get("StageName"),
         "probability": r.get("Probability"), "isClosed": bool(r.get("IsClosed")),
         "isWon": bool(r.get("IsWon")),
         "accountName": (r.get("Account") or {}).get("Name"),
         "country": (r.get("Account") or {}).get("BillingCountry"),
         "ownerName": (r.get("Owner") or {}).get("Name"),
         "partnerName": (r.get("Partner__r") or {}).get("Name"),
         "partnerInfluence": r.get("Partner_Source_Influence__c"),
         "channelManager": r.get("Channel_Manager__c"),
         "createdDate": r.get("CreatedDate"), "lastModifiedDate": r.get("LastModifiedDate"),
         "description": r.get("Description")}
        for r in res.get("records", [])
    ]
    primary = records[0] if records else None
    answer_md = (
        "\n".join([
            f"Opportunity: {primary['name']} (Id: {primary['id']})",
            f"Amount: {int(primary['amount'] or 0):,}",
            f"Close Date: {primary['closeDate'] or '-'}",
            f"Stage: {primary['stageName'] or '-'}",
            f"Owner: {primary['ownerName'] or '-'}",
            f"Partner: {primary['partnerName'] or '-'}",
            f"Country: {primary['country'] or '-'}",
            f"Is Closed: {primary['isClosed']}",
            f"Is Won: {primary['isWon']}",
            f"Last Modified: {primary['lastModifiedDate'] or '-'}",
        ]) if primary else "No matching opportunity found."
    )
    return {
        "tool": "get_opportunity_detail",
        "period": _summarize_period(period) if period else None,
        "answer_markdown": answer_md,
        "data": {"found": bool(records), "count": len(records), "primary": primary, "matches": records},
    }


async def get_deal_registrations(sf, period: str) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    soql = (
        f"SELECT COUNT(Id) totalRegistrations FROM Deal_Registration__c "
        f"WHERE CreatedDate >= {range_['start'].isoformat()}T00:00:00Z "
        f"AND CreatedDate <= {range_['end'].isoformat()}T23:59:59Z"
    )
    res = await sf.query(soql)
    return {
        "tool": "get_deal_registrations",
        "period": _summarize_period(period),
        "data": {"totalRegistrations": _num(res["records"][0], "totalRegistrations", "expr0")},
    }


async def get_growth(
    sf,
    metric: str,
    period_a: str,
    period_b: str,
    breakdown: str = "total",
    limit: int = 10,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period_a = _normalize_period(period_a)
    period_b = _normalize_period(period_b)
    _assert_enum(metric, METRICS, "metric")
    _assert_enum(period_a, PERIODS, "periodA")
    _assert_enum(period_b, PERIODS, "periodB")
    safe_limit = _clamp_limit(limit, 10, 50)

    getter = get_revenue if metric == "revenue" else get_pipeline
    a, b = await asyncio.gather(
        getter(sf, period_a, breakdown=breakdown, limit=safe_limit, channel_manager=channel_manager),
        getter(sf, period_b, breakdown=breakdown, limit=safe_limit, channel_manager=channel_manager),
    )

    if breakdown == "total":
        val_a = a["data"].get("totalRevenue" if metric == "revenue" else "totalPipeline", 0)
        val_b = b["data"].get("totalRevenue" if metric == "revenue" else "totalPipeline", 0)
        abs_change = val_a - val_b
        return {
            "tool": "get_growth", "metric": metric, "periodA": a["period"], "periodB": b["period"],
            "breakdown": breakdown,
            "data": {"valueA": val_a, "valueB": val_b, "absoluteChange": abs_change,
                     "percentageChange": (abs_change / val_b) if val_b != 0 else None},
        }

    key_field = "country" if breakdown == "country" else "partnerName" if breakdown == "partner" else "quarter"
    value_field = "totalRevenue" if metric == "revenue" else "totalPipeline"
    map_a = {row[key_field]: row for row in (a["data"] if isinstance(a["data"], list) else [])}
    map_b = {row[key_field]: row for row in (b["data"] if isinstance(b["data"], list) else [])}
    keys = set(map_a) | set(map_b)
    growth = []
    for k in keys:
        va = map_a.get(k, {}).get(value_field, 0)
        vb = map_b.get(k, {}).get(value_field, 0)
        abs_c = va - vb
        growth.append({key_field: k, "valueA": va, "valueB": vb, "absoluteChange": abs_c,
                       "percentageChange": (abs_c / vb) if vb != 0 else None})
    growth.sort(key=lambda x: x.get("absoluteChange", 0) or 0, reverse=True)
    return {
        "tool": "get_growth", "metric": metric, "periodA": a["period"], "periodB": b["period"],
        "breakdown": breakdown, "limit": safe_limit, "data": growth[:safe_limit],
    }


async def get_orphan_hygiene(
    sf,
    period: str,
    limit: int = 20,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    safe_limit = _clamp_limit(limit, 20, 50)
    range_ = _get_period_range(period)

    where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager,
                              extra_conditions=["Partner__c = null"])
    summary_res, top_res, stage_res, country_res = await asyncio.gather(
        sf.query(f"SELECT COUNT(Id) orphanCount, SUM(Amount) orphanValue FROM Opportunity WHERE {where}"),
        sf.query(f"SELECT Id, Name, Amount, StageName, CloseDate, Account.Name, Account.BillingCountry "
                 f"FROM Opportunity WHERE {where} ORDER BY Amount DESC NULLS LAST LIMIT {safe_limit}"),
        sf.query(f"SELECT StageName stage, COUNT(Id) orphanCount, SUM(Amount) orphanValue "
                 f"FROM Opportunity WHERE {where} GROUP BY StageName ORDER BY SUM(Amount) DESC"),
        sf.query(f"SELECT Account.BillingCountry country, COUNT(Id) orphanCount, SUM(Amount) orphanValue "
                 f"FROM Opportunity WHERE {where} GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC"),
    )
    return {
        "tool": "get_orphan_hygiene", "period": _summarize_period(period),
        "limit": safe_limit, "channelManager": channel_manager or None,
        "data": {
            "orphanCount": _num(summary_res["records"][0], "orphanCount", "expr0"),
            "orphanValue": _num(summary_res["records"][0], "orphanValue", "expr1"),
            "byStage": [{"stage": r.get("stage"), "orphanCount": _num(r, "orphanCount", "expr0"),
                         "orphanValue": _num(r, "orphanValue", "expr1")} for r in stage_res["records"]],
            "byCountry": [{"country": r.get("country"), "orphanCount": _num(r, "orphanCount", "expr0"),
                           "orphanValue": _num(r, "orphanValue", "expr1")} for r in country_res["records"]],
            "topOrphanOpps": top_res.get("records", []),
        },
    }


async def get_kpi_snapshot(
    sf,
    period: str,
    revenue_target: float | None = None,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    base = _build_opp_where(closed_mode=None, range_=range_, channel_manager=channel_manager)

    (won_res, open_res, total_closed_res, won_closed_res, avg_res, orphan_res, partner_stats_res) = await asyncio.gather(
        sf.query(f"SELECT SUM(Amount) revenue, COUNT(Id) wonCount FROM Opportunity WHERE {base} AND StageName = 'Closed Won'"),
        sf.query(f"SELECT SUM(Amount) pipeline, COUNT(Id) openCount FROM Opportunity WHERE {base} AND IsClosed = false AND StageName NOT IN ('Closed Won','Closed Lost')"),
        sf.query(f"SELECT COUNT(Id) totalClosed FROM Opportunity WHERE {base} AND IsClosed = true"),
        sf.query(f"SELECT COUNT(Id) wonClosed FROM Opportunity WHERE {base} AND IsClosed = true AND IsWon = true"),
        sf.query(f"SELECT AVG(Amount) avgClosedDeal FROM Opportunity WHERE {base} AND IsClosed = true"),
        sf.query(f"SELECT COUNT(Id) orphanCount FROM Opportunity WHERE {base} AND IsClosed = false AND Partner__c = null"),
        sf.query(f"SELECT Partner__c partnerId, SUM(Amount) amount FROM Opportunity WHERE {base} AND Partner__c != null GROUP BY Partner__c"),
    )

    try:
        focus_res = await sf.query(
            f"SELECT COUNT(Id) focusPartners FROM Account WHERE Type LIKE '%Partner%' "
            f"AND Target_Account_Status__c = 'Focus' AND BillingCountry IN {COUNTRIES_SQL}"
        )
        focus_partners = _num(focus_res["records"][0], "focusPartners", "expr0")
    except Exception:
        focus_partners = None

    total_closed = _num(total_closed_res["records"][0], "totalClosed", "expr0")
    won_closed = _num(won_closed_res["records"][0], "wonClosed", "expr0")
    revenue = _num(won_res["records"][0], "revenue", "expr0")
    pipeline = _num(open_res["records"][0], "pipeline", "expr0")
    open_count = _num(open_res["records"][0], "openCount", "expr1")
    active_partners = len(partner_stats_res.get("records", []))
    top3_revenue = sum(sorted([_num(r, "amount", "expr0") for r in partner_stats_res.get("records", [])], reverse=True)[:3])

    return {
        "tool": "get_kpi_snapshot", "period": _summarize_period(period),
        "channelManager": channel_manager or None,
        "data": {
            "revenue": revenue, "pipeline": pipeline,
            "winRate": (won_closed / total_closed) if total_closed > 0 else 0,
            "averageDealSizeClosed": _num(avg_res["records"][0], "avgClosedDeal", "expr0"),
            "activePartners": active_partners,
            "focusPartners": focus_partners,
            "orphanOpenCount": _num(orphan_res["records"][0], "orphanCount", "expr0"),
            "orphanOpenPct": (_num(orphan_res["records"][0], "orphanCount", "expr0") / open_count) if open_count > 0 else 0,
            "revenueConcentrationTop3": (top3_revenue / revenue) if revenue > 0 else 0,
            "coverageRatio": (pipeline / float(revenue_target)) if revenue_target and float(revenue_target) > 0 else None,
            "revenueTarget": float(revenue_target) if revenue_target is not None else None,
        },
    }


async def route_slash_command(sf, input_: str, channel_manager: str = DEFAULT_CHANNEL_MANAGER) -> dict[str, Any]:
    safe_input = str(input_).strip()[:200]
    if not safe_input.startswith("/"):
        raise ValueError("Slash command must start with /")

    parts = safe_input[1:].split()
    command = parts[0] if parts else ""
    rest = parts[1:]
    arg = rest[0].lower() if rest else ""

    if command == "pipeline":
        lowered = [s.lower() for s in rest]
        if "partner" in lowered:
            p_idx = lowered.index("partner")
            partner_tokens = list(rest[p_idx + 1:])
            period = "THIS_FISCAL_YEAR"
            pt_lower = [t.lower() for t in partner_tokens]

            def ends_with(arr: list, suffix: list) -> bool:
                return len(arr) >= len(suffix) and arr[-len(suffix):] == suffix

            if ends_with(pt_lower, ["next_quarter"]) or ends_with(pt_lower, ["next", "quarter"]):
                period = "NEXT_QUARTER"
                partner_tokens = partner_tokens[:(-1 if ends_with(pt_lower, ["next_quarter"]) else -2)]
            elif ends_with(pt_lower, ["this_quarter"]) or ends_with(pt_lower, ["this", "quarter"]) or ends_with(pt_lower, ["current", "quarter"]):
                period = "THIS_QUARTER"
                partner_tokens = partner_tokens[:(-1 if ends_with(pt_lower, ["this_quarter"]) else -2)]
            elif ends_with(pt_lower, ["last_quarter"]) or ends_with(pt_lower, ["last", "quarter"]):
                period = "LAST_QUARTER"
                partner_tokens = partner_tokens[:(-1 if ends_with(pt_lower, ["last_quarter"]) else -2)]
            elif ends_with(pt_lower, ["fy"]) or ends_with(pt_lower, ["fy27"]) or ends_with(pt_lower, ["current_fy"]) or ends_with(pt_lower, ["current", "fy"]):
                period = "THIS_FISCAL_YEAR"
                partner_tokens = partner_tokens[:(-2 if ends_with(pt_lower, ["current", "fy"]) else -1)]

            pn = " ".join(partner_tokens).strip()
            if not pn:
                raise ValueError("Partner name is required for /pipeline partner <name>")
            return await get_partner_detail(sf, pn, period, channel_manager="")

        return await get_pipeline(sf, "CURRENT", "total", channel_manager=channel_manager)

    if command == "revenue":
        return await get_revenue(sf, "THIS_FISCAL_YEAR", "total", channel_manager=channel_manager)

    if command == "top_partners":
        metric = "pipeline" if arg == "pipeline" else "revenue"
        return await get_top_partners(sf, metric, "THIS_QUARTER", limit=10, channel_manager=channel_manager)

    if command == "orphans":
        return await get_orphan_hygiene(sf, "THIS_QUARTER", limit=20, channel_manager=channel_manager)

    raise ValueError(f"Unsupported slash command: /{command}")


async def run_exploratory_analysis(sf, intent: str, channel_manager: str = DEFAULT_CHANNEL_MANAGER) -> dict[str, Any]:
    normalized = str(intent).strip()[:400].lower()

    if normalized.startswith("/"):
        return await route_slash_command(sf, normalized, channel_manager)

    # Detect period from intent text
    period = "THIS_FISCAL_YEAR"
    if m := re.search(r"\bq([1-4])\b", normalized):
        period = f"Q{m.group(1)}"
    elif m := re.search(r"\bquarter\s*([1-4])\b", normalized):
        period = f"Q{m.group(1)}"
    elif "next quarter" in normalized:
        period = "NEXT_QUARTER"
    elif "last quarter" in normalized:
        period = "LAST_QUARTER"
    elif "this quarter" in normalized or "current quarter" in normalized:
        period = "THIS_QUARTER"

    quoted = re.search(r"""['"]([^'"]+)['"]""", normalized)

    if "opportunity" in normalized and any(kw in normalized for kw in ["detail", "more details", "tell me more", "who owns", "sales rep", "owner"]):
        opp_name = quoted.group(1).strip() if quoted else None
        if opp_name:
            result = await get_opportunity_detail(sf, opportunity_name=opp_name, period=period, channel_manager="")
            return {"tool": "run_exploratory_analysis", "intent": intent,
                    "mappedTool": "get_opportunity_detail", "data": result["data"]}

    partner_m = re.search(r"partner\s+(.+?)(?:\s+(?:have|has|in|for|with|on|during|this|next|last|fy\d+|fy|q[1-4]|quarter)\b|[?.!,]|$)", normalized)
    if partner_m and any(kw in normalized for kw in ["pipeline", "open deals", "how many deals"]):
        pn = partner_m.group(1).strip()
        if pn:
            result = await get_partner_pipeline(sf, pn, period, open_opp_limit=20, channel_manager="")
            return {"tool": "run_exploratory_analysis", "intent": intent,
                    "mappedTool": "get_partner_pipeline", "data": result["data"],
                    "period": result["period"], "matchedPartners": result["matchedPartners"]}

    if "orphan" in normalized or "without partner" in normalized or "no partner" in normalized:
        result = await get_orphan_hygiene(sf, "THIS_QUARTER", channel_manager=channel_manager)
        return {"tool": "run_exploratory_analysis", "intent": intent, "mappedTool": "get_orphan_hygiene", "data": result["data"]}

    if "top partner" in normalized and "revenue" in normalized:
        result = await get_top_partners(sf, "revenue", "THIS_QUARTER", limit=10, channel_manager=channel_manager)
        return {"tool": "run_exploratory_analysis", "intent": intent, "mappedTool": "get_top_partners", "data": result["data"]}

    if "top partner" in normalized and "pipeline" in normalized:
        result = await get_top_partners(sf, "pipeline", "THIS_QUARTER", limit=10, channel_manager=channel_manager)
        return {"tool": "run_exploratory_analysis", "intent": intent, "mappedTool": "get_top_partners", "data": result["data"]}

    if "growth" in normalized or "yoy" in normalized or "qoq" in normalized:
        metric = "pipeline" if "pipeline" in normalized else "revenue"
        breakdown = "country" if "country" in normalized else "total"
        result = await get_growth(sf, metric, "THIS_FISCAL_YEAR", "LAST_FISCAL_YEAR", breakdown=breakdown, channel_manager=channel_manager)
        return {"tool": "run_exploratory_analysis", "intent": intent, "mappedTool": "get_growth", "data": result["data"]}

    if "pipeline" in normalized:
        if "opportunit" in normalized:
            q = quoted.group(1).strip() if quoted else intent
            result = await search_opportunities(sf, q, period=period, limit=10, channel_manager="")
            return {"tool": "run_exploratory_analysis", "intent": intent,
                    "mappedTool": "search_opportunities", "data": result["data"], "period": result["period"]}
        result = await get_pipeline(sf, "THIS_QUARTER", "total", channel_manager=channel_manager)
        return {"tool": "run_exploratory_analysis", "intent": intent, "mappedTool": "get_pipeline", "data": result["data"]}

    if "revenue" in normalized:
        result = await get_revenue(sf, "THIS_FISCAL_YEAR", "total", channel_manager=channel_manager)
        return {"tool": "run_exploratory_analysis", "intent": intent, "mappedTool": "get_revenue", "data": result["data"]}

    raise ValueError("Intent is unclear for deterministic routing. Try a direct canonical tool or slash command.")


async def get_opportunity_list(
    sf,
    partner_name: str | None = None,
    country: str | None = None,
    stage: str | None = None,
    min_amount: float | None = None,
    period: str = "THIS_FISCAL_YEAR",
    limit: int = 20,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    safe_limit = _clamp_limit(limit, 1, 100)
    range_ = _get_period_range(period)

    extra: list[str] = []
    if partner_name:
        extra.append(f"Partner__r.Name LIKE '%{_escape_soql(str(partner_name))}%'")
    if country:
        extra.append(f"Account.BillingCountry = '{_escape_soql(str(country))}'")
    if stage:
        extra.append(f"StageName = '{_escape_soql(str(stage))}'")
    if min_amount is not None and float(min_amount) > 0:
        extra.append(f"Amount >= {float(min_amount)}")

    where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager, extra_conditions=extra)
    soql = (
        f"SELECT Id, Name, Account.Name accountName, Partner__r.Name partnerName, StageName, Amount, "
        f"CloseDate, Account.BillingCountry, Owner.Name ownerName, Probability "
        f"FROM Opportunity WHERE {where} ORDER BY CloseDate ASC LIMIT {safe_limit}"
    )
    res = await sf.query(soql)
    return {
        "tool": "get_opportunity_list", "period": _summarize_period(period),
        "filters": {"partnerName": partner_name, "country": country, "stage": stage, "minAmount": min_amount},
        "data": [
            {"id": r["Id"], "name": r["Name"],
             "account": (r.get("Account") or {}).get("Name") or "-",
             "partner": (r.get("Partner__r") or {}).get("Name") or "-",
             "stage": r.get("StageName"), "amount": _num(r, "Amount", "Amount"),
             "probability": r.get("Probability") or 0,
             "owner": (r.get("Owner") or {}).get("Name") or "-",
             "closeDate": r.get("CloseDate"),
             "country": (r.get("Account") or {}).get("BillingCountry") or "-"}
            for r in res.get("records", [])
        ],
    }


async def get_partner_scorecard(
    sf,
    partner_name: str,
    period: str = "THIS_FISCAL_YEAR",
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    safe_partner = _escape_soql(str(partner_name))

    test_base = _build_opp_where(closed_mode=None, range_=range_, channel_manager=channel_manager)
    test_res = await sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE Partner__r.Name = '{safe_partner}' AND {test_base}")
    partner_cond = (
        f"Partner__r.Name = '{safe_partner}'"
        if (test_res.get("records") or [{}])[0].get("cnt", 0) > 0
        else f"Partner__r.Name LIKE '%{safe_partner}%'"
    )
    base_where = _build_opp_where(closed_mode=None, range_=range_, channel_manager=channel_manager, extra_conditions=[partner_cond])

    (rev_res, pipe_res, deal_res, avg_res, countries_res, stages_res, dates_res) = await asyncio.gather(
        sf.query(f"SELECT SUM(Amount) totalRevenue FROM Opportunity WHERE {base_where} AND StageName = 'Closed Won'"),
        sf.query(f"SELECT SUM(Amount) totalPipeline FROM Opportunity WHERE {base_where} AND IsClosed = false"),
        sf.query(f"SELECT COUNT(Id) dealCount FROM Opportunity WHERE {base_where}"),
        sf.query(f"SELECT AVG(Amount) avgAmount FROM Opportunity WHERE {base_where} AND StageName = 'Closed Won'"),
        sf.query(f"SELECT DISTINCT Account.BillingCountry country FROM Opportunity WHERE {base_where}"),
        sf.query(f"SELECT StageName stage, COUNT(Id) stageCount FROM Opportunity WHERE {base_where} AND IsClosed = false GROUP BY StageName"),
        sf.query(f"SELECT CloseDate FROM Opportunity WHERE {base_where}"),
    )

    by_q: dict[str, int] = {}
    for r in dates_res.get("records", []):
        if r.get("CloseDate"):
            q = _fiscal_quarter_from_date_str(r["CloseDate"])
            by_q[q] = by_q.get(q, 0) + 1

    return {
        "tool": "get_partner_scorecard", "period": _summarize_period(period),
        "partner": partner_name, "channelManager": channel_manager or None,
        "data": {
            "revenue": _num(rev_res["records"][0], "totalRevenue", "expr0"),
            "pipeline": _num(pipe_res["records"][0], "totalPipeline", "expr0"),
            "dealCount": _num(deal_res["records"][0], "dealCount", "expr0"),
            "avgDealSize": _num(avg_res["records"][0], "avgAmount", "expr0"),
            "topCountries": [r.get("country") for r in countries_res.get("records", []) if r.get("country")][:5],
            "openStages": [{"stage": r.get("stage"), "count": _num(r, "stageCount", "expr0")} for r in stages_res.get("records", [])],
            "byQuarter": [{"quarter": q, "count": by_q.get(q, 0)} for q in ["Q1", "Q2", "Q3", "Q4"]],
        },
    }


def list_available_metrics() -> dict[str, Any]:
    return {
        "tool": "list_available_metrics",
        "runtime": {"version": TOOL_VERSION, "defaultChannelManager": DEFAULT_CHANNEL_MANAGER or None},
        "canonicalTools": [
            {"name": "get_revenue", "purpose": "Closed won revenue metrics", "keyParams": ["period", "breakdown", "limit", "channel_manager"]},
            {"name": "get_pipeline", "purpose": "Open pipeline metrics", "keyParams": ["period", "breakdown", "limit", "channel_manager"]},
            {"name": "get_top_partners", "purpose": "Top partners by revenue or pipeline", "keyParams": ["metric", "period", "limit"]},
            {"name": "get_partner_detail", "purpose": "Partner scorecard for one partner", "keyParams": ["partner_name", "period"]},
            {"name": "get_partner_pipeline", "purpose": "Partner-specific open pipeline", "keyParams": ["partner_name", "period"]},
            {"name": "search_opportunities", "purpose": "Search opportunities by name", "keyParams": ["query", "period", "partner_name"]},
            {"name": "get_opportunity_detail", "purpose": "Opportunity detail by ID or name", "keyParams": ["opportunity_id|opportunity_name"]},
            {"name": "get_deal_registrations", "purpose": "Deal registration count by period", "keyParams": ["period"]},
            {"name": "get_growth", "purpose": "Growth between two periods", "keyParams": ["metric", "period_a", "period_b", "breakdown"]},
            {"name": "get_orphan_hygiene", "purpose": "Open opportunities missing partner", "keyParams": ["period", "limit"]},
            {"name": "get_kpi_snapshot", "purpose": "KPI bundle for channel leadership", "keyParams": ["period", "revenue_target"]},
            {"name": "route_slash_command", "purpose": "Slash command router", "keyParams": ["input"]},
            {"name": "run_exploratory_analysis", "purpose": "Natural-language intent mapping", "keyParams": ["intent"]},
            {"name": "get_opportunity_list", "purpose": "Paginated opportunity list", "keyParams": ["period", "partner_name", "country", "stage"]},
            {"name": "get_partner_scorecard", "purpose": "Deep partner scorecard", "keyParams": ["partner_name", "period"]},
            {"name": "get_weighted_pipeline", "purpose": "Probability-weighted pipeline", "keyParams": ["period", "breakdown", "min_probability"]},
            {"name": "get_channel_manager_performance", "purpose": "Channel manager metrics", "keyParams": ["period", "metric"]},
            {"name": "get_multi_period_trend", "purpose": "Multi-period trend analysis", "keyParams": ["metric", "periods", "breakdown"]},
            {"name": "get_deal_registrations_breakdown", "purpose": "Deal registrations with breakdown", "keyParams": ["period", "breakdown"]},
            {"name": "get_win_rate_by_country", "purpose": "Win rate by country", "keyParams": ["period"]},
            {"name": "get_time_to_close_stats", "purpose": "Time to close statistics", "keyParams": ["period", "breakdown"]},
        ],
        "adminTools": [
            {"name": "admin_discover_targets", "purpose": "Admin metadata diagnostics for quota/target fields", "keyParams": ["admin_key", "limit"]},
        ],
        "supportedPeriods": PERIODS,
        "supportedMetrics": METRICS,
        "southernEuropeCountries": COUNTRIES,
    }


async def admin_discover_targets(sf, admin_key: str, limit: int = 30) -> dict[str, Any]:
    safe_limit = _clamp_limit(limit, 30, 100)
    if not ADMIN_KEY:
        raise ValueError("ADMIN_KEY is not configured. Set ADMIN_KEY in .env to use admin diagnostics.")
    if not admin_key or admin_key != ADMIN_KEY:
        raise PermissionError("Unauthorized. Invalid adminKey.")

    queries = {
        "opportunityFields": f"SELECT QualifiedApiName, Label, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Opportunity' AND (QualifiedApiName LIKE '%Target%' OR QualifiedApiName LIKE '%Quota%' OR QualifiedApiName LIKE '%Goal%') ORDER BY QualifiedApiName LIMIT {safe_limit}",
        "accountFields": f"SELECT QualifiedApiName, Label, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Account' AND (QualifiedApiName LIKE '%Target%' OR QualifiedApiName LIKE '%Quota%' OR QualifiedApiName LIKE '%Goal%') ORDER BY QualifiedApiName LIMIT {safe_limit}",
        "customObjects": f"SELECT QualifiedApiName, Label FROM EntityDefinition WHERE IsCustomizable = true AND (QualifiedApiName LIKE '%Target%' OR QualifiedApiName LIKE '%Plan%' OR QualifiedApiName LIKE '%Quota%') ORDER BY QualifiedApiName LIMIT {safe_limit}",
        "reports": f"SELECT Id, Name, DeveloperName, LastRunDate FROM Report WHERE Name LIKE '%target%' OR Name LIKE '%quota%' OR Name LIKE '%plan%' ORDER BY LastRunDate DESC LIMIT {safe_limit}",
    }
    result: dict[str, Any] = {}
    for key, soql in queries.items():
        try:
            res = await sf.query(soql)
            result[key] = {"ok": True, "count": res.get("totalSize", 0), "records": res.get("records", [])}
        except Exception as e:
            result[key] = {"ok": False, "error": str(e), "records": []}
    return {
        "tool": "admin_discover_targets", "data": result,
        "nextStep": "Pick one authoritative target source and wire it into get_kpi_snapshot coverageRatio.",
    }


async def get_weighted_pipeline(
    sf,
    period: str = "THIS_FISCAL_YEAR",
    breakdown: str = "total",
    limit: int = 20,
    channel_manager: str = "",
    min_probability: float = 0,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    safe_limit = _clamp_limit(limit, 20, 1000)
    safe_prob = max(0.0, min(100.0, float(min_probability or 0)))
    breakdown = breakdown if breakdown in ["total", "country", "partner", "stage"] else "total"

    where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)
    soql = (
        f"SELECT Amount, Probability, Account.BillingCountry, Partner__r.Name, StageName "
        f"FROM Opportunity WHERE {where} AND Probability >= {safe_prob}"
    )
    res = await sf.query(soql)
    records = res.get("records", [])

    weighted_total = 0.0
    raw_total = 0.0
    breakdown_map: dict[str, dict] = {}

    for r in records:
        amount = r.get("Amount") or 0
        prob = r.get("Probability") or 0
        w = amount * prob / 100
        weighted_total += w
        raw_total += amount

        key: str | None = None
        if breakdown == "country":
            key = (r.get("Account") or {}).get("BillingCountry") or "Unknown"
        elif breakdown == "partner":
            key = (r.get("Partner__r") or {}).get("Name") or "Orphan"
        elif breakdown == "stage":
            key = r.get("StageName") or "Unknown"

        if key is not None:
            if key not in breakdown_map:
                breakdown_map[key] = {"weighted": 0.0, "raw": 0.0, "count": 0}
            breakdown_map[key]["weighted"] += w
            breakdown_map[key]["raw"] += amount
            breakdown_map[key]["count"] += 1

    breakdown_arr = sorted(
        [{"label": k, "weightedPipeline": round(v["weighted"]), "rawPipeline": round(v["raw"]),
          "dealCount": v["count"],
          "avgProbability": round((v["weighted"] / v["raw"] * 100) if v["raw"] > 0 else 0, 1)}
         for k, v in breakdown_map.items()],
        key=lambda x: x["weightedPipeline"], reverse=True
    )[:safe_limit]

    return {
        "tool": "get_weighted_pipeline", "period": _summarize_period(period),
        "breakdown": breakdown, "filters": {"minProbability": safe_prob, "channelManager": channel_manager or None},
        "data": {
            "weightedTotal": round(weighted_total), "rawTotal": round(raw_total),
            "coverageRatio": round(weighted_total / raw_total * 100, 1) if raw_total > 0 else 0,
            "dealCount": len(records), "breakdown": breakdown_arr,
        },
    }


async def get_channel_manager_performance(
    sf,
    period: str = "THIS_FISCAL_YEAR",
    metric: str = "both",
    limit: int = 20,
    channel_manager: str = "",
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    safe_limit = _clamp_limit(limit, 20, 500)
    metric = metric if metric in ["revenue", "pipeline", "both"] else "both"

    base_where = _build_opp_where(closed_mode=None, range_=range_, channel_manager="")

    (rev_res, pipe_res, win_rate_res, won_res) = await asyncio.gather(
        sf.query(f"SELECT Channel_Manager__c manager, SUM(Amount) totalRevenue, COUNT(Id) wonCount FROM Opportunity WHERE {base_where} AND StageName = 'Closed Won' GROUP BY Channel_Manager__c ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"),
        sf.query(f"SELECT Channel_Manager__c manager, SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE {base_where} AND IsClosed = false GROUP BY Channel_Manager__c ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"),
        sf.query(f"SELECT Channel_Manager__c manager, COUNT(Id) totalClosed FROM Opportunity WHERE {base_where} AND IsClosed = true GROUP BY Channel_Manager__c"),
        sf.query(f"SELECT Channel_Manager__c manager, COUNT(Id) wonCount FROM Opportunity WHERE {base_where} AND IsWon = true GROUP BY Channel_Manager__c"),
    )

    mgr_map: dict[str, dict] = {}
    for r in rev_res.get("records", []):
        k = r.get("manager") or "Unassigned"
        mgr_map[k] = {"manager": k, "revenue": _num(r, "totalRevenue", "expr0"),
                      "wonDeals": _num(r, "wonCount", "expr1"), "pipeline": 0, "dealCount": 0,
                      "totalClosed": 0, "wonClosed": 0}
    for r in pipe_res.get("records", []):
        k = r.get("manager") or "Unassigned"
        mgr_map.setdefault(k, {"manager": k, "revenue": 0, "wonDeals": 0, "pipeline": 0, "dealCount": 0, "totalClosed": 0, "wonClosed": 0})
        mgr_map[k]["pipeline"] = _num(r, "totalPipeline", "expr0")
        mgr_map[k]["dealCount"] = _num(r, "dealCount", "expr1")
    for r in win_rate_res.get("records", []):
        k = r.get("manager") or "Unassigned"
        mgr_map.setdefault(k, {"manager": k, "revenue": 0, "wonDeals": 0, "pipeline": 0, "dealCount": 0, "totalClosed": 0, "wonClosed": 0})
        mgr_map[k]["totalClosed"] = _num(r, "totalClosed", "expr0")
    for r in won_res.get("records", []):
        k = r.get("manager") or "Unassigned"
        mgr_map.setdefault(k, {"manager": k, "revenue": 0, "wonDeals": 0, "pipeline": 0, "dealCount": 0, "totalClosed": 0, "wonClosed": 0})
        mgr_map[k]["wonClosed"] = _num(r, "wonCount", "expr0")

    results = sorted(
        [{"manager": m["manager"], "revenue": m["revenue"], "pipeline": m["pipeline"],
          "dealCount": int(m["dealCount"] + m["wonDeals"]),
          "winRate": round(m["wonClosed"] / m["totalClosed"] * 100, 1) if m["totalClosed"] > 0 else 0}
         for m in mgr_map.values()],
        key=lambda x: x["revenue"], reverse=True
    )[:safe_limit]

    return {"tool": "get_channel_manager_performance", "period": _summarize_period(period), "metric": metric, "data": results}


async def get_multi_period_trend(
    sf,
    metric: str = "revenue",
    periods: list[str] | None = None,
    breakdown: str = "total",
    channel_manager: str = "",
    limit: int | None = None,
) -> dict[str, Any]:
    if not periods or not isinstance(periods, list):
        periods = ["Q1", "Q2", "Q3", "Q4"]
    if len(periods) > 8:
        raise ValueError("periods must have max 8 items")
    if metric not in ["revenue", "pipeline"]:
        raise ValueError("metric must be revenue or pipeline")
    breakdown = breakdown if breakdown in ["total", "country", "partner"] else "total"

    normalized_periods = [_normalize_period(p) for p in periods]
    for p in normalized_periods:
        _assert_enum(p, PERIODS, "period")

    getter = get_revenue if metric == "revenue" else get_pipeline
    results = await asyncio.gather(*[
        getter(sf, p, breakdown=breakdown, limit=limit or 20, channel_manager=channel_manager)
        for p in normalized_periods
    ])

    series_map: dict[str, dict] = {}
    period_labels = [r["period"] for r in results]

    for result, period_label in zip(results, period_labels):
        pl = period_label.get("fiscalLabel", period_label.get("label", ""))
        data = result["data"]
        if isinstance(data, list):
            for row in data:
                key_field = "country" if breakdown == "country" else "partnerName" if breakdown == "partner" else "quarter"
                label = row.get(key_field) or "Unknown"
                value_field = "totalRevenue" if metric == "revenue" else "totalPipeline"
                if label not in series_map:
                    series_map[label] = {"label": label}
                series_map[label][pl] = row.get(value_field, 0)
        else:
            value = data.get("totalRevenue" if metric == "revenue" else "totalPipeline", 0)
            series_map.setdefault("Total", {"label": "Total"})["Total"]
            series_map["Total"][pl] = value

    return {
        "tool": "get_multi_period_trend", "metric": metric, "breakdown": breakdown,
        "periods": period_labels, "data": list(series_map.values()),
    }


async def get_deal_registrations_breakdown(
    sf,
    period: str = "THIS_FISCAL_YEAR",
    breakdown: str = "total",
    limit: int = 20,
    channel_manager: str = "",
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    safe_limit = _clamp_limit(limit, 20, 500)
    breakdown = breakdown if breakdown in ["total", "partner", "country"] else "total"

    start_iso = f"{range_['start'].isoformat()}T00:00:00Z"
    end_iso = f"{range_['end'].isoformat()}T23:59:59Z"

    try:
        total_res = await sf.query(f"SELECT COUNT(Id) total FROM Deal_Registration__c WHERE CreatedDate >= {start_iso} AND CreatedDate <= {end_iso}")
        total = _num(total_res["records"][0], "total", "expr0")
        breakdown_data: list[dict] = []

        if breakdown == "partner":
            pres = await sf.query(
                f"SELECT Partner__r.Name partnerName, COUNT(Id) count FROM Deal_Registration__c "
                f"WHERE CreatedDate >= {start_iso} AND CreatedDate <= {end_iso} "
                f"GROUP BY Partner__r.Name ORDER BY COUNT(Id) DESC LIMIT {safe_limit}"
            )
            breakdown_data = [{"label": r.get("partnerName") or "Unknown", "value": _num(r, "count", "expr0")} for r in pres.get("records", [])]
        elif breakdown == "country":
            cres = await sf.query(
                f"SELECT Partner_Country__c country, COUNT(Id) count FROM Deal_Registration__c "
                f"WHERE CreatedDate >= {start_iso} AND CreatedDate <= {end_iso} "
                f"GROUP BY Partner_Country__c ORDER BY COUNT(Id) DESC LIMIT {safe_limit}"
            )
            breakdown_data = [{"label": r.get("country") or "Unknown", "value": _num(r, "count", "expr0")} for r in cres.get("records", [])]

        return {
            "tool": "get_deal_registrations_breakdown", "period": _summarize_period(period),
            "breakdown": breakdown, "data": {"total": int(total), "breakdown": breakdown_data},
        }
    except Exception as e:
        return {
            "tool": "get_deal_registrations_breakdown", "period": _summarize_period(period),
            "breakdown": breakdown,
            "data": {"total": 0, "breakdown": [], "note": f"Deal_Registration__c not available: {e}"},
        }


async def get_win_rate_by_country(
    sf,
    period: str = "THIS_FISCAL_YEAR",
    channel_manager: str = "",
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode=None, range_=range_, channel_manager=channel_manager)

    closed_res, won_res = await asyncio.gather(
        sf.query(f"SELECT Account.BillingCountry country, COUNT(Id) totalCount, SUM(Amount) totalAmount FROM Opportunity WHERE {base_where} AND IsClosed = true GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC"),
        sf.query(f"SELECT Account.BillingCountry country, COUNT(Id) wonCount, SUM(Amount) wonAmount FROM Opportunity WHERE {base_where} AND StageName = 'Closed Won' GROUP BY Account.BillingCountry"),
    )

    won_map = {r.get("country", "Unknown"): {"won": _num(r, "wonCount", "expr0"), "wonAmount": _num(r, "wonAmount", "expr1")}
               for r in won_res.get("records", [])}

    def _row_to_country_stats(r: dict) -> dict:
        c = r.get("country") or "Unknown"
        total = _num(r, "totalCount", "expr0")
        w = won_map.get(c, {})
        won_count = w.get("won", 0)
        won_amt = w.get("wonAmount", 0)
        return {
            "country": c,
            "winRate": round(won_count / total * 100, 1) if total > 0 else 0,
            "wonDeals": int(won_count),
            "totalDeals": int(total),
            "revenue": won_amt,
            "avgDealSize": round(won_amt / won_count) if won_count > 0 else 0,
        }

    results = sorted(
        [_row_to_country_stats(r) for r in closed_res.get("records", [])],
        key=lambda x: x["revenue"], reverse=True,
    )

    return {
        "tool": "get_win_rate_by_country", "period": _summarize_period(period),
        "channelManager": channel_manager or None, "data": results, "_chartType": "bar",
    }


async def get_time_to_close_stats(
    sf,
    period: str = "THIS_FISCAL_YEAR",
    breakdown: str = "total",
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
) -> dict[str, Any]:
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    breakdown = breakdown if breakdown in ["total", "country", "partner", "stage"] else "total"

    base_where = _build_opp_where(closed_mode="won", range_=range_, channel_manager=channel_manager)
    res = await sf.query(
        f"SELECT CreatedDate, CloseDate, Amount, StageName, "
        f"Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {base_where} ORDER BY CloseDate DESC LIMIT 2000"
    )

    records = res.get("records", [])
    group_map: dict[str, list[float]] = {}

    for r in records:
        cd = r.get("CreatedDate", "")[:10]
        cl = r.get("CloseDate", "")[:10]
        if not cd or not cl:
            continue
        try:
            days = (date.fromisoformat(cl) - date.fromisoformat(cd)).days
        except ValueError:
            continue
        if days < 0:
            continue

        if breakdown == "country":
            key = (r.get("Account") or {}).get("BillingCountry") or "Unknown"
        elif breakdown == "partner":
            key = (r.get("Partner__r") or {}).get("Name") or "Orphan"
        elif breakdown == "stage":
            key = r.get("StageName") or "Unknown"
        else:
            key = "Total"

        group_map.setdefault(key, []).append(float(days))

    def _stats(vals: list[float]) -> dict:
        if not vals:
            return {"count": 0, "avgDays": None, "medianDays": None, "minDays": None, "maxDays": None}
        vals_sorted = sorted(vals)
        n = len(vals_sorted)
        median = vals_sorted[n // 2] if n % 2 else (vals_sorted[n // 2 - 1] + vals_sorted[n // 2]) / 2
        return {"count": n, "avgDays": round(sum(vals) / n, 1), "medianDays": round(median, 1),
                "minDays": round(vals_sorted[0], 1), "maxDays": round(vals_sorted[-1], 1)}

    data = [{"label": k, **_stats(v)} for k, v in group_map.items()]
    data.sort(key=lambda x: x.get("avgDays") or 0, reverse=True)

    return {
        "tool": "get_time_to_close_stats", "period": _summarize_period(period),
        "breakdown": breakdown, "channelManager": channel_manager or None, "data": data,
    }
