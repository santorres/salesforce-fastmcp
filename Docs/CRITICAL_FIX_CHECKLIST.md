# Critical Fix Implementation Checklist

**Objective**: Fix 2 CRITICAL vulnerabilities in CLI  
**Estimated Time**: 40-48 hours (1 week full-time)  
**Status**: Ready to implement

---

## Quick Summary

### CRITICAL #1: Plaintext Credentials
**Problem**: `.env` file contains plaintext access tokens  
**Solution**: Remove `load_dotenv()`, use SF CLI secure storage  
**Effort**: 4-5 hours  
**Impact**: HIGH - Fixes credential exposure risk

### CRITICAL #2: Credential Leaks in Errors
**Problem**: 10 error handlers print full exceptions with tokens  
**Solution**: Create sanitization layer, update all error handlers  
**Effort**: 24-28 hours  
**Impact**: CRITICAL - Prevents token exposure in logs

---

## Implementation Tasks

### Phase 1A: Credential Storage Fix (4-5 hours)

- [ ] **TASK 1.1** (0.5h): Remove `load_dotenv()` from CLI
  - Edit: `cli/channel_cli.py` line 37
  - Remove: `load_dotenv()`
  - Verify: SF CLI import added

- [ ] **TASK 1.2** (1h): Update `get_sf()` function
  - Edit: `cli/channel_cli.py` lines 40-42
  - Add: Auth provider integration
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 1

- [ ] **TASK 1.3** (1h): Update `.env.example`
  - Edit: `.env.example` (entire file)
  - Add: Security warning header
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 2

- [ ] **TASK 1.4** (0.5h): Update `.gitignore`
  - Edit: `.gitignore`
  - Add: `.env`, `.env.local`, `.env.production`
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 3

- [ ] **TASK 1.5** (1h): Update documentation
  - Create/Edit: `Docs/CLI_USAGE.md` auth section
  - Add: SF CLI authentication instructions
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 4

- [ ] **TASK 1.6** (0.5h): Add pre-commit hook
  - Create: `.git/hooks/pre-commit`
  - Add: .env file check
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 5

### Phase 1B: Error Message Sanitization (24-28 hours)

- [ ] **TASK 2.1** (6h): Create error handler module
  - Create: `cli/error_handler.py`
  - Add: ErrorSanitizer class
  - Add: Safe message mapping
  - Add: Logging configuration
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 1

- [ ] **TASK 2.2** (12h): Update all 10 error handlers
  - Edit: `cli/channel_cli.py` (10 locations)
  
  Commands to update:
  - [ ] `kpi` (line 312)
  - [ ] `revenue` (line 334)
  - [ ] `pipeline` (line 356)
  - [ ] `partner` (line 376)
  - [ ] `qbr` (line 400)
  - [ ] `risk` (line 422)
  - [ ] `registrations` (line 441)
  - [ ] `top_partners` (line 463)
  - [ ] `search` (line 499)
  - [ ] `list_opps` (line 529)
  
  Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 2

- [ ] **TASK 2.3** (2h): Update imports in CLI
  - Edit: `cli/channel_cli.py` top section
  - Add: error_handler imports
  - Add: logging setup
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 2

- [ ] **TASK 2.4** (2h): Create/update `cli/__init__.py`
  - Edit/Create: `cli/__init__.py`
  - Add: Logging configuration
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 3

- [ ] **TASK 2.5** (2h): Update main entry point
  - Edit: `cli/channel_cli.py` `if __name__ == "__main__":`
  - Add: Logging setup
  - Add: Keyboard interrupt handling
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 4

- [ ] **TASK 2.6** (4h): Write and test error sanitization tests
  - Create: `test_cli_error_handler.py`
  - Add: 6+ unit tests
  - Run: `pytest test_cli_error_handler.py -v`
  - All tests: PASS ✅
  - Reference: **CLI_CRITICAL_REMEDIATION_GUIDE.md** Step 5

### Phase 1C: Testing & Verification (4-6 hours)

- [ ] **TASK 3.1** (2h): Manual testing - SF CLI auth
  - [ ] Install SF CLI: `brew install salesforce-cli`
  - [ ] Authenticate: `sf org login web`
  - [ ] Run: `channel kpi`
  - [ ] Verify: Command works
  - [ ] Verify: No `.env` file needed

- [ ] **TASK 3.2** (1h): Manual testing - Error handling
  - [ ] Unset all SF credentials
  - [ ] Run: `channel kpi`
  - [ ] Verify: Helpful error message shown
  - [ ] Verify: NO token/credential exposed
  - [ ] Check: `.channel_cli.log` has full error

- [ ] **TASK 3.3** (1h): Manual testing - All 10 commands
  - [ ] `channel kpi` - works ✅
  - [ ] `channel revenue` - works ✅
  - [ ] `channel pipeline` - works ✅
  - [ ] `channel partner "test"` - works ✅
  - [ ] `channel qbr "test"` - works ✅
  - [ ] `channel risk` - works ✅
  - [ ] `channel registrations` - works ✅
  - [ ] `channel top-partners` - works ✅
  - [ ] `channel search "test"` - works ✅
  - [ ] `channel list-opps` - works ✅

- [ ] **TASK 3.4** (1h): Manual testing - JSON output
  - [ ] `channel kpi --json` - works ✅
  - [ ] `channel revenue --json` - works ✅
  - [ ] Verify: Output is valid JSON

- [ ] **TASK 3.5** (1h): Integration tests
  - [ ] Create: `test_critical_fixes.sh`
  - [ ] Run: `./test_critical_fixes.sh`
  - [ ] All tests: PASS ✅

- [ ] **TASK 3.6** (0.5h): Code review
  - [ ] No `load_dotenv()` in code
  - [ ] No plaintext .env references
  - [ ] All error paths use ErrorSanitizer
  - [ ] No tokens in error messages
  - [ ] No credentials in code comments

---

## Detailed Task Instructions

### TASK 1.1: Remove load_dotenv()

```bash
# Edit file
nano cli/channel_cli.py

# Find line 37: load_dotenv()
# Delete the entire line
# Save and exit (Ctrl+X, Y, Enter in nano)
```

**Verification**:
```bash
grep -n "load_dotenv" cli/channel_cli.py
# Should show NO results (or only in .env.example)
```

---

### TASK 2.1: Create error_handler.py

```bash
# Copy the code from CLI_CRITICAL_REMEDIATION_GUIDE.md Step 1
# Create new file
cat > cli/error_handler.py << 'EOF'
# Paste the error_handler.py code from the guide
EOF
```

**Verification**:
```bash
python3 -m py_compile cli/error_handler.py
# Should succeed with no output
```

---

### TASK 2.2: Update error handlers

**Pattern for each command** (10 times):

```python
# FIND THIS:
except Exception as e:
    handle_error(e, "command_name")

# REPLACE WITH THIS:
except asyncio.TimeoutError as e:
    handle_error(e, "command_name")
except (ConnectionError, httpx.HTTPError) as e:
    handle_error(e, "command_name")
except ValueError as e:
    handle_error(e, "command_name")
except Exception as e:
    handle_error(e, "command_name")
```

**Verification**:
```bash
grep -n "except Exception as e:" cli/channel_cli.py
# Should show ZERO results after update
grep -n "handle_error(e," cli/channel_cli.py
# Should show 10+ results (all error handlers updated)
```

---

### TASK 2.6: Run error handler tests

```bash
# Run tests
pytest test_cli_error_handler.py -v

# Expected output:
# test_bearer_token_sanitized PASSED
# test_session_id_sanitized PASSED
# test_org_id_sanitized PASSED
# test_api_key_sanitized PASSED
# test_url_with_credentials_sanitized PASSED
# test_normal_message_unchanged PASSED
# ====== 6 passed in X.XXs ======
```

---

### TASK 3.1: Test SF CLI Auth

```bash
# Ensure SF CLI installed
sf --version
# Should show version number

# Authenticate (opens browser)
sf org login web

# Test CLI works
channel kpi

# Expected: Works OR shows helpful error about credentials
# NOT ACCEPTABLE: Shows plaintext token or org ID
```

---

### TASK 3.2: Test Error Messages Are Safe

```bash
# Remove credentials
unset SALESFORCE_BASE_URL
unset SALESFORCE_ACCESS_TOKEN
unset SALESFORCE_SID

# Try to run command
channel kpi 2>&1

# Check output:
# ✅ GOOD: "Failed to authenticate with Salesforce"
# ✅ GOOD: "Ensure SF CLI is installed"
# ❌ BAD: "00D50000000IZ3E" (org ID)
# ❌ BAD: "AQEAQCp..." (token)
# ❌ BAD: Bearer token visible

# Check log file
cat .channel_cli.log
# Should contain full error details (for debugging)
```

---

### TASK 3.5: Integration Tests

```bash
# Create test script
cat > test_critical_fixes.sh << 'EOF'
# Paste the test script from CLI_CRITICAL_REMEDIATION_GUIDE.md
EOF

chmod +x test_critical_fixes.sh

# Run tests
./test_critical_fixes.sh

# Expected: All tests PASS ✅
```

---

## Time Breakdown

| Task | Effort | Status |
|------|--------|--------|
| 1.1: Remove load_dotenv | 0.5h | ⏳ |
| 1.2: Update get_sf() | 1h | ⏳ |
| 1.3: Update .env.example | 1h | ⏳ |
| 1.4: Update .gitignore | 0.5h | ⏳ |
| 1.5: Update documentation | 1h | ⏳ |
| 1.6: Pre-commit hook | 0.5h | ⏳ |
| **Subtotal Phase 1A** | **4-5h** | |
| 2.1: Create error_handler.py | 6h | ⏳ |
| 2.2: Update 10 error handlers | 12h | ⏳ |
| 2.3: Update imports | 2h | ⏳ |
| 2.4: Update __init__.py | 2h | ⏳ |
| 2.5: Update main entry point | 2h | ⏳ |
| 2.6: Write tests | 4h | ⏳ |
| **Subtotal Phase 1B** | **24-28h** | |
| 3.1: Test SF CLI auth | 2h | ⏳ |
| 3.2: Test error messages | 1h | ⏳ |
| 3.3: Test all 10 commands | 1h | ⏳ |
| 3.4: Test JSON output | 1h | ⏳ |
| 3.5: Integration tests | 1h | ⏳ |
| 3.6: Code review | 0.5h | ⏳ |
| **Subtotal Phase 1C** | **6-7h** | |
| **TOTAL** | **34-40h** | |

---

## Success Criteria Checklist

Before considering the critical fixes COMPLETE:

### Security ✅
- [ ] No `.env` files required
- [ ] No plaintext credentials in code
- [ ] No tokens in error messages
- [ ] SF CLI secure storage used
- [ ] Pre-commit hook prevents accidental commits

### Functionality ✅
- [ ] All 10 CLI commands work
- [ ] JSON output works
- [ ] Help text works (`--help`)
- [ ] Error messages are helpful (not cryptic)

### Testing ✅
- [ ] Unit tests pass (error handler tests)
- [ ] Integration tests pass (test_critical_fixes.sh)
- [ ] Manual testing complete (all 10 commands)
- [ ] No new issues introduced

### Code Quality ✅
- [ ] Code is readable and documented
- [ ] No security warnings from static analysis
- [ ] Logging is working
- [ ] Exit codes are appropriate

### Documentation ✅
- [ ] CLI usage guide updated
- [ ] .env.example has security warning
- [ ] Comments added to error handler
- [ ] Deployment notes updated

---

## Rollback Plan

If critical issues found:

```bash
# Option 1: Revert specific commit
git revert <commit-hash>

# Option 2: Restore specific file
git checkout <commit-hash> -- cli/channel_cli.py

# Option 3: Keep fixes but revert to dev-only
# (use dev credentials, plan to retry)
```

---

## Team Communication

### Before Starting
- [ ] Notify team: "Starting critical security fixes"
- [ ] Share timeline: "1 week, can use dev credentials during work"
- [ ] Block calendar: "No CLI to production during this week"

### During Work
- [ ] Daily standup: Report progress
- [ ] Escalate blockers immediately
- [ ] Share test results

### After Completion
- [ ] Code review by 2+ team members
- [ ] Notify team: "Critical fixes complete"
- [ ] Share testing results
- [ ] Update security status

---

## Sign-Off

### Developer Checklist
- [ ] Code written and tested
- [ ] All tests pass
- [ ] No security warnings
- [ ] Documented changes

### Code Reviewer Checklist
- [ ] Code reviewed for security
- [ ] No hardcoded credentials
- [ ] Error messages safe
- [ ] Tests adequate

### QA Checklist
- [ ] All manual tests pass
- [ ] All integration tests pass
- [ ] No regressions introduced
- [ ] Error messages helpful

### Security Checklist
- [ ] Critical vulnerabilities fixed
- [ ] No new vulnerabilities introduced
- [ ] Documentation accurate
- [ ] Deployment safe

---

## Post-Fix Steps

### Immediately After
1. [ ] Merge to main branch
2. [ ] Tag release (e.g., `v1.0.1-critical-security-fix`)
3. [ ] Update changelog
4. [ ] Notify team

### Within 48 hours
1. [ ] Deploy to all environments
2. [ ] Monitor for issues
3. [ ] Verify SF CLI working in production

### Within 1 week
1. [ ] Schedule Phase 2 (HIGH severity fixes)
2. [ ] Update security status document
3. [ ] Celebrate! 🎉

---

## Resources

- **Main Guide**: CLI_CRITICAL_REMEDIATION_GUIDE.md
- **CLI Assessment**: CLI_SECURITY_ASSESSMENT.md (sections 2-3)
- **Error Handler Code**: Available in guide Step 1
- **Test Code**: Available in guide Step 5

---

**Created**: June 16, 2026  
**Target Start**: ASAP  
**Target Completion**: 1 week  
**Status**: Ready to implement

---

## Next Steps

1. ✅ **Review this checklist** (you are here)
2. ⏳ **Start Phase 1A** (credential storage fix)
3. ⏳ **Complete Phase 1A** (4-5 hours)
4. ⏳ **Start Phase 1B** (error message sanitization)
5. ⏳ **Complete Phase 1B** (24-28 hours)
6. ⏳ **Execute Phase 1C** (testing & verification)
7. ⏳ **Code review & merge**
8. ⏳ **Deploy to production**
9. ⏳ **Plan Phase 2 (HIGH severity fixes)**

**Begin now?** Run `channel kpi` to verify current state, then start with TASK 1.1.

