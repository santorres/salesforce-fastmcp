# Corporate GitHub Deployment Guide

**Purpose**: Instructions for syncing code to corporate GitHub while keeping internal documentation private.

---

## Branch Structure

### Your Personal GitHub (`origin`)
```
main (full repository)
├── MCP server code
├── Configuration
├── Tests
└── Docs/ (all documentation - PRIVATE)
    ├── Security docs
    ├── Architecture docs
    ├── Roadmaps
    └── Playbooks

corporate/main (code-only)
├── MCP server code
├── Configuration
├── Tests
└── [Docs/ REMOVED]
```

### Corporate GitHub (`corporate`)
```
main (what you push)
├── MCP server code
├── Configuration
├── Tests
└── [No documentation]
```

---

## Setup: Add Corporate Remote

**First time only:**

```bash
# Add corporate GitHub as remote
git remote add corporate https://github.com/semperis/salesforce-fastmcp.git

# Verify
git remote -v
```

**Output should show:**
```
origin      https://github.com/santorres/salesforce-fastmcp.git (fetch)
origin      https://github.com/santorres/salesforce-fastmcp.git (push)
corporate   https://github.com/semperis/salesforce-fastmcp.git (fetch)
corporate   https://github.com/semperis/salesforce-fastmcp.git (push)
```

---

## Workflow: Push to Corporate

### When You Have Code Changes

```bash
# 1. Make changes on main (your personal working branch)
git checkout main
# ... edit code, test, commit ...
git commit -m "Your change description"

# 2. Merge changes to corporate/main
git checkout corporate/main
git merge main --no-edit

# 3. Verify Docs/ is NOT present
ls -la Docs/  # Should show: ls: Docs/: No such file or directory

# 4. Push to corporate GitHub
git push corporate corporate/main:main

# 5. Back to main
git checkout main
```

---

## Workflow: Sync Corporate Changes Back

If corporate team makes changes to their repo:

```bash
# 1. Fetch corporate changes
git fetch corporate

# 2. Merge into corporate/main
git checkout corporate/main
git merge corporate/main --no-edit

# 3. Sync to your main (careful with conflicts)
git checkout main
git merge corporate/main

# 4. Resolve any Docs/ conflicts (if they appear)
# Docs/ stays in main, not in corporate/main
```

---

## What Gets Shared vs Private

### ✅ Shared with Corporate (on `corporate/main`)
- `server.py` - MCP server
- `salesforce_client.py` - Salesforce integration
- `config/` - Configuration
- `requirements.txt` - Dependencies
- `.env.example` - Environment template (no secrets)
- `tests/` - Test suite
- `README.md` - Basic overview

### ❌ NOT Shared (stays in `Docs/` on `main`)
- `Docs/SECURITY_BRIEF.md` - Internal security assessment
- `Docs/SECURITY_IMPLEMENTATION_SUMMARY.md` - Security implementation
- `Docs/OBSERVABILITY_ROADMAP.md` - Future observability plan
- `Docs/SCALABILITY_ARCHITECTURE.md` - Internal architecture
- `Docs/AUTHENTICATION_STRATEGY.md` - Internal auth strategy
- `Docs/YAML_ONLY_SCALABILITY.md` - Internal scalability docs
- All playbooks and internal guides

---

## Key Rules

⚠️ **IMPORTANT:**

1. **Never push `main` to corporate**
   - ❌ `git push corporate main:main` (WRONG)
   - ✅ `git push corporate corporate/main:main` (CORRECT)

2. **corporate/main should never have Docs/**
   - Always verify: `ls Docs/` returns error
   - If Docs/ appears, remove it: `git rm -r Docs/`

3. **Keep main and corporate/main synced**
   - Merge main → corporate/main regularly
   - This brings code changes to corporate branch

4. **Docs/ only lives on main**
   - When you merge main → corporate/main, git will skip Docs/ removal
   - But Docs/ already doesn't exist on corporate/main, so no conflict

---

## Common Tasks

### Task 1: Push New Code to Corporate

```bash
# Make sure you're on main
git checkout main

# Add feature or bugfix
git commit -m "Add feature X"

# Switch to corporate branch
git checkout corporate/main

# Get the code change (not Docs/)
git merge main --no-edit

# Push to corporate
git push corporate corporate/main:main

# Back to main for more work
git checkout main
```

### Task 2: Check What's Different

```bash
# Compare branches
git diff main corporate/main

# Should only show differences in Docs/ folder
# If something else differs, investigate
```

### Task 3: Verify Docs Are Hidden

```bash
# On corporate/main, this should fail:
git checkout corporate/main
ls Docs/
# Output: ls: Docs/: No such file or directory ✅

# On main, this should succeed:
git checkout main
ls Docs/
# Output: AUTHENTICATION_QUICKSTART.md, SECURITY_BRIEF.md, etc. ✅
```

---

## Troubleshooting

### "I accidentally pushed main to corporate"

```bash
# Get corporate back to correct state
git fetch corporate
git reset corporate/main
git push corporate corporate/main:main --force
```

### "Docs/ appeared on corporate/main"

```bash
git checkout corporate/main
git rm -r Docs/
git commit -m "Remove leaked documentation"
git push corporate corporate/main:main
```

### "I want to pull corporate changes"

```bash
# Fetch their changes
git fetch corporate

# Create local branch to inspect
git checkout -b review/corporate-changes corporate/main

# Check what changed
git diff main review/corporate-changes

# If good, merge to your main
git checkout main
git merge review/corporate-changes
```

---

## Git Aliases (Optional)

Add these to `.git/config` or `~/.gitconfig` for convenience:

```bash
git config --global alias.corp-push '!git push corporate corporate/main:main'
git config --global alias.corp-fetch '!git fetch corporate'
```

Then you can just run:
```bash
git corp-push    # Instead of: git push corporate corporate/main:main
git corp-fetch   # Instead of: git fetch corporate
```

---

## Status Summary

```bash
# Run this to verify everything is correct:
git branch -v && echo "---" && git remote -v
```

You should see:
- ✅ `main` on your personal GitHub (has Docs/)
- ✅ `corporate/main` local (no Docs/)
- ✅ `corporate` remote pointing to corporate GitHub

---

**Last Updated**: June 16, 2026  
**Status**: Ready for corporate deployment
