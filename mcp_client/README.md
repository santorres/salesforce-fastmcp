# MCP Client — Ollama + Local LLM Integration

Interactive chat interface combining **Ollama** (local LLM) with **FastMCP** (Salesforce analytics tools).

## Quick Start

### Prerequisites

1. **Ollama installed and running**
   ```bash
   # Download: https://ollama.ai
   # Run: ollama serve
   # (keep this running in a separate terminal)
   ```

2. **nous-hermes2 model available**
   ```bash
   ollama pull nous-hermes2:latest
   ```

3. **MCP server running**
   ```bash
   # On Salesforce laptop (already has auth)
   MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py
   ```

### Installation

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt
```

### Run Interactive Chat

**Local MCP server (same laptop):**
```bash
python mcp_client/chat.py
```

**Remote MCP server (different laptop):**
```bash
MCP_SERVER_URL="http://192.168.1.100:8000/mcp" python mcp_client/chat.py
```

### Example Conversation

```
You: Show me revenue by country this quarter