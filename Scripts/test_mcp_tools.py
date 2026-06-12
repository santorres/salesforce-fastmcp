#!/usr/bin/env python3
"""Test MCP tools using the FastMCP server via stdio."""

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
                    "name": "test-mcp-tools-script",
                    "version": "1.0.0"
                }
            })
            if response.get("error"):
                raise RuntimeError(f"Initialize failed: {response['error']}")
        except Exception as e:
            self.close()
            raise
    
    def list_tools(self):
        """List available tools."""
        response = self._send_jsonrpc("tools/list")
        return response
    
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

class MCPTester:
    """Test suite for MCP tools."""
    
    def __init__(self):
        self.client = None
    
    def start(self):
        """Initialize the client."""
        self.client = MCPClient()
    
    def test_list_tools(self) -> bool:
        """Test tools/list method."""
        print("📋 Testing tools/list...")
        
        try:
            response = self.client.list_tools()
            
            if response.get("error"):
                print(f"❌ tools/list failed: {response['error']}")
                return False
            
            tools = response.get("result", {}).get("tools", [])
            expected_tools = ["salesforce_query", "salesforce_sobjects", "salesforce_recent"]
            
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
            
            has_all_tools = all(
                any(tool["name"] == expected for tool in tools)
                for expected in expected_tools
            )
            
            if has_all_tools:
                print("✅ All expected tools are available\n")
                return True
            else:
                print("❌ Some expected tools are missing\n")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_tool(self, tool_name: str, args=None) -> bool:
        """Test a specific tool."""
        if args is None:
            args = {}
        
        print(f"🔧 Testing {tool_name}...")
        
        try:
            response = self.client.call_tool(tool_name, args)
            
            if response.get("error"):
                print(f"❌ {tool_name} failed: {response['error']}")
                return False
            
            content = response.get("result", {}).get("content", [{}])[0].get("text", "")
            
            if content:
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        print(f"✅ {tool_name} returned data: {type(data).__name__} with keys: {keys}")
                    elif isinstance(data, list):
                        print(f"✅ {tool_name} returned data: list with {len(data)} items")
                    else:
                        print(f"✅ {tool_name} returned data: {type(data).__name__}")
                except json.JSONDecodeError:
                    print(f"✅ {tool_name} returned text ({len(content)} chars)")
            else:
                print(f"⚠️  {tool_name} returned no content")
            
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        results = {
            "serverStart": False,
            "listTools": False,
            "query": False,
            "sobjects": False,
            "recent": False
        }
        
        try:
            print("🚀 Starting MCP server...\n")
            self.start()
            results["serverStart"] = True
            
            results["listTools"] = self.test_list_tools()
            results["query"] = self.test_tool("salesforce_query", {"q": "SELECT Id FROM Account LIMIT 1"})
            results["sobjects"] = self.test_tool("salesforce_sobjects")
            results["recent"] = self.test_tool("salesforce_recent", {"limit": 5})
            
        except Exception as e:
            print(f"Test suite error: {e}")
        finally:
            self.cleanup()
        
        return results
    
    def print_summary(self, results):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("📊 MCP SERVER TEST RESULTS")
        print("=" * 50)
        
        tests = [
            ("Server Startup", results["serverStart"]),
            ("List Tools", results["listTools"]),
            ("Salesforce Query", results["query"]),
            ("Salesforce SObjects", results["sobjects"]),
            ("Salesforce Recent", results["recent"])
        ]
        
        for name, passed in tests:
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
        
        passed_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print(f"\n📈 Summary: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("🎉 All tests passed! Your Salesforce MCP connector is working perfectly!")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
    
    def cleanup(self):
        """Clean up resources."""
        if self.client:
            self.client.close()

def main():
    """Main function."""
    tester = MCPTester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main()
