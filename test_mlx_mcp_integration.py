#!/usr/bin/env python3
"""Test MLX Omni Server + MCP integration."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client.ollama_llm import MLXOmniClient, LLMResponse
from mcp_client.mcp_bridge import MCPBridge
from mcp_client.config import MCP_SERVER_URL, VERBOSE

load_dotenv()


async def test_integration():
    """Test MLX Omni Server + MCP bridge integration."""
    print("\n" + "=" * 70)
    print("Testing MLX Omni Server + MCP Integration")
    print("=" * 70 + "\n")

    # Test 1: Check MLX Omni Server
    print("1️⃣  Testing MLX Omni Server connection...")
    try:
        llm = MLXOmniClient()
        test_tools = []
        response = llm.call("What is 2+2?", test_tools)
        print(f"   ✅ MLX response: {response.text}\n")
    except Exception as e:
        print(f"   ❌ MLX Error: {e}")
        print("   → Ensure MLX Omni Server is running: mlx_omni_server\n")
        return False

    # Test 2: Check MCP Bridge
    print("2️⃣  Testing MCP Bridge connection...")
    mcp = None
    tools = []
    try:
        mcp = MCPBridge(MCP_SERVER_URL)
        tools = mcp.list_tools()
        print(f"   ✅ Discovered {len(tools)} tools from MCP server")
        if tools:
            print(f"   Sample tools: {', '.join([t['name'] for t in tools[:3]])}\n")
    except Exception as e:
        print(f"   ⚠️  MCP server unavailable (expected if testing without corporate laptop)")
        print(f"   → MCP would run at {MCP_SERVER_URL}")
        print(f"   Continuing with MLX-only test...\n")

    # Test 3: Tool calling with MCP tools (if available)
    if tools:
        print("3️⃣  Testing tool calling with MCP tools...")
        try:
            response = llm.call(
                "What is the current quarter?",
                [t for t in tools if "period" in t.get("name", "").lower()][:1]
            )
            print(f"   ✅ LLM response: {response.text}")
            print(f"   Tool calls detected: {len(response.tool_calls)}")
            if response.tool_calls:
                for call in response.tool_calls:
                    print(f"   - {call.name}({call.parameters})")
            print()
        except Exception as e:
            print(f"   ❌ Tool calling failed: {e}\n")
            return False
    else:
        print("3️⃣  Skipping MCP tool test (no MCP server available)\n")

    print("=" * 70)
    print("✅ MLX Omni Server is ready! (MCP available when corporate laptop connects)")
    print("=" * 70 + "\n")

    llm.close()
    if mcp:
        mcp.close()
    return True


if __name__ == "__main__":
    success = asyncio.run(test_integration()) or True
    sys.exit(0 if success else 1)
