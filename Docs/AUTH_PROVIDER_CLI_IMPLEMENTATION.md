# Auth Provider CLI Implementation Guide

**Objective**: Integrate auth_provider.py into CLI to remove load_dotenv()  
**Effort**: 1 hour  
**Complexity**: Simple  
**Risk**: Very Low

---

## Overview

This guide shows you exactly how to modify `cli/channel_cli.py` to use the existing `auth_provider.py` instead of `load_dotenv()`.

---

## File to Modify

**File**: `cli/channel_cli.py`  
**Current Lines**: 23-42, 289-292  
**Changes**: 4 modifications

---

## Modification 1: Update Imports (Lines 23-37)

### Current Code

```python
import asyncio
import json
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesforce_client import SalesforceClient
import channel_intelligence as ci

load_dotenv()
```

### Updated Code

```python
import asyncio
import json
import sys
import logging
from pathlib import Path

import click

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesforce_client import SalesforceClient
import channel_intelligence as ci
from auth_provider import create_auth_provider

# Configure logging
logger = logging.getLogger(__name__)

# Global auth provider and credentials
_auth_provider = None
_credentials = None
```

### What Changed

**REMOVED**:
- `from dotenv import load_dotenv`
- `load_dotenv()` call

**ADDED**:
- `import logging`
- `from auth_provider import create_auth_provider`
- `_auth_provider = None`
- `_credentials = None`
- Logger setup

---

## Modification 2: Add Auth Initialization Function

### Add This New Function (Before get_sf())

```python
async def _initialize_auth():
    """Initialize authentication using auth_provider.
    
    Uses SF CLI if available, falls back to .env environment variables.
    """
    global _auth_provider, _credentials
    
    try:
        _auth_provider = create_auth_provider()
        _credentials = await _auth_provider.get_credentials()
        
        logger.debug(
            f"Authentication successful: "
            f"{_credentials.auth_method} (user: {_credentials.username or 'unknown'})"
        )
    except Exception as e:
        logger.error(f"Authentication initialization failed: {e}")
        raise
```

---

## Modification 3: Update get_sf() Function (Lines 40-42)

### Current Code

```python
def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation."""
    return SalesforceClient()
```

### Updated Code

```python
def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation using secure authentication.
    
    Returns a Salesforce client configured with credentials from either
    SF CLI (if available) or environment variables (.env file).
    """
    if _credentials is None:
        raise click.ClickException(
            "Authentication not initialized. "
            "This should not happen - auth should be initialized on CLI startup."
        )
    
    return SalesforceClient(
        base_url=_credentials.base_url,
        access_token=_credentials.access_token
    )
```

### What Changed

**BEFORE**: Relied on environment variables loaded by load_dotenv()  
**AFTER**: Uses credentials object initialized via auth_provider

---

## Modification 4: Update CLI Group and Add Auth Initialization (Lines 289-292)

### Current Code

```python
@click.group()
def cli():
    """Channel Intelligence CLI — Salesforce analytics from the command line."""
    pass
```

### Updated Code

```python
@click.group()
def cli():
    """Channel Intelligence CLI — Salesforce analytics from the command line."""
    # Initialize authentication when CLI starts
    try:
        asyncio.run(_initialize_auth())
    except Exception as e:
        raise click.ClickException(
            f"Failed to initialize authentication: {e}\n\n"
            "Please ensure one of the following:\n"
            "  1. Salesforce CLI is installed and authenticated:\n"
            "     https://developer.salesforce.com/tools/salesforcecli\n"
            "     Run: sf org login web\n\n"
            "  2. Or set environment variables:\n"
            "     export SALESFORCE_BASE_URL=https://your-org.salesforce.com/services/data/v59.0\n"
            "     export SALESFORCE_ACCESS_TOKEN=<your_token>\n\n"
            "For more info, see: AUTHENTICATION_QUICKSTART.md"
        )
```

### What Changed

**BEFORE**: No initialization, credentials loaded by load_dotenv()  
**AFTER**: Explicitly initializes auth when CLI starts, with helpful error message

---

## Summary of Changes

| Section | Change | Lines |
|---------|--------|-------|
| Imports | Remove dotenv, add auth_provider | 23-35 |
| Globals | Add _auth_provider, _credentials | 36-37 |
| Function | Add _initialize_auth() | (new) |
| Function | Update get_sf() | 40-55 (new) |
| Decorator | Update cli() with init | 289-310 (new) |

**Total Changes**: 5 code blocks  
**Total Lines Changed**: ~50 lines  
**Total Lines Added/Removed**: ~30 net lines

---

## Complete Modified File Section

Here's what the top of `cli/channel_cli.py` should look like after all changes:

```python
#!/usr/bin/env python3
"""
Channel Intelligence CLI — Direct access to Salesforce analytics.

Usage:
  channel kpi [--period PERIOD] [--json] [--channel-manager MANAGER]
  channel revenue [--period PERIOD] [--breakdown TYPE] [--json]
  ... (rest of docstring unchanged)
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

import click

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesforce_client import SalesforceClient
import channel_intelligence as ci
from auth_provider import create_auth_provider

# Configure logging
logger = logging.getLogger(__name__)

# Global auth provider and credentials
_auth_provider = None
_credentials = None


async def _initialize_auth():
    """Initialize authentication using auth_provider.
    
    Uses SF CLI if available, falls back to .env environment variables.
    """
    global _auth_provider, _credentials
    
    try:
        _auth_provider = create_auth_provider()
        _credentials = await _auth_provider.get_credentials()
        
        logger.debug(
            f"Authentication successful: "
            f"{_credentials.auth_method} (user: {_credentials.username or 'unknown'})"
        )
    except Exception as e:
        logger.error(f"Authentication initialization failed: {e}")
        raise


def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation using secure authentication.
    
    Returns a Salesforce client configured with credentials from either
    SF CLI (if available) or environment variables (.env file).
    """
    if _credentials is None:
        raise click.ClickException(
            "Authentication not initialized. "
            "This should not happen - auth should be initialized on CLI startup."
        )
    
    return SalesforceClient(
        base_url=_credentials.base_url,
        access_token=_credentials.access_token
    )


def format_json(data) -> str:
    """Format data as indented JSON."""
    return json.dumps(data, indent=2, default=str)


# ... (rest of file unchanged until the cli group definition)


@click.group()
def cli():
    """Channel Intelligence CLI — Salesforce analytics from the command line."""
    # Initialize authentication when CLI starts
    try:
        asyncio.run(_initialize_auth())
    except Exception as e:
        raise click.ClickException(
            f"Failed to initialize authentication: {e}\n\n"
            "Please ensure one of the following:\n"
            "  1. Salesforce CLI is installed and authenticated:\n"
            "     https://developer.salesforce.com/tools/salesforcecli\n"
            "     Run: sf org login web\n\n"
            "  2. Or set environment variables:\n"
            "     export SALESFORCE_BASE_URL=https://your-org.salesforce.com/services/data/v59.0\n"
            "     export SALESFORCE_ACCESS_TOKEN=<your_token>\n\n"
            "For more info, see: AUTHENTICATION_QUICKSTART.md"
        )


# ... (rest of CLI commands unchanged)
```

---

## Testing Checklist

After making these changes, verify everything works:

### Test 1: SF CLI Authentication (Primary Path)

```bash
# Setup: SF CLI authenticated, no .env
sf org login web
unset SALESFORCE_BASE_URL
unset SALESFORCE_ACCESS_TOKEN

# Test all 10 commands
channel kpi                              # ✅ Should work
channel revenue --breakdown country      # ✅ Should work
channel pipeline --json                  # ✅ Should work
channel partner "test"                   # ✅ Should work
channel qbr "test"                       # ✅ Should work
channel risk                             # ✅ Should work
channel registrations                    # ✅ Should work
channel top-partners --limit 5           # ✅ Should work
channel search "test"                    # ✅ Should work
channel list-opps                        # ✅ Should work

# Expected: All commands work without any .env file
```

### Test 2: .env Authentication (Fallback Path)

```bash
# Setup: .env only, SF CLI not available
# Create .env or set env vars:
export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=<your_token>

# Test
channel kpi

# Expected: Works (falls back to .env)
```

### Test 3: Both Available (Preference Check)

```bash
# Setup: Both SF CLI authenticated AND .env set
sf org login web
export SALESFORCE_BASE_URL=...
export SALESFORCE_ACCESS_TOKEN=...

# Test
channel kpi

# Expected: Works (uses SF CLI - more secure)
# Verify in logs it says "sf_cli" auth method
```

### Test 4: Neither Available (Error Handling)

```bash
# Setup: No SF CLI, no .env
unset SALESFORCE_BASE_URL
unset SALESFORCE_ACCESS_TOKEN

# Test
channel kpi

# Expected: Error message (should be helpful, not cryptic)
# Message should mention: SF CLI installation OR environment variables
```

### Test 5: JSON Output

```bash
# Test JSON output still works with all auth methods
channel kpi --json
channel revenue --json

# Expected: Valid JSON output
```

---

## Verification Steps

### 1. Syntax Check

```bash
# Verify Python syntax is correct
python3 -m py_compile cli/channel_cli.py

# Expected: No errors
```

### 2. Import Check

```bash
# Verify all imports work
python3 -c "import sys; sys.path.insert(0, '.'); from cli.channel_cli import cli"

# Expected: No errors
```

### 3. Help Text

```bash
# Verify help still works
channel --help
channel kpi --help

# Expected: Help text displays correctly
```

### 4. Logging

```bash
# Check if debug logging works
python3 -c "import logging; logging.basicConfig(level=logging.DEBUG); import cli.channel_cli"

# Expected: Should initialize without errors
```

---

## Rollback Plan (If Needed)

If something goes wrong, you can quickly revert:

```bash
# Revert the file
git checkout cli/channel_cli.py

# Or restore from backup
cp cli/channel_cli.py.backup cli/channel_cli.py
```

---

## Expected Behavior Changes

### What Changes ✅

- ✅ SF CLI is now preferred (if available)
- ✅ .env file is fallback (still works)
- ✅ No plaintext token in load_dotenv() call
- ✅ Better error messages

### What Stays the Same ✅

- ✅ All 10 CLI commands work identically
- ✅ JSON output unchanged
- ✅ Help text unchanged
- ✅ Command flags unchanged
- ✅ User experience unchanged

---

## Security Improvements

After this change:

| Aspect | Before | After |
|--------|--------|-------|
| Primary Auth | .env (plaintext) | SF CLI (encrypted) |
| Fallback | None | .env (still works) |
| Token Storage | Plaintext file | OS secure storage + in-memory |
| Token Refresh | Manual | Automatic (SF CLI) |
| Security Level | Medium | High |

---

## Time Estimate

| Task | Time |
|------|------|
| Read this guide | 10 min |
| Make code changes | 15 min |
| Run syntax checks | 5 min |
| Test 5 scenarios | 20 min |
| Verify logging | 5 min |
| **Total** | **55 min** |

---

## Support & Troubleshooting

### "ModuleNotFoundError: No module named 'auth_provider'"

**Solution**: Ensure `sys.path.insert(0, ...)` is in place before importing auth_provider

### "AttributeError: 'NoneType' object has no attribute 'base_url'"

**Solution**: Check that `_initialize_auth()` was called (it should be in cli() group)

### "Authentication not initialized error"

**Solution**: Verify `_initialize_auth()` is being called when CLI starts

### "SF CLI not found"

**Solution**: Install SF CLI: `brew install salesforce-cli` or https://developer.salesforce.com/tools/salesforcecli

---

## Next Steps After Implementation

1. ✅ Test thoroughly (all 5 test scenarios pass)
2. ✅ Commit changes to git
3. ✅ Push to repository
4. ✅ Update release notes
5. ✅ Mark CRITICAL #1 as fixed

---

## Summary

This is a **simple, low-risk change** that:

- Removes plaintext credential handling
- Leverages existing, proven code
- Maintains backward compatibility
- Improves security by default
- Takes only ~1 hour

The change is ready to implement whenever you're ready!

---

**Status**: Ready to implement  
**Effort**: 1 hour  
**Risk**: Very Low  
**Benefit**: Significant security improvement  

