#!/usr/bin/env python3
"""MCP stdio-to-HTTP proxy: bridges Claude Desktop to a remote FastMCP streamable-http server."""
import sys
import os
from http.client import HTTPConnection
from urllib.parse import urlparse

SERVER_URL = os.getenv('SALESFORCE_MCP_URL', 'http://100.121.106.95:8000/mcp')

parsed = urlparse(SERVER_URL)
host = parsed.hostname
port = parsed.port or 80
path = parsed.path

session_id = None

while True:
    line = sys.stdin.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue

    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
        }
        if session_id:
            headers['mcp-session-id'] = session_id

        conn = HTTPConnection(host, port, timeout=60)
        conn.request('POST', path, body=line.encode(), headers=headers)
        resp = conn.getresponse()

        # Capture session ID from initialize response
        if session_id is None:
            session_id = resp.getheader('mcp-session-id')

        if resp.status >= 400:
            sys.stderr.write(f'Server error {resp.status}\n')
            sys.stderr.flush()
            conn.close()
            continue

        while True:
            raw = resp.readline()
            if not raw:
                break
            chunk = raw.decode().strip()
            if chunk.startswith('data: '):
                data = chunk[6:].strip()
                if data:
                    sys.stdout.write(data + '\n')
                    sys.stdout.flush()

        conn.close()

    except ConnectionRefusedError:
        sys.stderr.write(f'Connection failed: Cannot reach {SERVER_URL}\n')
        sys.stderr.write('Make sure server laptop is running: python3 server.py\n')
        sys.stderr.flush()
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f'Error: {type(e).__name__}: {e}\n')
        sys.stderr.flush()
