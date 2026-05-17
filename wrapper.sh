#!/bin/bash
# MCP proxy: connects Claude Desktop (stdio) to remote FastMCP server via streamable-http
# The remote server runs: python3 server.py (with MCP_TRANSPORT=streamable-http MCP_PORT=8000)
# Usage: Configure claude_desktop_config.json to call this script as the command for the salesforce MCP server

SERVER_URL="${SALESFORCE_MCP_URL:-http://100.121.106.95:8000/mcp}"

exec /opt/homebrew/bin/python3 "$(dirname "$0")/proxy.py"
