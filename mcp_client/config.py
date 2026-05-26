"""Configuration for Ollama LLM + MCP client wrapper."""
import os
from typing import Optional

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nous-hermes2:latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))  # Lower = more deterministic
OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.9"))

# MCP server settings — flexible local or remote
MCP_SERVER_MODE = os.getenv("MCP_SERVER_MODE", "http")  # "stdio" or "http"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")  # Used if mode=http
MCP_STDIO_CMD = os.getenv("MCP_STDIO_CMD", "python server.py")  # Used if mode=stdio

# Retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RETRY_DELAY_MS = int(os.getenv("RETRY_DELAY_MS", "500"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"

# Tool calling settings
MAX_TOOLS_PER_CALL = 3  # Prevent LLM from calling too many tools at once
TIMEOUT_SECONDS = 30

def get_config_summary() -> str:
    """Return human-readable config for debugging."""
    return f"""
MCP Client Configuration:
  Model: {OLLAMA_MODEL}
  Ollama URL: {OLLAMA_BASE_URL}
  Temperature: {OLLAMA_TEMPERATURE}

  MCP Mode: {MCP_SERVER_MODE}
  MCP Server: {MCP_SERVER_URL if MCP_SERVER_MODE == "http" else MCP_STDIO_CMD}

  Max Retries: {MAX_RETRIES}
  Verbose: {VERBOSE}
""".strip()
