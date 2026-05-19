# Salesforce CLI Queries — MCP Prompt Equivalents

Each section shows the natural language prompt used in Claude Desktop, followed by the
equivalent `sf data query` command you can run directly in the terminal.

All queries are scoped to Southern Europe: Italy, Spain, Portugal, Greece, Cyprus, Malta.

**Dates assume today = 2026-05-19 (FY27, Q2)**
- THIS_FISCAL_YEAR: 2026-02-01 → 2027-01-31
- LAST_FISCAL_YEAR: 2025-02-01 → 2026-01-31
- THIS_QUARTER (Q2): 2026-05-01 → 2026-07-31
- LAST_QUARTER (Q1): 2026-02-01 → 2026-04-30
- NEXT_QUARTER (Q3): 2026-08-01 → 2026-10-31

---

## Revenue & Attainment

### "What's our total closed-won revenue for this fiscal year?"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "Break down FY27 revenue by country"

```bash
sf data query \
  --query "SELECT Account.BillingCountry country, SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

---

### "How are we tracking against target in Spain this year?"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry = 'Spain' AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "Compare revenue this fiscal year versus last fiscal year"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2025-02-01 AND CloseDate <= 2026-01-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "Show me Q1 revenue"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2026-04-30" \
  --json \
  -o santiagot@semperis.com
```

---

### "What was revenue in FY26 Q1 versus FY27 Q1?"

FY27 Q1 (Feb–Apr 2026):
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2026-04-30" \
  --json \
  -o santiagot@semperis.com
```

FY26 Q1 (Feb–Apr 2025):
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2025-02-01 AND CloseDate <= 2025-04-30" \
  --json \
  -o santiagot@semperis.com
```

---

### "Show revenue growth from last fiscal year to this one broken down by country"

This FY by country:
```bash
sf data query \
  --query "SELECT Account.BillingCountry country, SUM(Amount) totalRevenue FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

Last FY by country:
```bash
sf data query \
  --query "SELECT Account.BillingCountry country, SUM(Amount) totalRevenue FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2025-02-01 AND CloseDate <= 2026-01-31 GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

---

## Pipeline

### "What does our pipeline look like this quarter?"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "Show me the pipeline by stage for this quarter"

```bash
sf data query \
  --query "SELECT StageName, SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31 GROUP BY StageName ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

---

### "What's coming up in the next 60 days?"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-05-19 AND CloseDate <= 2026-07-18" \
  --json \
  -o santiagot@semperis.com
```

---

### "Show pipeline for both this quarter and next quarter combined"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-10-31" \
  --json \
  -o santiagot@semperis.com
```

---

## Partners

### "Who are our top 10 partners by revenue this fiscal year?"

```bash
sf data query \
  --query "SELECT Partner__r.Name partnerName, SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 AND Partner__c != null GROUP BY Partner__r.Name ORDER BY SUM(Amount) DESC LIMIT 10" \
  --json \
  -o santiagot@semperis.com
```

---

### "Give me a full scorecard for Accenture" — revenue

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) wonDeals FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND Partner__r.Name LIKE '%Accenture%' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

### "Give me a full scorecard for Accenture" — open pipeline

```bash
sf data query \
  --query "SELECT SUM(Amount) totalPipeline, COUNT(Id) openDeals FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND Partner__r.Name LIKE '%Accenture%' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

### "Give me a full scorecard for Accenture" — pipeline by stage

```bash
sf data query \
  --query "SELECT StageName, SUM(Amount) totalPipeline, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND Partner__r.Name LIKE '%Accenture%' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 GROUP BY StageName ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

---

### "How is Inetum Spain performing this quarter?"

```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) wonDeals FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND Partner__r.Name LIKE '%Inetum%' AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "Which partners are most active?" (by last modified date)

```bash
sf data query \
  --query "SELECT Partner__r.Name partnerName, COUNT(Id) dealCount, SUM(Amount) totalPipeline, MAX(LastModifiedDate) lastActivity FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND Partner__c != null AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31 GROUP BY Partner__r.Name ORDER BY MAX(LastModifiedDate) DESC LIMIT 15" \
  --json \
  -o santiagot@semperis.com
```

---

## Hygiene & Risk

### "Show me all orphan deals without a partner assigned this quarter"

```bash
sf data query \
  --query "SELECT Name, Account.Name, Amount, StageName, CloseDate FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND Partner__c = null AND IsClosed = false AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31 ORDER BY Amount DESC LIMIT 20" \
  --json \
  -o santiagot@semperis.com
```

---

### "Which deals haven't moved in the last 60 days?"

```bash
sf data query \
  --query "SELECT Name, Partner__r.Name partnerName, StageName, Amount, CloseDate, LastModifiedDate FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31 AND LastModifiedDate < 2026-03-20T00:00:00Z ORDER BY LastModifiedDate ASC LIMIT 20" \
  --json \
  -o santiagot@semperis.com
```

---

### "What deals are high risk — low probability and closing soon?"

```bash
sf data query \
  --query "SELECT Name, Partner__r.Name partnerName, StageName, Amount, Probability, CloseDate FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND Probability < 40 AND CloseDate >= 2026-05-19 AND CloseDate <= 2026-06-18 ORDER BY CloseDate ASC LIMIT 20" \
  --json \
  -o santiagot@semperis.com
```

---

### "Show me deals we lost this quarter and where we lost them" (by partner)

```bash
sf data query \
  --query "SELECT Partner__r.Name partnerName, COUNT(Id) lostCount, SUM(Amount) lostAmount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Lost' AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31 GROUP BY Partner__r.Name ORDER BY COUNT(Id) DESC LIMIT 10" \
  --json \
  -o santiagot@semperis.com
```

---

## KPIs & Trends

### "Give me a full KPI snapshot for this fiscal year" — revenue + pipeline

Revenue:
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) wonDeals FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

Pipeline:
```bash
sf data query \
  --query "SELECT SUM(Amount) totalPipeline, COUNT(Id) openDeals FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

Orphans (partner coverage):
```bash
sf data query \
  --query "SELECT COUNT(Id) totalOpen FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

```bash
sf data query \
  --query "SELECT COUNT(Id) orphanCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = false AND Partner__c = null AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "Show me revenue trend across Q1, Q2, Q3, Q4"

Q1 (Feb–Apr 2026):
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2026-04-30" \
  --json \
  -o santiagot@semperis.com
```

Q2 (May–Jul 2026):
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31" \
  --json \
  -o santiagot@semperis.com
```

Q3 (Aug–Oct 2026):
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-08-01 AND CloseDate <= 2026-10-31" \
  --json \
  -o santiagot@semperis.com
```

Q4 (Nov 2026–Jan 2027):
```bash
sf data query \
  --query "SELECT SUM(Amount) totalRevenue, COUNT(Id) dealCount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-11-01 AND CloseDate <= 2027-01-31" \
  --json \
  -o santiagot@semperis.com
```

---

### "What's our win rate by country this year?"

All closed deals:
```bash
sf data query \
  --query "SELECT Account.BillingCountry country, COUNT(Id) totalClosed, SUM(Amount) totalAmount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND IsClosed = true AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

Won deals only (divide by total for win rate):
```bash
sf data query \
  --query "SELECT Account.BillingCountry country, COUNT(Id) wonCount, SUM(Amount) wonAmount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND StageName = 'Closed Won' AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 GROUP BY Account.BillingCountry ORDER BY SUM(Amount) DESC" \
  --json \
  -o santiagot@semperis.com
```

---

### "How do deal registrations compare quarter over quarter?"

```bash
sf data query \
  --query "SELECT Partner_Registration_Approval__c status, COUNT(Id) cnt, SUM(Amount) totalAmount FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND Partner_Registration_Approval__c != null AND CloseDate >= 2026-02-01 AND CloseDate <= 2027-01-31 GROUP BY Partner_Registration_Approval__c" \
  --json \
  -o santiagot@semperis.com
```

By quarter (Q1):
```bash
sf data query \
  --query "SELECT Partner_Registration_Approval__c status, COUNT(Id) cnt FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND Partner_Registration_Approval__c != null AND CloseDate >= 2026-02-01 AND CloseDate <= 2026-04-30 GROUP BY Partner_Registration_Approval__c" \
  --json \
  -o santiagot@semperis.com
```

By quarter (Q2):
```bash
sf data query \
  --query "SELECT Partner_Registration_Approval__c status, COUNT(Id) cnt FROM Opportunity WHERE Account.BillingCountry IN ('Italy','Spain','Portugal','Greece','Cyprus','Malta') AND Partner_Registration_Approval__c != null AND CloseDate >= 2026-05-01 AND CloseDate <= 2026-07-31 GROUP BY Partner_Registration_Approval__c" \
  --json \
  -o santiagot@semperis.com
```
