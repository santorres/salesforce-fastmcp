# Testing From Zero: Step-by-Step Guide

## Prerequisites
You have:
- ✅ Salesforce CLI installed (`sf org login web` already run)
- ✅ Existing `.env` file with MCP and old browser cookie settings

## Test Scenario: Fresh Start (RECOMMENDED) - Keep .env, Invalidate Token

### Step 1: Update .env to Use Auto-Detection

Edit your existing `.env` file to enable auto-detection:

```bash
cd /Users/santiagot/Applications/salesforce-fastmcp

# Edit .env and make these changes:
cat > .env << 'EOF'
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Salesforce Authentication
# Set auth method to auto-detect (tries SF CLI first, then browser cookie)
SALESFORCE_AUTH_METHOD=auto

# Browser cookie method (only used if SF CLI not available)
# Keep these for fallback, but SF CLI will be used if available
# Uncomment and set a real token only if SF CLI is not available
# SALESFORCE_SID=INVALID_TOKEN
# SALESFORCE_BASE_URL=https://semperis.my.salesforce.com/services/data/v62.0

# For explicit SF CLI with specific org, uncomment and set:
# SALESFORCE_ORG_USERNAME=santiagot@semperis.com
EOF
```

**Why this works:**
- `SALESFORCE_AUTH_METHOD=auto` tells server to auto-detect
- Old `SALESFORCE_SID` is commented out (invalid/expired token)
- Browser cookie env vars are not set or invalid
- SF CLI IS available → auto-detection will use SF CLI ✓

### Step 2: Verify SF CLI is Ready

```bash
# Check SF CLI works and you have authenticated orgs
sf org list

# Should show your authenticated org(s)
```

### Step 3: Run Server (It Will Auto-Detect SF CLI!)

```bash
python server.py
```

**What happens automatically:**

1. Server starts
2. Loads `.env` file (has `SALESFORCE_AUTH_METHOD=auto`)
3. `initialize_client()` is called during startup
4. `create_auth_provider("auto")` is called
5. Auto-detection runs:
   - Checks: Is SF CLI available? → YES ✓
   - Checks: Are browser cookie env vars valid? → NO (commented out)
   - Uses: SFCliAuthProvider ✓
6. SF CLI provider automatically:
   - Queries `sf org list --json`
   - Finds your authenticated org
   - Retrieves access token via `sf org auth show-access-token`
   - Constructs correct base URL with API version
   - Initializes SalesforceClient
7. Server ready and authenticated! ✓

### Step 4: Check Server Output

You should see logs like:

```
2026-06-12 22:44:07 | Initializing authentication provider...
2026-06-12 22:44:08 | Retrieving credentials...
2026-06-12 22:44:13 | SF CLI auth: using org santiagot@semperis.com (00D5w000004rH0yEAE)
2026-06-12 22:44:13 | Creating Salesforce client (auth: sf_cli)
2026-06-12 22:44:13 | Authentication successful for santiagot@semperis.com
```

**SUCCESS!** Server auto-detected SF CLI and bypassed the invalid browser cookie token!

---

## Test Scenario 2: Explicit SF CLI (More Verbose)

To be more explicit about using SF CLI, uncomment in `.env`:

```bash
# In .env, uncomment these lines:
SALESFORCE_AUTH_METHOD=sf_cli

# Optionally specify org if you have multiple:
# SALESFORCE_ORG_USERNAME=santiagot@semperis.com

# Run server
python server.py
```

**Behavior:** Explicitly uses SF CLI (skips auto-detection).

---

## Test Scenario 3: Fallback to Browser Cookie (if SF CLI unavailable)

If SF CLI is not available or you prefer to use a stored token:

```bash
# Get token from SF CLI (do this once)
sf org auth show-access-token -o santiagot@semperis.com

# Create .env with the token
cat > .env << 'EOF'
SALESFORCE_AUTH_METHOD=browser_cookie
SALESFORCE_BASE_URL=https://semperis.my.salesforce.com/services/data/v66.0
SALESFORCE_ACCESS_TOKEN=<paste_your_token_here>

MCP_TRANSPORT=stdio
MCP_HOST=0.0.0.0
MCP_PORT=8000
EOF

# Run server
python server.py
```

**Behavior:** Uses the token from env vars instead of SF CLI.

---

## Quick Verification Test (Without Running Server)

To verify everything works without actually starting the server:

```bash
cd /Users/santiagot/Applications/salesforce-fastmcp

python3 << 'PYEOF'
import asyncio
import os

# Clear any old Salesforce env vars (simulate fresh start)
for key in list(os.environ.keys()):
    if 'SALESFORCE' in key:
        del os.environ[key]

async def test():
    from server import initialize_client, get_client
    
    print("Testing auto-detection and initialization...\n")
    
    await initialize_client()
    print("✓ Client initialized\n")
    
    client = get_client()
    print(f"✓ Base URL: {client.base_url}")
    print(f"✓ Token (first 50 chars): {client.access_token[:50]}...\n")
    
    # Try a simple query to verify it works
    print("Testing Salesforce connectivity...")
    result = await client.query("SELECT COUNT() FROM Account")
    print(f"✓ Query successful!")
    print(f"✓ Total accounts: {result['totalSize']}\n")
    
    print("✅ ALL TESTS PASSED - Everything is working!")

asyncio.run(test())
PYEOF
```

**Expected output:**
```
Testing auto-detection and initialization...

✓ Client initialized

✓ Base URL: https://semperis.my.salesforce.com/services/data/v66.0
✓ Token (first 50 chars): 00D5w000004rH0y!AQEAQEULLrK2ayHqqdhfBgDvQJMgFeGT...

Testing Salesforce connectivity...
✓ Query successful!
✓ Total accounts: 48948

✅ ALL TESTS PASSED - Everything is working!
```

---

## Authentication Flow Diagram

```
START: python server.py
  ↓
Load .env file
  ↓
initialize_client() called
  ↓
create_auth_provider() checks SALESFORCE_AUTH_METHOD
  ├─ If set to "sf_cli": Use SFCliAuthProvider ✓
  ├─ If set to "browser_cookie": Use BrowserCookieAuthProvider ✓
  ├─ If set to "auto": Auto-detect (see below)
  └─ If NOT set: Default to "auto"
  ↓
Auto-detection logic (when SALESFORCE_AUTH_METHOD=auto):
  ├─ Is SF CLI available?
  │  ├─ YES → Use SFCliAuthProvider ✓
  │  │         (ignores invalid/expired browser cookie tokens)
  │  └─ NO → Check browser cookie env vars
  │     ├─ Valid → Use BrowserCookieAuthProvider ✓
  │     └─ Invalid/NOT set → Error with setup instructions
  ↓
Get credentials from selected provider:
  ├─ SF CLI: Query `sf org list` → get token → construct URL
  ├─ Browser Cookie: Read from env vars
  ↓
Initialize SalesforceClient with credentials
  ↓
Server ready! ✓
```

**In your case:**
- `.env` has `SALESFORCE_AUTH_METHOD=auto`
- `SALESFORCE_SID` is commented out (invalid)
- SF CLI is available
- Result: Uses SF CLI auth, ignores invalid token ✓

---

## Summary Table

| Scenario | .env | Behavior | Result |
|----------|------|----------|--------|
| **Fresh Start** | None or minimal | Auto-detects SF CLI | ✅ Uses SF CLI |
| **Explicit SF CLI** | `SALESFORCE_AUTH_METHOD=sf_cli` | Uses SF CLI | ✅ Uses SF CLI |
| **Explicit Auto** | `SALESFORCE_AUTH_METHOD=auto` | Auto-detects | ✅ Uses SF CLI (or fallback) |
| **Browser Cookie** | Token in env vars | Uses env vars | ✅ Uses token |
| **Existing Setup** | Old .env file | Uses whatever is set | ✅ Still works |

---

## The Simple Answer

**To test from zero with your existing `.env`:**

```bash
# Option 1: Simplest (keep .env, enable auto-detect)
cd /Users/santiagot/Applications/salesforce-fastmcp

# Edit .env: 
# - Add: SALESFORCE_AUTH_METHOD=auto
# - Comment out: SALESFORCE_SID and SALESFORCE_BASE_URL

python server.py

# Option 2: Even simpler (if .env already has SALESFORCE_AUTH_METHOD=auto)
python server.py
```

**That's it!** The server will:
1. Load `.env` with `SALESFORCE_AUTH_METHOD=auto`
2. See that SF CLI is available ✓
3. Ignore the commented-out/invalid browser cookie token
4. Query SF CLI for your authenticated org ✓
5. Retrieve your access token ✓
6. Connect to Salesforce ✓
7. Start serving MCP requests ✓

**No token refresh needed, automatic, secure!** 🚀

---

## Troubleshooting

### Error: "No valid authentication method available"

**Cause:** No SF CLI and no browser cookie env vars

**Fix:**
```bash
# Install and authenticate SF CLI
sf org login web

# Or set browser cookie env vars
export SALESFORCE_BASE_URL=...
export SALESFORCE_ACCESS_TOKEN=...
```

### Error: "SF CLI not found"

**Cause:** SF CLI not installed

**Fix:**
```bash
# Install via Homebrew
brew install salesforce-cli

# Then authenticate
sf org login web
```

### Server doesn't start with existing .env

**Cause:** Old .env has incorrect settings

**Fix:**
```bash
# Backup old config
mv .env .env.backup

# Start fresh (auto-detect)
python server.py
```

---

## Next Steps

1. Follow **Test Scenario 1: Fresh Start** above
2. Verify logs show SF CLI auth
3. Run the verification test script
4. Start using the server! ✅
