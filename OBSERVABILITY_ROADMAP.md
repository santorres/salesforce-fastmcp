# Observability Roadmap: Langfuse Integration

**Status**: 📋 Planning Phase  
**Date**: June 16, 2026  
**Priority**: Medium (Post-launch, pending MCP approval)  
**Audience**: Engineering team, Security team, IT infrastructure

---

## Executive Summary

This document outlines the plan to add comprehensive observability and governance to the Salesforce FastMCP Connector using **Langfuse**, an open-source LLM observability platform.

**Key Decision**: Langfuse (self-hosted) instead of LangSmith (cloud-based) due to:
- ✅ Open source (no vendor lock-in)
- ✅ Self-hosted on corporate infrastructure (no data leaving network)
- ✅ LLM-agnostic (works with any LLM Client, not tied to specific product)
- ✅ Free (no subscription costs)
- ✅ Meets all 5 observability priorities
- ✅ Solves corporate network restrictions (no outbound HTTPS to external APIs)

**Timeline**: Implement after MCP approval and initial deployment (Q3-Q4 2026)

---

## Problem Statement

**Current State:**
- Basic audit logging (local SOQL query tracking)
- No visibility into LLM Client reasoning/decisions
- Limited governance for multi-team access control
- No integrated tracing of LLM reasoning + MCP execution

**Desired State:**
- See what LLM Client is thinking at each step
- Trace complete execution flow (LLM reasoning → MCP tool selection → SOQL execution)
- Multi-team access control with audit trails
- Flag and monitor sensitive operations
- Full user identity tracking
- Data stays on corporate infrastructure

---

## Requirements & Priorities

### Priority 1: Security/Audit Trail ⭐⭐⭐⭐⭐
- Complete trace history with metadata (who, what, when, why)
- All queries logged with user identity
- Compliance-ready audit trail
- Forensic analysis capability for security incidents

### Priority 2: Agent Decision-Making ⭐⭐⭐⭐⭐
- See step-by-step reasoning at each step
- Understand why LLM Client chose a specific tool
- Visualize decision flow and branches
- Debug LLM reasoning issues

### Priority 3: Governance ⭐⭐⭐⭐⭐
- Multi-team access control (regional teams, etc.)
- Role-based access (admin, auditor, viewer, etc.)
- User/team workspaces (isolated from other teams)
- API key management per user/team

### Priority 4: Sensitive Operations ⭐⭐⭐⭐
- Flag specific operations as "sensitive"
- Custom tagging system
- Rules/alerts for sensitive operations
- Audit trails for compliance

### Priority 5: User Identity Tracking ⭐⭐⭐⭐⭐
- All traces include user email/identity
- Know WHO did what, WHEN, and WHY
- Integration with Semperis SSO

---

## Solution: Langfuse

### What is Langfuse?

**Langfuse** is an open-source LLM observability platform designed for:
- Tracing LLM applications (see every step)
- Debugging agent behavior
- Production monitoring
- Team collaboration and governance

**Key Characteristics:**
- Open source (GitHub: github.com/langfuse/langfuse)
- Self-hostable on corporate infrastructure
- LLM-agnostic (works with any LLM implementation)
- Production-optimized
- Active community and regular updates

### Why Langfuse Over LangSmith?

| Aspect | LangSmith | Langfuse | Winner |
|--------|-----------|----------|--------|
| **Open Source** | ❌ No (proprietary) | ✅ Yes | Langfuse |
| **Self-Hosted** | ❌ Cloud-only | ✅ Yes | Langfuse |
| **On-Premise** | ❌ No | ✅ Yes | Langfuse |
| **Network Friendly** | ❌ Requires outbound HTTPS | ✅ All internal | Langfuse |
| **Data Privacy** | ❌ Cloud (external) | ✅ Corporate network | Langfuse |
| **Cost** | 💰 Subscription | ✅ Free | Langfuse |
| **LLM-Agnostic** | ⚠️ LLM-agnostic but LangSmith is proprietary | ✅ True LLM-agnostic | Langfuse |
| **Observability** | ✅ Excellent | ✅ Excellent | Tie |
| **Agent Tracing** | ✅ Yes | ✅ Yes | Tie |
| **Community** | ✅ Large | ✅ Growing | Tie |

**Verdict**: Langfuse is better suited for **corporate deployment** with **on-premise requirements**.

---

## How Langfuse Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         Your Corporate Network (Internal Only)          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Langfuse Deployment                      │  │
│  │  ┌──────────────┐  ┌────────────────────────┐   │  │
│  │  │ Web Server   │  │ Async Worker           │   │  │
│  │  │ (UI + API)   │  │ (background processing)│   │  │
│  │  └──────────────┘  └────────────────────────┘   │  │
│  │                                                  │  │
│  │  ┌──────────────┐  ┌────────────────────────┐   │  │
│  │  │ PostgreSQL   │  │ ClickHouse             │   │  │
│  │  │ (transactional)│ (analytics/OLAP)        │   │  │
│  │  └──────────────┘  └────────────────────────┘   │  │
│  │                                                  │  │
│  │  ┌──────────────┐  ┌────────────────────────┐   │  │
│  │  │ Redis        │  │ S3/Blob Storage        │   │  │
│  │  │ (caching)    │  │ (event files)          │   │  │
│  │  └──────────────┘  └────────────────────────┘   │  │
│  └──────────────────────────────────────────────────┘  │
│         ↑                                               │
│         │ (HTTP/internal)                              │
│  ┌──────┴──────────────────────────────────────────┐   │
│  │      Your MCP Server + LLM Client               │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │ Send traces to Langfuse API                │ │   │
│  │  │ (Python SDK / OpenTelemetry)               │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│         ↓                                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │      Salesforce API                             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

KEY BENEFIT: All data stays within corporate network
             No outbound HTTPS to external APIs
```

### Data Flow Example

```
User: santorres@semperis.com asks:
  "Show me Accenture's Q2 pipeline"

1. LLM CLIENT STEP
   ├─ Receives query
   ├─ Parses: partner="Accenture", period="Q2"
   ├─ Decides: Call salesforce_opportunities_by_partner()
   └─ Langfuse logs: [reasoning_trace]

2. MCP EXECUTION STEP
   ├─ Receives tool call from LLM
   ├─ Constructs SOQL query
   ├─ Executes: SELECT ... FROM Opportunity WHERE Partner__r.Name = 'Accenture'...
   ├─ Returns: 34 records
   └─ Langfuse logs: [soql_trace] with duration, records count

3. LLM RESPONSE STEP
   ├─ Processes results
   ├─ Formats response
   ├─ Returns to user
   └─ Langfuse logs: [response_trace]

Langfuse Dashboard Shows:
  User: santorres@semperis.com
  Time: 2026-06-16 14:32:01
  Operation: query_opportunities
  Steps:
    1. Reasoning (234ms)
    2. SOQL Execution (245ms)
    3. Formatting (89ms)
  Total: 568ms
  Records Returned: 34
  Status: ✅ Success
```

---

## How Langfuse Meets Your 5 Priorities

### ✅ Priority 1: Security/Audit Trail

**What You Get:**
- Complete trace history for every operation
- User identity in all traces (from Semperis SSO)
- Timestamp, duration, status for each step
- SOQL queries captured
- Error details captured
- Full audit trail for compliance

**Example Audit Log:**
```
Trace ID: abc123xyz
User: santorres@semperis.com
Timestamp: 2026-06-16 14:32:01 UTC
Operation: query_opportunities_by_partner
Status: ✅ Success
Duration: 568ms

Step 1: LLM Reasoning
  Input: "Show me Accenture's Q2 pipeline"
  Decision: Call salesforce_opportunities_by_partner
  Parameters: partner_name="Accenture", stage_name=...
  Duration: 234ms

Step 2: MCP Execution
  SOQL: SELECT Id, Name, Amount... FROM Opportunity WHERE Partner__r.Name = 'Accenture'...
  Duration: 245ms
  Records: 34
  Status: Success

Step 3: Formatting
  Duration: 89ms
  Response: [34 opportunity records formatted for user]

Searchable/Filterable by:
  - User
  - Date range
  - Operation type
  - Status (success/error)
  - Duration
  - Custom tags
```

---

### ✅ Priority 2: Agent Decision-Making

**What You Get:**
- Step-by-step visualization of reasoning
- See what LLM Client considered at each step
- Understanding of tool selection process
- Debugging capability for unexpected behavior
- Agent graphs showing decision flow

**Example Decision Flow:**
```
LLM Reasoning Trace:

Q: "How is Accenture performing this quarter?"

Step 1: Question Analysis
  └─ Identified entities: partner="Accenture", period="Q2 FY27"
  └─ Intent: Revenue + Pipeline analysis
  └─ Decision: Need 2 queries

Step 2: Tool Selection
  ├─ Consider: get_revenue() - shows closed deals
  ├─ Consider: salesforce_opportunities_by_partner() - shows pipeline
  └─ Selected: BOTH (to give complete picture)

Step 3: Parameter Mapping
  ├─ partner_name = "Accenture" ✓
  ├─ period = "THIS_QUARTER" (auto-mapped from Q2 FY27)
  └─ stage_name = All stages (since asking for performance overview)

Step 4: Tool Execution
  ├─ Call 1: get_revenue() → 2.3M closed
  ├─ Call 2: salesforce_opportunities_by_partner() → 3.1M pipeline
  └─ Reasoning: "Good revenue this quarter + healthy pipeline ahead"

Step 5: Response Formatting
  └─ Compiled response with both metrics

Langfuse Shows:
  ✅ Full reasoning chain
  ✅ Why each tool was selected
  ✅ Parameters used
  ✅ Execution results
  ✅ Final response
```

---

### ✅ Priority 3: Governance

**What You Get:**
- Multi-team workspace isolation
- Role-based access control (RBAC)
  - Admin: Full access, can view all traces, manage users
  - Manager: View team traces, manage team members
  - Auditor: Read-only access to all traces (compliance)
  - User: View own traces only
- API key management per user/team
- Team-level access control
- Usage quotas per team (optional)

**Expected Governance Model:**
```
Organization: Semperis
│
├─ Workspace: EMEA Region
│  ├─ Team: Southern Europe
│  │  ├─ User: santorres@semperis.com (Manager)
│  │  ├─ User: channeldirector1@semperis.com (User)
│  │  └─ Traces: All queries from this team
│  │
│  └─ Team: Northern Europe
│     ├─ User: cd-nordic@semperis.com (Manager)
│     └─ Traces: Only this team's queries
│
├─ Workspace: APAC Region
│  └─ Team: APAC Channel
│     └─ Traces: Only APAC queries
│
└─ Admin Workspace
   └─ User: security-team@semperis.com (Auditor - sees all)
```

**Verification Needed**: Confirm Langfuse has built-in RBAC or if we need custom implementation.

---

### ✅ Priority 4: Sensitive Operations

**What You Get:**
- Custom tagging system for traces
- Flag operations as "sensitive"
- Rules/alerts for sensitive operations
- Compliance monitoring

**Example Sensitive Operations:**
```
Tag: "sensitive" = true
├─ Queries returning > 1000 records (potential data exfiltration)
├─ Queries involving confidential accounts (Telefonica, Vodafone, Orange)
├─ Queries from users querying outside their region
├─ Queries at unusual times (off-hours)
└─ Bulk exports or large result sets

Langfuse Rules:
  Rule 1: IF tag=sensitive AND user NOT IN allow_list THEN alert_security_team
  Rule 2: IF record_count > 1000 THEN tag=sensitive, log_detailed
  Rule 3: IF account IN confidential_list THEN tag=sensitive, require_approval

Alert Example:
  ⚠️ SENSITIVE OPERATION
  User: unknown_user@semperis.com
  Operation: query_opportunities_by_partner
  Account: Telefonica (CONFIDENTIAL)
  Records: 547
  Time: 02:34 AM (off-hours)
  Action: Flagged for security review
```

**Verification Needed**: Confirm tagging and rule system capabilities.

---

### ✅ Priority 5: User Identity Tracking

**What You Get:**
- User email in all traces (from Semperis SSO)
- Timestamp for each action
- Complete audit trail: WHO did WHAT, WHEN
- Attribution of all queries and actions

**Example:**
```
Trace Timeline for santorres@semperis.com
─────────────────────────────────────────

2026-06-16 14:32:01  ✅ query_opportunities_by_partner
                     Partner: Accenture | Records: 34

2026-06-16 14:45:23  ✅ get_revenue
                     Period: THIS_QUARTER | Amount: €2.3M

2026-06-16 15:01:45  ✅ salesforce_opportunities_by_partner
                     Partner: Inetum Spain | Records: 12

[Same user can view own traces]
[Managers can view team traces]
[Auditors can view all traces]
[Users cannot see other users' traces unless admin sets otherwise]
```

---

## Infrastructure Requirements

### Hardware & Services Needed

**Components:**
- PostgreSQL database (transactional data)
- ClickHouse instance (analytics/OLAP)
- Redis cache
- S3-compatible storage or blob storage
- Langfuse Web Server
- Langfuse Async Worker

**Deployment Options:**

**Option 1: Docker Compose (Development/Testing)**
- Single machine with Docker
- Quick setup (~30 minutes)
- Good for PoC/evaluation
- Not recommended for production

**Option 2: Kubernetes (Production Recommended)**
- Scalable, highly available
- Helm charts available
- Production-ready
- Effort: 2-4 hours initial setup
- Maintenance: Standard K8s operations

**Option 3: Cloud VM (Simple Production)**
- VM on AWS/Azure/GCP
- Docker Compose on VM
- Mid-ground between simple and scalable
- Effort: 1-2 hours setup

**Option 4: Managed Services (Easiest)**
- Use managed Postgres (RDS, Azure DB, etc.)
- Use managed ClickHouse (ClickHouse Cloud)
- Self-host Langfuse on VM
- Reduces infrastructure burden

### Network Requirements

- **No outbound HTTPS required** (stays internal)
- Internal HTTP(S) between LLM Client, MCP, and Langfuse
- Optional: Secure TLS between components
- Optional: VPN/tunnel if components on different networks

### Performance Characteristics

- **Trace ingestion**: Batched (minimal overhead)
- **API key caching**: Redis (fast lookups)
- **Analytical queries**: ClickHouse (optimized for analytics)
- **Expected overhead**: <1% latency increase to MCP queries

---

## Implementation Phases

### Phase 0: Approval & Planning (Current - Q2 2026)
- [ ] Get corporate security approval for MCP usage
- [ ] Document requirements and roadmap (this document)
- [ ] Plan for future Langfuse implementation
- **Timeline**: Before MCP launch

### Phase 1: Verification & PoC (Q3 2026)
- [ ] Verify Langfuse governance/RBAC capabilities
- [ ] Check infrastructure availability
  - [ ] Postgres available?
  - [ ] ClickHouse available?
  - [ ] Redis available?
  - [ ] Storage available?
- [ ] Deploy Langfuse locally (Docker Compose)
- [ ] Send test traces from MCP
- [ ] Evaluate UI and features
- [ ] Estimate implementation effort
- **Timeline**: 2-3 weeks
- **Owner**: Engineering team

### Phase 2: Design & Planning (Q3 2026)
- [ ] Finalize governance model (teams, roles, access levels)
- [ ] Define trace schema (what to capture)
- [ ] Design sensitive operation tagging system
- [ ] Plan user identity integration with Semperis SSO
- [ ] Create deployment plan (K8s vs VM vs Cloud)
- [ ] Estimate infrastructure costs
- **Timeline**: 1-2 weeks
- **Owner**: Engineering + IT Infrastructure

### Phase 3: Production Deployment (Q4 2026)
- [ ] Provision infrastructure
- [ ] Deploy Langfuse
- [ ] Configure governance/RBAC
- [ ] Set up user/team structure
- [ ] Configure alerts and rules
- **Timeline**: 2-4 weeks
- **Owner**: IT Infrastructure + Engineering

### Phase 4: MCP Integration (Q4 2026)
- [ ] Add Langfuse SDK to MCP
- [ ] Instrument SOQL query methods
- [ ] Implement trace tagging
- [ ] Set up user identity injection
- [ ] Test end-to-end tracing
- [ ] Deploy to production
- **Timeline**: 1-2 weeks
- **Owner**: Engineering team

### Phase 5: LLM Client Integration (Q4 2026)
- [ ] Configure LLM Client to send traces to Langfuse
  - Environment variables or SDK integration
  - Depends on LLM implementation
- [ ] Verify traces from LLM reasoning
- [ ] Test full end-to-end tracing (LLM → MCP → Salesforce)
- [ ] Validate governance model works
- **Timeline**: 1 week
- **Owner**: Engineering team

### Phase 6: Security Review & Launch (Q4 2026)
- [ ] Security team reviews Langfuse deployment
- [ ] Audit team validates audit trails
- [ ] Compliance verification
- [ ] Channel director training
- [ ] Go-live
- **Timeline**: 1-2 weeks
- **Owner**: Security + Compliance + Engineering

---

## Key Verification Points

Before we implement, these questions need answers:

### Governance/RBAC
- [ ] Does Langfuse have team-based access control?
- [ ] Can we define custom roles (Admin, Manager, Auditor, User)?
- [ ] Can we isolate teams' data from each other?
- [ ] How are API keys managed?

**Where to verify**: GitHub issues/discussions, Langfuse docs, community Slack

### Sensitive Operations
- [ ] Can we tag traces with custom metadata?
- [ ] Can we create rules based on tags?
- [ ] Can we trigger alerts based on trace content?

**Where to verify**: PoC deployment, GitHub docs

### User Identity Integration
- [ ] How do we inject Semperis SSO identity into traces?
- [ ] Can we extract from LLM Client context?
- [ ] Can we extract from MCP context?

**Where to verify**: PoC deployment, integration testing

### Infrastructure
- [ ] Do we have Postgres, ClickHouse, Redis available?
- [ ] Can they be deployed on corporate infrastructure?
- [ ] What's the total cost (if any)?
- [ ] Who manages the infrastructure?

**Where to verify**: IT Infrastructure team

---

## Benefits Summary

### Immediate Benefits (Upon Launch)
- ✅ Complete audit trail for all queries
- ✅ User identity tracking
- ✅ Compliance-ready logging
- ✅ Security team visibility

### Medium-term Benefits (Q1 2027)
- ✅ LLM reasoning visibility (improves decision debugging)
- ✅ Multi-team governance (supports scaling)
- ✅ Sensitive operation alerting (proactive security)

### Long-term Benefits (2027+)
- ✅ ML-powered anomaly detection (insider threat detection)
- ✅ Performance optimization insights
- ✅ User training data (how users interact with tool)
- ✅ Product improvement guidance

---

## Risks & Mitigations

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Governance features not available in Langfuse | Medium | PoC before commitment; custom implementation fallback |
| Infrastructure not available | Low | Start with Docker Compose; escalate to IT if needed |
| Performance overhead | Low | Trace batching, Redis caching minimize impact |
| User adoption/training needed | Medium | Create documentation, training materials |
| Integration complexity with LLM Client | Medium | PoC during Phase 1; depends on LLM implementation |
| Data privacy concerns | Low | All data on-premise; security review required |

---

## Next Actions (Post-MCP Approval)

1. **Document this roadmap** (Done ✅)
2. **Schedule governance verification** (Week 1 of Q3)
   - Check Langfuse GitHub for governance features
3. **Check infrastructure** (Week 1 of Q3)
   - Talk to IT: Available Postgres, ClickHouse, Redis?
4. **Create PoC plan** (Week 2 of Q3)
   - Deploy Langfuse locally
   - Test trace ingestion
   - Evaluate governance/features
5. **Decision gate** (Week 4 of Q3)
   - Is Langfuse ready for production?
   - Estimate effort and timeline
   - Get funding/approval for Phase 2

---

## Open Questions for Future Phases

1. What are "sensitive operations" specifically for your org?
   - Data exfiltration (record count threshold?)
   - Confidential accounts (which accounts?)
   - Time-based anomalies (what hours are unusual?)
   - User-based anomalies (which queries are unexpected?)

2. What governance model fits your org?
   - By region? By partner type? By user role?
   - What permissions for each role?

3. What LLM Client will be used?
   - Different clients have different tracing capabilities
   - Affects integration effort

4. What infrastructure is available?
   - Existing K8s? Docker hosts? Cloud availability?

5. What's the SLA for Langfuse availability?
   - Is this critical infrastructure?
   - Backup/disaster recovery needed?

---

## Appendix: Langfuse Resources

**Official Resources:**
- GitHub: https://github.com/langfuse/langfuse
- Docs: https://langfuse.com/docs
- Community: https://langfuse.com/discord

**Key Documentation to Review Later:**
- Self-hosting guide: https://langfuse.com/docs/deployment/self-host
- User management: (need to verify URL)
- Tracing setup: https://langfuse.com/docs/tracing
- Integration examples: https://langfuse.com/docs/integrations

---

## Document Control

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-16 | Santiago Torres | Initial roadmap |

**Next Review**: Q3 2026 (after MCP approval and PoC planning)

**Status**: 📋 **PLANNING** - Waiting for MCP approval before proceeding

---

**Document Purpose**: This roadmap documents the plan to add Langfuse observability to the MCP connector. It should be reviewed and updated as the project progresses, and referenced when implementation begins.
