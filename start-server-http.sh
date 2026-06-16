#!/bin/bash
# Start the Salesforce FastMCP server in HTTP mode
# This is required for OpenCode to connect via SSE (Server-Sent Events)
# Usage: ./start-server-http.sh [port]
# Default port: 8000

PORT="${1:-8000}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found at .venv/bin/activate"
    exit 1
fi

# Start server in HTTP mode
echo "Starting Salesforce FastMCP server in HTTP mode on port $PORT..."
echo "Server will be available at http://localhost:$PORT/mcp"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

export MCP_TRANSPORT=streamable-http
export MCP_PORT=$PORT

python server.py
