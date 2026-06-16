# Salesforce MCP Authentication Strategy

## Executive Summary

This document outlines a plan to implement multiple authentication methods for the Salesforce MCP connector while maintaining backward compatibility with the existing browser cookie-based authentication.

**Status**: ✅ **YES, this is 100% possible and backward compatible**

---

## Current State

**Current Auth Method**: Browser Cookie (Bearer Token)
- Credentials: `SALESFORCE_BASE_URL` + `SALESFORCE_ACCESS_TOKEN` (or `SALESFORCE_SID`)
- How it works: User authenticates via browser, copies session cookie/token to env vars
- Fragility: Tokens expire, require manual refresh

---

## Proposed Auth Methods

### 1. **SF CLI Authentication** (NEW - Recommended for developers)

**How it works:**
- User runs: `sf org login web` (already authenticated via SF CLI)
- MCP server queries SF CLI for the access token on startup
- Flow:
  ```
  MCP Server (Python)
  ├─> Execute: sf org list --json
  ├─> Parse result to get org info
  ├─> Extract: instanceUrl, username
  ├─> Execute: sf org auth show-access-token -o <username>
  └─> Cache token in memory for session
  ```

**Advantages:**
- ✅ No manual token management
- ✅ Automatic token refresh (SF CLI handles it)
- ✅ Leverages existing SF CLI setup
- ✅ Multiple org support (can select which org to use)
- ✅ Most secure (tokens never stored in env vars)

**Implementation Requirements:**
- Subprocess calls to SF CLI (`sf org list --json`, `sf org auth show-access-token`)
- Auto-detect authenticated orgs
- Allow user to specify org via env var (default to first or default dev hub)
- Handle SF CLI not installed gracefully

**Data Flow:**
```
SF CLI Database (encrypted by OS)
         ↓
    [sf commands]
         ↓
   Python subprocess
         ↓
  In-memory cache (NEVER persisted)
         ↓
   SalesforceClient
```

---

### 2. **Browser Cookie Auth** (EXISTING - Keep for backward compatibility)

**Current implementation**: Already working
- User provides: `SALESFORCE_BASE_URL` + `SALESFORCE_ACCESS_TOKEN`
- No changes needed to support this ongoing

**Advantages:**
- ✅ Already implemented
- ✅ Works for quick testing/debugging
- ✅ Useful for CI/CD environments

**Limitations:**
- ❌ Tokens expire
- ❌ Manual refresh required
- ❌ Less secure (tokens in env vars)

---

### 3. **Direct OAuth** (FUTURE - Phase 2)

**How it would work:**
- Implement OAuth 2.0 Web Server Flow
- MCP server acts as OAuth client
- User grants consent once, automatic token refresh thereafter
- Tokens stored securely (e.g., system keychain)

**Timeline**: Post Phase 1 (lower priority for now)

---

## Architecture Design

### Authentication Provider Interface

```python
# Abstract base class for all auth methods
class AuthProvider(ABC):
    @abstractmethod
    async def get_credentials(self) -> Credentials:
        """Return (base_url, access_token)"""
        pass
    
    @abstractmethod
    async def refresh_if_needed(self) -> bool:
        """Refresh token if expired. Return True if refreshed."""
        pass

class Credentials(NamedTuple):
    base_url: str
    access_token: str
```

### Concrete Implementations

```python
# 1. SF CLI Auth Provider
class SFCliAuthProvider(AuthProvider):
    async def get_credentials(self) -> Credentials:
        # subprocess.run(['sf', 'org', 'list', '--json'])
        # subprocess.run(['sf', 'org', 'auth', 'show-access-token', '-o', username])
        pass

# 2. Browser Cookie Auth Provider
class BrowserCookieAuthProvider(AuthProvider):
    async def get_credentials(self) -> Credentials:
        # Read from env vars SALESFORCE_BASE_URL, SALESFORCE_ACCESS_TOKEN
        pass

# 3. Direct OAuth Auth Provider (Future)
class DirectOAuthAuthProvider(AuthProvider):
    async def get_credentials(self) -> Credentials:
        # OAuth 2.0 flow
        pass

# Factory function
def create_auth_provider(method: str) -> AuthProvider:
    if method == "sf_cli":
        return SFCliAuthProvider()
    elif method == "browser_cookie":
        return BrowserCookieAuthProvider()
    else:
        raise ValueError(f"Unknown auth method: {method}")
```

### Configuration

**Environment Variable**: `SALESFORCE_AUTH_METHOD`

```bash
# Option 1: Use SF CLI (recommended)
export SALESFORCE_AUTH_METHOD=sf_cli
export SALESFORCE_ORG_USERNAME=santiagot@semperis.com  # Optional, defaults to first auth'd org

# Option 2: Use browser cookie (existing)
export SALESFORCE_AUTH_METHOD=browser_cookie
export SALESFORCE_BASE_URL=https://semperis.my.salesforce.com
export SALESFORCE_ACCESS_TOKEN=<token>

# Option 3: Auto-detect (default behavior)
# Falls back: sf_cli -> browser_cookie -> error
export SALESFORCE_AUTH_METHOD=auto
```

---

## Implementation Plan

### Phase 1: Core Auth Infrastructure (Non-Breaking)

1. **Create `auth_provider.py`** (new file)
   - Abstract `AuthProvider` base class
   - `Credentials` NamedTuple
   - Factory function `create_auth_provider()`
   - Implementation: `BrowserCookieAuthProvider` (existing logic)
   - Implementation: `SFCliAuthProvider` (new)

2. **Modify `server.py`**
   - Replace global `_client` initialization with auth provider
   - Call `auth_provider.get_credentials()` on startup
   - Pass credentials to `SalesforceClient`
   - Keep all existing MCP tool signatures identical

3. **Modify `salesforce_client.py`**
   - No breaking changes
   - Still accepts `base_url` + `access_token` in `__init__`
   - Auth provider handles credential sourcing

4. **Update `.env.example`**
   - Add `SALESFORCE_AUTH_METHOD=auto`
   - Add `SALESFORCE_ORG_USERNAME=` (for SF CLI)
   - Keep existing vars for backward compatibility

### Phase 2: Testing & Validation

1. Test SF CLI auth method with multiple orgs
2. Test browser cookie auth method (existing behavior)
3. Test auto-detection fallback
4. Verify no breaking changes to MCP tools
5. Test in CI/CD environment (cookie method)

### Phase 3: Documentation

1. Update README with auth setup instructions
2. Create per-auth-method quick-start guides
3. Document troubleshooting for each method
4. Add security best practices

---

## Backward Compatibility Guarantee

✅ **NO breaking changes**

- Existing `SALESFORCE_BASE_URL` + `SALESFORCE_ACCESS_TOKEN` setup continues to work
- `SALESFORCE_AUTH_METHOD=browser_cookie` is the default if env vars are present
- All MCP tool signatures unchanged
- All existing integrations continue to work

---

## Security Considerations

### SF CLI Auth Provider
- ✅ Tokens stored encrypted by OS/SF CLI
- ✅ Tokens never persisted to disk by MCP
- ✅ Tokens cached only in Python memory for session
- ✅ Automatic expiration handling

### Browser Cookie Auth Provider
- ⚠️ Tokens stored in environment variables (less secure)
- ✅ Use only for development/CI where unavoidable
- ✅ Consider using system keychain for sensitive environments

### Recommendations
1. Use SF CLI method in development (most secure)
2. Use browser cookie method in CI only if SF CLI not available
3. Never commit tokens to Git (add to `.gitignore`)
4. Log token usage but never log token values

---

## Error Handling & Fallbacks

```
Initialize Auth
├─ Try SF CLI first (if SF_AUTH_METHOD=sf_cli or auto)
│  ├─ SF CLI installed? → Yes: parse orgs
│  ├─ Org available? → Yes: get token
│  └─ Success? → Cache token, continue
│
├─ Try Browser Cookie (if SF_AUTH_METHOD=browser_cookie or auto)
│  ├─ Env vars set? → Yes: validate
│  ├─ Token valid? → Yes: continue
│  └─ Success? → Continue
│
└─ Error: No valid auth method available
   → Print helpful message with setup instructions
   → Exit with code 1
```

---

## Files to Create/Modify

### New Files
- `auth_provider.py` - Authentication abstraction layer
- `AUTHENTICATION_STRATEGY.md` - This document

### Modified Files
- `server.py` - Use auth provider instead of env vars
- `salesforce_client.py` - No changes (keep as-is)
- `.env.example` - Add new auth method options
- `.gitignore` - Already excludes `.env`
- `README.md` - Add auth setup instructions

### Unchanged Files
- All MCP tool implementations
- All business logic

---

## Testing Strategy

### Unit Tests
```python
# test_auth_provider.py
- Test BrowserCookieAuthProvider with env vars
- Test SFCliAuthProvider with mocked subprocess
- Test factory function
- Test error handling
```

### Integration Tests
```bash
# Test with actual SF CLI
export SALESFORCE_AUTH_METHOD=sf_cli
python server.py
# Verify: connects to Salesforce successfully

# Test with browser cookie (existing)
export SALESFORCE_AUTH_METHOD=browser_cookie
export SALESFORCE_BASE_URL=...
export SALESFORCE_ACCESS_TOKEN=...
python server.py
# Verify: connects to Salesforce successfully

# Test auto-detection
export SALESFORCE_AUTH_METHOD=auto
# (with SF CLI installed)
python server.py
# Verify: uses SF CLI method

# Test auto-detection fallback
unset SALESFORCE_AUTH_METHOD
# (with only browser cookie env vars)
python server.py
# Verify: uses browser cookie method
```

---

## Questions for Discussion

1. **Default behavior**: Should `auto` detect SF CLI first, or allow user preference?
   - **Recommendation**: Detect SF CLI first (more secure), fall back to browser cookie

2. **Multiple orgs**: If user has multiple SF CLI orgs, which to use?
   - **Recommendation**: Use default dev hub if set, otherwise first org, allow override via env var

3. **Token refresh**: Should MCP handle token refresh or let SF CLI/browser handle it?
   - **Recommendation**: SF CLI handles refresh automatically; browser cookie tokens refresh via browser

4. **CI/CD**: Which auth method for CI pipelines?
   - **Recommendation**: Browser cookie (explicit token in secrets), SF CLI if available

---

## Rollout Plan

1. **Week 1**: Implement Phase 1 (auth_provider.py + modifications)
2. **Week 1**: Test Phase 2 (validation across methods)
3. **Week 2**: Documentation Phase 3
4. **Week 2**: Commit & deploy
5. **Future**: Implement Phase 3 (Direct OAuth)

---

## Success Criteria

- ✅ SF CLI auth method works for development
- ✅ Browser cookie auth method still works (backward compatible)
- ✅ No breaking changes to existing setups
- ✅ Auto-detection works as expected
- ✅ All MCP tools function identically across auth methods
- ✅ Error messages are helpful
- ✅ Documentation is clear

