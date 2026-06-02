# MCP Client Setup & Testing Guide

Complete setup guide for demoing the Salesforce FastMCP server with **Ollama** (local LLM) instead of cloud LLM.

## Architecture Overview (For IT Review)

```
┌─────────────────────────────────────────────────────────────┐
│         Corporate Laptop (No Cloud LLM Access)              │
│                                                             │
│  ┌─────────────────┐      ┌──────────────────┐            │
│  │ Ollama          │      │ MCP Client       │            │
│  │ (nous-hermes2)  │◄─────│ Wrapper          │            │
│  └─────────────────┘      │ (chat.py)        │            │
│                           └──────────────────┘            │
│                                  ▲                        │
│                                  │                        │
│                                  ▼                        │
│                           ┌──────────────────┐           │
│                           │ MCP Server       │           │
│                           │ (server.py)      │           │
│                           └──────────────────┘           │
│                                  ▲                        │
│                                  │                        │
│                                  ▼                        │
│                           ┌──────────────────┐           │
│                           │ Salesforce       │           │
│                           │ REST API         │           │
│                           └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘

**Key Points for IT:**
- Ollama runs locally (no external API calls for LLM inference)
- MCP server handles Salesforce authentication (uses browser cookies in .env)
- Tool execution is deterministic (same inputs always produce same outputs)
- **Production Path:** Swap Ollama for AWS Bedrock → no code changes to MCP client
```

---

## Step 1: Install Ollama

### macOS (Apple Silicon/Intel)

1. Download from https://ollama.ai
2. Run the installer
3. Verify installation:
   ```bash
   ollama --version
   ```

### Linux/Windows

Follow platform-specific instructions at https://ollama.ai

---

## Step 2: Pull the Nous-Hermes2 Model

Nous-Hermes2 is optimized for:
- Multi-turn conversations
- Tool calling (structured function invocations)
- Business context understanding

```bash
ollama pull nous-hermes2:latest
```

This downloads a ~6.1 GB model. Verify:

```bash
ollama ls
# Expected output includes: nous-hermes2:latest   6.1 GB
```

---

## Step 3: Start Ollama Server

Ollama runs as a background service. Keep this terminal open while testing.

```bash
ollama serve
```

Expected output:
```
✓ Listening on 127.0.0.1:11434
```

Verify it's working:
```bash
curl http://localhost:11434/api/models
```

---

## Step 4: Install MCP Client Dependencies

```bash
# Install or update dependencies
pip install -r requirements.txt

# Verify ollama library is installed
python -c "import ollama; print(ollama.__version__)"
```

---

## Step 5: Start the MCP Server

The MCP server (server.py) connects to Salesforce. It runs independently of Ollama.

**On the Salesforce-authenticated laptop:**

```bash
# Terminal 1: Start MCP server in HTTP mode
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py
```

Expected output:
```
2026-05-26 10:30:45 | Registered 54 tools
2026-05-26 10:30:45 | Server listening on http://0.0.0.0:8000
```

Verify tools are discoverable:
```bash
# Terminal 2: Query tool list (JSON-RPC)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }' | jq '.result.tools | length'

# Expected: 54
```

---

## Step 6: Run the Interactive Chat Interface

**On the corporate laptop (with Ollama):**

```bash
# Local connection to MCP server (same laptop)
python mcp_client/chat.py

# OR remote connection (MCP on different laptop)
MCP_SERVER_URL="http://192.168.1.x:8000/mcp" python mcp_client/chat.py
```

You should see:
```
======================================================================
Salesforce Channel Analytics — Local LLM Interface
======================================================================

MCP Client Configuration:
  Model: nous-hermes2:latest
  Ollama URL: http://localhost:11434

  MCP Mode: http
  MCP Server: http://localhost:8000/mcp

  Max Retries: 2
  Verbose: false

Type 'quit' or 'exit' to end session
======================================================================

You:
```

---

## Testing Checklist

### Test 1: Simple Revenue Question

```
You: What was our revenue this quarter?
```

Expected:
- Ollama calls `get_revenue` with period=THIS_QUARTER
- Returns revenue amount + deal count
- Response takes 5-10 seconds (Ollama inference time)

### Test 2: Multi-Tool Question

```
You: Show me our top 5 partners and their pipeline
```

Expected:
- Ollama calls both `get_top_partners` (revenue-based) and partner pipeline tools
- Shows partner names with pipeline amounts
- Demonstrates tool sequencing

### Test 3: Breakdown Query

```
You: Break down this quarter's revenue by country
```

Expected:
- Ollama calls `get_revenue` with breakdown=country
- Shows revenue per country (Italy, Spain, Portugal, Greece, Cyprus, Malta)

### Test 4: Risk Analysis

```
You: Show me high-risk deals closing soon
```

Expected:
- Ollama calls `get_high_risk_deals`
- Shows deals with probability < 40% closing within 30 days
- Each deal shows: amount, company, probability, days until close

### Test 5: Error Handling (Intentional)

```
You: Show me revenue for InvalidPeriod
```

Expected:
- Tool call fails
- MCP client retries (if transient error)
- Finally reports: "Tool failed after 2 retries"
- Session continues (doesn't crash)

---

## Environment Variables

Configure MCP client behavior via `.env`:

```bash
# .env (add to existing file)

# Ollama settings
OLLAMA_MODEL=nous-hermes2:latest
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.3

# MCP server settings
MCP_SERVER_MODE=http
MCP_SERVER_URL=http://localhost:8000/mcp

# Retry & timeout
MAX_RETRIES=2
RETRY_DELAY_MS=500

# Debug
VERBOSE=true
LOG_LEVEL=INFO
```

Reload by restarting `python mcp_client/chat.py`

---

## Troubleshooting

### "Cannot connect to Ollama at http://localhost:11434"

**Fix:** 
```bash
# Terminal 1: Start Ollama server
ollama serve

# Verify:
curl http://localhost:11434/api/models
```

### "Cannot connect to MCP server at http://localhost:8000/mcp"

**Fix:**
```bash
# Terminal 2: Ensure MCP server is running
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py

# Verify:
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Tool calls never execute (slow or hanging)

**Debug:**
```bash
# Enable verbose logging
VERBOSE=true LOG_LEVEL=DEBUG python mcp_client/chat.py

# Watch output for:
# - Tool discovery (should list 54 tools)
# - LLM response (should parse tool calls correctly)
# - Tool execution (should see tool_name and parameters)
```

### Ollama model taking too long to load

**This is expected** on first run. Nous-Hermes2 is 6.1 GB.

- First inference: ~30-60 seconds (loads model into RAM)
- Subsequent inferences: ~3-10 seconds
- Apple Silicon (M1/M2/M3): faster due to metal acceleration

**Optimization:**
```bash
# Keep Ollama running between sessions
# (Don't restart between tests — model stays in RAM)
```

---

## For IT Review: Production Migration Path

### Phase 1: Demo (Current)
- ✅ Ollama (local, no external API calls)
- ✅ MCP Server (existing, unchanged)
- ✅ Browser cookies for Salesforce auth

### Phase 2: Production (Bedrock)
```python
# Swap only the LLM backend — no other code changes
# mcp_client/bedrock_llm.py (new, replaces ollama_llm.py)

import boto3
client = boto3.client('bedrock-runtime', region_name='eu-west-1')

response = client.invoke_model(
    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    body=json.dumps({"messages": messages, "tools": tools})
)
```

- Same MCP server
- Same `chat.py` (only import changes)
- Same tool calling, same architecture

### Phase 3: Glean Integration
```
Glean ←→ (MCP Connector Plugin) ←→ MCP Server ←→ Salesforce
```

- MCP server: swap browser cookies for OAuth/API credentials
- No CLI needed (Glean becomes the interface)
- Same 54 tools, same reliability

**Key:** MCP client/server architecture is agnostic to LLM backend.

---

## Demo Script for IT/AI Team (10 minutes)

```bash
# 1. Show Ollama running
echo "1. Ollama Model"
ollama ls
echo ""

# 2. Show MCP server running (open in browser)
echo "2. MCP Server Discovery"
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | jq '.result.tools | length'
echo "tools discovered"
echo ""

# 3. Run 3 demo questions
echo "3. Demo Queries"
python mcp_client/chat.py << 'EOF'
What's our revenue this quarter?
Show me top 3 partners
How many deals are high risk?
quit
EOF
```

---

## Next Steps

1. ✅ Build MCP client wrapper (completed)
2. 🔄 **Test with 10 diverse questions** (verify reliability)
3. 📊 Log all Q&A for IT review (proof of tool calling accuracy)
4. 🚀 Plan Bedrock integration (when IT approves)
5. 🔗 Plan Glean MCP connector (when cloud LLM is approved)
