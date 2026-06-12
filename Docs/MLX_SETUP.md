# MLX Omni Server + MCP Client Setup

This guide covers setting up the Salesforce FastMCP client to use **MLX Omni Server** for local LLM inference instead of Ollama.

## Why MLX Omni Server?

- **Apple Silicon optimized** — runs natively on M1/M2/M3 Macs
- **OpenAI-compatible API** — uses standard function calling format
- **Auto-discovers models** — pulls from HuggingFace automatically
- **Better tool calling** — more reliable at following tool schemas than Ollama

## Architecture

```
┌─────────────────────────────────────────────┐
│  Your Terminal                              │
│  python mcp_client/chat.py                  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ Chat Interface (chat.py)             │  │
│  │ - Takes user questions               │  │
│  │ - Orchestrates LLM + tool execution  │  │
│  └──────────────────────────────────────┘  │
│           ↓                    ↓             │
│  ┌──────────────────┐  ┌──────────────┐   │
│  │ MLX Omni Client  │  │ MCP Bridge   │   │
│  │ (localhost:8000) │  │ (remote MCP) │   │
│  └──────────────────┘  └──────────────┘   │
└─────────────────────────────────────────────┘
          ↓                        ↓
    MLX Omni Server      MCP FastMCP Server
    (local inference)    (corporate laptop,
                         Salesforce auth)
```

## Installation

### 1. Install MLX Framework

```bash
pip install mlx-lm
```

### 2. Install MLX Omni Server

```bash
pip install mlx-omni-server
```

Or from source:
```bash
git clone https://github.com/madroidmaq/mlx-omni-server.git
cd mlx-omni-server
pip install -e .
```

### 3. Update MCP Client Dependencies

```bash
pip install -r requirements.txt
```

This installs `openai>=1.0.0` (OpenAI SDK for MLX Omni compatibility).

## Running the Stack

### Terminal 1: MLX Omni Server

Start the local inference server:

```bash
mlx_omni_server
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Models auto-download from HuggingFace on first use. Popular options:
- `Qwen2.5-3B` (fast, default)
- `Gemma-3-2B` (lightweight)
- `SmolLM2-135M` (smallest)

To specify a model:
```bash
mlx_omni_server --model-name Gemma-3-2B
```

### Terminal 2: MCP FastMCP Server

On your **corporate laptop** (where Salesforce auth works):

```bash
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py
```

### Terminal 3: MCP Client Chat

```bash
cd /path/to/salesforce-fastmcp
python mcp_client/chat.py
```

The client will:
1. Connect to MLX Omni Server at `localhost:8000/v1` for inference
2. Connect to remote MCP server (from MCP_SERVER_URL env var)
3. Execute tool calls against Salesforce

## Testing

### Quick Test

```bash
python test_mlx_mcp_integration.py
```

This verifies:
- ✅ MLX Omni Server responds
- ✅ MCP bridge connects to FastMCP
- ✅ Tool discovery works

### Interactive Test

```bash
python mcp_client/chat.py

You: What is our current quarter pipeline?
```

The LLM should:
1. Recognize the question needs the `get_pipeline()` tool
2. Call it with `period="THIS_QUARTER"`
3. Execute on remote MCP server
4. Synthesize results into natural language

## Configuration

Defaults in `mcp_client/config.py`:

```python
OLLAMA_MODEL = "mlx"  # MLX Omni model name
OLLAMA_BASE_URL = "http://localhost:8000/v1"  # OpenAI-compatible endpoint
OLLAMA_TEMPERATURE = 0.0  # Deterministic (best for tool calling)
MCP_SERVER_URL = "http://localhost:8000/mcp"  # Remote MCP server
```

Override with environment variables:

```bash
export OLLAMA_MODEL=Gemma-3-2B
export OLLAMA_BASE_URL=http://localhost:8000/v1
export MCP_SERVER_URL=http://santiagot-mac-1.tail3db141.ts.net:8000/mcp
python mcp_client/chat.py
```

## Troubleshooting

### "Cannot connect to MLX Omni Server at localhost:8000"

- Is it running? Check `http://localhost:8000/docs`
- Try: `mlx_omni_server`

### "Connection refused" to MCP server

- Is MCP FastMCP running?
- Check MCP_SERVER_URL is correct (local or Tailscale address)

### Tool calling not working

- Set `VERBOSE=true` to see tool detection
- Ensure temperature is 0.0 (not 0.3)
- Check MLX model supports function calling (most do)

### Model download is slow

- First run downloads ~2GB per model from HuggingFace
- Subsequent runs use cached model
- Models stored in `~/.cache/huggingface`

## Performance Notes

On M1/M2/M3 MacBook:
- **Inference time**: 100-200ms per request (tool calling)
- **Memory**: 4-8GB per model (depending on size)
- **Disk**: ~2GB per model in cache

For production/demo:
- Stick with smaller models (2B-7B parameters)
- Qwen, Gemma, Llama are good options
- Avoid 70B+ unless on higher RAM systems

## Next Steps

Once verified working locally:

1. **Test with remote MCP** — SSH to corporate laptop, run client
2. **Demonstrate to colleagues** — show natural language queries working end-to-end
3. **Prepare for cloud** — when approved, migrate to AWS Bedrock or Glean

See [CLI_PLAYBOOK.md](CLI_PLAYBOOK.md) for use cases and automation patterns.
