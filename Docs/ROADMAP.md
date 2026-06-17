# Development Roadmap: Future Initiatives

This document consolidates the development roadmap for three future initiatives: observability with Langfuse, YAML-only scalability, and cloud-native architecture.

**Timeline:** Q3 2026 onwards (post-MCP launch)

---

## Table of Contents

1. [Initiative 1: Observability with Langfuse](#initiative-1-observability-with-langfuse)
2. [Initiative 2: YAML-Only Scalability for Multi-User Deployment](#initiative-2-yaml-only-scalability-for-multi-user-deployment)
3. [Initiative 3: Cloud-Native Scalability Architecture](#initiative-3-cloud-native-scalability-architecture)
4. [Consolidated Implementation Timeline](#consolidated-implementation-timeline)

---

## Initiative 1: Observability with Langfuse

**Status:** 📋 Planning Phase  
**Timeline:** Q3-Q4 2026 (post-launch)  
**Priority:** Medium

### Executive Summary

Add comprehensive observability and governance to the MCP connector using **Langfuse**, an open-source LLM observability platform.

**Key Decision:** Langfuse (self-hosted) instead of LangSmith (cloud-based) because:
- ✅ Open source (no vendor lock-in)
- ✅ Self-hosted on corporate infrastructure (no data leaving network)
- ✅ LLM-agnostic (works with any LLM Client)
- ✅ Free (no subscription costs)
- ✅ Meets all 5 observability priorities

### 5 Core Priorities

| Priority | Goal | Example |
|----------|------|---------|
| **Security/Audit Trail** | Complete trace history with user identity | Who accessed what, when, why |
| **Agent Decision-Making** | See step-by-step LLM reasoning | Why LLM chose specific tool |
| **Governance** | Multi-team access control with RBAC | Regional teams see only their data |
| **Sensitive Operations** | Flag and alert on sensitive queries | Large exports, confidential accounts |
| **User Identity Tracking** | Attribution of all actions | All traces include user email |

### Why Langfuse?

| Aspect | LangSmith | Langfuse | Winner |
|--------|-----------|----------|--------|
| **Open Source** | ❌ No | ✅ Yes | Langfuse |
| **Self-Hosted** | ❌ Cloud-only | ✅ Yes | Langfuse |
| **On-Premise** | ❌ No | ✅ Yes | Langfuse |
| **Network Friendly** | ❌ Requires outbound HTTPS | ✅ All internal | Langfuse |
| **Data Privacy** | ❌ Cloud (external) | ✅ Corporate network | Langfuse |
| **Cost** | 💰 Subscription | ✅ Free | Langfuse |
| **Observability** | ✅ Excellent | ✅ Excellent | Tie |

### Infrastructure Requirements

**Components:**
- PostgreSQL database (transactional data)
- ClickHouse instance (analytics/OLAP)
- Redis cache
- S3-compatible storage or blob storage
- Langfuse Web Server
- Langfuse Async Worker

**Deployment Options:**
1. **Docker Compose** (Development/Testing) — Quick setup (~30 min), not production-ready
2. **Kubernetes** (Production Recommended) — Scalable, HA, Helm charts available
3. **Cloud VM** (Simple Production) — Mid-ground between simple and scalable
4. **Managed Services** (Easiest) — Use managed Postgres, ClickHouse; self-host Langfuse

**Performance:**
- Trace ingestion: Batched (minimal overhead)
- API key caching: Redis (fast lookups)
- Analytical queries: ClickHouse (optimized)
- Expected overhead: <1% latency increase

### Implementation Phases

**Phase 0: Approval & Planning (Current - Q2 2026)**
- [ ] Get corporate security approval for MCP usage
- [ ] Document requirements and roadmap
- **Timeline:** Before MCP launch

**Phase 1: Verification & PoC (Q3 2026)**
- [ ] Verify Langfuse governance/RBAC capabilities
- [ ] Check infrastructure availability (Postgres, ClickHouse, Redis)
- [ ] Deploy Langfuse locally (Docker Compose)
- [ ] Send test traces from MCP
- [ ] Evaluate UI and features
- **Timeline:** 2-3 weeks
- **Owner:** Engineering team

**Phase 2: Design & Planning (Q3 2026)**
- [ ] Finalize governance model (teams, roles, access levels)
- [ ] Define trace schema (what to capture)
- [ ] Design sensitive operation tagging
- [ ] Plan user identity integration with Semperis SSO
- [ ] Create deployment plan
- **Timeline:** 1-2 weeks
- **Owner:** Engineering + IT Infrastructure

**Phase 3: Production Deployment (Q4 2026)**
- [ ] Provision infrastructure
- [ ] Deploy Langfuse
- [ ] Configure governance/RBAC
- [ ] Set up user/team structure
- [ ] Configure alerts and rules
- **Timeline:** 2-4 weeks
- **Owner:** IT Infrastructure + Engineering

**Phase 4: MCP Integration (Q4 2026)**
- [ ] Add Langfuse SDK to MCP
- [ ] Instrument SOQL query methods
- [ ] Implement trace tagging
- [ ] Set up user identity injection
- [ ] Test end-to-end tracing
- **Timeline:** 1-2 weeks
- **Owner:** Engineering team

**Phase 5: LLM Client Integration (Q4 2026)**
- [ ] Configure LLM Client to send traces to Langfuse
- [ ] Verify traces from LLM reasoning
- [ ] Test full end-to-end tracing
- [ ] Validate governance model
- **Timeline:** 1 week
- **Owner:** Engineering team

**Phase 6: Security Review & Launch (Q4 2026)**
- [ ] Security team reviews Langfuse deployment
- [ ] Audit team validates audit trails
- [ ] Compliance verification
- [ ] Channel director training
- [ ] Go-live
- **Timeline:** 1-2 weeks
- **Owner:** Security + Compliance + Engineering

### Key Verification Points (Before Implementation)

- [ ] Does Langfuse have team-based access control?
- [ ] Can we define custom roles (Admin, Manager, Auditor, User)?
- [ ] Can we isolate teams' data from each other?
- [ ] Can we tag traces with custom metadata?
- [ ] Can we create rules based on tags?
- [ ] How do we inject Semperis SSO identity into traces?
- [ ] Do we have Postgres, ClickHouse, Redis available?
- [ ] What's the total cost (if any)?

### Benefits Summary

**Immediate (Upon Launch):**
- ✅ Complete audit trail for all queries
- ✅ User identity tracking
- ✅ Compliance-ready logging
- ✅ Security team visibility

**Medium-term (Q1 2027):**
- ✅ LLM reasoning visibility (improves debugging)
- ✅ Multi-team governance (supports scaling)
- ✅ Sensitive operation alerting (proactive security)

**Long-term (2027+):**
- ✅ ML-powered anomaly detection
- ✅ Performance optimization insights
- ✅ User training data
- ✅ Product improvement guidance

### Resources

- GitHub: https://github.com/langfuse/langfuse
- Docs: https://langfuse.com/docs
- Self-hosting guide: https://langfuse.com/docs/deployment/self-host
- Community: https://langfuse.com/discord

---

## Initiative 2: YAML-Only Scalability for Multi-User Deployment

**Status:** 🎯 Feasible, Ready for Implementation  
**Timeline:** Q3 2026 (parallel with Langfuse PoC)  
**Priority:** High (enables multi-user GLEAN integration)

### Executive Summary

Support 20+ channel directors with different territories using **YAML files only** — no database, no extra infrastructure.

**Verdict:** ✅ **100% FEASIBLE**

**Why it works:**
- YAML is fast to load (< 100ms for reasonable sizes)
- In-memory caching eliminates repeated disk I/O
- 20 users with territories = tiny data (< 1 MB YAML)
- Single file co-located with server = zero network overhead
- Hot reload with file watcher = updates without restart

### Core Architecture

```
GLEAN (Corporate AI Tool)
    ↓ (HTTP request with auth header)
MCP Server (Co-located)
    ├─ Extract user from auth header
    ├─ Load deployment/users.yaml (in memory)
    ├─ Lookup user → territories/countries
    ├─ Load config/sales_targets.yaml
    └─ Execute tool with filtering
    ↓
Salesforce (filtered queries)
```

### User Context Model

```python
@dataclass
class UserContext:
    username: str              # e.g., "santiago@semperis.com"
    territories: list[str]    # e.g., ["South_Europe"]
    countries: list[str]      # e.g., ["Italy", "Spain", "Portugal"]
    partners: list[str]       # Filtered partners, empty = all
    role: str                 # "channel_director", "admin"
```

### YAML File Structure (Example)

```yaml
# deployment/users.yaml
organizations:
  "00D5w000004rH0yEAE":
    name: "Semperis EMEA"
    users:
      santiago@semperis.com:
        name: "Santiago Tortes"
        role: "channel_director"
        territories: ["South_Europe"]
        countries: ["Italy", "Spain", "Portugal"]
        partners: []  # Empty = all partners
        metadata:
          email_backup: "santiago.tortes@semperis.com"
          cost_center: "EU-001"
      
      maria@semperis.com:
        name: "Maria Garcia"
        role: "channel_director"
        territories: ["South_Europe"]
        countries: ["Greece", "Cyprus", "Malta"]
        partners: ["Deloitte", "PWC"]
      
      john@semperis.com:
        name: "John Doe"
        role: "admin"
        territories: []  # Empty = all territories
        countries: []    # Empty = all countries
        partners: []
```

### Performance Characteristics

```
File Size (20 users):
  users.yaml: ~5 KB
  sales_targets.yaml: ~50 KB
  Total: ~55 KB

Load Time (first request):
  Parse YAML: ~35ms (one-time)

Subsequent Requests (from memory):
  User lookup (O(1)): ~0.1ms
  Territory filter: ~1ms
  Config filter: ~2ms
  Total: ~3ms ✅

Memory Footprint:
  Total: ~350 KB (negligible)

Scalability:
  20 users: Perfect ✅
  50 users: Still sub-millisecond ✅
  100 users: Still feasible ✅
  1000+ users: Consider database migration
```

### Hot Reload (Zero Downtime)

**Problem:** Users want to add/update territories without server restart.

**Solution:** File watcher + hot reload

```python
from watchdog.observers import Observer

class YAMLFileWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if 'users.yaml' in event.src_path:
            user_resolver._load_users()
            user_resolver._cache.clear()
            print("✅ Users reloaded successfully")
```

**Update Flow:**
1. Team edits `deployment/users.yaml`
2. Commit to git (optional)
3. File watcher detects change (~100ms)
4. Reload from disk, clear memory cache
5. Next request uses updated config immediately
6. **Total downtime: 0ms** ✅

### Adding a New User (Git-Based)

```bash
# 1. Create feature branch
git checkout -b feature/add-user-carlos

# 2. Edit deployment/users.yaml
# Add carlos@semperis.com entry

# 3. Commit
git add deployment/users.yaml
git commit -m "Add carlos@semperis.com to Spain territory"

# 4. Create PR for review
git push origin feature/add-user-carlos

# 5. After approval, merge
git merge feature/add-user-carlos

# 6. File watcher detects change automatically
# 7. Carlos can immediately use MCP server! ✅
```

### Implementation Phases

**Phase 1 (Week 1): Design & Setup**
- [ ] Design users.yaml structure
- [ ] Create sample users.yaml with 20+ users
- [ ] Design how GLEAN passes user identity
- [ ] Update scalability doc

**Phase 2 (Week 2-3): Core Implementation**
- [ ] Create `UserContext` dataclass
- [ ] Implement `YAMLUserResolver` class
- [ ] Update authentication to extract username
- [ ] Add user context injection to tools
- [ ] Test with local YAML file

**Phase 3 (Week 3-4): Tool Integration**
- [ ] Update all tools to use user context
- [ ] Add automatic filtering by territory/country
- [ ] Test filtering works correctly

**Phase 4 (Week 4-5): Hot Reload & Polish**
- [ ] Implement file watcher for hot reload
- [ ] Add logging for user context resolution
- [ ] Create deployment guide
- [ ] Test multi-user scenarios

**Phase 5 (Week 5+): GLEAN Integration**
- [ ] Coordinate with GLEAN team on user identity passing
- [ ] Implement header extraction (or JWT parsing)
- [ ] Test end-to-end GLEAN → MCP → Salesforce
- [ ] Load test with 20 concurrent users

### YAML-Only vs Database Comparison

| Aspect | YAML-Only | Database |
|--------|-----------|----------|
| **Setup Time** | 1 hour | 1-2 weeks |
| **Infrastructure** | None (co-located) | New PostgreSQL instance |
| **Maintenance** | None | DBA team, backups, monitoring |
| **Approvals** | File in git | New infrastructure (big approval) |
| **Cost** | $0 | $5-50/month + engineering |
| **Scaling to 20 users** | Perfect ✅ | Overkill |

**Verdict:** YAML-Only is the RIGHT choice for your constraints!

### Benefits

| Benefit | Impact |
|---------|--------|
| **Multi-Tenancy** | Support different GLEAN instances with different territories |
| **Role-Based Access** | Channel directors only see their territories |
| **Security** | Users can't access data outside their scope |
| **Flexibility** | Easy to update territories (edit YAML + git) |
| **Auditability** | Git commits provide audit trail of changes |
| **Dynamic Config** | Hot reload = updates without restart |
| **Zero Infrastructure** | No database, no DevOps overhead |

---

## Initiative 3: Cloud-Native Scalability Architecture

**Status:** 📐 Designed, Ready for Implementation  
**Timeline:** Q3-Q4 2026 (enables enterprise SaaS)  
**Priority:** Medium (for future multi-org SaaS)

### Executive Summary

Design multi-org, multi-tenant MCP server that can scale to 100+ users across multiple companies with pluggable config providers.

**Current Limitation:** Single hardcoded config, no user/territory mapping

**Proposed Solution:** User Context Awareness + Pluggable Config Providers

### Architecture Layers

```
MCP Client (LLM)
    ↓
Authentication (SF CLI / Browser Cookie)
    ↓ username
User Context Resolver
    ↓ UserContext {territories, role, partners}
Config Provider (Pluggable)
    ├─ YAML Provider (current)
    ├─ Database Provider (recommended for cloud)
    ├─ Salesforce Custom Object Provider
    └─ API Provider (external service)
    ↓ SalesConfig {targets, fiscal calendar, ...}
Context-Aware Tool Execution
    ↓ (automatically filtered by user scope)
Salesforce API
    ↓ (filtered response)
LLM Client
```

### Pluggable Config Providers

**1. YAML Provider (Current)**
```
Pros: Simple, local, no dependencies
Cons: Not multi-tenant, requires restart for updates
Usage: Development, small deployments
```

**2. Database Provider (Recommended for Cloud)**
```
Pros: Multi-tenant, dynamic, scalable, audit trail
Cons: Requires database, network latency
Usage: Production, multi-user
Schema:
  territories (territory_id, org_id, name, revenue_target_fy27, ...)
  countries (country_id, territory_id, name, ...)
  users (user_id, org_id, username, role, assigned_territories, ...)
```

**3. Salesforce Custom Object Provider**
```
Pros: Single source of truth (Salesforce), real-time updates
Cons: Requires custom objects, API calls
Usage: If territory/target data lives in Salesforce
Custom Objects:
  Territory__c
  Channel_Director_Assignment__c
```

**4. API Provider (Distributed Architecture)**
```
Pros: External service ownership, abstraction
Cons: Network dependency
Usage: Multi-org SaaS deployment
Endpoint: GET /api/config?org_id=...&user_id=...
```

### User/Territory Mapping Model

```
Company: Semperis EMEA
├── Territory: South_Europe
│   ├── Director: Santiago (Italy, Spain, Portugal)
│   └── Director: Maria (Greece, Cyprus, Malta)
├── Territory: Central_Europe
│   ├── Director: Klaus (all countries)
│   └── ...
└── Admin: John (all territories, all countries)
```

### Multi-Org Support

```
Organization A (Semperis)
├── Org ID: 00D5w000004rH0yEAE
├── User: santiago@semperis.com
└── Config: Semperis sales targets

Organization B (Partner Company)
├── Org ID: 00D5w000004rH1zFAE
├── User: john@partner.com
└── Config: Partner sales targets

Same MCP server supports both without conflict!
```

### Request Flow Example

```
1. LLM Client sends: POST /mcp/call
   Headers: Authorization: Bearer <token>
   Body: {"method": "get_revenue", "params": {"period": "THIS_QUARTER"}}

2. Server Authenticates
   ├─ Extracts username: "santiago@semperis.com"
   └─ Gets org_id: "00D5w000004rH0yEAE"

3. Server Resolves User Context
   ├─ Input: username, org_id
   └─ Output: UserContext(
        territories=["South_Europe"],
        countries=["Italy", "Spain", "Portugal"],
        role="channel_director"
      )

4. Server Loads Config
   ├─ Input: user_context
   └─ Output: SalesConfig(territories with targets for South Europe only)

5. Server Injects Context into Tool
   ├─ Calls get_revenue(
        period="THIS_QUARTER",
        user_context=user_context,  # NEW
        config=config               # NEW
      )

6. Tool Executes with Filtering
   ├─ Builds SOQL: WHERE BillingCountry IN ('Italy', 'Spain', 'Portugal')
   ├─ Calls Salesforce
   └─ Returns: {Italy: {...}, Spain: {...}, Portugal: {...}}

7. Response
   Santiago sees only his territories ✅
```

### Implementation Phases

**Phase 1: User Context Framework (2-3 weeks)**
- [ ] Create `UserContext` dataclass
- [ ] Create `UserResolver` abstraction
- [ ] Implement `YAMLUserResolver` (file-based)
- [ ] Update authentication to resolve user context on startup
- [ ] Add user context to request scope

**Phase 2: Config Provider Abstraction (2-3 weeks)**
- [ ] Create `ConfigProvider` abstraction
- [ ] Refactor current YAML loading → `YAMLConfigProvider`
- [ ] Implement `DatabaseConfigProvider` (PostgreSQL)
- [ ] Add config caching and refresh logic
- [ ] Environment-based provider selection

**Phase 3: Tool Integration (2-3 weeks)**
- [ ] Update all tools to accept `user_context` and `config`
- [ ] Add automatic filtering by territory/country/partner
- [ ] Update channel_intelligence.py to use context
- [ ] Add context validation

**Phase 4: Cloud Deployment Support (1-2 weeks)**
- [ ] Multi-org support (different Salesforce orgs)
- [ ] Database schema and migrations
- [ ] API endpoint provider example
- [ ] Docker/Kubernetes deployment guide

**Phase 5: Admin Interface (Optional - Future)**
- [ ] User management API
- [ ] Config management API
- [ ] Audit logging
- [ ] Web UI for configuration

### Deployment Scenarios

**Scenario 1: Single Developer (Current)**
```
Config: YAML
User Resolver: Local YAML
Users: You (admin)
Database: None
```

**Scenario 2: Multi-Territory Company (Small)**
```
Config: YAML (still works)
User Resolver: YAML
Users: 5-10 Channel Directors
Database: Optional
```

**Scenario 3: Enterprise SaaS (Large Scale)**
```
Config: Database
User Resolver: Database + LDAP integration
Users: 100+ across multiple companies
Database: PostgreSQL (required)
```

**Scenario 4: Hybrid (Flexible)**
```
Config: API Provider
User Resolver: API Provider
Users: Flexible
Database: Managed externally
```

### Benefits

| Aspect | Benefit |
|--------|---------|
| **Multi-Tenancy** | Support multiple orgs/companies simultaneously |
| **Role-Based Access** | Channel Directors only see their territories |
| **Security** | Users can't access data outside their scope |
| **Scalability** | Database provider handles 1000s of users |
| **Flexibility** | Swap providers without changing code |
| **Auditability** | Log who accessed what and when |
| **Dynamic Config** | Update targets without restarting server |
| **Cloud-Ready** | Designed for SaaS deployment |

### Backward Compatibility

**If user_context is not provided, assume admin/full access:**

```python
@mcp.tool
async def salesforce_get_revenue(
    period: str,
    user_context: UserContext | None = None,
):
    if user_context is None:
        user_context = UserContext(
            username="system",
            territories=[],  # All
            countries=[],    # All
            partners=[],     # All
            role="admin"
        )
    # Rest of function uses user_context for filtering
```

---

## Consolidated Implementation Timeline

### Q3 2026

**Week 1-2: Planning & Verification**
- Langfuse: Verify governance/RBAC capabilities, check infrastructure
- YAML Scalability: Design users.yaml structure, create sample file
- Cloud Architecture: Confirm deployment scenarios, get stakeholder input

**Week 3-4: PoC Deployment**
- Langfuse: Deploy locally (Docker Compose), test trace ingestion
- YAML Scalability: Implement `UserContext` + `YAMLUserResolver`
- Cloud Architecture: Start Phase 1 (User Context Framework)

**Week 5+: Evaluation & Refinement**
- Langfuse: Evaluate UI, verify governance model, estimate effort
- YAML Scalability: Test with 20 sample users, implement hot reload
- Cloud Architecture: Continue Phase 1-2 integration

### Q4 2026

**Langfuse:**
- Phase 2: Design & Planning
- Phase 3: Production Deployment
- Phase 4: MCP Integration

**YAML Scalability:**
- Phase 3-4: Tool Integration, Hot Reload
- Phase 5: GLEAN Integration testing

**Cloud Architecture:**
- Phase 2-3: Config Provider Abstraction, Tool Integration
- Phase 4: Cloud Deployment Support

### Q1 2027+

**Langfuse:**
- Phase 5-6: LLM Client Integration, Security Review, Launch

**Cloud Architecture:**
- Phase 5 (Optional): Admin Interface

---

## Key Open Questions

### Langfuse
1. What are "sensitive operations" specifically for your org?
2. What governance model fits your org? (by region/partner/role)
3. What LLM Client will be used? (affects tracing capabilities)
4. What infrastructure is available?
5. What's the SLA for Langfuse availability?

### YAML Scalability
1. How does GLEAN pass user identity to MCP? (header/JWT/auth)
2. Will users edit YAML directly, or through admin interface?
3. How frequently do territories/partners change?

### Cloud Architecture
1. Will this be single-org or multi-org SaaS?
2. How are users/territories currently managed? (LDAP/Salesforce/spreadsheet)
3. How many concurrent users do we expect?
4. What's acceptable latency for user resolution? (<500ms)
5. Do we need audit logs of all access?
6. Can infrastructure provide PostgreSQL/MySQL?

---

## Next Steps

1. **Q3 Week 1:** Schedule verification meetings for each initiative
2. **Q3 Week 2:** Approve PoC plans and budgets
3. **Q3 Week 3:** Begin PoC deployments in parallel
4. **Q3 Week 5:** Evaluate results, adjust Q4 plans
5. **Q4:** Execute full implementation phases

---

## Resources

**Langfuse:**
- GitHub: https://github.com/langfuse/langfuse
- Docs: https://langfuse.com/docs
- Self-hosting: https://langfuse.com/docs/deployment/self-host

**Architecture References:**
- 12-factor app: https://12factor.net
- RBAC best practices: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- Multi-tenancy patterns: https://en.wikipedia.org/wiki/Multitenancy
