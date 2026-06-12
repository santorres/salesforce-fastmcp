# Scalability Architecture: Multi-Territory, Multi-User Deployment

## Executive Summary

**Current Problem:**
- Single hardcoded config file (`sales_targets.yaml`) for all users
- No user/territory mapping - anyone using the server sees all territories
- Not suitable for multi-tenant cloud deployment
- Can't distinguish which Channel Director is asking questions

**Proposed Solution:**
- **User Context Awareness** - Identify WHO is authenticated
- **Role-Based Territory Assignment** - Map users to their territory scopes
- **Pluggable Config Providers** - Load config from YAML, database, or API
- **Context-Based Filtering** - Automatically filter data by user's territories
- **Cloud-Native Design** - Multi-tenant SaaS ready

**This document covers:**
1. Architecture design
2. User/territory mapping model
3. Config provider abstraction
4. Implementation roadmap
5. Migration strategy

---

## Part 1: Current State Analysis

### Current Architecture

```
Salesforce MCP Server
├── server.py
│   └── Uses hardcoded ConfigManager
│       └── Loads config/sales_targets.yaml
│           └── Single config for all users
├── channel_intelligence.py
│   └── Uses constants from ci_config.py
│       └── COUNTRIES, PERIODS, DEFAULT_CHANNEL_MANAGER
└── auth_provider.py
    ├── Authenticates user (SF CLI or browser cookie)
    └── Returns username + org info
        └── But doesn't map to territory/role!
```

### Current Limitations

| Aspect | Current | Problem |
|--------|---------|---------|
| **User Identification** | ✅ Have username from auth | ❌ No territory mapping |
| **Territory Scope** | Hardcoded in YAML | ❌ Same for all users |
| **Config Loading** | File-based | ⚠️ Not scalable for 100+ users |
| **Multi-Tenancy** | Not supported | ❌ Single org only |
| **Role-Based Access** | None | ❌ No permission model |
| **Dynamic Config** | No | ⚠️ Requires restart to change targets |

---

## Part 2: Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Client (LLM)                            │
└────────────────────────┬────────────────────────────────────────────┘
                         │ (authenticated request)
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP Server (Cloud)                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 1. Authentication (SF CLI / Browser Cookie)                 │  │
│  │    └─ Extracts: username (e.g., santiago@company.com)       │  │
│  └────────────────────┬─────────────────────────────────────────┘  │
│                       │                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 2. User Context Resolver                                   │  │
│  │    Input: username                                          │  │
│  │    Output: UserContext {                                   │  │
│  │      - username                                            │  │
│  │      - territories: ["South_Europe", "EMEA"]              │  │
│  │      - role: "channel_director"                            │  │
│  │      - partner_filter: ["Accenture", "TCS"]               │  │
│  │    }                                                        │  │
│  └────────────────────┬─────────────────────────────────────────┘  │
│                       │                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 3. Config Provider (Pluggable)                              │  │
│  │    ├─ YAML Provider (current)                              │  │
│  │    ├─ Database Provider (Postgres/MySQL)                  │  │
│  │    ├─ Salesforce Custom Object Provider                   │  │
│  │    └─ API Provider (external service)                     │  │
│  │                                                            │  │
│  │    Loads: SalesConfig {                                  │  │
│  │      - revenue_targets                                    │  │
│  │      - fiscal_calendar                                    │  │
│  │      - partner_mappings                                   │  │
│  │      - [any custom config]                               │  │
│  │    }                                                       │  │
│  └────────────────────┬─────────────────────────────────────────┘  │
│                       │                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 4. Context-Aware Tool Execution                             │  │
│  │    Each tool receives:                                      │  │
│  │    - user_context (territories, role, filters)             │  │
│  │    - config (targets, fiscal calendar)                     │  │
│  │    Automatically filters queries by user's territories     │  │
│  └────────────────────┬─────────────────────────────────────────┘  │
│                       │                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5. Salesforce API (with filtering)                          │  │
│  │    └─ Returns filtered data only for user's territories     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Salesforce Organization                          │
│    (Same for all users, but queries filtered by territory)         │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. User Context (New)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserContext:
    """Represents an authenticated user's scope and permissions."""
    username: str              # e.g., "santiago@company.com"
    user_id: str              # Salesforce User ID or system ID
    territories: list[str]    # e.g., ["South_Europe", "EMEA"]
    role: str                 # e.g., "channel_director", "admin", "analyst"
    partners: list[str]       # Filtered partners, or empty for all
    countries: list[str]      # Filtered countries, or empty for all
    org_id: str              # Salesforce org this user belongs to
    metadata: dict            # Custom metadata (departments, regions, etc.)
```

#### 2. Config Provider Interface (New)

```python
from abc import ABC, abstractmethod

class ConfigProvider(ABC):
    """Pluggable configuration loader."""
    
    @abstractmethod
    async def get_config(self, user_context: UserContext) -> SalesConfig:
        """Load config for a user (may vary by territory/role)."""
        pass
    
    @abstractmethod
    async def refresh_config(self, user_context: UserContext) -> None:
        """Refresh cached config (e.g., after updates)."""
        pass

# Implementations:
class YAMLConfigProvider(ConfigProvider):
    """Load from sales_targets.yaml (current)."""
    pass

class DatabaseConfigProvider(ConfigProvider):
    """Load from PostgreSQL/MySQL."""
    pass

class SalesforceConfigProvider(ConfigProvider):
    """Load from Salesforce custom objects."""
    pass

class APIConfigProvider(ConfigProvider):
    """Load from external API endpoint."""
    pass
```

#### 3. User Resolver (New)

Maps username → UserContext

```python
class UserResolver(ABC):
    """Map authenticated user to context."""
    
    @abstractmethod
    async def resolve_user(self, username: str, org_id: str) -> UserContext:
        """Resolve user context from username."""
        pass

# Implementations:
class LocalUserResolver(UserResolver):
    """Load user mappings from YAML/JSON file."""
    pass

class SalesforceUserResolver(UserResolver):
    """Load from Salesforce custom objects."""
    pass

class LDAPUserResolver(UserResolver):
    """Resolve from corporate LDAP/Active Directory."""
    pass

class APIUserResolver(UserResolver):
    """Call external API to resolve user."""
    pass
```

---

## Part 3: User/Territory Mapping Model

### Scenario: Company with Multiple Territories

```
Company: Semperis EMEA
├── Territory: South_Europe
│   ├── Channel Director: Santiago Tortes (santiago@semperis.com)
│   │   ├── Assigned Countries: Italy, Spain, Portugal
│   │   ├── Assigned Partners: [Accenture, TCS, Inetum]
│   │   └── Can see: All data for these countries/partners only
│   │
│   └── Channel Director: Maria Garcia (maria@semperis.com)
│       ├── Assigned Countries: Greece, Cyprus, Malta
│       ├── Assigned Partners: [Deloitte, PWC]
│       └── Can see: All data for these countries/partners only
│
├── Territory: Central_Europe
│   ├── Channel Director: Klaus Mueller (klaus@semperis.com)
│   │   ├── Assigned Countries: Germany, Austria, Switzerland
│   │   ├── Assigned Partners: [All]
│   │   └── Can see: All Central Europe data
│   │
│   └── ...
│
└── Admin: John Doe (john@semperis.com)
    ├── Role: admin
    ├── Territories: [All]
    ├── Can see: Everything
    └── Can manage: User mappings, config, targets
```

### User Mapping File Format (YAML)

```yaml
# deployment/users.yaml
organizations:
  "00D5w000004rH0yEAE":  # Salesforce Org ID
    name: "Semperis EMEA"
    
    users:
      santiago@semperis.com:
        name: "Santiago Tortes"
        role: "channel_director"
        territories: ["South_Europe"]
        countries: ["Italy", "Spain", "Portugal"]
        partners: []  # Empty = all partners
        metadata:
          department: "EMEA Sales"
          cost_center: "EU-001"
      
      maria@semperis.com:
        name: "Maria Garcia"
        role: "channel_director"
        territories: ["South_Europe"]
        countries: ["Greece", "Cyprus", "Malta"]
        partners: ["Deloitte", "PWC"]
        metadata:
          department: "EMEA Sales"
          cost_center: "EU-002"
      
      klaus@semperis.com:
        name: "Klaus Mueller"
        role: "channel_director"
        territories: ["Central_Europe"]
        countries: []  # Empty = all countries in territory
        partners: []
        metadata:
          department: "EMEA Sales"
          cost_center: "EU-003"
      
      john@semperis.com:
        name: "John Doe"
        role: "admin"
        territories: []  # Empty = all territories
        countries: []    # Empty = all countries
        partners: []     # Empty = all partners
        metadata:
          department: "Management"
```

### Behavior Examples

**User 1: Santiago (Channel Director - South Europe)**
```python
user_context = await user_resolver.resolve_user("santiago@semperis.com", org_id)
# Result:
# UserContext(
#   username="santiago@semperis.com",
#   territories=["South_Europe"],
#   countries=["Italy", "Spain", "Portugal"],
#   partners=[],  # all
#   role="channel_director"
# )

# When Santiago runs: GET /revenue
# Tool automatically filters WHERE Country IN ('Italy', 'Spain', 'Portugal')
```

**User 2: John (Admin)**
```python
user_context = await user_resolver.resolve_user("john@semperis.com", org_id)
# Result:
# UserContext(
#   username="john@semperis.com",
#   territories=[],  # all
#   countries=[],    # all
#   partners=[],     # all
#   role="admin"
# )

# When John runs: GET /revenue
# No filtering - sees all data globally
```

---

## Part 4: Config Provider Architecture

### Provider Selection Logic

```python
config_provider = create_config_provider(
    provider_type=os.getenv("CONFIG_PROVIDER", "yaml"),  # yaml, database, salesforce, api
    config_path=os.getenv("CONFIG_PATH", "config/sales_targets.yaml"),
    database_url=os.getenv("DATABASE_URL"),
    api_endpoint=os.getenv("CONFIG_API_ENDPOINT")
)
```

### Provider Implementations

#### 1. YAML Provider (Current - No Changes)
```
Pros: Simple, local, no dependencies
Cons: Not multi-tenant, requires restart for updates

Usage: Development, small deployments
Environment: CONFIG_PROVIDER=yaml
```

#### 2. Database Provider (Recommended for Cloud)
```
Pros: Multi-tenant, dynamic, scalable, audit trail
Cons: Requires database, network latency

Usage: Production, multi-user
Environment: CONFIG_PROVIDER=database
           DATABASE_URL=postgresql://...
           
Schema:
  territories (territory_id, org_id, name, revenue_target_fy27, ...)
  countries (country_id, territory_id, name, revenue_target_fy27, ...)
  partners (partner_id, territory_id, name, revenue_target, ...)
  users (user_id, org_id, username, role, assigned_territories, ...)
```

#### 3. Salesforce Custom Object Provider
```
Pros: Single source of truth (Salesforce), real-time updates
Cons: Requires custom objects, API calls

Usage: If territory/target data lives in Salesforce
Environment: CONFIG_PROVIDER=salesforce
           
Custom Objects:
  Territory__c (fields: Name, Revenue_Target__c, ...)
  Channel_Director_Assignment__c (fields: User__c, Territory__c, Countries__c, ...)
```

#### 4. API Provider
```
Pros: External service ownership, abstraction
Cons: Network dependency, external service required

Usage: Distributed architecture
Environment: CONFIG_PROVIDER=api
           CONFIG_API_ENDPOINT=https://config-service.company.com/api/config
           
Endpoint: GET /api/config?org_id=...&user_id=...
Response: {territories, targets, fiscal_calendar, ...}
```

---

## Part 5: Request Flow with User Context

### Example: Channel Director Requests Pipeline

```
1. LLM Client sends request
   POST /mcp/call
   Headers: Authorization: Bearer <token>
   Body: {
     "method": "salesforce_get_pipeline",
     "params": {
       "period": "THIS_QUARTER",
       "breakdown": "country"
     }
   }

2. Server Authenticates
   ├─ Extracts username from auth token/session
   │  └─ Result: "santiago@semperis.com"
   │
   └─ Calls auth_provider.get_credentials()
      └─ Result: Credentials(username="santiago@semperis.com", org_id="00D5w000004rH0yEAE")

3. Server Resolves User Context
   ├─ Calls user_resolver.resolve_user("santiago@semperis.com", "00D5w000004rH0yEAE")
   │
   └─ Result: UserContext(
       username="santiago@semperis.com",
       territories=["South_Europe"],
       countries=["Italy", "Spain", "Portugal"],
       partners=[],
       role="channel_director"
     )

4. Server Loads Config
   ├─ Calls config_provider.get_config(user_context)
   │
   └─ Result: SalesConfig(
       territories={
         "South_Europe": {
           "countries": {
             "Italy": {"revenue_target": 825000, ...},
             "Spain": {"revenue_target": 1825000, ...},
             "Portugal": {"revenue_target": 1000000, ...}
           }
         }
       },
       fiscal_calendar={...}
     )

5. Server Injects Context into Tool
   ├─ Calls salesforce_get_pipeline(
       period="THIS_QUARTER",
       breakdown="country",
       user_context=user_context,  # NEW
       config=config                # NEW
     )

6. Tool Executes with Filtering
   ├─ Builds SOQL query
   │  └─ WHERE BillingCountry IN ('Italy', 'Spain', 'Portugal')
   │
   ├─ Calls Salesforce API
   │
   └─ Returns data for Santiago's territories only

7. Response
   {
     "Italy": {
       "pipeline": 1500000,
       "count": 23,
       ...
     },
     "Spain": {
       "pipeline": 3200000,
       "count": 45,
       ...
     },
     "Portugal": {
       "pipeline": 800000,
       "count": 12,
       ...
     }
   }

   Santiago sees only his territories, never sees Greece/Cyprus/Malta data!
```

---

## Part 6: Implementation Roadmap

### Phase 1: User Context Framework (2-3 weeks)
- [ ] Create `UserContext` dataclass
- [ ] Create `UserResolver` abstraction
- [ ] Implement `YAMLUserResolver` (file-based)
- [ ] Update authentication to resolve user context on startup
- [ ] Add user context to request scope (FastMCP)

### Phase 2: Config Provider Abstraction (2-3 weeks)
- [ ] Create `ConfigProvider` abstraction
- [ ] Refactor current YAML loading → `YAMLConfigProvider`
- [ ] Implement `DatabaseConfigProvider` (PostgreSQL)
- [ ] Add config caching and refresh logic
- [ ] Environment-based provider selection

### Phase 3: Tool Integration (2-3 weeks)
- [ ] Update all tools to accept `user_context` and `config`
- [ ] Add automatic filtering by territory/country/partner
- [ ] Update channel_intelligence.py to use context
- [ ] Add context validation (ensure user can access data)

### Phase 4: Cloud Deployment Support (1-2 weeks)
- [ ] Multi-org support (different Salesforce orgs)
- [ ] Database schema and migrations
- [ ] API endpoint provider example
- [ ] Docker/Kubernetes deployment guide

### Phase 5: Admin Interface (Optional - Future)
- [ ] User management API
- [ ] Config management API
- [ ] Audit logging
- [ ] Web UI for configuration

---

## Part 7: Migration Strategy

### Step 1: Backward Compatibility (No Breaking Changes)

```python
# If user_context is not provided, assume admin/full access
@mcp.tool
async def salesforce_get_pipeline(
    period: str,
    breakdown: str = "total",
    user_context: UserContext | None = None,  # Optional, defaults to admin
):
    # If user_context is None, create admin context (full access)
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

### Step 2: Local Testing with YAML

```yaml
# deployment/users.yaml
organizations:
  "00D5w000004rH0yEAE":
    name: "Your Org"
    users:
      santiagot@semperis.com:
        role: "admin"
        territories: []
        countries: []
        partners: []
```

```bash
# Set environment variable
export USER_RESOLVER=yaml
export USER_MAPPING_PATH=deployment/users.yaml

python server.py
```

### Step 3: Migrate to Database (When Ready)

```bash
# Set environment variable
export USER_RESOLVER=database
export DATABASE_URL=postgresql://...

# Run migrations
python deployment/migrate_to_db.py

python server.py
```

---

## Part 8: Benefits and Considerations

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

### Considerations

| Aspect | Consideration |
|--------|---|
| **Performance** | User resolution adds latency; implement caching |
| **Database** | Requires database for production deployments |
| **User Mapping** | Need process to maintain user/territory assignments |
| **Config Sync** | Multiple servers need synchronized config |
| **Audit Trail** | Consider logging all config changes |
| **Testing** | More complex; need fixtures for different users |

---

## Part 9: Example Deployment Scenarios

### Scenario 1: Single Developer (Current)
```
Config: YAML
User Resolver: Local YAML
Users: You (admin)
Database: None

Files:
  config/sales_targets.yaml
  deployment/users.yaml (minimal)
```

### Scenario 2: Multi-Territory Company (Small)
```
Config: YAML (still works)
User Resolver: YAML (file-based)
Users: 5-10 Channel Directors
Database: Optional

Files:
  config/sales_targets.yaml (territories)
  deployment/users.yaml (user assignments)

Updates: Manual edit YAML files, redeploy
```

### Scenario 3: Enterprise SaaS (Large Scale)
```
Config: Database
User Resolver: Database + LDAP integration
Users: 100+ across multiple companies
Database: PostgreSQL (required)

Architecture:
  ├── Config API (reads/writes to database)
  ├── User API (syncs from LDAP/AD)
  ├── Audit API (logs all access)
  └── MCP Server (uses all above)

Updates: Dynamic, no restart needed
```

### Scenario 4: Hybrid (Flexible)
```
Config: API Provider (calls external service)
User Resolver: API Provider (calls user service)
Users: Flexible
Database: Managed externally

Allows: Decoupled architecture, external ownership of config
```

---

## Part 10: Next Steps

1. **Design Review** - Validate this architecture with stakeholders
2. **Phase 1 Implementation** - Start with UserContext and YAML resolver
3. **Testing** - Build test fixtures for different user contexts
4. **Documentation** - Create deployment guides
5. **Pilot** - Test with real channel directors before full deployment

---

## Questions for Discussion

1. **Primary Deployment Model:** Will this be single-org or multi-org SaaS?
2. **User Management:** How are users/territories currently managed? (LDAP, Salesforce, spreadsheet?)
3. **Config Updates:** How often do targets/territories change?
4. **Performance:** What's acceptable latency for user resolution? (must be <500ms)
5. **Audit Requirements:** Do we need audit logs of who accessed what?
6. **Database:** Can infrastructure provide PostgreSQL/MySQL?
7. **Scaling:** How many concurrent users do we expect?

