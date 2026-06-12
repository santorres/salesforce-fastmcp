#!/usr/bin/env python3
"""Interactive MCP tester for Salesforce connector using stdio."""

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
                    "name": "interactive-test-script",
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

class InteractiveMCPTester:
    """Interactive test interface for MCP tools."""
    
    def __init__(self):
        self.client = None
    
    def show_menu(self):
        """Display the menu."""
        print("🔧 Available Tests:")
        print("==================")
        print("1. List all available tools")
        print("2. Query Salesforce (custom SOQL)")
        print("3. Get all Salesforce objects")
        print("4. Get recent records")
        print("5. Quick Account query")
        print("6. Quick Opportunity query")
        print("0. Exit")
        print()
    
    def list_tools(self):
        """List all available tools."""
        print("📋 Listing available tools...")
        
        try:
            response = self.client.list_tools()
            
            if response.get("error"):
                print(f"❌ Error: {response['error']}")
                return
            
            tools = response.get("result", {}).get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            
            for i, tool in enumerate(tools, 1):
                print(f"\n{i}. {tool['name']}")
                print(f"   Description: {tool['description']}")
                if tool.get("inputSchema", {}).get("properties"):
                    params = list(tool["inputSchema"]["properties"].keys())
                    print(f"   Parameters: {', '.join(params)}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def custom_query(self):
        """Execute a custom SOQL query."""
        query = input("Enter SOQL query: ").strip()
        
        if not query:
            print("❌ Query cannot be empty")
            return
        
        print(f"\n🔍 Executing: {query}")
        
        try:
            response = self.client.call_tool("salesforce_query", {"q": query})
            
            if response.get("error"):
                print(f"❌ Query Error: {response['error']}")
                return
            
            content = response.get("result", {}).get("content", [{}])[0].get("text", "")
            
            if content:
                try:
                    result = json.loads(content)
                    print("✅ Query Results:")
                    print(f"   Total Size: {result.get('totalSize', 0)}")
                    print(f"   Records: {len(result.get('records', []))}")
                    
                    if result.get("records"):
                        print("\n   Sample Record:")
                        sample = json.dumps(result["records"][0], indent=2)
                        for line in sample.split("\n"):
                            print(f"   {line}")
                except json.JSONDecodeError:
                    print(f"⚠️  Response: {content}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def get_sobjects(self):
        """Get all Salesforce objects."""
        print("📊 Getting Salesforce objects...")
        
        try:
            response = self.client.call_tool("salesforce_sobjects", {})
            
            if response.get("error"):
                print(f"❌ Error: {response['error']}")
                return
            
            content = response.get("result", {}).get("content", [{}])[0].get("text", "")
            
            if content:
                try:
                    result = json.loads(content)
                    sobjects = result.get("sobjects", [])
                    print(f"✅ Salesforce Objects:")
                    print(f"   Total Objects: {len(sobjects)}")
                    
                    if sobjects:
                        print("\n   Sample Objects:")
                        for obj in sobjects[:5]:
                            print(f"   - {obj.get('name')} ({obj.get('label')})")
                        
                        if len(sobjects) > 5:
                            print(f"   ... and {len(sobjects) - 5} more")
                except json.JSONDecodeError:
                    print(f"⚠️  Response: {content}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def get_recent(self):
        """Get recent records."""
        print("📈 Getting recent records...")
        
        try:
            response = self.client.call_tool("salesforce_recent", {"limit": 10})
            
            if response.get("error"):
                print(f"❌ Error: {response['error']}")
                return
            
            content = response.get("result", {}).get("content", [{}])[0].get("text", "")
            
            if content:
                try:
                    result = json.loads(content)
                    print("✅ Recent Records:")
                    
                    if isinstance(result, list) and len(result) > 0:
                        for i, record in enumerate(result, 1):
                            name = record.get("Name") or record.get("attributes", {}).get("type", "Unknown")
                            print(f"   {i}. {name}")
                    else:
                        print("   No recent records found")
                except json.JSONDecodeError:
                    print(f"⚠️  Response: {content}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def quick_account_query(self):
        """Quick account query."""
        print("👥 Quick Account Query...")
        
        try:
            response = self.client.call_tool("salesforce_query", {
                "q": "SELECT Id, Name, Type, Industry FROM Account LIMIT 5"
            })
            
            if response.get("error"):
                print(f"❌ Error: {response['error']}")
                return
            
            content = response.get("result", {}).get("content", [{}])[0].get("text", "")
            
            if content:
                try:
                    result = json.loads(content)
                    print("✅ Account Results:")
                    print(f"   Total Accounts: {result.get('totalSize', 0)}")
                    
                    for i, account in enumerate(result.get("records", []), 1):
                        name = account.get("Name", "Unknown")
                        account_type = account.get("Type", "No Type")
                        industry = account.get("Industry", "No Industry")
                        print(f"   {i}. {name} ({account_type}) - {industry}")
                except json.JSONDecodeError:
                    print(f"⚠️  Response: {content}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def quick_opportunity_query(self):
        """Quick opportunity query."""
        print("💰 Quick Opportunity Query...")
        
        try:
            response = self.client.call_tool("salesforce_query", {
                "q": "SELECT Id, Name, StageName, Amount FROM Opportunity LIMIT 5"
            })
            
            if response.get("error"):
                print(f"❌ Error: {response['error']}")
                return
            
            content = response.get("result", {}).get("content", [{}])[0].get("text", "")
            
            if content:
                try:
                    result = json.loads(content)
                    print("✅ Opportunity Results:")
                    print(f"   Total Opportunities: {result.get('totalSize', 0)}")
                    
                    for i, opp in enumerate(result.get("records", []), 1):
                        name = opp.get("Name", "Unknown")
                        stage = opp.get("StageName", "Unknown")
                        amount = opp.get("Amount", "0")
                        print(f"   {i}. {name} - {stage} (${amount})")
                except json.JSONDecodeError:
                    print(f"⚠️  Response: {content}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_choice(self, choice: str) -> bool:
        """Handle user menu choice. Returns False if user wants to exit."""
        print()
        
        if choice == "1":
            self.list_tools()
        elif choice == "2":
            self.custom_query()
        elif choice == "3":
            self.get_sobjects()
        elif choice == "4":
            self.get_recent()
        elif choice == "5":
            self.quick_account_query()
        elif choice == "6":
            self.quick_opportunity_query()
        elif choice == "0":
            return False
        else:
            print("❌ Invalid choice. Please try again.\n")
            return True
        
        return True
    
    def run(self):
        """Run the interactive tester."""
        print("🚀 Starting Salesforce MCP Server...\n")
        
        try:
            self.client = MCPClient()
            print("✅ Connected to MCP server!\n")
            
            while True:
                self.show_menu()
                choice = input("Choose an option (0-6): ").strip()
                
                should_continue = self.handle_choice(choice)
                if not should_continue:
                    break
                
                print("\n" + "=" * 50 + "\n")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if self.client:
                self.client.close()
            
            print("\n🧹 Shutting down...")
            print("👋 Thanks for testing the Salesforce MCP Connector!")

def main():
    """Main function."""
    tester = InteractiveMCPTester()
    tester.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        sys.exit(0)
