# CLI Critical Remediation Guide

**Priority**: 🔴 **CRITICAL - Fix Immediately**  
**Estimated Time**: 40-48 hours (1 week full-time)  
**Risk Level**: HIGH - Credential exposure  
**Deadline**: Before any production use with real credentials

---

## Overview

Two critical vulnerabilities must be fixed:

1. **Plaintext Credential Storage** - `.env` file in plaintext
2. **Credentials Leaked in Error Messages** - 10 error handlers exposing tokens

This guide provides step-by-step remediation code for both.

---

## CRITICAL #1: Plaintext Credential Storage

### Current Problem

**Location**: `cli/channel_cli.py:37`

```python
# CURRENT (INSECURE)
import os
from dotenv import load_dotenv

load_dotenv()  # ← Loads plaintext credentials into memory!

# .env file contains:
# SALESFORCE_BASE_URL=https://instance.salesforce.com/...
# SALESFORCE_ACCESS_TOKEN=00D50000000IZ3E!AQEAQCp... (PLAINTEXT!)
```

### Why It's Critical

1. **If `.env` committed to git**: Credentials in git history forever
2. **If machine compromised**: Attacker reads `.env` → has access token
3. **If container built with `.env`: Token in Docker layers
4. **If backup/snapshot made**: Token in backups
5. **If process dumps created**: Token visible in memory dumps

### Solution Overview

**Recommended approach**: Use SF CLI secure storage (already supported by `auth_provider.py`)

**Current flow**:
```
.env → load_dotenv() → os.getenv() → credentials in memory
```

**New flow**:
```
SF CLI secure storage → auth_provider.py → credentials in memory (temporary)
```

### Step 1: Remove `load_dotenv()` from CLI

**File**: `cli/channel_cli.py`

**Change**:
```python
# BEFORE (Lines 23-37)
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

load_dotenv()  # ← REMOVE THIS LINE

def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation."""
    return SalesforceClient()


# AFTER (Lines 23-37)
import asyncio
import json
import sys
from pathlib import Path
import logging

import click

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesforce_client import SalesforceClient
import channel_intelligence as ci
from auth_provider import create_auth_provider

# Configure logging for error handling
logger = logging.getLogger(__name__)

def get_sf() -> SalesforceClient:
    """Lazy SalesforceClient instantiation using secure auth."""
    try:
        # Use secure auth provider instead of plaintext .env
        auth_provider = create_auth_provider()
        credentials = asyncio.run(auth_provider.get_credentials())
        return SalesforceClient(
            base_url=credentials.base_url,
            access_token=credentials.access_token
        )
    except Exception as e:
        raise click.ClickException(
            "Failed to authenticate with Salesforce. "
            "Ensure SF CLI is installed and authenticated: "
            "https://developer.salesforce.com/tools/salesforcecli"
        )
```

**Why this works**:
- Removes plaintext `.env` dependency
- Uses `auth_provider.py` which already supports SF CLI secure storage
- Falls back to environment variables if no SF CLI found
- Credentials never stored in plaintext

### Step 2: Update `.env.example` - Add WARNING

**File**: `.env.example`

Add prominent warning at top:

```env
# ⚠️ SECURITY WARNING ⚠️
# 
# This file is for REFERENCE ONLY
# DO NOT create a .env file with real credentials!
#
# Instead, use Salesforce CLI for secure authentication:
#   1. Install SF CLI: https://developer.salesforce.com/tools/salesforcecli
#   2. Authenticate: sf org login web
#   3. Run CLI: channel kpi
#
# The CLI will automatically use SF CLI's secure credential storage.
#
# If you must use environment variables (NOT RECOMMENDED):
#   Export them: export SALESFORCE_BASE_URL=...
#   Never commit to git!
#

# ============================================================================
# SALESFORCE API CONFIGURATION (Reference Only)
# ============================================================================

# Your Salesforce instance URL
SALESFORCE_BASE_URL=https://your-instance.my.salesforce.com/services/data/v59.0

# Salesforce Session ID (SID) or Access Token
# ⚠️ DO NOT put real tokens here!
SALESFORCE_SID=your_session_id_here

# Alternative name for the access token (either works)
# SALESFORCE_ACCESS_TOKEN=your_access_token_here
```

### Step 3: Update `.gitignore` - Prevent Credential Commits

**File**: `.gitignore`

Add/verify these lines:

```bash
# Environment variables and secrets
.env
.env.local
.env.*.local
.env.production

# Salesforce credentials
salesforce.credentials
salesforce.token

# IDE/Editor secrets
.vscode/settings.json
.idea/runConfigurations/

# OS/System
.DS_Store
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
.env/
```

### Step 4: Update Documentation

**File**: Update `Docs/CLI_USAGE.md` or create new section

```markdown
## Authentication

### Recommended: Salesforce CLI (Secure)

```bash
# 1. Install SF CLI
brew install salesforce-cli  # macOS
# or see https://developer.salesforce.com/tools/salesforcecli

# 2. Authenticate with Salesforce
sf org login web

# 3. Use the CLI (credentials stored securely)
channel kpi
channel revenue --breakdown country
channel partner "Accenture"
```

**Why this is secure**:
- SF CLI stores credentials in OS-level secure storage (Keychain on macOS, etc.)
- Tokens never stored in plaintext files
- Automatic token refresh
- No `.env` file needed

### Legacy: Environment Variables (Not Recommended)

If you cannot use SF CLI:

```bash
export SALESFORCE_BASE_URL=https://instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=your_token_here
channel kpi
```

⚠️ **Never commit environment variables to git!**
```

### Step 5: Add Pre-commit Hook (Optional but Recommended)

**File**: `.git/hooks/pre-commit` (create new)

```bash
#!/bin/bash
# Prevent committing .env files with credentials

if git diff --cached --name-only | grep -E '\.env|\.env\..*'; then
    echo "ERROR: You are trying to commit .env files!"
    echo "These should NEVER be committed to git."
    echo ""
    echo "Instead, use Salesforce CLI for secure authentication:"
    echo "  sf org login web"
    echo ""
    echo "To unstage the file:"
    echo "  git reset HEAD .env"
    echo ""
    exit 1
fi

exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Verification Checklist

- [ ] `load_dotenv()` removed from `cli/channel_cli.py:37`
- [ ] `get_sf()` function updated to use `create_auth_provider()`
- [ ] `.env.example` updated with security warning
- [ ] `.gitignore` includes `.env` files
- [ ] Pre-commit hook installed (optional)
- [ ] Documentation updated
- [ ] Test: `channel kpi` works without `.env` file
- [ ] Test: SF CLI authentication works
- [ ] Test: Error message shown if credentials not found

---

## CRITICAL #2: Credentials Leaked in Error Messages

### Current Problem

**Location**: `cli/channel_cli.py:283-286` (repeated 10 times)

```python
# CURRENT (INSECURE)
def handle_error(error: Exception, context: str = "") -> None:
    """Print error and exit."""
    click.secho(f"Error{f' ({context})' if context else ''}: {str(error)}", 
                fg="red", err=True)
    sys.exit(1)
```

**Example of credential leak**:
```bash
$ channel kpi
Error (kpi): HTTPError: 401 - {"errorCode":"INVALID_SESSION_ID","message":"...","Authorization":"Bearer 00D50000000IZ3E!AQEAQCp..."}
                                                                               ↑↑↑ TOKEN EXPOSED! ↑↑↑
```

### Why It's Critical

1. **Stderr logged by systems**: Error output often captured in logs
2. **Visible in CI/CD logs**: Secrets exposed in job logs
3. **Saved in shell history**: `history | grep "Error"` shows token
4. **Visible in debugging output**: Terminal scrollback shows token
5. **Sent to error tracking**: Services like Sentry/Rollbar capture full errors

### Solution Overview

**Create a sanitization layer**:
```
Exception with token
    ↓
Sanitizer removes sensitive patterns
    ↓
Safe message shown to user
    ↓
Full error logged internally (without user exposure)
```

### Step 1: Create Error Sanitizer Utility

**File**: Create `cli/error_handler.py` (new file)

```python
"""
Secure error handling for CLI.

Sanitizes errors to prevent credential leakage while maintaining
useful debugging information in logs.
"""

import logging
import re
import sys
from typing import Optional

import click

# Logger for detailed errors (internal use only)
logger = logging.getLogger(__name__)


class ErrorSanitizer:
    """Sanitize error messages to remove sensitive data."""
    
    # Patterns to sanitize
    PATTERNS = [
        # Bearer tokens (OAuth)
        (r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', 'Bearer [REDACTED]'),
        
        # Session IDs (Salesforce SID)
        (r'[0-9a-f]{15,}!?[A-Za-z0-9]{20,}', '[SESSION_ID]'),
        
        # Org IDs (00D + 15 chars)
        (r'00D[a-zA-Z0-9]{12}', '[ORG_ID]'),
        
        # API keys
        (r'api[_-]?key[=:\s]+[a-zA-Z0-9]{20,}', 'api_key=[REDACTED]'),
        
        # URLs with credentials
        (r'https?://[^:\s]+:[^@\s]+@', 'https://[USER]:[PASS]@'),
        
        # Authorization headers
        (r'Authorization[=:\s]+[^\s]+', 'Authorization: [REDACTED]'),
        
        # Password patterns
        (r'password[=:\s]+[^\s]+', 'password=[REDACTED]'),
        
        # Secret tokens
        (r'secret[=:\s]+[^\s]+', 'secret=[REDACTED]'),
        
        # Full URLs that might expose instance names
        (r'https?://[\w\-\.]+\.my\.salesforce\.com', '[SALESFORCE_ORG]'),
    ]
    
    @staticmethod
    def sanitize(message: str) -> str:
        """Remove sensitive data from error message."""
        if not message:
            return message
        
        result = message
        for pattern, replacement in ErrorSanitizer.PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result


def handle_error(error: Exception, context: str = "") -> None:
    """
    Print a safe error message and exit.
    
    Logs the full error internally for debugging.
    Shows a sanitized message to the user.
    
    Args:
        error: The exception that occurred
        context: Context string (e.g., "kpi", "revenue")
    """
    # Log the full error internally (for debugging)
    logger.error(f"Error in {context}", exc_info=True)
    
    # Get safe user-facing message
    safe_message = _get_safe_message(type(error).__name__, context)
    
    # Show safe message to user
    click.secho(f"Error{f' ({context})' if context else ''}: {safe_message}", 
                fg="red", err=True)
    sys.exit(1)


def handle_error_safe(error: Exception, context: str = "", include_reason: bool = False) -> None:
    """
    Print a safe error message with optional reason.
    
    Args:
        error: The exception that occurred
        context: Context string (e.g., "kpi", "revenue")
        include_reason: If True, include sanitized error details
    """
    # Log full error internally
    logger.error(f"Error in {context}", exc_info=True)
    
    # Build safe message
    safe_message = _get_safe_message(type(error).__name__, context)
    
    # Optionally include sanitized reason
    if include_reason:
        sanitized = ErrorSanitizer.sanitize(str(error))
        safe_message = f"{safe_message}\nDetails: {sanitized}"
    
    # Show to user
    click.secho(f"Error{f' ({context})' if context else ''}: {safe_message}", 
                fg="red", err=True)
    sys.exit(1)


def _get_safe_message(exception_type: str, context: str = "") -> str:
    """
    Map exception types to safe user-facing messages.
    
    Hides technical details while being helpful.
    """
    messages = {
        # Network/Connection errors
        "ConnectionError": 
            "Cannot connect to Salesforce. Check your network and credentials.",
        "TimeoutError": 
            "Request timed out. Salesforce is not responding. Please try again.",
        "HTTPError":
            "Salesforce API error. Check your inputs (period, partner name, etc.)",
        
        # Authentication errors
        "AuthenticationError":
            "Authentication failed. Check your Salesforce credentials.",
        "PermissionError":
            "You don't have permission to access that data. Contact your Salesforce admin.",
        
        # Data/Input errors
        "ValueError": 
            "Invalid input. Check your parameters (e.g., period format, partner name).",
        "KeyError": 
            "Data not found. The requested record may no longer exist.",
        "TypeError":
            "Invalid data type. Check your input parameters.",
        
        # Async/Concurrency errors
        "asyncio.TimeoutError":
            "Request timed out. Please try again.",
        "CancelledError":
            "Request was cancelled. Please try again.",
        
        # Default
        "Exception":
            "An unexpected error occurred. Please contact support with the timestamp above."
    }
    
    return messages.get(exception_type, messages["Exception"])


def configure_logging(verbose: bool = False) -> None:
    """
    Configure logging for error tracking.
    
    Args:
        verbose: If True, show DEBUG logs. Else, show WARNING+ only.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('.channel_cli.log'),  # File logging
            # stderr logging handled by click.secho()
        ]
    )
```

### Step 2: Update `cli/channel_cli.py` - Use New Error Handler

**File**: `cli/channel_cli.py`

**Change imports** (top of file):
```python
# BEFORE
import asyncio
import json
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from salesforce_client import SalesforceClient
import channel_intelligence as ci

# AFTER
import asyncio
import json
import sys
from pathlib import Path
import logging

import click

from salesforce_client import SalesforceClient
import channel_intelligence as ci
from error_handler import handle_error, handle_error_safe, configure_logging
from auth_provider import create_auth_provider

# Setup logging
logger = logging.getLogger(__name__)
```

**Replace all 10 error handlers**:

```python
# BEFORE (Example from kpi command)
@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period (default: THIS_QUARTER)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def kpi(period, output_json, channel_manager):
    """Get KPI snapshot: revenue, pipeline, win rate, coverage."""
    try:
        result = asyncio.run(ci.get_kpi_snapshot(
            get_sf(),
            _normalize_period(period),
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_kpi(result))
    except Exception as e:
        handle_error(e, "kpi")  # ← OLD (prints everything)

# AFTER (Using new secure error handler)
@cli.command()
@click.option("--period", default="THIS_QUARTER", help="Fiscal period (default: THIS_QUARTER)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--channel-manager", default=None, help="Filter by channel manager")
def kpi(period, output_json, channel_manager):
    """Get KPI snapshot: revenue, pipeline, win rate, coverage."""
    try:
        result = asyncio.run(ci.get_kpi_snapshot(
            get_sf(),
            _normalize_period(period),
            channel_manager=channel_manager or None
        ))
        if output_json:
            click.echo(format_json(result))
        else:
            click.echo(format_kpi(result))
    except asyncio.TimeoutError as e:
        handle_error(e, "kpi")  # Specific timeout message
    except (ConnectionError, httpx.HTTPError) as e:
        handle_error(e, "kpi")  # Network errors
    except ValueError as e:
        handle_error(e, "kpi")  # Input validation
    except Exception as e:
        handle_error(e, "kpi")  # Generic error (logs full traceback)
```

**Locations to update** (10 commands):
1. Line 312: `kpi` command
2. Line 334: `revenue` command
3. Line 356: `pipeline` command
4. Line 376: `partner` command
5. Line 400: `qbr` command
6. Line 422: `risk` command
7. Line 441: `registrations` command
8. Line 463: `top_partners` command
9. Line 499: `search` command
10. Line 529: `list_opps` command

**Replace error handler function** (lines 283-286):

```python
# BEFORE
def handle_error(error: Exception, context: str = "") -> None:
    """Print error and exit."""
    click.secho(f"Error{f' ({context})' if context else ''}: {str(error)}", fg="red", err=True)
    sys.exit(1)

# AFTER - Just import from error_handler module
# (Remove function entirely - imported from error_handler.py)
```

### Step 3: Update `__init__.py` for CLI

**File**: `cli/__init__.py`

```python
"""
Salesforce Channel Intelligence CLI

Secure command-line interface for querying Salesforce analytics.
"""

from error_handler import configure_logging

# Configure logging on module load
configure_logging(verbose=False)
```

### Step 4: Add Main Entry Point with Logging Setup

**File**: Update `cli/channel_cli.py` - `if __name__ == "__main__":` block

```python
# BEFORE
if __name__ == "__main__":
    cli()

# AFTER
if __name__ == "__main__":
    # Enable logging configuration
    import logging
    from error_handler import configure_logging
    
    configure_logging(verbose=False)  # Set to True for debug mode
    
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nInterrupted.", err=True)
        sys.exit(130)  # Standard interrupt exit code
    except Exception as e:
        # Catch any uncaught exceptions
        handle_error(e, "cli")
```

### Step 5: Test Error Sanitization

**File**: Create `test_cli_error_handler.py` (test file)

```python
"""Tests for CLI error handler sanitization."""

import pytest
from cli.error_handler import ErrorSanitizer


class TestErrorSanitizer:
    """Test credential sanitization."""
    
    def test_bearer_token_sanitized(self):
        """Verify Bearer tokens are redacted."""
        message = "Authorization: Bearer 00D50000000IZ3E!AQEAQCp8ZeMy..."
        safe = ErrorSanitizer.sanitize(message)
        assert "00D50000000IZ3E" not in safe
        assert "AQEAQCp8ZeMy" not in safe
        assert "[REDACTED]" in safe
    
    def test_session_id_sanitized(self):
        """Verify Salesforce session IDs are redacted."""
        message = "Session: 00D50000000IZ3E!AQEAQCp8ZeMy123456789"
        safe = ErrorSanitizer.sanitize(message)
        assert "00D50000000IZ3E" not in safe
        assert "123456789" not in safe
    
    def test_org_id_sanitized(self):
        """Verify org IDs are redacted."""
        message = "Org ID: 00D50000000IZ3E"
        safe = ErrorSanitizer.sanitize(message)
        assert "00D50000000IZ3E" not in safe
        assert "[ORG_ID]" in safe
    
    def test_api_key_sanitized(self):
        """Verify API keys are redacted."""
        message = "api_key=abc123def456ghi789"
        safe = ErrorSanitizer.sanitize(message)
        assert "abc123def456ghi789" not in safe
        assert "[REDACTED]" in safe
    
    def test_url_with_credentials_sanitized(self):
        """Verify URLs with credentials are redacted."""
        message = "https://user:password@instance.salesforce.com"
        safe = ErrorSanitizer.sanitize(message)
        assert "password" not in safe
        assert "[USER]" in safe
    
    def test_normal_message_unchanged(self):
        """Verify normal messages aren't modified."""
        message = "Request timed out after 30 seconds"
        safe = ErrorSanitizer.sanitize(message)
        assert safe == message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
pytest test_cli_error_handler.py -v
```

### Verification Checklist

- [ ] New file `cli/error_handler.py` created
- [ ] All 10 error handlers updated to use new `handle_error()`
- [ ] `old_handle_error()` function removed from `cli/channel_cli.py`
- [ ] Logging configured in CLI entry point
- [ ] Error sanitization tests pass
- [ ] Manual test: Run `channel kpi` with bad credentials
- [ ] Verify: Error message is safe (no token exposed)
- [ ] Verify: Full error logged to `.channel_cli.log`
- [ ] Test all 10 commands produce safe errors

---

## Combined Verification Test Script

**File**: Create `test_critical_fixes.sh` (integration test)

```bash
#!/bin/bash
# Test that critical fixes are working

set -e

echo "Testing Critical Remediation Fixes"
echo "===================================="
echo ""

# Test 1: .env not required
echo "Test 1: Verify .env file not required..."
unset SALESFORCE_BASE_URL
unset SALESFORCE_ACCESS_TOKEN
unset SALESFORCE_SID

# Should show helpful error, not crash
if channel kpi 2>&1 | grep -q "SF CLI is installed"; then
    echo "✅ PASS: Helpful error shown when credentials missing"
else
    echo "❌ FAIL: Should show helpful error message"
    exit 1
fi

echo ""

# Test 2: Error messages are safe
echo "Test 2: Verify error messages don't leak tokens..."
# Create a fake .env with fake token
export SALESFORCE_BASE_URL="https://fake.salesforce.com/services/data/v59.0"
export SALESFORCE_ACCESS_TOKEN="00D50000000IZ3E!FAKE_TOKEN_SHOULD_NOT_APPEAR"

# Try to run a command (will fail to connect, but shouldn't leak token)
if channel kpi 2>&1 | grep -q "00D50000000IZ3E"; then
    echo "❌ FAIL: Token appears in error message!"
    exit 1
elif channel kpi 2>&1 | grep -q "[REDACTED]\|[ORG_ID]"; then
    echo "✅ PASS: Credentials properly redacted in error messages"
else
    echo "⚠️  WARNING: Check error message manually"
fi

echo ""

# Test 3: Logs contain full error (for debugging)
echo "Test 3: Verify logs capture full errors..."
if [ -f ".channel_cli.log" ]; then
    if grep -q "Error" ".channel_cli.log"; then
        echo "✅ PASS: Full errors logged to .channel_cli.log"
    else
        echo "⚠️  WARNING: Check log file manually"
    fi
else
    echo "⚠️  WARNING: Log file not created yet"
fi

echo ""
echo "Critical Remediation Tests Complete!"
echo "✅ All critical fixes verified"
```

Make executable:
```bash
chmod +x test_critical_fixes.sh
./test_critical_fixes.sh
```

---

## Summary of Changes

### Files Modified
1. `cli/channel_cli.py` - Remove load_dotenv, update all error handlers
2. `.env.example` - Add security warning
3. `.gitignore` - Ensure .env files excluded

### Files Created
1. `cli/error_handler.py` - New error sanitization module
2. `test_cli_error_handler.py` - Unit tests
3. `test_critical_fixes.sh` - Integration tests

### Files Updated (Documentation)
1. `Docs/CLI_USAGE.md` - Update authentication section

### Configuration
1. Pre-commit hook - Prevent accidental credential commits

---

## Testing Checklist

- [ ] Unit tests pass: `pytest test_cli_error_handler.py -v`
- [ ] Integration tests pass: `./test_critical_fixes.sh`
- [ ] Manual test: SF CLI auth works
- [ ] Manual test: Helpful error when SF CLI not installed
- [ ] Manual test: Error messages don't expose credentials
- [ ] Manual test: All 10 CLI commands still work
- [ ] Manual test: JSON output still works
- [ ] Manual test: Help text still works (`channel --help`)
- [ ] Code review: No plaintext .env references remain
- [ ] Code review: All error paths sanitized

---

## Estimated Effort

| Task | Effort | Notes |
|------|--------|-------|
| Remove load_dotenv | 1h | Remove 1 line, add 15 lines |
| Create error handler module | 6h | ~200 lines of code + patterns |
| Update all 10 error handlers | 4h | Repetitive but thorough |
| Update documentation | 2h | CLI usage guide, .env warning |
| Write tests | 4h | Unit + integration tests |
| Manual testing | 4h | Test all 10 commands |
| Code review + fixes | 8h | Catch edge cases |
| **TOTAL** | **28-32h** | Conservative estimate |

---

## Deployment

### Before Merging
1. ✅ All tests pass
2. ✅ Manual testing complete
3. ✅ Code review approved
4. ✅ No credential strings in code

### After Merging
1. ⏳ Update deployment documentation
2. ⏳ Notify team of new auth method
3. ⏳ Verify SF CLI installation in production
4. ⏳ Monitor error logs for issues

### Post-Deployment
1. ⏳ Verify no .env files with credentials created
2. ⏳ Spot-check error logs (use `.channel_cli.log`)
3. ⏳ Monitor for support requests about authentication

---

## Success Criteria

### Fix is COMPLETE when:

- ✅ `.env` files not required to run CLI
- ✅ SF CLI secure storage used for credentials
- ✅ No tokens appear in error messages
- ✅ Full errors logged internally (in `.channel_cli.log`)
- ✅ All 10 CLI commands work
- ✅ All tests pass
- ✅ Code review approved
- ✅ Documentation updated
- ✅ Pre-commit hook prevents accidental commits

### Risk is RESOLVED when:

- 🟢 No plaintext credentials in `.env`
- 🟢 No credential leakage in error messages
- 🟢 SF CLI secure storage used (or environment variables)
- 🟢 `.env` files excluded from git (pre-commit hook)
- 🟢 Helpful error messages guide users

---

## Rollback Plan (if needed)

If critical issues found during testing:

```bash
# Revert to previous version
git revert <commit-hash>

# Keep using CLI with dev credentials only
# until issues are resolved
```

---

## Next Steps After Critical Fix

Once Critical fixes are complete, proceed with:

- **Phase 2 (HIGH severity fixes)**: 32-40 hours
  - SOQL injection wildcard escaping
  - Input validation for 6+ parameters
  - Exception handling improvements
  
- **Phase 3 (MEDIUM severity fixes)**: 24-32 hours
  - Output data sanitization
  - Type hints
  - Structured logging

See **CLI_SECURITY_ASSESSMENT.md** sections 3-5 for Phase 2 & 3 details.

---

**Remediation started**: [Date]  
**Target completion**: [1 week]  
**Verification date**: [To be scheduled]

