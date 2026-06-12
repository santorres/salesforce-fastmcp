# Testing From Zero: Step-by-Step Guide

## Prerequisites
You have:
- ✅ Salesforce CLI installed (`sf org login web` already run)
- ✅ No `.env` file (or one with old browser cookie auth)

## Test Scenario: Fresh Start (RECOMMENDED)

### Step 1: Remove/Clear Old .env (optional, but clearest test)

```bash
cd /Users/santiagot/Applications/salesforce-fastmcp

# Option A: Remove old .env completely
rm .env

# Option B: Create minimal .env with only MCP settings
cat > .env << 'EOF'
MCP_TRANSPORT=stdio
MCP_HOST=0.0.0.0
MCP_PORT=8000
EOF
```

### Step 2: Verify SF CLI is Ready

```bash
# Check SF CLI works
sf org list

# Should show your authenticated org
```

### Step 3: Run Server (It Will Auto-Detect SF CLI!)

```bash
python server.py
```

**What happens automatically:**

1. Server starts
2. `initialize_client()` is called during startup
3. `create_auth_provider()` checks `SALESFORCE_AUTH_METHOD` env var
4. Env var not set → defaults to `"auto"`
5. Auto-detection runs:
   - ✓ Checks: Is SF CLI available?
   - ✓ Answer: YES
   - ✓ Uses: SFCliAuthProvider
6. SF CLI provider automatically:
   - Queries: `sf org list --json`
   - Finds your authenticated org
   - Retrieves: Access token via `sf org auth show-access-token`
   - Constructs: Correct base URL with API version
   - Initializes SalesforceClient
7. Server ready and authenticated! ✓

### Step 4: Check Server Output

You should see logs like:

```
2026-06-12 22:30:06 | Initializing authentication provider...
2026-06-12 22:30:06 | Retrieving credentials...
2026-06-12 22:30:11 | SF CLI auth: using org santiagot@semperis.com (00D5w000004rH0yEAE)
2026-06-12 22:30:11 | Creating Salesforce client (auth: sf_cli)
2026-06-12 22:30:11 | Authentication successful for santiagot@semperis.com
2026-06-12 22:30:12 | Server ready for user: santiagot@semperis.com
```

**✅ SUCCESS!** Server auto-detected SF CLI and is ready.

---

## Test Scenario 2: Explicit SF CLI (More Verbose)

To be 100% explicit about using SF CLI:

```bash
# Create .env
cat > .env << 'EOF'
SALESFORCE_AUTH_METHOD=sf_cli
SALESFORCE_ORG_USERNAME=santiagot@semperis.com

MCP_TRANSPORT=stdio
MCP_HOST=0.0.0.0
MCP_PORT=8000
EOF

# Run server
python server.py
```

**Behavior:** Same as fresh start, but you're explicitly telling it to use SF CLI.

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
START: python server.py (no .env or minimal .env)
  ↓
initialize_client() called
  ↓
create_auth_provider() called with no explicit method
  ↓
Check SALESFORCE_AUTH_METHOD env var
  ├─ If set: Use that method
  └─ If NOT set: Default to "auto"
  ↓
Auto-detection logic:
  ├─ Is SF CLI available?
  │  ├─ YES → Use SFCliAuthProvider ✓
  │  └─ NO → Check browser cookie env vars
  │     ├─ Set → Use BrowserCookieAuthProvider ✓
  │     └─ NOT set → Error (provide setup instructions)
  ↓
Get credentials:
  ├─ SF CLI: Query `sf org list` → get token → construct URL
  ├─ Browser Cookie: Read from env vars
  ↓
Initialize SalesforceClient with credentials
  ↓
Server ready! ✓
```

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

**To test from zero:**

```bash
# Option 1: Simplest (let it auto-detect)
cd /Users/santiagot/Applications/salesforce-fastmcp
rm .env  # optional, removes old config
python server.py

# Option 2: With minimal config
echo "MCP_TRANSPORT=stdio" > .env
python server.py
```

**That's it!** The server will:
1. See that SF CLI is available ✓
2. Query SF CLI for your authenticated org ✓
3. Retrieve your access token ✓
4. Connect to Salesforce ✓
5. Start serving MCP requests ✓

**No manual token copying, no env vars to set, no configuration needed!** 🚀

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
