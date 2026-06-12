# Authentication Quick Start Guide

## Overview

This MCP connector supports three authentication methods:

1. **SF CLI (Recommended)** - Secure, automatic token refresh
2. **Browser Cookie (Fallback)** - For development/CI environments  
3. **Direct OAuth (Future)** - Coming in Phase 2

## Method 1: SF CLI Authentication (RECOMMENDED)

### Setup (One-time)

```bash
# 1. Install Salesforce CLI if you haven't already
# macOS (via Homebrew):
brew install salesforce-cli

# Or from: https://developer.salesforce.com/tools/salesforcecli

# 2. Authenticate with your Salesforce org
sf org login web

# 3. Follow the browser prompt to grant access
```

### Usage

```bash
# .env or environment
export SALESFORCE_AUTH_METHOD=sf_cli
# Optional: specify which org to use (if you have multiple)
# export SALESFORCE_ORG_USERNAME=your.email@company.com

# Run the server
python server.py
```

### Advantages
✅ No manual token management  
✅ Automatic token refresh  
✅ Most secure (tokens stored encrypted by OS)  
✅ No tokens in environment variables  

---

## Method 2: Browser Cookie Authentication (Backward Compatible)

### Setup

```bash
# 1. Log into your Salesforce org in the browser
# https://your-instance.my.salesforce.com

# 2. Get the session ID from browser cookies or use SF CLI to get the token:
sf org auth show-access-token -o your.email@company.com

# 3. Create .env file or set environment variables
export SALESFORCE_AUTH_METHOD=browser_cookie
export SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com/services/data/v66.0
export SALESFORCE_ACCESS_TOKEN=<paste_token_here>

# 4. Run the server
python server.py
```

### Advantages
✅ Works for development  
✅ Backward compatible with existing setups  
✅ Good for CI/CD (store token in secrets manager)  

### Limitations
⚠️ Tokens expire (must be refreshed manually)  
⚠️ Tokens stored in environment variables (less secure)  

---

## Method 3: Auto-Detection (Default)

If you don't set `SALESFORCE_AUTH_METHOD`, the server will auto-detect:

```bash
# No explicit auth method set - auto-detect
# 1. Check if SF CLI is available → use SF CLI auth
# 2. Check if browser cookie env vars are set → use browser cookie
# 3. Fail with helpful error message
```

```bash
# .env
SALESFORCE_AUTH_METHOD=auto
# (optional) SALESFORCE_ORG_USERNAME=your.email@company.com
```

**Recommended for most users**

---

## Configuration Reference

### Environment Variables

#### SF CLI Auth
```bash
SALESFORCE_AUTH_METHOD=sf_cli

# Optional: specify org (defaults to first authenticated)
SALESFORCE_ORG_USERNAME=santiagot@semperis.com

# Optional: custom path to sf executable (default: 'sf')
SALESFORCE_CLI_PATH=/custom/path/to/sf
```

#### Browser Cookie Auth
```bash
SALESFORCE_AUTH_METHOD=browser_cookie

# Required for browser cookie method
SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com/services/data/v66.0
SALESFORCE_ACCESS_TOKEN=<your_access_token>

# Alternative names (both work)
# SALESFORCE_SID=<your_session_id>
```

#### Auto-Detection (Default)
```bash
SALESFORCE_AUTH_METHOD=auto
# Tries SF CLI first, falls back to browser cookie
```

---

## Troubleshooting

### "No valid authentication method available"

**Solution:**
```bash
# Install SF CLI and authenticate
sf org login web

# Then run server with auto-detect
export SALESFORCE_AUTH_METHOD=auto
python server.py
```

### "SF CLI not found"

**Solution:**
```bash
# Install Salesforce CLI
brew install salesforce-cli

# Or download from: https://developer.salesforce.com/tools/salesforcecli

# Then authenticate
sf org login web
```

### "Org 'email@example.com' not found in SF CLI"

**Solution:**
```bash
# List authenticated orgs
sf org list

# Use one of the usernames from the output
export SALESFORCE_ORG_USERNAME=santiagot@semperis.com

# Or just use auto-detect (no username needed)
export SALESFORCE_AUTH_METHOD=auto
```

### "Access token expired"

**Solution (Browser Cookie method only):**
```bash
# Get a new token
sf org auth show-access-token -o your.email@company.com

# Update your .env
export SALESFORCE_ACCESS_TOKEN=<new_token>
```

**Note:** SF CLI method doesn't require this - tokens refresh automatically!

### "Invalid instance URL format"

**Solution:**
```bash
# Correct format includes the /services/data/vXX.X path
SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com/services/data/v66.0

# Incorrect (missing path):
# SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com
```

---

## .env File Template

```bash
# Authentication method (recommended: auto)
SALESFORCE_AUTH_METHOD=auto

# ============ SF CLI Authentication ============
# (No config needed - uses SF CLI automatically)
# Optional: specify org if you have multiple
# SALESFORCE_ORG_USERNAME=your.email@company.com

# ============ Browser Cookie (Fallback) ============
# Only needed if SF CLI is not available
# SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com/services/data/v66.0
# SALESFORCE_ACCESS_TOKEN=your_access_token_here

# ============ Server Configuration ============
MCP_TRANSPORT=stdio
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_LOG_FILE=mcp_requests.log
```

---

## Testing Your Setup

```bash
# Test SF CLI auth
python3 << 'EOF'
import asyncio
from auth_provider import create_auth_provider

async def test():
    provider = create_auth_provider()
    creds = await provider.get_credentials()
    print(f"✓ Auth method: {creds.auth_method}")
    print(f"✓ Org: {creds.username}")
    print(f"✓ URL: {creds.base_url}")

asyncio.run(test())
EOF
```

---

## Security Best Practices

1. **Use SF CLI when possible**
   - Most secure - tokens never stored in env vars
   - Automatic refresh - no manual token management

2. **For Browser Cookie method:**
   - Never commit tokens to Git
   - Use `.env` file (ignored by Git)
   - Store in secrets manager for CI/CD

3. **Keep tokens secret**
   - Don't share tokens
   - Don't log token values
   - Regenerate if compromised

---

## For CI/CD Environments

**Option 1: Use Browser Cookie (most compatible)**
```bash
# In your CI/CD secrets:
SALESFORCE_AUTH_METHOD=browser_cookie
SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com/services/data/v66.0
SALESFORCE_ACCESS_TOKEN=<token_from_secrets>
```

**Option 2: Use SF CLI (if available)**
```bash
# Install SF CLI in your CI pipeline
# Authenticate to org
# Let auto-detect handle the rest
export SALESFORCE_AUTH_METHOD=auto
```

---

## Next Steps

1. Choose your authentication method above
2. Follow the setup instructions
3. Test with the test script above
4. Review `AUTHENTICATION_STRATEGY.md` for more details

**Questions?** Check the strategy document or run with `--help`
