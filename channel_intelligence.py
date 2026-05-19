"""Southern Europe Channel Intelligence — ported from LocalPartner server.js.

Provides deterministic analytics tools scoped to Italy, Spain, Portugal, Greece,
Cyprus, and Malta.  All functions accept a SalesforceClient instance as their
first argument so they can share the authenticated session managed by server.py.
"""

import asyncio
import re
from datetime import date, timedelta
from typing import Any

from ci_config import (
    TOOL_VERSION,
    COUNTRIES, COUNTRIES_SQL,
    PERIODS, METRICS, BREAKDOWNS_REVENUE, BREAKDOWNS_PIPELINE,
    DEFAULT_CHANNEL_MANAGER, ADMIN_KEY, DEFAULT_PARTNER_TARGET,
    ConfigManager, get_config, _normalize_partner_key,
)
from ci_fiscal import (
    _start_of_fiscal_year, _end_of_fiscal_year, _fiscal_year_number,
    _fiscal_year_label, _fiscal_quarter_range, _fiscal_quarter_from_date_str,
    _get_period_range,
    _escape_soql, _clamp_limit, _normalize_period, _assert_enum,
    _summarize_period, _build_opp_where, _num,
)

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
    territory: str | None = None,
    revenue_target: int | None = None,
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

    # Resolve target from config if not explicitly provided
    cfg = get_config()
    fy_label = _fiscal_year_label(range_["start"])
    fy_key = f"fy{fy_label[2:]}"  # FY27 -> fy27

    target = revenue_target
    if not target:
        if partner_name:
            target = cfg.get_partner_target(partner_name, country=country, fiscal_year=fy_key)
        elif territory and country:
            target = cfg.get_territory_target(territory, country=country, fiscal_year=fy_key)
        elif territory:
            target = cfg.get_territory_target(territory, fiscal_year=fy_key)

    if breakdown == "total":
        res = await sf.query(f"SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE {where}")
        total_revenue = _num(res["records"][0], "totalRevenue", "expr0")
        deal_count = _num(res["records"][0], "dealCount", "expr1")

        result = {
            "tool": "get_revenue", "period": _summarize_period(period),
            "breakdown": breakdown, "channelManager": channel_manager or None,
            "data": {
                "totalRevenue": total_revenue,
                "dealCount": deal_count,
            },
        }

        if target:
            attainment_pct = (total_revenue / target * 100) if target > 0 else 0
            result["data"]["target"] = target
            result["data"]["attainmentPct"] = round(attainment_pct, 1)
            result["data"]["gap"] = round(target - total_revenue, 0)

        return result

    if breakdown == "country":
        res = await sf.query(
            f"SELECT Account.BillingCountry country, SUM(Amount) totalRevenue, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        data = []
        for r in res["records"]:
            country_name = r.get("country")
            revenue = _num(r, "totalRevenue", "expr0")

            item = {
                "country": country_name,
                "totalRevenue": revenue,
                "dealCount": _num(r, "dealCount", "expr1"),
            }

            if territory and country_name:
                country_target = cfg.get_territory_target(territory, country=country_name, fiscal_year=fy_key)
                if country_target:
                    item["target"] = country_target
                    item["attainmentPct"] = round(revenue / country_target * 100, 1) if country_target > 0 else 0

            data.append(item)

        return {
            "tool": "get_revenue", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": data,
        }

    if breakdown == "partner":
        res = await sf.query(
            f"SELECT Partner__c partnerId, Partner__r.Name partnerName, SUM(Amount) totalRevenue, COUNT(Id) dealCount "
            f"FROM Opportunity WHERE {where} AND Partner__c != null "
            f"GROUP BY Partner__c, Partner__r.Name ORDER BY SUM(Amount) DESC LIMIT {safe_limit}"
        )
        data = []
        for r in res["records"]:
            partner = r.get("partnerName")
            revenue = _num(r, "totalRevenue", "expr0")

            item = {
                "partnerId": r.get("partnerId"),
                "partnerName": partner,
                "totalRevenue": revenue,
                "dealCount": _num(r, "dealCount", "expr1"),
            }

            if partner:
                partner_target = cfg.get_partner_target(partner, country=country, fiscal_year=fy_key)
                if partner_target:
                    item["target"] = partner_target
                    item["attainmentPct"] = round(revenue / partner_target * 100, 1) if partner_target > 0 else 0

            data.append(item)

        return {
            "tool": "get_revenue", "period": _summarize_period(period),
            "breakdown": breakdown, "limit": safe_limit, "channelManager": channel_manager or None,
            "data": data,
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
    country: str | None = None,
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
    if country:
        conditions.append(f"Account.BillingCountry = '{_escape_soql(str(country))}'")
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
    country: str | None = None,
    period: str | None = None,
    channel_manager: str = "",
) -> dict[str, Any]:
    conditions = [f"Account.BillingCountry IN {COUNTRIES_SQL}"]

    if country:
        conditions.append(f"Account.BillingCountry = '{_escape_soql(str(country))}'")

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


async def get_deal_registrations(
    sf,
    period: str,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """Count and analyze deal registrations (Partner_Registration_Approval__c on Opportunity).

    Returns: registration counts + amounts by status + approval & close rates.
    Note: Uses CreatedDate for period filtering (Partner_Opportunity_Registration_Date__c may have data integrity issues).
    """
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)

    where_conditions = [
        f"Account.BillingCountry IN {COUNTRIES_SQL}",
        f"Partner_Registration_Approval__c != null",
        f"CreatedDate >= {range_['start'].isoformat()}T00:00:00Z",
        f"CreatedDate <= {range_['end'].isoformat()}T23:59:59Z",
    ]
    if channel_manager:
        where_conditions.append(f"Channel_Manager__c = '{_escape_soql(channel_manager)}'")

    where = " AND ".join(where_conditions)

    # Query 1: Count and amount by status
    status_res = await sf.query(
        f"SELECT Partner_Registration_Approval__c, COUNT(Id) total_count, SUM(Amount) total_amount "
        f"FROM Opportunity WHERE {where} GROUP BY Partner_Registration_Approval__c"
    )

    # Queries 2-4: Conversion rates (run in parallel)
    approved_where = f"{where} AND Partner_Registration_Approval__c = 'Approved'"
    trackable_where = f"{where} AND Partner_Registration_Approval__c IN ('Submitted', 'In Review', 'Approved', 'Rejected')"

    approved_count_res, approved_won_res, trackable_res = await asyncio.gather(
        sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE {approved_where}"),
        sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE {approved_where} AND IsWon = true"),
        sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE {trackable_where}"),
    )

    # Parse status breakdown results
    by_status = []
    total_count = 0
    total_amount = 0

    for r in status_res.get("records", []):
        status = r.get("Partner_Registration_Approval__c", "Unknown")
        count = _num(r, "total_count", "expr0")
        amount = _num(r, "total_amount", "expr1")
        by_status.append({"status": status, "count": count, "amount": amount})
        total_count += count
        total_amount += amount

    # Parse conversion rate results
    approved_total = _num(approved_count_res.get("records", [{}])[0], "cnt", "expr0")
    approved_won = _num(approved_won_res.get("records", [{}])[0], "cnt", "expr0")
    trackable_total = _num(trackable_res.get("records", [{}])[0], "cnt", "expr0")

    approval_rate = (approved_total / trackable_total * 100) if trackable_total > 0 else 0
    close_rate = (approved_won / approved_total * 100) if approved_total > 0 else 0

    by_status.sort(key=lambda x: {"Approved": 1, "Submitted": 2, "In Review": 3, "Rejected": 4}.get(x["status"], 5))

    return {
        "tool": "get_deal_registrations",
        "period": _summarize_period(period),
        "channel_manager": channel_manager or None,
        "data": {
            "total_count": total_count,
            "total_amount": round(total_amount, 0),
            "by_status": by_status,
            "approval_rate_pct": round(approval_rate, 1),
            "close_rate_pct": round(close_rate, 1),
        },
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


def _detect_period(normalized: str) -> str:
    """Extract the most specific period mention from a lowercase intent string."""
    if m := re.search(r"\bfy(\d{2})_?q([1-4])\b", normalized):
        return f"FY{m.group(1)}_Q{m.group(2)}"
    if m := re.search(r"\bq([1-4])_?fy(\d{2})\b", normalized):
        return f"FY{m.group(2)}_Q{m.group(1)}"
    if m := re.search(r"\bq([1-4])\b", normalized):
        return f"Q{m.group(1)}"
    if m := re.search(r"\bquarter\s*([1-4])\b", normalized):
        return f"Q{m.group(1)}"
    if "next quarter" in normalized:
        return "NEXT_QUARTER"
    if "last quarter" in normalized:
        return "LAST_QUARTER"
    if "this quarter" in normalized or "current quarter" in normalized:
        return "THIS_QUARTER"
    if "last year" in normalized or "previous year" in normalized or "last fiscal" in normalized:
        return "LAST_FISCAL_YEAR"
    if "last 30" in normalized or "past 30" in normalized:
        return "LAST_30_DAYS"
    if "next 60" in normalized or "coming 60" in normalized:
        return "NEXT_60_DAYS"
    return "THIS_FISCAL_YEAR"


# Complete keyword → (tool, description, base_params) routing table.
# Entries are checked in order; first match wins.
# Each entry: (trigger_keywords, tool_name, description, base_params_dict)
_ROUTING_TABLE: list[tuple[list[str], str, str, dict]] = [
    # --- Opportunity detail ---
    (["opportunity detail", "tell me about", "who owns", "sales rep", "opp detail"],
     "get_opportunity_detail",
     "Detailed view of a single opportunity",
     {"opportunity_name": "<name>", "period": "THIS_FISCAL_YEAR"}),
    # --- Partner-specific pipeline ---
    (["partner pipeline", "partner open deals", "partner open opportunities"],
     "get_partner_pipeline",
     "Open pipeline for a specific partner with deal list",
     {"partner_name": "<name>", "period": "THIS_FISCAL_YEAR"}),
    # --- Partner scorecard ---
    (["partner scorecard", "partner deep dive", "partner detail"],
     "get_partner_scorecard",
     "Deep-dive partner scorecard: revenue, pipeline, trend, countries",
     {"partner_name": "<name>", "period": "THIS_FISCAL_YEAR"}),
    # --- QBR ---
    (["qbr", "business review", "quarterly review"],
     "generate_partner_qbr",
     "Full partner Quarterly Business Review pack",
     {"partner_name": "<name>"}),
    # --- Orphan hygiene ---
    (["orphan", "without partner", "no partner", "unassigned deal"],
     "get_orphan_hygiene",
     "Open deals with no partner assigned",
     {"period": "THIS_QUARTER"}),
    # --- Deal registrations (before kpi to avoid "summary" collision) ---
    (["deal registration", "deal reg", " dr "],
     "get_deal_registrations_breakdown",
     "Deal registration breakdown by partner, country, or status",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- KPI snapshot / dashboard ---
    (["kpi", "snapshot", "dashboard", "overview", "health check"],
     "get_kpi_snapshot",
     "Core KPI bundle: revenue, pipeline, win rate, partner coverage, orphan %",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Growth / YoY / QoQ ---
    (["growth", "yoy", "qoq", "year over year", "quarter over quarter", "compare period"],
     "get_growth",
     "Period-over-period growth for revenue or pipeline",
     {"metric": "revenue", "period_a": "THIS_FISCAL_YEAR", "period_b": "LAST_FISCAL_YEAR"}),
    # --- Multi-period trend ---
    (["trend", "quarterly trend", "multi period", "over time"],
     "get_multi_period_trend",
     "Revenue or pipeline trend across multiple quarters",
     {"metric": "revenue", "periods": ["Q1", "Q2", "Q3", "Q4"], "breakdown": "total"}),
    # --- Stalled deals ---
    (["stalled", "stuck", "no activity", "not moving"],
     "get_stalled_deals",
     "Deals with no recent stage progression or activity",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Lost deals ---
    (["lost deal", "closed lost", "why we lost", "loss analysis"],
     "get_lost_deals",
     "Closed Lost deals with reason analysis",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Win rate by country ---
    (["win rate", "win ratio", "close rate"],
     "get_win_rate_by_country",
     "Win rate broken down by country",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Time to close ---
    (["time to close", "cycle time", "sales cycle", "days to close"],
     "get_time_to_close_stats",
     "Average time-to-close statistics",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Deal aging ---
    (["aging", "age of deal", "how old", "days in stage"],
     "get_deal_aging_by_stage",
     "Deals broken down by age in current stage",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- High-risk deals ---
    (["high risk", "at risk", "risk", "risky deal"],
     "get_high_risk_deals",
     "Deals flagged as high-risk by age, value, or stage",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Stage risk ---
    (["stage risk", "stage health", "stage profile"],
     "get_stage_risk_profile",
     "Risk profile broken down by pipeline stage",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Weighted pipeline ---
    (["weighted", "probability weighted", "expected value"],
     "get_weighted_pipeline",
     "Pipeline weighted by close probability",
     {"period": "THIS_QUARTER"}),
    # --- Channel manager performance ---
    (["channel manager performance", "manager comparison", "cm performance"],
     "get_channel_manager_performance",
     "Compare performance across channel managers",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- New vs existing business ---
    (["new business", "existing business", "new vs existing", "new logo"],
     "get_new_vs_existing",
     "Split of new-logo vs existing-account revenue",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Partner activity ---
    (["partner activity", "activity summary", "partner engagement"],
     "get_partner_activity_summary",
     "Recent partner activity and engagement signals",
     {"period": "THIS_QUARTER"}),
    # --- Stage velocity ---
    (["velocity", "progression", "stage speed", "moving through"],
     "get_stage_progression_velocity",
     "How fast deals move through stages",
     {"period": "THIS_FISCAL_YEAR"}),
    # --- Top partners by pipeline ---
    (["top partner", "best partner", "leading partner"],
     "get_top_partners",
     "Partners ranked by revenue or pipeline",
     {"metric": "revenue", "period": "THIS_QUARTER"}),
    # --- Pipeline (broad) ---
    (["pipeline", "open deal", "forecast", "open opportunit"],
     "get_pipeline",
     "Open pipeline analytics by country, stage, partner, or quarter",
     {"period": "THIS_QUARTER", "breakdown": "total"}),
    # --- Revenue (broad) ---
    (["revenue", "closed won", "attainment", "quota", "target achieved"],
     "get_revenue",
     "Closed-Won revenue with optional target attainment",
     {"period": "THIS_FISCAL_YEAR", "breakdown": "total"}),
]


async def run_exploratory_analysis(sf, intent: str, channel_manager: str = DEFAULT_CHANNEL_MANAGER) -> dict[str, Any]:
    """Route a natural-language intent to the best matching tool.

    For slash commands (/pipeline, /revenue, /orphans, /top_partners) the tool is
    executed directly. For free-text intents the function returns a structured hint
    with the recommended tool and suggested parameters so the LLM can call it
    precisely — this avoids silent fallthrough to the wrong tool.
    """
    normalized = str(intent).strip()[:400].lower()

    if normalized.startswith("/"):
        return await route_slash_command(sf, normalized, channel_manager)

    period = _detect_period(normalized)
    quoted = re.search(r"""['"]([^'"]+)['"]""", normalized)

    # --- Execute routes for the highest-confidence patterns ---
    # (opportunity detail and partner pipeline require extracted names, so execute directly)
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

    # --- Keyword-table routing: return structured hint rather than executing ---
    for triggers, tool_name, description, base_params in _ROUTING_TABLE:
        if any(kw in normalized for kw in triggers):
            # Inject detected period into params that accept one
            params = dict(base_params)
            if "period" in params:
                params["period"] = period
            if "period_a" in params:
                params["period_a"] = period
            return {
                "tool": "run_exploratory_analysis",
                "intent": intent,
                "matched": True,
                "use_tool": tool_name,
                "description": description,
                "suggested_params": {
                    **params,
                    **({"channel_manager": channel_manager} if channel_manager else {}),
                },
                "hint": (
                    f"Call `{tool_name}` directly with the suggested_params above. "
                    "Adjust period, breakdown, or limit as needed."
                ),
            }

    # --- Nothing matched — return catalogue so LLM can choose ---
    return {
        "tool": "run_exploratory_analysis",
        "intent": intent,
        "matched": False,
        "hint": (
            "Intent did not match any routing rule. "
            "Call one of the tools below directly for precise results."
        ),
        "available_tools": [
            {"tool": t, "description": d, "example_params": p}
            for _, t, d, p in _ROUTING_TABLE
        ],
    }


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
        sf.query(f"SELECT Account.BillingCountry country, COUNT(Id) cnt FROM Opportunity WHERE {base_where} GROUP BY Account.BillingCountry ORDER BY COUNT(Id) DESC LIMIT 10"),
        sf.query(f"SELECT StageName stage, COUNT(Id) stageCount FROM Opportunity WHERE {base_where} AND IsClosed = false GROUP BY StageName"),
        sf.query(f"SELECT CloseDate FROM Opportunity WHERE {base_where} LIMIT 2000"),
    )

    by_q: dict[str, int] = {}
    for r in dates_res.get("records", []):
        if r.get("CloseDate"):
            q = _fiscal_quarter_from_date_str(r["CloseDate"])
            by_q[q] = by_q.get(q, 0) + 1

    result: dict[str, Any] = {
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
    if not dates_res.get("done", True):
        result["truncationWarning"] = (
            "Partner has >2000 opportunities — quarterly trend counts reflect only the first 2000 records "
            "returned by Salesforce. Revenue and pipeline totals (from aggregate queries) are not affected."
        )
    return result


async def generate_partner_qbr(
    sf,
    partner_name: str,
    period: str = "THIS_QUARTER",
    prior_period: str | None = None,
    channel_manager: str = DEFAULT_CHANNEL_MANAGER,
    revenue_target: float | None = None,
    top_opps_limit: int = 10,
) -> dict[str, Any]:
    """Generate a full QBR document for a partner with all relevant metrics."""
    period = _normalize_period(period)
    range_ = _get_period_range(period)

    # Auto-compute prior period (same quarter, 1 FY back)
    if prior_period is None:
        m_fl = re.match(r"^FY(\d{2})_(Q[1-4])$", range_.get("fiscal_label", ""))
        if m_fl:
            prior_period = f"FY{int(m_fl.group(1)) - 1:02d}_{m_fl.group(2)}"
    else:
        prior_period = _normalize_period(prior_period)

    safe_limit = min(max(int(top_opps_limit), 1), 20)
    today = date.today()

    # Partner condition for direct SOQL (lost-deals query)
    escaped_partner = _escape_soql(str(partner_name).strip())
    partner_cond = f"Partner__r.Name LIKE '%{escaped_partner}%'"
    where_review = _build_opp_where(
        closed_mode=None, range_=range_, channel_manager=channel_manager,
        extra_conditions=[partner_cond],
    )

    results = await asyncio.gather(
        # 0: review period detail (revenue, win rate, won count)
        get_partner_detail(sf, partner_name, period, channel_manager=channel_manager),
        # 1: time to close
        get_time_to_close_stats(sf, period, "total", channel_manager=channel_manager),
        # 2: deal registrations
        get_deal_registrations_breakdown(sf, period, "total", channel_manager=channel_manager),
        # 3: revenue by country
        get_revenue(sf, period, "country", channel_manager=channel_manager, partner_name=partner_name),
        # 4: open pipeline total
        get_pipeline(sf, "THIS_FISCAL_YEAR", "total", channel_manager=channel_manager, partner_name=partner_name),
        # 5: open pipeline by stage
        get_pipeline(sf, "THIS_FISCAL_YEAR", "stage", channel_manager=channel_manager, partner_name=partner_name),
        # 6: open pipeline by country
        get_pipeline(sf, "THIS_FISCAL_YEAR", "country", channel_manager=channel_manager, partner_name=partner_name),
        # 7: top open opportunities
        get_opportunity_list(sf, partner_name=partner_name, period="THIS_FISCAL_YEAR", limit=safe_limit, channel_manager=channel_manager),
        # 8: next quarter pipeline
        get_pipeline(sf, "NEXT_QUARTER", "total", channel_manager=channel_manager, partner_name=partner_name),
        # 9: lost deal count for review period
        sf.query(f"SELECT COUNT(Id) lostCount FROM Opportunity WHERE {where_review} AND IsClosed = true AND IsWon = false"),
        # 10: prior period revenue (or noop)
        get_revenue(sf, prior_period, "total", channel_manager=channel_manager, partner_name=partner_name) if prior_period else asyncio.sleep(0),
        return_exceptions=True,
    )

    def _safe(val, default=None):
        return default if isinstance(val, Exception) or val is None else val

    review          = _safe(results[0], {})
    ttc_result      = _safe(results[1], {})
    deal_regs_res   = _safe(results[2], {})
    rev_ctry_res    = _safe(results[3], {})
    pipe_total_res  = _safe(results[4], {})
    pipe_stage_res  = _safe(results[5], {})
    pipe_ctry_res   = _safe(results[6], {})
    opps_res        = _safe(results[7], {})
    next_q_res      = _safe(results[8], {})
    lost_res        = _safe(results[9])
    prior_rev_res   = _safe(results[10], {})

    # --- Business Performance ---
    review_data = review.get("data", {})
    revenue     = review_data.get("revenue", 0) or 0
    won_count   = int(review_data.get("closedWonCount", 0) or 0)
    win_rate    = (review_data.get("winRate", 0) or 0) * 100
    avg_deal    = (revenue / won_count) if won_count > 0 else 0

    lost_count = 0
    if isinstance(lost_res, dict):
        lost_count = int(_num((lost_res.get("records") or [{}])[0], "lostCount", "expr0"))

    ttc_list    = ttc_result.get("data", [])
    avg_days    = ttc_list[0].get("avgDays") if ttc_list else None

    deal_reg_count = (deal_regs_res.get("data") or {}).get("total_count", 0)

    prior_revenue = 0.0
    if isinstance(prior_rev_res.get("data"), dict):
        prior_revenue = prior_rev_res["data"].get("totalRevenue", 0) or 0

    growth_pct = ((revenue - prior_revenue) / prior_revenue * 100) if prior_revenue > 0 else None
    attainment = (revenue / float(revenue_target) * 100) if revenue_target and float(revenue_target) > 0 else None

    # --- Pipeline Health ---
    pipe_total  = (pipe_total_res.get("data") or {})
    open_pipe   = pipe_total.get("totalPipeline", 0) or 0
    open_deals  = int(pipe_total.get("dealCount", 0) or 0)
    pipe_stages = pipe_stage_res.get("data") or []
    top_opps    = opps_res.get("data") or []
    coverage    = (open_pipe / float(revenue_target) * 100) if revenue_target and float(revenue_target) > 0 else None

    # --- Geography ---
    rev_by_ctry  = rev_ctry_res.get("data") or []
    pipe_by_ctry = pipe_ctry_res.get("data") or []

    # --- Forward Looking ---
    next_q       = (next_q_res.get("data") or {})
    nq_pipeline  = next_q.get("totalPipeline", 0) or 0
    nq_deals     = int(next_q.get("dealCount", 0) or 0)

    sixty_days = today + timedelta(days=60)
    closing_soon = [
        o for o in top_opps
        if o.get("closeDate") and o["closeDate"][:10] <= sixty_days.isoformat()
    ]
    closing_value = sum(o.get("amount", 0) or 0 for o in closing_soon)

    # --- Period labels ---
    period_summary = _summarize_period(period)
    fiscal_label   = period_summary.get("fiscalLabel", period)
    start_str      = period_summary.get("startDate", "")
    end_str        = period_summary.get("endDate", "")
    prior_label    = prior_period or "N/A"

    def _fmt(d: str) -> str:
        try:
            return date.fromisoformat(d).strftime("%b %Y")
        except Exception:
            return d

    period_display = f"{fiscal_label} ({_fmt(start_str)} – {_fmt(end_str)})"

    # --- Markdown report ---
    def _m(v: float) -> str:
        return f"{int(v):,}"

    def _p(v: float) -> str:
        return f"{v:.1f}%"

    md: list[str] = [
        f"# QBR: {partner_name}",
        f"**Period:** {period_display}",
        f"**Prepared:** {today.isoformat()}",
        "",
        "---",
        "## Business Performance",
        "",
        "### Revenue",
        f"- Closed-Won: {_m(revenue)}",
    ]

    if growth_pct is not None:
        sign = "+" if growth_pct >= 0 else ""
        md.append(f"- vs {prior_label}: {sign}{_p(growth_pct)} ({_m(prior_revenue)} → {_m(revenue)})")

    if attainment is not None:
        md.append(f"- Attainment: {_p(attainment)} of {_m(float(revenue_target))} target")

    md += [
        "",
        "### Deals",
        f"- Won: {won_count} | Lost: {lost_count} | Win Rate: {_p(win_rate)}",
        f"- Avg Deal Size: {_m(avg_deal)}",
    ]
    if avg_days is not None:
        md.append(f"- Avg Time to Close: {avg_days:.0f} days")
    md.append(f"- Deal Registrations: {deal_reg_count}")

    md += [
        "",
        "---",
        "## Pipeline Health",
        f"- Open Pipeline: {_m(open_pipe)} ({open_deals} deals)",
    ]
    if coverage is not None:
        md.append(f"- Pipeline Coverage: {_p(coverage)} of target")

    if pipe_stages:
        parts = [f"{s.get('stage', '?')} {_m(s.get('totalPipeline', 0) or 0)}" for s in pipe_stages[:6]]
        md.append(f"- By Stage: {' | '.join(parts)}")

    if top_opps:
        md += [
            "",
            "### Top Open Opportunities",
            "| Opportunity | Amount | Stage | Close Date |",
            "|-------------|--------|-------|------------|",
        ]
        for o in top_opps[:safe_limit]:
            name  = (o.get("name") or "-")[:45]
            amt   = _m(o.get("amount", 0) or 0)
            stage = (o.get("stage") or "-")[:20]
            cd    = o.get("closeDate", "-") or "-"
            md.append(f"| {name} | {amt} | {stage} | {cd} |")

    if rev_by_ctry or pipe_by_ctry:
        md += [
            "",
            "---",
            "## Geography",
            "| Country | Revenue | Pipeline |",
            "|---------|---------|----------|",
        ]
        ctry_rev  = {r.get("country", "Unknown"): r.get("totalRevenue", 0) or 0 for r in rev_by_ctry}
        ctry_pipe = {r.get("country", "Unknown"): r.get("totalPipeline", 0) or 0 for r in pipe_by_ctry}
        all_ctry  = sorted(
            set(list(ctry_rev) + list(ctry_pipe)),
            key=lambda c: (ctry_rev.get(c, 0) or 0) + (ctry_pipe.get(c, 0) or 0),
            reverse=True,
        )
        for c in all_ctry[:6]:
            md.append(f"| {c} | {_m(ctry_rev.get(c, 0) or 0)} | {_m(ctry_pipe.get(c, 0) or 0)} |")

    md += [
        "",
        "---",
        "## Forward Looking",
        f"- Next Quarter Pipeline: {_m(nq_pipeline)} ({nq_deals} deals)",
    ]
    if closing_soon:
        md.append(f"- Closing in 60 days: {len(closing_soon)} deals, {_m(closing_value)}")

    return {
        "tool": "generate_partner_qbr",
        "partner": partner_name,
        "period": period_summary,
        "priorPeriod": prior_label,
        "channelManager": channel_manager or None,
        "revenueTarget": float(revenue_target) if revenue_target is not None else None,
        "sections": {
            "businessPerformance": {
                "revenue": revenue,
                "priorRevenue": prior_revenue,
                "growthPct": round(growth_pct, 1) if growth_pct is not None else None,
                "wonDeals": won_count,
                "lostDeals": lost_count,
                "winRate": round(win_rate, 1),
                "avgDealSize": round(avg_deal),
                "avgDaysToClose": avg_days,
                "dealRegistrations": deal_reg_count,
                "attainmentPct": round(attainment, 1) if attainment is not None else None,
            },
            "pipelineHealth": {
                "openPipeline": open_pipe,
                "openDealCount": open_deals,
                "coveragePct": round(coverage, 1) if coverage is not None else None,
                "byStage": pipe_stages,
                "topOpportunities": top_opps,
            },
            "geography": {
                "revenueByCountry": rev_by_ctry,
                "pipelineByCountry": pipe_by_ctry,
            },
            "forwardLooking": {
                "nextQuarterPipeline": nq_pipeline,
                "nextQuarterDeals": nq_deals,
                "closingIn60Days": [
                    {"name": o.get("name"), "amount": o.get("amount"), "closeDate": o.get("closeDate")}
                    for o in closing_soon
                ],
            },
        },
        "markdown_report": "\n".join(md),
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
            {"name": "generate_partner_qbr", "purpose": "Full QBR document for a partner (markdown report)", "keyParams": ["partner_name", "period", "revenue_target"]},
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
            series_map.setdefault("Total", {"label": "Total"})
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
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """Deal registration breakdown: by partner, country, or status.

    Tracks registrations on Opportunity via Partner_Registration_Approval__c field.
    Returns counts + amounts + conversion rates by breakdown dimension.
    Note: Uses CreatedDate for period filtering (Partner_Opportunity_Registration_Date__c may have data integrity issues).
    """
    period = _normalize_period(period)
    _assert_enum(period, PERIODS, "period")
    range_ = _get_period_range(period)
    safe_limit = _clamp_limit(limit, 10, 100)
    breakdown = breakdown if breakdown in ["total", "partner", "country", "status"] else "total"

    where_conditions = [
        f"Account.BillingCountry IN {COUNTRIES_SQL}",
        f"Partner_Registration_Approval__c != null",
        f"CreatedDate >= {range_['start'].isoformat()}T00:00:00Z",
        f"CreatedDate <= {range_['end'].isoformat()}T23:59:59Z",
    ]
    if channel_manager:
        where_conditions.append(f"Channel_Manager__c = '{_escape_soql(channel_manager)}'")

    base_where = " AND ".join(where_conditions)

    # Run conversion stats queries in parallel
    total_res, approved_res, approved_won_res, trackable_res = await asyncio.gather(
        sf.query(f"SELECT COUNT(Id) cnt_total, SUM(Amount) amt_total FROM Opportunity WHERE {base_where}"),
        sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE {base_where} AND Partner_Registration_Approval__c = 'Approved'"),
        sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE {base_where} AND Partner_Registration_Approval__c = 'Approved' AND IsWon = true"),
        sf.query(f"SELECT COUNT(Id) cnt FROM Opportunity WHERE {base_where} AND Partner_Registration_Approval__c IN ('Submitted', 'In Review', 'Approved', 'Rejected')"),
    )

    total_count = _num(total_res.get("records", [{}])[0], "cnt_total", "expr0")
    total_amount = _num(total_res.get("records", [{}])[0], "amt_total", "expr1")
    approved_total = _num(approved_res.get("records", [{}])[0], "cnt", "expr0")
    approved_won = _num(approved_won_res.get("records", [{}])[0], "cnt", "expr0")
    trackable_total = _num(trackable_res.get("records", [{}])[0], "cnt", "expr0")

    approval_rate = (approved_total / trackable_total * 100) if trackable_total > 0 else 0
    close_rate = (approved_won / approved_total * 100) if approved_total > 0 else 0

    # Query 3: Breakdown
    breakdown_data = []

    if breakdown == "partner":
        pres = await sf.query(
            f"SELECT Partner__r.Name partnerName, COUNT(Id) cnt_dr, SUM(Amount) amt_dr "
            f"FROM Opportunity WHERE {base_where} GROUP BY Partner__r.Name ORDER BY COUNT(Id) DESC LIMIT {safe_limit}"
        )
        breakdown_data = [
            {
                "label": r.get("partnerName") or "Unknown",
                "count": _num(r, "cnt_dr", "expr0"),
                "amount": _num(r, "amt_dr", "expr1"),
            }
            for r in pres.get("records", [])
        ]

    elif breakdown == "country":
        cres = await sf.query(
            f"SELECT Account.BillingCountry country, COUNT(Id) cnt_dr, SUM(Amount) amt_dr "
            f"FROM Opportunity WHERE {base_where} GROUP BY Account.BillingCountry ORDER BY COUNT(Id) DESC LIMIT {safe_limit}"
        )
        breakdown_data = [
            {
                "label": r.get("country") or "Unknown",
                "count": _num(r, "cnt_dr", "expr0"),
                "amount": _num(r, "amt_dr", "expr1"),
            }
            for r in cres.get("records", [])
        ]

    elif breakdown == "status":
        sres = await sf.query(
            f"SELECT Partner_Registration_Approval__c, COUNT(Id) cnt_dr, SUM(Amount) amt_dr "
            f"FROM Opportunity WHERE {base_where} GROUP BY Partner_Registration_Approval__c ORDER BY COUNT(Id) DESC"
        )
        breakdown_data = [
            {
                "label": r.get("Partner_Registration_Approval__c") or "Unknown",
                "count": _num(r, "cnt_dr", "expr0"),
                "amount": _num(r, "amt_dr", "expr1"),
            }
            for r in sres.get("records", [])
        ]

    return {
        "tool": "get_deal_registrations_breakdown",
        "period": _summarize_period(period),
        "breakdown": breakdown,
        "channel_manager": channel_manager or None,
        "data": {
            "total_count": total_count,
            "total_amount": round(total_amount, 0),
            "approval_rate_pct": round(approval_rate, 1),
            "close_rate_pct": round(close_rate, 1),
            "breakdown": breakdown_data,
        },
    }


async def get_deal_registrations_trend(
    sf,
    periods: list[str] | None = None,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """Deal registration trend across multiple fiscal quarters.

    Shows count, amount, approval rate, and close rate per quarter side-by-side.
    Defaults to Q1, Q2, Q3, Q4 of current fiscal year.
    """
    if not periods:
        periods = ["Q1", "Q2", "Q3", "Q4"]

    normalized = [_normalize_period(p) for p in periods]
    for p in normalized:
        _assert_enum(p, PERIODS, "period")

    results = await asyncio.gather(*[
        get_deal_registrations(sf, p, channel_manager=channel_manager)
        for p in normalized
    ])

    trend = []
    for res in results:
        period_info = res.get("period", {})
        d = res.get("data", {})
        trend.append({
            "quarter": period_info.get("fiscalLabel", period_info.get("label", "")),
            "period_label": f"{period_info.get('startDate', '')} – {period_info.get('endDate', '')}",
            "total_count": d.get("total_count", 0),
            "total_amount": d.get("total_amount", 0),
            "approval_rate_pct": d.get("approval_rate_pct", 0),
            "close_rate_pct": d.get("close_rate_pct", 0),
        })

    return {
        "tool": "get_deal_registrations_trend",
        "periods": [res.get("period") for res in results],
        "channel_manager": channel_manager or None,
        "data": trend,
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


# ---------------------------------------------------------------------------
# PHASE 1 TOOLS: Activity, Risk, Lost Deals, Stage Velocity
# ---------------------------------------------------------------------------

async def get_stalled_deals(
    sf,
    period: str = "THIS_QUARTER",
    days_threshold: int = 60,
    stage_filter: str | None = None,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Find deals that haven't been modified in X days (stalled/at-risk).

    Returns: Opportunity list grouped by stage, showing age and last modified date.
    """
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)

    res = await sf.query(
        f"SELECT Id, Name, Amount, StageName, Probability, CloseDate, "
        f"LastModifiedDate, Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {base_where} ORDER BY LastModifiedDate ASC LIMIT 2000"
    )

    records = res.get("records", [])
    today = date.today()
    stalled = []

    for r in records:
        stage = r.get("StageName", "Unknown")
        if stage_filter and stage != stage_filter:
            continue

        lmd = r.get("LastModifiedDate", "")[:10]
        if not lmd:
            continue

        try:
            last_mod_date = date.fromisoformat(lmd)
            days_since = (today - last_mod_date).days
        except ValueError:
            continue

        if days_since >= days_threshold:
            stalled.append({
                "id": r.get("Id"),
                "name": r.get("Name"),
                "amount": r.get("Amount"),
                "stage": stage,
                "probability": r.get("Probability"),
                "closeDate": r.get("CloseDate"),
                "lastModifiedDate": lmd,
                "daysSinceModified": days_since,
                "country": (r.get("Account") or {}).get("BillingCountry"),
                "partner": (r.get("Partner__r") or {}).get("Name"),
            })

    stalled.sort(key=lambda x: x["daysSinceModified"], reverse=True)

    stage_breakdown = {}
    for s in stalled:
        stage = s["stage"]
        stage_breakdown.setdefault(stage, []).append(s)

    return {
        "tool": "get_stalled_deals",
        "period": _summarize_period(period),
        "threshold_days": days_threshold,
        "stage_filter": stage_filter,
        "total_stalled": len(stalled),
        "by_stage": {k: {"count": len(v), "deals": v} for k, v in stage_breakdown.items()},
        "all_deals": stalled,
    }


async def get_partner_activity_summary(
    sf,
    period: str = "THIS_QUARTER",
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Partner activity summary: open pipeline, deal count, last deal modification.

    Proxy for engagement level using LastModifiedDate of most recent opportunity.
    """
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)

    res = await sf.query(
        f"SELECT Amount, StageName, LastModifiedDate, Partner__r.Name "
        f"FROM Opportunity WHERE {base_where} ORDER BY LastModifiedDate DESC LIMIT 2000"
    )

    records = res.get("records", [])
    today = date.today()
    partner_map: dict[str, dict] = {}

    for r in records:
        partner = (r.get("Partner__r") or {}).get("Name") or "Orphan"
        amount = r.get("Amount", 0)

        if partner not in partner_map:
            partner_map[partner] = {
                "partner": partner,
                "open_pipeline_amount": 0,
                "deal_count": 0,
                "last_deal_modified_date": None,
                "days_since_last_activity": None,
                "deals_modified_this_week": 0,
                "deals_modified_this_month": 0,
            }

        partner_map[partner]["open_pipeline_amount"] += amount
        partner_map[partner]["deal_count"] += 1

        lmd = r.get("LastModifiedDate", "")[:10]
        if lmd:
            try:
                last_mod_date = date.fromisoformat(lmd)
                days = (today - last_mod_date).days

                if partner_map[partner]["last_deal_modified_date"] is None:
                    partner_map[partner]["last_deal_modified_date"] = lmd
                    partner_map[partner]["days_since_last_activity"] = days

                if days <= 7:
                    partner_map[partner]["deals_modified_this_week"] += 1
                if days <= 30:
                    partner_map[partner]["deals_modified_this_month"] += 1
            except ValueError:
                pass

    data = list(partner_map.values())
    data.sort(key=lambda x: x["days_since_last_activity"] or 999)

    return {
        "tool": "get_partner_activity_summary",
        "period": _summarize_period(period),
        "total_partners": len(data),
        "data": data,
    }


async def get_opportunity_recency(
    sf,
    opportunity_id_or_name: str,
) -> dict[str, Any]:
    """
    Get full details of an opportunity including recency/modification tracking.

    Shows when the deal was last modified and how many days it's been idle.
    """
    where = f"Id = '{opportunity_id_or_name}' OR Name LIKE '%{opportunity_id_or_name}%'"

    res = await sf.query(
        f"SELECT Id, Name, Amount, StageName, Probability, CloseDate, "
        f"CreatedDate, LastModifiedDate, Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {where} LIMIT 10"
    )

    records = res.get("records", [])
    if not records:
        return {"tool": "get_opportunity_recency", "error": "Opportunity not found"}

    r = records[0]
    today = date.today()

    lmd = r.get("LastModifiedDate", "")[:10]
    cd = r.get("CreatedDate", "")[:10]
    days_since_modified = None
    days_in_stage = None

    if lmd:
        try:
            last_mod_date = date.fromisoformat(lmd)
            days_since_modified = (today - last_mod_date).days
        except ValueError:
            pass

    if cd:
        try:
            created_date = date.fromisoformat(cd)
            days_in_stage = (today - created_date).days
        except ValueError:
            pass

    return {
        "tool": "get_opportunity_recency",
        "opportunity": {
            "id": r.get("Id"),
            "name": r.get("Name"),
            "amount": r.get("Amount"),
            "stage": r.get("StageName"),
            "probability": r.get("Probability"),
            "closeDate": r.get("CloseDate"),
            "createdDate": cd,
            "lastModifiedDate": lmd,
            "daysSinceModified": days_since_modified,
            "daysInStage": days_in_stage,
            "country": (r.get("Account") or {}).get("BillingCountry"),
            "partner": (r.get("Partner__r") or {}).get("Name"),
        },
    }


async def get_lost_deals(
    sf,
    period: str = "THIS_QUARTER",
    group_by: str | None = None,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Analyze lost deals: count, amount, by stage/partner/country.

    Grouping: None (total), 'stage', 'partner', 'country'
    """
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode="lost", range_=range_, channel_manager=channel_manager)

    res = await sf.query(
        f"SELECT Amount, StageName, Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {base_where} LIMIT 2000"
    )

    lost_records = res.get("records", [])

    # Also get won deals for calculating loss rate
    won_where = _build_opp_where(closed_mode="won", range_=range_, channel_manager=channel_manager)
    won_res = await sf.query(
        f"SELECT Amount FROM Opportunity WHERE {won_where} LIMIT 2000"
    )
    won_records = won_res.get("records", [])

    total_lost = len(lost_records)
    total_won = len(won_records)
    total_deals = total_lost + total_won
    loss_rate_pct = (total_lost / total_deals * 100) if total_deals > 0 else 0

    if not group_by:
        total_lost_amount = sum(r.get("Amount", 0) for r in lost_records)
        avg_deal_size = (total_lost_amount / total_lost) if total_lost > 0 else 0

        return {
            "tool": "get_lost_deals",
            "period": _summarize_period(period),
            "group_by": None,
            "total_lost_count": total_lost,
            "total_lost_amount": total_lost_amount,
            "total_won_count": total_won,
            "loss_rate_pct": round(loss_rate_pct, 1),
            "avg_deal_size_lost": round(avg_deal_size, 0),
        }

    group_map: dict[str, dict] = {}
    for r in lost_records:
        if group_by == "stage":
            key = r.get("StageName", "Unknown")
        elif group_by == "partner":
            key = (r.get("Partner__r") or {}).get("Name") or "Orphan"
        elif group_by == "country":
            key = (r.get("Account") or {}).get("BillingCountry") or "Unknown"
        else:
            key = "Total"

        if key not in group_map:
            group_map[key] = {"label": key, "count": 0, "amount": 0}

        group_map[key]["count"] += 1
        group_map[key]["amount"] += r.get("Amount", 0)

    data = list(group_map.values())
    for item in data:
        item["avg_deal_size"] = round(item["amount"] / item["count"], 0) if item["count"] > 0 else 0

    data.sort(key=lambda x: x["amount"], reverse=True)

    return {
        "tool": "get_lost_deals",
        "period": _summarize_period(period),
        "group_by": group_by,
        "total_lost_count": total_lost,
        "total_won_count": total_won,
        "loss_rate_pct": round(loss_rate_pct, 1),
        "by_group": data,
    }


async def get_new_vs_existing(
    sf,
    period: str = "THIS_QUARTER",
    breakdown: str | None = None,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Revenue/pipeline split by Type (New Business vs. Renewal/Expansion).

    Breakdown: None (total), 'partner', 'country', 'channel_manager'
    """
    range_ = _get_period_range(period)

    # Get closed-won
    won_where = _build_opp_where(closed_mode="won", range_=range_, channel_manager=channel_manager)
    won_res = await sf.query(
        f"SELECT Amount, Type, Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {won_where} LIMIT 2000"
    )
    won_records = won_res.get("records", [])

    # Get open pipeline
    open_where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)
    open_res = await sf.query(
        f"SELECT Amount, Type, Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {open_where} LIMIT 2000"
    )
    open_records = open_res.get("records", [])

    all_records = won_records + open_records

    if not breakdown:
        new_won = sum(r.get("Amount", 0) for r in won_records if r.get("Type") == "New Business")
        existing_won = sum(r.get("Amount", 0) for r in won_records if r.get("Type") != "New Business")
        new_pipeline = sum(r.get("Amount", 0) for r in open_records if r.get("Type") == "New Business")
        existing_pipeline = sum(r.get("Amount", 0) for r in open_records if r.get("Type") != "New Business")

        total_won = new_won + existing_won
        total_pipeline = new_pipeline + existing_pipeline

        return {
            "tool": "get_new_vs_existing",
            "period": _summarize_period(period),
            "breakdown": None,
            "closed_won": {
                "new_business": new_won,
                "existing_business": existing_won,
                "new_business_pct": round(new_won / total_won * 100, 1) if total_won > 0 else 0,
            },
            "open_pipeline": {
                "new_business": new_pipeline,
                "existing_business": existing_pipeline,
                "new_business_pct": round(new_pipeline / total_pipeline * 100, 1) if total_pipeline > 0 else 0,
            },
        }

    group_map: dict[str, dict] = {}
    for r in all_records:
        if breakdown == "partner":
            key = (r.get("Partner__r") or {}).get("Name") or "Orphan"
        elif breakdown == "country":
            key = (r.get("Account") or {}).get("BillingCountry") or "Unknown"
        else:
            key = "Total"

        if key not in group_map:
            group_map[key] = {
                "label": key,
                "new_won": 0,
                "existing_won": 0,
                "new_pipeline": 0,
                "existing_pipeline": 0,
            }

        is_new = r.get("Type") == "New Business"
        amount = r.get("Amount", 0)

        if r in won_records:
            if is_new:
                group_map[key]["new_won"] += amount
            else:
                group_map[key]["existing_won"] += amount
        else:
            if is_new:
                group_map[key]["new_pipeline"] += amount
            else:
                group_map[key]["existing_pipeline"] += amount

    for item in group_map.values():
        total_won = item["new_won"] + item["existing_won"]
        total_pipeline = item["new_pipeline"] + item["existing_pipeline"]
        item["new_won_pct"] = round(item["new_won"] / total_won * 100, 1) if total_won > 0 else 0
        item["new_pipeline_pct"] = round(item["new_pipeline"] / total_pipeline * 100, 1) if total_pipeline > 0 else 0

    data = list(group_map.values())
    data.sort(key=lambda x: x["new_won"] + x["new_pipeline"], reverse=True)

    return {
        "tool": "get_new_vs_existing",
        "period": _summarize_period(period),
        "breakdown": breakdown,
        "data": data,
    }


async def get_stage_risk_profile(
    sf,
    period: str = "THIS_QUARTER",
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Stage risk profile: for each stage, show probability distribution, count, and quality.

    High-risk stages: avg probability < 40%
    Medium-risk stages: 40-60%
    Low-risk stages: > 60%
    """
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)

    res = await sf.query(
        f"SELECT Amount, StageName, Probability "
        f"FROM Opportunity WHERE {base_where} ORDER BY StageName LIMIT 2000"
    )

    records = res.get("records", [])
    stage_map: dict[str, list] = {}

    for r in records:
        stage = r.get("StageName", "Unknown")
        stage_map.setdefault(stage, []).append(r)

    data = []
    for stage, deals in stage_map.items():
        amounts = [d.get("Amount", 0) for d in deals]
        probs = [d.get("Probability", 50) for d in deals]

        total_amount = sum(amounts)
        avg_prob = sum(probs) / len(probs) if probs else 0
        weighted_amount = sum(a * p / 100 for a, p in zip(amounts, probs))

        amounts_sorted = sorted(amounts)
        n = len(amounts_sorted)
        median_amount = amounts_sorted[n // 2] if n % 2 else (amounts_sorted[n // 2 - 1] + amounts_sorted[n // 2]) / 2

        if avg_prob > 60:
            confidence = "HIGH"
        elif avg_prob > 40:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        data.append({
            "stage": stage,
            "deal_count": len(deals),
            "total_pipeline_amount": round(total_amount, 0),
            "avg_probability_pct": round(avg_prob, 1),
            "weighted_pipeline": round(weighted_amount, 0),
            "coverage_ratio": round(weighted_amount / total_amount * 100, 1) if total_amount > 0 else 0,
            "min_amount": round(min(amounts), 0) if amounts else 0,
            "max_amount": round(max(amounts), 0) if amounts else 0,
            "median_amount": round(median_amount, 0),
            "confidence_level": confidence,
        })

    data.sort(key=lambda x: x["avg_probability_pct"], reverse=True)

    return {
        "tool": "get_stage_risk_profile",
        "period": _summarize_period(period),
        "data": data,
    }


async def get_deal_aging_by_stage(
    sf,
    period: str = "THIS_QUARTER",
    days_threshold: int = 60,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Bottleneck detection: for each stage, show how many deals are older than threshold.

    Identifies stalled deals that need intervention.
    """
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)

    res = await sf.query(
        f"SELECT Id, StageName, CreatedDate, LastModifiedDate, Amount "
        f"FROM Opportunity WHERE {base_where} ORDER BY StageName LIMIT 2000"
    )

    records = res.get("records", [])
    today = date.today()
    stage_map: dict[str, dict] = {}

    for r in records:
        stage = r.get("StageName", "Unknown")

        if stage not in stage_map:
            stage_map[stage] = {
                "stage": stage,
                "total_deals": 0,
                "deals_under_threshold": 0,
                "deals_over_threshold": 0,
                "avg_age_days": 0,
                "oldest_deal_age_days": 0,
                "ages": [],
            }

        lmd = r.get("LastModifiedDate", "")[:10]
        if not lmd:
            continue

        try:
            last_mod_date = date.fromisoformat(lmd)
            age_days = (today - last_mod_date).days
        except ValueError:
            continue

        stage_map[stage]["total_deals"] += 1
        stage_map[stage]["ages"].append(age_days)

        if age_days >= days_threshold:
            stage_map[stage]["deals_over_threshold"] += 1
        else:
            stage_map[stage]["deals_under_threshold"] += 1

        if age_days > stage_map[stage]["oldest_deal_age_days"]:
            stage_map[stage]["oldest_deal_age_days"] = age_days

    data = []
    for stage, info in stage_map.items():
        if info["ages"]:
            info["avg_age_days"] = round(sum(info["ages"]) / len(info["ages"]), 1)
        del info["ages"]
        data.append(info)

    data.sort(key=lambda x: x["deals_over_threshold"], reverse=True)

    return {
        "tool": "get_deal_aging_by_stage",
        "period": _summarize_period(period),
        "days_threshold": days_threshold,
        "data": data,
    }


async def get_high_risk_deals(
    sf,
    period: str = "THIS_QUARTER",
    probability_threshold: int = 40,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    High-risk deals: low probability + closing soon.

    Criteria: Probability < threshold AND CloseDate within 30 days.
    """
    range_ = _get_period_range(period)
    base_where = _build_opp_where(closed_mode="open", range_=range_, channel_manager=channel_manager)

    res = await sf.query(
        f"SELECT Id, Name, Amount, StageName, Probability, CloseDate, "
        f"Account.BillingCountry, Partner__r.Name "
        f"FROM Opportunity WHERE {base_where} ORDER BY CloseDate ASC LIMIT 2000"
    )

    records = res.get("records", [])
    today = date.today()
    high_risk = []

    for r in records:
        prob = r.get("Probability") or 50
        close_date_str = r.get("CloseDate", "")[:10]

        if not close_date_str or prob >= probability_threshold:
            continue

        try:
            close_date = date.fromisoformat(close_date_str)
            days_until_close = (close_date - today).days
        except ValueError:
            continue

        if days_until_close >= 0 and days_until_close <= 30:
            high_risk.append({
                "id": r.get("Id"),
                "name": r.get("Name"),
                "amount": r.get("Amount"),
                "stage": r.get("StageName"),
                "probability": prob,
                "closeDate": close_date_str,
                "daysUntilClose": days_until_close,
                "riskScore": round(100 - prob - (days_until_close * 2), 1),
                "country": (r.get("Account") or {}).get("BillingCountry"),
                "partner": (r.get("Partner__r") or {}).get("Name"),
                "recommendation": f"High-risk: {prob}% prob, closing in {days_until_close} days",
            })

    high_risk.sort(key=lambda x: x["riskScore"], reverse=True)

    return {
        "tool": "get_high_risk_deals",
        "period": _summarize_period(period),
        "probability_threshold_pct": probability_threshold,
        "total_high_risk": len(high_risk),
        "deals": high_risk,
    }


async def get_stage_progression_velocity(
    sf,
    period: str = "LAST_FISCAL_YEAR",
    lookback_periods: int = 4,
    channel_manager: str | None = None,
) -> dict[str, Any]:
    """
    Historical stage progression velocity: avg days in each stage (from closed-won deals).

    Uses past closed-won deals to infer how long deals typically spend in each stage.
    Compares current open deals against historical velocity.
    """
    # Get closed-won deals from historical period
    range_ = _get_period_range(period)
    won_where = _build_opp_where(closed_mode="won", range_=range_, channel_manager=channel_manager)

    won_res = await sf.query(
        f"SELECT CreatedDate, CloseDate, StageName, Amount "
        f"FROM Opportunity WHERE {won_where} ORDER BY CloseDate DESC LIMIT 2000"
    )

    won_records = won_res.get("records", [])

    stage_velocity: dict[str, list] = {}
    for r in won_records:
        cd = r.get("CreatedDate", "")[:10]
        cl = r.get("CloseDate", "")[:10]
        stage = r.get("StageName", "Unknown")

        if not cd or not cl:
            continue

        try:
            days = (date.fromisoformat(cl) - date.fromisoformat(cd)).days
        except ValueError:
            continue

        if days < 0:
            continue

        stage_velocity.setdefault(stage, []).append(days)

    # Get current open deals to compare
    open_range = _get_period_range("THIS_QUARTER")
    open_where = _build_opp_where(closed_mode="open", range_=open_range, channel_manager=channel_manager)

    open_res = await sf.query(
        f"SELECT CreatedDate, StageName "
        f"FROM Opportunity WHERE {open_where} LIMIT 2000"
    )

    open_records = open_res.get("records", [])
    today = date.today()
    current_stage_age: dict[str, list] = {}

    for r in open_records:
        cd = r.get("CreatedDate", "")[:10]
        stage = r.get("StageName", "Unknown")

        if not cd:
            continue

        try:
            days = (today - date.fromisoformat(cd)).days
        except ValueError:
            continue

        current_stage_age.setdefault(stage, []).append(days)

    data = []
    for stage, historical_days in stage_velocity.items():
        avg_historical = sum(historical_days) / len(historical_days) if historical_days else 0
        median_historical = sorted(historical_days)[len(historical_days) // 2] if historical_days else 0

        current_ages = current_stage_age.get(stage, [])
        avg_current = sum(current_ages) / len(current_ages) if current_ages else 0

        aged_deals = sum(1 for age in current_ages if age > avg_historical * 1.5) if avg_historical > 0 else 0

        data.append({
            "stage": stage,
            "historical_avg_days": round(avg_historical, 1),
            "historical_median_days": round(median_historical, 1),
            "deals_passed_through_stage": len(historical_days),
            "current_deals_in_stage": len(current_ages),
            "current_avg_age_days": round(avg_current, 1),
            "deals_aged_vs_historical": aged_deals,
        })

    data.sort(key=lambda x: x["historical_avg_days"], reverse=True)

    return {
        "tool": "get_stage_progression_velocity",
        "lookback_period": _summarize_period(period),
        "current_period": "THIS_QUARTER",
        "data": data,
    }
