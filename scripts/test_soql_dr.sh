#!/bin/bash
# Test deal registration queries directly with sf CLI
# Run this on the server laptop where you have Salesforce auth
# Uses org: santiagot@semperis.com

ORG="-o santiagot@semperis.com"

echo "========================================"
echo "Testing Deal Registration SOQL Queries"
echo "========================================"

# Test 1: Simple count of all registered deals
echo ""
echo "Test 1: Count all registered deals (no date filter)"
echo "Query: SELECT COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null"
sf data query $ORG --query "SELECT COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null" --json

# Test 2: Count by status (GROUP BY)
echo ""
echo "Test 2: Count by status"
echo "Query: SELECT Partner_Registration_Approval__c, COUNT(Id) cnt FROM Opportunity WHERE Partner_Registration_Approval__c != null GROUP BY Partner_Registration_Approval__c"
sf data query $ORG --query "SELECT Partner_Registration_Approval__c, COUNT(Id) cnt FROM Opportunity WHERE Partner_Registration_Approval__c != null GROUP BY Partner_Registration_Approval__c" --json

# Test 3: With CreatedDate filter (THIS FISCAL YEAR = Feb 1, 2026 - Jan 31, 2027)
echo ""
echo "Test 3: With CreatedDate filter (FY27)"
echo "Query: SELECT COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null AND CreatedDate >= '2026-02-01T00:00:00Z' AND CreatedDate <= '2027-01-31T23:59:59Z'"
sf data query $ORG --query "SELECT COUNT(Id) FROM Opportunity WHERE Partner_Registration_Approval__c != null AND CreatedDate >= '2026-02-01T00:00:00Z' AND CreatedDate <= '2027-01-31T23:59:59Z'" --json

# Test 4: With CreatedDate + GROUP BY
echo ""
echo "Test 4: With CreatedDate filter + GROUP BY status"
echo "Query: SELECT Partner_Registration_Approval__c, COUNT(Id) cnt FROM Opportunity WHERE Partner_Registration_Approval__c != null AND CreatedDate >= '2026-02-01T00:00:00Z' AND CreatedDate <= '2027-01-31T23:59:59Z' GROUP BY Partner_Registration_Approval__c"
sf data query $ORG --query "SELECT Partner_Registration_Approval__c, COUNT(Id) cnt FROM Opportunity WHERE Partner_Registration_Approval__c != null AND CreatedDate >= '2026-02-01T00:00:00Z' AND CreatedDate <= '2027-01-31T23:59:59Z' GROUP BY Partner_Registration_Approval__c" --json

# Test 5: Full query with Country filter
echo ""
echo "Test 5: Full query with country filter + GROUP BY"
echo "Query: SELECT Partner_Registration_Approval__c, COUNT(Id) cnt_dr, SUM(Amount) amt_dr FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND Partner_Registration_Approval__c != null AND CreatedDate >= '2026-02-01T00:00:00Z' AND CreatedDate <= '2027-01-31T23:59:59Z' GROUP BY Partner_Registration_Approval__c"
sf data query $ORG --query "SELECT Partner_Registration_Approval__c, COUNT(Id) cnt_dr, SUM(Amount) amt_dr FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND Partner_Registration_Approval__c != null AND CreatedDate >= '2026-02-01T00:00:00Z' AND CreatedDate <= '2027-01-31T23:59:59Z' GROUP BY Partner_Registration_Approval__c" --json

echo ""
echo "========================================"
echo "Done. Review the errors above."
echo "========================================"
