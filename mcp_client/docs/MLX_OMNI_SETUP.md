# MLX Omni Server Setup Guide

## Quick Start

### 1. Create a dedicated venv for the MLX Omni Server

```bash
mkdir -p ~/mlx-server
cd ~/mlx-server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 2. Install MLX Omni Server

```bash
pip install mlx-omni-server
```

Verify:
```bash
mlx-omni-server --help
python -c "import mlx_omni_server; print('OK')"
```

### 3. Start the server (run in its own terminal)

```bash
cd ~/mlx-server
source .venv/bin/activate
mlx-omni-server --port 10240
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:10240
```

### 4. Verify the server works

```bash
# In another terminal:
curl http://localhost:10240/v1/models

# Quick test:
curl -X POST http://localhost:10240/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mlx-community/gemma-3-1b-it-4bit-DWQ", "messages": [{"role": "user", "content": "Hello"}]}'
```

### 5. Connect the MCP client

The project's `mcp_client/chat.py` is configured to connect to `http://localhost:10240/v1`.

```bash
# In the salesforce-fastmcp directory
cd /Users/santiago/Projects/salesforce-fastmcp

# Create project venv (if not already done)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Now run the chat client
python mcp_client/chat.py
```

---

## Architecture

```
Terminal A: MLX Omni Server
  Command: mlx-omni-server --port 10240
  venv: ~/mlx-server/.venv
  Role: Inference engine (accepts LLM queries, returns completions)

Terminal B: MCP Client (chat.py)
  Command: python mcp_client/chat.py
  venv: salesforce-fastmcp/.venv
  Role: Chat interface that calls MLX Omni for LLM responses
         and calls Salesforce MCP for data tools

Terminal C: Salesforce FastMCP Server
  Command: python server.py  (on corporate laptop)
  Role: Provides Salesforce data via MCP tools
```

---

## Configuration

**File:** `mcp_client/config.py`

### MLX Omni Server settings

| Variable | Default | Override with env var |
|----------|---------|------------------------|
| `MLX_MODEL` | `Qwen/Qwen2.5-3B-Instruct` | `MLX_MODEL=...` |
| `MLX_BASE_URL` | `http://localhost:10240/v1` | `MLX_BASE_URL=...` |
| `MLX_TEMPERATURE` | `0.0` (deterministic) | `MLX_TEMPERATURE=...` |
| `MLX_TOP_P` | `1.0` | `MLX_TOP_P=...` |

### Example: Use a different model

```bash
# Try a smaller model (faster)
export MLX_MODEL="mlx-community/gemma-3-1b-it-4bit-DWQ"
python mcp_client/chat.py

# Use a different server (e.g., if running on another machine)
export MLX_BASE_URL="http://192.168.1.100:10240/v1"
python mcp_client/chat.py
```

---

## Available Models

The following models are pre-downloaded and cached in `~/.cache/huggingface/hub/`:

**Text generation (LLM chat):**
- `Qwen/Qwen2.5-3B-Instruct` ← recommended, already configured
- `mlx-community/gemma-3-1b-it-4bit-DWQ` (small, fast)
- `mlx-community/Llama-3.2-1B-Instruct-4bit` (very small)
- `mlx-community/Qwen3-0.6B-4bit-DWQ` (smallest)
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` (reasoning)

**Embeddings:**
- `mlx-community/all-MiniLM-L6-v2-4bit`

**Audio:**
- `mlx-community/whisper-large-v3-turbo` (speech-to-text)
- `lucasnewman/f5-tts-mlx` (text-to-speech)
- `prince-canuma/Kokoro-82M` (TTS voice)

**Images:**
- `dhairyashil/FLUX.1-schnell-mflux-4bit` (image generation)

---

## Troubleshooting

### Server won't start

**Error:** `Address already in use`
- Port 10240 is occupied. Kill the old process or use a different port.
- `lsof -i :10240` to find the process ID
- `kill -9 <pid>` to kill it

**Error:** `ModuleNotFoundError: No module named 'mlx_omni_server'`
- Did you activate the venv? Run: `source ~/mlx-server/.venv/bin/activate`
- Is mlx-omni-server installed? Run: `pip list | grep mlx-omni`

**Error:** Memory or METAL issues
- These models require Apple Silicon GPU. The server **will not work** on Intel Macs.
- Check: `python -c "import mlx; print(mlx.core.metal_device_get_available())"` should be `True`

### Client can't connect

**Error:** `Connection refused` on localhost:10240
- Is the server running? Check: `curl http://localhost:10240/v1/models`
- Is the port correct? Check `mcp_client/config.py` line 7

**Error:** Model not found
- The model name must exactly match one from `curl http://localhost:10240/v1/models`
- Double-check spelling (e.g., `Qwen/Qwen2.5-3B-Instruct`, not `qwen2.5`)

---

## Performance Notes

**Cold start:** First request for a model is slow (3–10 seconds) as it loads weights.
Subsequent requests are fast (< 1 second) thanks to in-memory caching.

**Model selection:**
- **Qwen 2.5-3B-Instruct**: balanced speed + quality, recommended
- **Gemma 3-1B-IT**: faster, good for quick demos
- **Llama 3.2-1B**: very fast, simpler tasks
- Larger models are slower but better at reasoning

**Temperature:**
- `0.0` → deterministic (best for tool calling, consistent responses)
- `0.5–1.0` → creative (good for exploratory queries)

---

## Next Steps

1. Keep the MLX Omni Server running in a dedicated terminal
2. Run `python mcp_client/chat.py` to interact with it
3. Test with: `You: show me revenue by country last quarter`
4. The client will call MLX for intent understanding, then call the Salesforce MCP for data

---

## Documentation references

- [MLX Omni Server official docs](https://deepwiki.com/madroidmaq/mlx-omni-server/1-overview)
- [MLX framework](https://github.com/ml-explore/mlx)
- [HuggingFace model hub](https://huggingface.co/mlx-community)
