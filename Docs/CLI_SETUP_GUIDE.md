# Channel Intelligence CLI - Setup & Installation Guide

**Version**: 2.0 | **Updated**: June 16, 2026

---

## Prerequisites

- **Python 3.8+** (check with `python3 --version`)
- **Salesforce CLI** (optional but recommended)
- **Virtual environment** (already created in project)

---

## Step 1: Navigate to Project

```bash
cd /Users/santiagot/Applications/salesforce-fastmcp
```

---

## Step 2: Activate Virtual Environment

```bash
source .venv/bin/activate
```

Your prompt should show `(.venv)` prefix. When done, use `deactivate` to exit.

---

## Step 3: Install Dependencies (First Time Only)

```bash
pip install -r requirements.txt
```

---

## Step 4: Set Up Authentication

Choose ONE option:

### Option A: Salesforce CLI (Recommended - Most Secure)

**Install Salesforce CLI:**
```bash
brew install salesforce-cli
# Or download from: https://developer.salesforce.com/tools/salesforcecli
```

**Authenticate:**
```bash
sf org login web
# Opens a browser for you to log in
# Follow the prompts to authenticate
```

**Verify:**
```bash
sf org list
# Shows your authenticated organization(s)
```

**Credentials stored in:** OS keychain (encrypted, automatic refresh)

### Option B: Environment Variables

If Salesforce CLI is unavailable, use environment variables:

```bash
export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=your_access_token_here
```

Replace:
- `your-instance` with your Salesforce org instance (e.g., `semperis`)
- `your_access_token_here` with your actual access token

### Option C: .env File (Persistent)

Create `.env` in project root:

```bash
cp .env.example .env
```

Edit `.env` and uncomment + fill in:
```
SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
SALESFORCE_ACCESS_TOKEN=your_access_token_here
```

**Priority order:**
1. Salesforce CLI (if available)
2. Environment variables (if set)
3. .env file (if present)
4. Error message if none available

---

## Step 5: Verify Installation

Test the CLI is working:

```bash
python3 -m cli.channel_cli --help
```

Should show all available commands.

Test a command:

```bash
python3 -m cli.channel_cli kpi
```

Should display KPI snapshot without errors.

---

## Troubleshooting Setup

### "ModuleNotFoundError: No module named 'click'"

**Solution:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Failed to initialize authentication"

**Check SF CLI:**
```bash
sf org list
```

If empty, run:
```bash
sf org login web
```

**Or set environment variables:**
```bash
export SALESFORCE_BASE_URL=https://your-instance.salesforce.com/services/data/v59.0
export SALESFORCE_ACCESS_TOKEN=your_token_here
```

### "python3: command not found"

Install Python 3.8+:
```bash
# macOS with Homebrew
brew install python3

# Or download from https://www.python.org
```

### Virtual environment issues

Recreate it:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Daily Usage

Every session:

```bash
# Navigate to project
cd /Users/santiagot/Applications/salesforce-fastmcp

# Activate environment
source .venv/bin/activate

# Run CLI commands
python3 -m cli.channel_cli kpi
python3 -m cli.channel_cli revenue --breakdown partner
# ... other commands

# Deactivate when done
deactivate
```

---

## Optional: Create Alias for Faster Access

Add to your `~/.zshrc` or `~/.bash_profile`:

```bash
alias channel='cd /Users/santiagot/Applications/salesforce-fastmcp && source .venv/bin/activate && python3 -m cli.channel_cli'
```

Reload:
```bash
source ~/.zshrc
# or
source ~/.bash_profile
```

Then use:
```bash
channel kpi
channel revenue --breakdown partner
channel top-partners
```

---

## Available Commands

10 commands available (see CLI_QUICK_REFERENCE.md for full details):

1. **kpi** - Key performance indicators
2. **revenue** - Revenue analysis with breakdowns
3. **pipeline** - Open opportunities analysis
4. **risk** - High-risk deals detection
5. **partner** - Partner scorecard
6. **qbr** - Quarterly business review
7. **registrations** - Deal registrations trend
8. **top-partners** - Partner rankings
9. **search** - Search opportunities
10. **list-opps** - List open opportunities

---

## Command Structure

All commands follow this format:

```bash
python3 -m cli.channel_cli COMMAND [OPTIONS]
```

**Get help for any command:**
```bash
python3 -m cli.channel_cli COMMAND --help

# Examples:
python3 -m cli.channel_cli kpi --help
python3 -m cli.channel_cli revenue --help
```

---

## Common Options

All commands support:
- `--period PERIOD` - Change time period (default: THIS_QUARTER)
- `--json` - Output as JSON instead of formatted tables

Many commands support:
- `--limit N` - Limit results
- `--breakdown TYPE` - Break down by dimension (partner, country, stage, etc.)
- `--stage STAGE` - Filter by opportunity stage
- `--partner NAME` - Filter by partner name
- `--country COUNTRY` - Filter by country

See CLI_QUICK_REFERENCE.md for complete option list.

---

## Authentication Security

**Salesforce CLI (Recommended):**
- ✅ Credentials encrypted in OS keychain
- ✅ Tokens refresh automatically
- ✅ No plaintext storage
- ✅ No manual token management

**Environment Variables:**
- ⚠️ Plaintext in terminal history
- ⚠️ Manual token refresh needed
- ✅ Works when SF CLI unavailable

**Best Practice:**
Use Salesforce CLI when possible. Only use env vars as fallback.

---

## Test Your Setup

Run all tests:

```bash
bash test_cli.sh
```

This runs 14 tests covering:
- Virtual environment
- Dependencies
- Imports
- Help text
- All 10 commands
- JSON output
- Filter options
- Period options

Expected: All tests pass (✅)

---

## What's Next

See **CLI_QUICK_REFERENCE.md** for:
- All 10 commands with examples
- Real-world usage patterns
- Quick workflows
- Tips and tricks

---

## File Structure

```
salesforce-fastmcp/
├── .venv/                    # Virtual environment
├── cli/
│   └── channel_cli.py        # CLI implementation
├── channel_intelligence.py   # Business logic
├── salesforce_client.py      # Salesforce API client
├── auth_provider.py          # Authentication handler
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment file
├── test_cli.sh              # Test script
└── Docs/
    ├── CLI_QUICK_REFERENCE.md    # Command reference (start here)
    └── CLI_SETUP_GUIDE.md        # This file
```

---

## Performance

Commands typically run in 5-10 seconds depending on:
- Time period (quarter = faster, year = slower)
- Data volume (risk = faster, list-opps = slower)
- Filter complexity (fewer filters = faster)

**Tips for speed:**
- Use specific periods instead of fiscal year when possible
- Use `--limit` to reduce results
- Use filters (--partner, --stage) to narrow down data

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.8 | 3.10+ |
| RAM | 2GB | 4GB+ |
| Disk Space | 500MB | 1GB+ |
| Internet | Required | Required (Salesforce API) |
| OS | macOS/Linux/Windows | macOS 12+ |

---

## Getting Help

**For command-specific help:**
```bash
python3 -m cli.channel_cli COMMAND --help
```

**For usage examples:**
See CLI_QUICK_REFERENCE.md

**For setup issues:**
See Troubleshooting Setup section above

---

**Status:** ✅ Ready to Use | **Version:** 2.0 | **Last Updated:** June 16, 2026

