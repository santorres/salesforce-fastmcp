#!/bin/bash
# MCP proxy: connects Claude Desktop (stdio) to remote FastMCP server via streamable-http
# The remote server runs: python3 server.py (with MCP_TRANSPORT=streamable-http MCP_PORT=8000)
# Usage: Configure claude_desktop_config.json to call this script as the command for the salesforce MCP server

SERVER_URL="${SALESFORCE_MCP_URL:-http://100.121.106.95:8000/mcp}"

exec /opt/homebrew/bin/python3 << 'PYTHON_PROXY'
import asyncio
import sys
import os
import httpx

SERVER_URL = os.getenv('SALESFORCE_MCP_URL', 'http://100.121.106.95:8000/mcp')

async def proxy():
    """Proxy stdio to remote MCP server via streamable-http (SSE)."""
    async with httpx.AsyncClient(timeout=None) as client:
        async for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                # POST the MCP message to the remote server
                # streamable-http expects: POST with JSON body, returns SSE stream
                async with client.stream(
                    'POST',
                    SERVER_URL,
                    content=line,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream',
                    }
                ) as resp:
                    if resp.status_code >= 400:
                        error_msg = await resp.atext()
                        sys.stderr.write(f'Server error {resp.status_code}: {error_msg}\n')
                        sys.stderr.flush()
                        continue

                    # Parse SSE response stream
                    async for chunk in resp.aiter_lines():
                        # SSE format: "data: {json}"
                        if chunk.startswith('data: '):
                            data = chunk[6:].strip()
                            if data:
                                sys.stdout.write(data + '\n')
                                sys.stdout.flush()

            except asyncio.CancelledError:
                break
            except httpx.ConnectError:
                sys.stderr.write(f'Connection failed: Cannot reach {SERVER_URL}\n')
                sys.stderr.write('Make sure the server laptop is running: python3 server.py\n')
                sys.stderr.flush()
                sys.exit(1)
            except Exception as e:
                sys.stderr.write(f'Error: {type(e).__name__}: {e}\n')
                sys.stderr.flush()

try:
    asyncio.run(proxy())
except KeyboardInterrupt:
    pass
PYTHON_PROXY
