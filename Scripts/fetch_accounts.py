#!/usr/bin/env python3
"""Fetch accounts from Salesforce using the FastMCP server via stdio."""

import json
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
venv_python = project_root / ".venv" / "bin" / "python"

class MCPClient:
    """Simple MCP client using stdio."""
    
    def __init__(self):
        self.process = None
        self.request_id = 0
        self._start_server()
        self._initialize()
    
    def _start_server(self):
        """Start the MCP server in stdio mode."""
        env = {}
        env["MCP_TRANSPORT"] = "stdio"
        
        self.process = subprocess.Popen(
            [str(venv_python), str(project_root / "server.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=str(project_root),
            env={**dict(subprocess.os.environ), **env}
        )
    
    def _send_jsonrpc(self, method: str, params=None):
        """Send a JSON-RPC 2.0 request and get the response."""
        self.request_id += 1
        
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }
        if params:
            payload["params"] = params
        
        try:
            self.process.stdin.write(json.dumps(payload) + "\n")
            self.process.stdin.flush()
            
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("Server closed connection")
            
            return json.loads(response_line)
        except Exception as e:
            raise RuntimeError(f"MCP communication error: {e}")
    
    def _initialize(self):
        """Initialize the MCP connection."""
        try:
            response = self._send_jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "fetch-accounts-script",
                    "version": "1.0.0"
                }
            })
            if response.get("error"):
                raise RuntimeError(f"Initialize failed: {response['error']}")
        except Exception as e:
            self.close()
            raise
    
    def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the MCP server."""
        response = self._send_jsonrpc("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return response
    
    def close(self):
        """Close the server process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

def main():
    """Main function."""
    print("🚀 Starting MCP server...")
    
    try:
        client = MCPClient()
        print("✅ Server ready. Fetching accounts...\n")
        
        response = client.call_tool("salesforce_query", {
            "q": "SELECT Id, Name, Type, Industry FROM Account LIMIT 5"
        })
        
        if response.get("error"):
            print(f"❌ Error: {response['error'].get('message', 'Unknown error')}")
            return False
        
        content = response.get("result", {}).get("content", [{}])[0].get("text", "")
        if content:
            data = json.loads(content)
            print("📊 Account Data:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print("❌ No response content")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
