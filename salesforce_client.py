"""Salesforce API client using httpx for async HTTP requests."""

import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx


class SalesforceError(Exception):
    """Custom exception for Salesforce API errors."""
    pass


class SalesforceClient:
    """Async Salesforce REST API client."""

    def __init__(self, base_url: str | None = None, access_token: str | None = None):
        self.base_url = base_url or os.getenv("SALESFORCE_BASE_URL")
        self.access_token = access_token or os.getenv("SALESFORCE_ACCESS_TOKEN") or os.getenv("SALESFORCE_SID")

        if not self.base_url or not self.access_token:
            raise SalesforceError(
                "Missing required environment variables: SALESFORCE_BASE_URL and "
                "SALESFORCE_ACCESS_TOKEN (or SALESFORCE_SID)"
            )

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle API error responses."""
        if response.status_code == 401:
            try:
                error_body = response.json()
                if isinstance(error_body, list):
                    for error in error_body:
                        if error.get("errorCode") == "INVALID_SESSION_ID":
                            raise SalesforceError(
                                "Salesforce access token has expired. Please refresh your bearer token."
                            )
            except (ValueError, KeyError):
                pass

        if response.status_code >= 400:
            try:
                error_body = response.json()
                if isinstance(error_body, list):
                    error_messages = [e.get("message", str(e)) for e in error_body]
                    raise SalesforceError(f"Salesforce API Error: {', '.join(error_messages)}")
                raise SalesforceError(f"Salesforce API Error: {error_body}")
            except ValueError:
                raise SalesforceError(f"Salesforce API Error: {response.text}")

    async def query(self, soql: str) -> dict[str, Any]:
        """Execute a SOQL query."""
        client = await self._get_client()
        response = await client.get("/query", params={"q": soql})
        self._handle_error(response)
        return response.json()

    async def get_sobjects(self) -> dict[str, Any]:
        """List all available Salesforce objects."""
        client = await self._get_client()
        response = await client.get("/sobjects")
        self._handle_error(response)
        return response.json()

    async def get_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch recently accessed records."""
        client = await self._get_client()
        response = await client.get("/recent", params={"limit": limit})
        self._handle_error(response)
        return response.json()

    async def search(self, sosl: str) -> dict[str, Any]:
        """Execute a SOSL search."""
        client = await self._get_client()
        response = await client.get("/search", params={"q": sosl})
        self._handle_error(response)
        return response.json()

    async def describe(self, object_name: str) -> dict[str, Any]:
        """Get detailed metadata for a Salesforce object."""
        client = await self._get_client()
        response = await client.get(f"/sobjects/{object_name}/describe")
        self._handle_error(response)
        return response.json()

    async def create_record(self, object_name: str, record_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record."""
        client = await self._get_client()
        response = await client.post(f"/sobjects/{object_name}", json=record_data)
        self._handle_error(response)
        return response.json()

    async def update_record(
        self, object_name: str, record_id: str, record_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing record."""
        client = await self._get_client()
        response = await client.patch(f"/sobjects/{object_name}/{record_id}", json=record_data)
        self._handle_error(response)
        return {"success": True, "id": record_id}

    async def delete_record(self, object_name: str, record_id: str) -> dict[str, Any]:
        """Delete a record."""
        client = await self._get_client()
        response = await client.delete(f"/sobjects/{object_name}/{record_id}")
        self._handle_error(response)
        return {"success": True, "id": record_id}

    async def get_related_records(
        self,
        object_name: str,
        record_id: str,
        relationship_name: str | None = None,
    ) -> dict[str, Any]:
        """Get related records for a Salesforce record."""
        client = await self._get_client()

        if relationship_name:
            # Query specific relationship
            query = f"SELECT Id, Name FROM {object_name} WHERE Id = '{record_id}'"
            response = await client.get(f"/query?q={quote(query)}")
            self._handle_error(response)
            data = response.json()

            if not data.get("records"):
                raise SalesforceError(f"Record {record_id} not found in {object_name}")

            # Get related records via SOQL
            related_query = (
                f"SELECT Id, Name FROM {relationship_name} "
                f"WHERE {object_name}Id = '{record_id}' LIMIT 100"
            )
            related_response = await client.get(f"/query?q={quote(related_query)}")
            self._handle_error(related_response)
            return related_response.json()

        # Get object description to find all relationships
        describe_data = await self.describe(object_name)
        relationships = describe_data.get("childRelationships", [])

        related_data: dict[str, list] = {}
        for rel in relationships[:5]:  # Limit to first 5 relationships
            try:
                rel_query = (
                    f"SELECT Id, Name FROM {rel['childSObject']} "
                    f"WHERE {rel['field']} = '{record_id}' LIMIT 10"
                )
                rel_response = await client.get(f"/query?q={quote(rel_query)}")
                if rel_response.status_code == 200:
                    rel_data = rel_response.json()
                    rel_name = rel.get("relationshipName") or rel["childSObject"]
                    related_data[rel_name] = rel_data.get("records", [])
            except Exception:
                # Skip relationships that fail (permissions, etc.)
                continue

        return {"relationships": related_data}

    async def lookup_records(
        self,
        object_name: str,
        search_term: str,
        search_fields: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search for records by name, email, or other fields."""
        client = await self._get_client()
        search_fields = search_fields or ["Name"]
        fields_to_search = ", ".join(search_fields)

        # Try SOSL search first
        sosl_query = (
            f"FIND {{{search_term}*}} IN ALL FIELDS "
            f"RETURNING {object_name}(Id, {fields_to_search}) LIMIT {limit}"
        )

        try:
            response = await client.get(f"/search?q={quote(sosl_query)}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass

        # Fallback to SOQL if SOSL fails
        where_clause = " OR ".join(
            [f"{field} LIKE '%{search_term}%'" for field in search_fields]
        )
        soql_query = (
            f"SELECT Id, {fields_to_search} FROM {object_name} "
            f"WHERE {where_clause} LIMIT {limit}"
        )

        response = await client.get(f"/query?q={quote(soql_query)}")
        self._handle_error(response)
        return response.json()

    async def get_hierarchy(
        self,
        object_name: str,
        record_id: str,
        direction: str = "down",
    ) -> dict[str, Any]:
        """Navigate parent-child relationships."""
        client = await self._get_client()
        describe_data = await self.describe(object_name)

        if direction == "up":
            # Find parent relationships
            parent_fields = [
                field for field in describe_data.get("fields", [])
                if field.get("type") == "reference"
                and field.get("name", "").endswith("Id")
                and field.get("name") != "Id"
            ][:3]  # Limit to first 3

            if not parent_fields:
                return {"message": "No parent relationships found", "parents": []}

            field_names = ", ".join(f["name"] for f in parent_fields)
            query = f"SELECT Id, {field_names} FROM {object_name} WHERE Id = '{record_id}'"
            response = await client.get(f"/query?q={quote(query)}")
            self._handle_error(response)
            data = response.json()

            return {
                "record": data.get("records", [{}])[0] if data.get("records") else {},
                "parentFields": parent_fields,
            }

        # Direction is "down" - find child relationships
        child_rels = [
            rel for rel in describe_data.get("childRelationships", [])
            if rel.get("field") and (
                "Parent" in rel.get("field", "") or rel.get("relationshipName")
            )
        ][:3]

        children: dict[str, list] = {}
        for rel in child_rels:
            try:
                child_query = (
                    f"SELECT Id, Name FROM {rel['childSObject']} "
                    f"WHERE {rel['field']} = '{record_id}' LIMIT 5"
                )
                child_response = await client.get(f"/query?q={quote(child_query)}")
                if child_response.status_code == 200:
                    child_data = child_response.json()
                    rel_name = rel.get("relationshipName") or rel["childSObject"]
                    children[rel_name] = child_data.get("records", [])
            except Exception:
                continue

        return {"children": children}

    async def get_aggregated_data(
        self,
        object_name: str,
        aggregates: list[dict[str, Any]],
        group_by: str | None = None,
        where_clause: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get statistical analysis of Salesforce data."""
        client = await self._get_client()

        # Build aggregation functions
        aggregate_fields = []
        for agg in aggregates:
            func = agg.get("function", "COUNT").upper()
            field = agg.get("field", "Id")
            alias = agg.get("alias", f"{func}_{field}")

            if func == "COUNT" and field == "Id":
                aggregate_fields.append("COUNT(Id)")
            else:
                aggregate_fields.append(f"{func}({field}) {alias}")

        aggregate_str = ", ".join(aggregate_fields)

        # Build SELECT clause
        select_fields = f"{group_by}, {aggregate_str}" if group_by else aggregate_str

        # Build WHERE clause
        where_filter = f" WHERE {where_clause}" if where_clause else ""

        # Build GROUP BY statement
        group_by_stmt = f" GROUP BY {group_by}" if group_by else ""

        # Build complete query
        query = f"SELECT {select_fields} FROM {object_name}{where_filter}{group_by_stmt} LIMIT {limit}"

        response = await client.get(f"/query?q={quote(query)}")
        self._handle_error(response)

        return {
            "query": query,
            "aggregates": aggregates,
            "groupBy": group_by,
            "results": response.json(),
        }

    async def get_report_data(
        self,
        report_id: str | None = None,
        report_name: str | None = None,
    ) -> dict[str, Any]:
        """Access and run existing Salesforce reports."""
        client = await self._get_client()
        target_report_id = report_id

        # If reportName provided, find the report ID
        if report_name and not report_id:
            report_query = (
                f"SELECT Id, Name, DeveloperName FROM Report "
                f"WHERE Name LIKE '%{report_name}%' OR DeveloperName LIKE '%{report_name}%' LIMIT 10"
            )
            response = await client.get(f"/query?q={quote(report_query)}")
            self._handle_error(response)
            data = response.json()

            if not data.get("records"):
                raise SalesforceError(f"No reports found matching: {report_name}")

            if len(data["records"]) > 1:
                return {
                    "message": "Multiple reports found. Please specify reportId or be more specific.",
                    "availableReports": [
                        {
                            "id": r["Id"],
                            "name": r["Name"],
                            "developerName": r.get("DeveloperName"),
                        }
                        for r in data["records"]
                    ],
                }

            target_report_id = data["records"][0]["Id"]

        if not target_report_id:
            # List available reports
            reports_query = (
                "SELECT Id, Name, DeveloperName, LastRunDate FROM Report "
                "WHERE LastRunDate != null ORDER BY LastRunDate DESC LIMIT 20"
            )
            response = await client.get(f"/query?q={quote(reports_query)}")
            self._handle_error(response)

            return {
                "message": "Available reports in your org:",
                "reports": response.json().get("records", []),
            }

        # Try to get report via analytics API
        try:
            report_response = await client.get(f"/analytics/reports/{target_report_id}")
            if report_response.status_code == 200:
                return {
                    "reportId": target_report_id,
                    "metadata": report_response.json(),
                }
        except Exception:
            pass

        # Fallback to report record info
        report_query = (
            f"SELECT Id, Name, DeveloperName, Description, LastRunDate "
            f"FROM Report WHERE Id = '{target_report_id}'"
        )
        response = await client.get(f"/query?q={quote(report_query)}")
        self._handle_error(response)
        records = response.json().get("records", [])

        return {
            "message": "Report found but analytics API access may be limited",
            "report": records[0] if records else None,
        }

    async def get_trend_analysis(
        self,
        object_name: str,
        date_field: str = "CreatedDate",
        period: str = "month",
        metrics: list[dict[str, Any]] | None = None,
        timeframe: int = 6,
    ) -> dict[str, Any]:
        """Analyze trends over time for Salesforce data."""
        client = await self._get_client()

        # Calculate date range
        now = datetime.now()
        if period == "month":
            start_date = now - timedelta(days=timeframe * 30)
        elif period == "week":
            start_date = now - timedelta(weeks=timeframe)
        else:  # day
            start_date = now - timedelta(days=timeframe)

        start_date_str = start_date.strftime("%Y-%m-%d")

        # Build date grouping function
        if period == "month":
            date_grouping = f"CALENDAR_YEAR({date_field}), CALENDAR_MONTH({date_field})"
        elif period == "week":
            date_grouping = f"CALENDAR_YEAR({date_field}), WEEK_IN_YEAR({date_field})"
        else:
            date_grouping = f"CALENDAR_YEAR({date_field}), DAY_IN_MONTH({date_field})"

        # Build metrics
        default_metrics = metrics if metrics else [{"function": "COUNT", "field": "Id", "alias": "Total"}]
        metrics_fields = []
        for metric in default_metrics:
            func = metric.get("function", "COUNT").upper()
            field = metric.get("field", "Id")
            alias = metric.get("alias", f"{func}_{field}")
            metrics_fields.append(f"{func}({field}) {alias}")

        metrics_str = ", ".join(metrics_fields)

        # Build query
        query = (
            f"SELECT {date_grouping}, {metrics_str} FROM {object_name} "
            f"WHERE {date_field} >= {start_date_str} "
            f"GROUP BY {date_grouping} ORDER BY {date_grouping} DESC LIMIT 50"
        )

        response = await client.get(f"/query?q={quote(query)}")
        self._handle_error(response)

        return {
            "query": query,
            "period": period,
            "timeframe": timeframe,
            "dateField": date_field,
            "metrics": default_metrics,
            "trends": response.json().get("records", []),
        }

    async def get_pipeline_analysis(
        self,
        timeframe: str = "THIS_QUARTER",
        owner_id: str | None = None,
        include_forecasting: bool = False,
    ) -> dict[str, Any]:
        """Comprehensive sales pipeline analysis."""
        client = await self._get_client()
        owner_filter = f" AND OwnerId = '{owner_id}'" if owner_id else ""

        # Current pipeline overview
        pipeline_query = f"""
            SELECT StageName, COUNT(Id) RecordCount, SUM(Amount) TotalValue, AVG(Amount) AvgDealSize,
                   AVG(Probability) AvgProbability
            FROM Opportunity
            WHERE CloseDate >= {timeframe} AND IsClosed = false{owner_filter}
            GROUP BY StageName
            ORDER BY SUM(Amount) DESC
        """.strip()

        # Win/Loss analysis
        win_loss_query = f"""
            SELECT IsWon, COUNT(Id) Count, SUM(Amount) Value
            FROM Opportunity
            WHERE CloseDate = {timeframe} AND IsClosed = true{owner_filter}
            GROUP BY IsWon
        """.strip()

        # Stage conversion rates
        conversion_query = f"""
            SELECT StageName, COUNT(Id) OppsInStage
            FROM Opportunity
            WHERE CloseDate >= {timeframe}{owner_filter}
            GROUP BY StageName
        """.strip()

        # Execute queries
        pipeline_response = await client.get(f"/query?q={quote(pipeline_query)}")
        self._handle_error(pipeline_response)
        pipeline_data = pipeline_response.json()

        win_loss_response = await client.get(f"/query?q={quote(win_loss_query)}")
        self._handle_error(win_loss_response)
        win_loss_data = win_loss_response.json()

        conversion_response = await client.get(f"/query?q={quote(conversion_query)}")
        self._handle_error(conversion_response)
        conversion_data = conversion_response.json()

        # Optional forecasting data
        forecast_data = None
        if include_forecasting:
            try:
                forecast_query = f"""
                    SELECT SUM(Amount) WeightedValue, SUM(Amount * Probability / 100) ForecastAmount
                    FROM Opportunity
                    WHERE CloseDate = {timeframe} AND IsClosed = false{owner_filter}
                """.strip()
                forecast_response = await client.get(f"/query?q={quote(forecast_query)}")
                if forecast_response.status_code == 200:
                    forecast_records = forecast_response.json().get("records", [])
                    forecast_data = forecast_records[0] if forecast_records else None
            except Exception:
                forecast_data = {"error": "Forecasting data not available"}

        pipeline_records = pipeline_data.get("records", [])
        return {
            "timeframe": timeframe,
            "ownerId": owner_id,
            "summary": {
                "totalPipelineValue": sum(
                    stage.get("TotalValue") or 0 for stage in pipeline_records
                ),
                "totalOpportunities": sum(
                    stage.get("RecordCount") or 0 for stage in pipeline_records
                ),
                "stageBreakdown": pipeline_records,
            },
            "winLossAnalysis": win_loss_data.get("records", []),
            "conversionRates": conversion_data.get("records", []),
            "forecasting": forecast_data,
        }

    async def get_case_insights(
        self,
        timeframe: str = "THIS_MONTH",
        priority: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Support case analysis including volume, resolution times, and escalations."""
        client = await self._get_client()

        # Build filters
        filters = f"CreatedDate = {timeframe}"
        if priority:
            filters += f" AND Priority = '{priority}'"
        if status:
            filters += f" AND Status = '{status}'"

        # Case volume and resolution metrics
        volume_query = f"""
            SELECT Status, Priority, COUNT(Id) CaseCount
            FROM Case
            WHERE {filters}
            GROUP BY Status, Priority
            ORDER BY Priority, Status
        """.strip()

        # Escalation analysis
        escalation_query = f"""
            SELECT COUNT(Id) TotalCases
            FROM Case
            WHERE {filters}
        """.strip()

        # Channel/Account type breakdown
        channel_query = f"""
            SELECT Account.Type AccountType, COUNT(Id) CaseCount
            FROM Case
            WHERE {filters} AND Account.Type != null
            GROUP BY Account.Type
            ORDER BY COUNT(Id) DESC
        """.strip()

        # Owner performance
        owner_query = f"""
            SELECT Owner.Name, COUNT(Id) CasesHandled
            FROM Case
            WHERE {filters}
            GROUP BY Owner.Name
            ORDER BY COUNT(Id) DESC
            LIMIT 10
        """.strip()

        # Execute queries
        volume_response = await client.get(f"/query?q={quote(volume_query)}")
        self._handle_error(volume_response)

        escalation_response = await client.get(f"/query?q={quote(escalation_query)}")
        self._handle_error(escalation_response)

        channel_response = await client.get(f"/query?q={quote(channel_query)}")
        self._handle_error(channel_response)

        owner_response = await client.get(f"/query?q={quote(owner_query)}")
        self._handle_error(owner_response)

        escalation_records = escalation_response.json().get("records", [])
        return {
            "timeframe": timeframe,
            "filters": {"priority": priority, "status": status},
            "volumeMetrics": volume_response.json().get("records", []),
            "escalationMetrics": escalation_records[0] if escalation_records else {},
            "channelBreakdown": channel_response.json().get("records", []),
            "ownerPerformance": owner_response.json().get("records", []),
        }

    async def get_lead_funnel_analysis(
        self,
        source: str | None = None,
        timeframe: str = "THIS_QUARTER",
        conversion_stage: str = "Opportunity",
    ) -> dict[str, Any]:
        """Lead conversion funnel analysis by source with quality metrics."""
        client = await self._get_client()
        source_filter = f" AND LeadSource = '{source}'" if source else ""

        # Lead volume by source and status
        volume_query = f"""
            SELECT LeadSource, Status, COUNT(Id) LeadCount
            FROM Lead
            WHERE CreatedDate = {timeframe}{source_filter}
            GROUP BY LeadSource, Status
            ORDER BY LeadSource, Status
        """.strip()

        # Conversion analysis
        conversion_query = f"""
            SELECT LeadSource,
                   COUNT(Id) TotalLeads,
                   SUM(CASE WHEN IsConverted = true THEN 1 ELSE 0 END) ConvertedLeads
            FROM Lead
            WHERE CreatedDate = {timeframe}{source_filter}
            GROUP BY LeadSource
            ORDER BY COUNT(Id) DESC
        """.strip()

        # Lead quality scoring
        quality_query = f"""
            SELECT LeadSource, Rating, COUNT(Id) Count
            FROM Lead
            WHERE CreatedDate = {timeframe} AND Rating != null{source_filter}
            GROUP BY LeadSource, Rating
            ORDER BY LeadSource, Rating
        """.strip()

        # Opportunity creation from leads
        opportunity_query = f"""
            SELECT Account.Name, ConvertedOpportunity.Amount, ConvertedOpportunity.StageName,
                   ConvertedOpportunity.CloseDate, LeadSource
            FROM Lead
            WHERE CreatedDate = {timeframe} AND IsConverted = true
                  AND ConvertedOpportunity.Id != null{source_filter}
            ORDER BY ConvertedOpportunity.Amount DESC NULLS LAST
            LIMIT 20
        """.strip()

        # Execute queries
        volume_response = await client.get(f"/query?q={quote(volume_query)}")
        self._handle_error(volume_response)

        conversion_response = await client.get(f"/query?q={quote(conversion_query)}")
        self._handle_error(conversion_response)

        quality_response = await client.get(f"/query?q={quote(quality_query)}")
        self._handle_error(quality_response)

        opportunity_response = await client.get(f"/query?q={quote(opportunity_query)}")
        self._handle_error(opportunity_response)

        # Calculate funnel metrics
        conversion_records = conversion_response.json().get("records", [])
        funnel_metrics = []
        for record in conversion_records:
            total = record.get("TotalLeads") or 0
            converted = record.get("ConvertedLeads") or 0
            rate = (converted / total * 100) if total > 0 else 0

            funnel_metrics.append({
                "source": record.get("LeadSource"),
                "totalLeads": total,
                "convertedLeads": converted,
                "conversionRate": f"{rate:.2f}%",
            })

        return {
            "timeframe": timeframe,
            "sourceFilter": source,
            "conversionStage": conversion_stage,
            "leadVolume": volume_response.json().get("records", []),
            "funnelMetrics": funnel_metrics,
            "qualityAnalysis": quality_response.json().get("records", []),
            "topOpportunities": opportunity_response.json().get("records", []),
        }
