#!/usr/bin/env python3
"""Debug script: Show exactly what data flows through tool execution."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client.mcp_bridge import MCPBridge
from mcp_client.config import MCP_SERVER_URL

def test_tool_directly():
    """Test tool execution directly through MCP bridge."""
    print("\n" + "=" * 70)
    print("Debug: Direct MCP Tool Execution")
    print("=" * 70 + "\n")

    try:
        mcp = MCPBridge(MCP_SERVER_URL)
        print(f"✅ Connected to MCP at {MCP_SERVER_URL}\n")

        # List available tools
        tools = mcp.list_tools()
        print(f"✅ Found {len(tools)} tools\n")

        # Find revenue tool
        revenue_tool = next((t for t in tools if t["name"] == "get_revenue"), None)
        if not revenue_tool:
            print("❌ get_revenue tool not found")
            return False

        print("Calling get_revenue with LAST_QUARTER and country breakdown...\n")
        result = mcp.call_tool("get_revenue", {
            "period": "LAST_QUARTER",
            "breakdown": "country"
        })

        print("=" * 70)
        print("RAW TOOL RESULT:")
        print("=" * 70)
        print(json.dumps(result, indent=2)[:2000])
        print("\n" + ("..." if len(json.dumps(result)) > 2000 else ""))

        # Parse the actual data
        if "content" in result:
            # MCP wraps results in content[]
            content = result.get("content", [])
            if content and "text" in content[0]:
                data_str = content[0]["text"]
                try:
                    data = json.loads(data_str)
                    if "data" in data:
                        print("\n" + "=" * 70)
                        print("PARSED DATA (what should be used in synthesis):")
                        print("=" * 70)
                        for country, values in data["data"].items():
                            revenue = values.get("totalRevenue", 0)
                            deals = values.get("dealCount", 0)
                            print(f"{country}: ${revenue:,.2f} ({deals} deals)")
                except json.JSONDecodeError:
                    print("Could not parse data as JSON")

        mcp.close()
        print("\n✅ Tool execution succeeded")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nNote: This requires MCP server running at {MCP_SERVER_URL}")
        print("On corporate laptop, run:")
        print("  MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py")
        return False


if __name__ == "__main__":
    success = test_tool_directly()
    sys.exit(0 if success else 1)
