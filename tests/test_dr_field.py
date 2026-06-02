#!/usr/bin/env python3
"""Diagnostic script to test Partner_Registration_Approval__c field queries."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

load_dotenv()

# Import Salesforce client
sys.path.insert(0, '/Users/santiago/Projects/salesforce-fastmcp')
from mcp.server import get_client

async def test_queries():
    """Test progressive SOQL queries to isolate the issue."""
    sf = get_client()

    print("=" * 80)
    print("DIAGNOSTIC: Testing Partner_Registration_Approval__c field")
    print("=" * 80)

    tests = [
        {
            "name": "Simple field select (no WHERE)",
            "query": "SELECT Partner_Registration_Approval__c FROM Opportunity LIMIT 5",
        },
        {
            "name": "Field with != null check",
            "query": "SELECT Partner_Registration_Approval__c FROM Opportunity WHERE Partner_Registration_Approval__c != null LIMIT 5",
        },
        {
            "name": "COUNT with != null",
            "query": "SELECT COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null",
        },
        {
            "name": "COUNT with date filter",
            "query": "SELECT COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null AND Partner_Opportunity_Registration_Date__c != null",
        },
        {
            "name": "Simple GROUP BY",
            "query": "SELECT Partner_Registration_Approval__c, COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null GROUP BY Partner_Registration_Approval__c",
        },
        {
            "name": "GROUP BY with SUM",
            "query": "SELECT Partner_Registration_Approval__c, COUNT(Id) cnt, SUM(Amount) amt FROM Opportunity WHERE Partner_Registration_Approval__c != null GROUP BY Partner_Registration_Approval__c",
        },
        {
            "name": "GROUP BY with date range (THIS_QUARTER)",
            "query": "SELECT Partner_Registration_Approval__c, COUNT(Id) cnt, SUM(Amount) amt FROM Opportunity WHERE Partner_Registration_Approval__c != null AND Partner_Opportunity_Registration_Date__c >= 2026-05-01T00:00:00Z AND Partner_Opportunity_Registration_Date__c <= 2026-07-31T23:59:59Z GROUP BY Partner_Registration_Approval__c",
        },
        {
            "name": "GROUP BY with Country filter",
            "query": "SELECT Partner_Registration_Approval__c, COUNT(Id) cnt, SUM(Amount) amt FROM Opportunity WHERE Account.BillingCountry IN ('Spain', 'Italy') AND Partner_Registration_Approval__c != null GROUP BY Partner_Registration_Approval__c",
        },
    ]

    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Query: {test['query']}")
        print("-" * 80)
        try:
            result = await sf.query(test['query'])
            total = result.get('totalSize', 0)
            records = result.get('records', [])
            print(f"✅ SUCCESS - {total} records returned")
            if records:
                print(f"   Sample: {records[0]}")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_queries())
