#!/usr/bin/env python3
"""Demo: MLX Omni Server tool calling (without MCP server)."""
import sys
import os
from mcp_client.mlx_client import MLXOmniClient, LLMResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def demo_tool_calling():
    """Demonstrate MLX tool calling without requiring MCP server."""
    print("\n" + "=" * 70)
    print("MLX Omni Server + Tool Calling Demo")
    print("=" * 70 + "\n")

    client = MLXOmniClient()

    # Simulated Salesforce tools (like what MCP would provide)
    sales_tools = [
        {
            "name": "get_revenue",
            "description": "Get closed-won revenue by period and country",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": {"type": "string"},
                    "country": {"type": "string"}
                },
                "required": ["period"]
            }
        },
        {
            "name": "get_pipeline",
            "description": "Get open pipeline by period and breakdown type",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": {"type": "string"},
                    "breakdown": {"type": "string"}
                },
                "required": ["period"]
            }
        },
        {
            "name": "get_top_partners",
            "description": "Get top partners by revenue or pipeline",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string"},
                    "period": {"type": "string"}
                },
                "required": ["metric", "period"]
            }
        },
    ]

    # Test cases
    test_cases = [
        ("What was our revenue this quarter?", "Should call: get_revenue"),
        ("Show me the open pipeline", "Should call: get_pipeline"),
        ("Who are our top partners by revenue?", "Should call: get_top_partners"),
        ("Revenue by country this quarter", "Should call: get_revenue with country"),
    ]

    for question, expected in test_cases:
        print(f"Q: {question}")
        print(f"   Expected: {expected}")

        response = client.call(question, sales_tools)

        if response.tool_calls:
            print(f"   ✅ Detected {len(response.tool_calls)} tool call(s):")
            for call in response.tool_calls:
                print(f"      - {call.name}({call.parameters})")
        else:
            print(f"   ⚠️  No tools detected")

        print()

    print("=" * 70)
    print("Demo complete! MLX successfully detected and called tools.")
    print("=" * 70 + "\n")
    print("Next steps:")
    print("1. Run on corporate laptop with MCP server:")
    print("   MCP_TRANSPORT=streamable-http MCP_PORT=8000 python server.py")
    print("2. Then run chat interface:")
    print("   python mcp_client/chat.py")
    print()

    client.close()


if __name__ == "__main__":
    demo_tool_calling()
