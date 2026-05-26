"""REPL Chat Interface — interactive Ollama + MCP client."""
import sys
import json
import time
import logging
from typing import Optional

from .config import (
    get_config_summary,
    LOG_LEVEL,
    VERBOSE,
    MAX_RETRIES,
    RETRY_DELAY_MS,
)
from .ollama_llm import OllamaClient, ToolCall
from .mcp_bridge import MCPBridge

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ChatSession:
    """Interactive chat session with Ollama + MCP."""

    def __init__(self, mcp_url: Optional[str] = None, ollama_url: Optional[str] = None):
        """Initialize chat session."""
        self.mcp = MCPBridge(mcp_url) if mcp_url else MCPBridge()
        self.ollama = OllamaClient(base_url=ollama_url) if ollama_url else OllamaClient()
        self.tools = self.mcp.list_tools()
        self.conversation_history = []

        logger.info(f"Initialized chat session with {len(self.tools)} tools")

    def _execute_tool_call(self, tool_call: ToolCall, retries: int = 0) -> dict:
        """Execute a tool call with retry logic."""
        try:
            result = self.mcp.call_tool(tool_call.name, tool_call.parameters)

            # Check if result contains an error
            if isinstance(result, dict) and "error" in result:
                if retries < MAX_RETRIES:
                    logger.warning(
                        f"Tool {tool_call.name} failed (retry {retries + 1}/{MAX_RETRIES}): "
                        f"{result.get('error', 'unknown')}"
                    )
                    time.sleep(RETRY_DELAY_MS / 1000.0)
                    return self._execute_tool_call(tool_call, retries + 1)
                else:
                    logger.error(
                        f"Tool {tool_call.name} failed after {MAX_RETRIES} retries: "
                        f"{result.get('error')}"
                    )
                    return {
                        "error": f"Tool failed after {MAX_RETRIES} retries",
                        "tool": tool_call.name,
                        "details": result,
                    }

            return result

        except Exception as e:
            logger.error(f"Exception calling {tool_call.name}: {e}")
            return {"error": str(e), "tool": tool_call.name}

    def _execute_tool_calls(self, tool_calls: list[ToolCall]) -> list[dict]:
        """Execute multiple tool calls, collecting results."""
        results = []
        for tool_call in tool_calls:
            result = self._execute_tool_call(tool_call)
            results.append(
                {
                    "tool": tool_call.name,
                    "result": result,
                }
            )
        return results

    def _format_tool_results(self, results: list[dict]) -> str:
        """Format tool results for display."""
        output = []
        for item in results:
            tool_name = item["tool"]
            result = item["result"]

            if "error" in result:
                output.append(f"❌ {tool_name}: {result['error']}")
            else:
                # Truncate large results
                result_str = json.dumps(result, indent=2)
                if len(result_str) > 1000:
                    result_str = result_str[:1000] + "\n... (truncated)"
                output.append(f"✅ {tool_name}:\n{result_str}")

        return "\n\n".join(output)

    def chat(self, question: str) -> str:
        """
        Process a question and return an answer.

        Flow:
        1. Send question + tools to Ollama
        2. Parse tool calls from response
        3. Execute tools (with retries)
        4. Get final answer from Ollama with tool results
        """
        logger.info(f"User: {question}")

        # Step 1: Ask Ollama which tools to use
        llm_response = self.ollama.call(question, self.tools, self.conversation_history)

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": question})

        # Step 2: Check for tool calls
        if not llm_response.tool_calls:
            # No tools needed, return LLM response directly
            answer = llm_response.text
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer

        # Step 3: Execute tools
        logger.info(f"Executing {len(llm_response.tool_calls)} tool calls")
        tool_results = self._execute_tool_calls(llm_response.tool_calls)
        formatted_results = self._format_tool_results(tool_results)

        # Step 4: Ask Ollama to synthesize final answer with tool results
        synthesis_prompt = (
            f"Based on these tool results:\n\n{formatted_results}\n\n"
            f"Provide a concise, business-focused answer to: {question}"
        )

        final_response = self.ollama.call(
            synthesis_prompt, self.tools, self.conversation_history
        )

        answer = final_response.text
        self.conversation_history.append({"role": "assistant", "content": answer})

        return answer

    def close(self):
        """Clean up resources."""
        self.mcp.close()
        self.ollama.close()


def main():
    """Interactive REPL chat interface."""
    print("\n" + "=" * 70)
    print("Salesforce Channel Analytics — Local LLM Interface")
    print("=" * 70)
    print(get_config_summary())
    print("\nType 'quit' or 'exit' to end session")
    print("=" * 70 + "\n")

    try:
        session = ChatSession()

        while True:
            try:
                question = input("You: ").strip()

                if not question:
                    continue

                if question.lower() in ("quit", "exit", "q"):
                    print("\nGoodbye!")
                    break

                print("\n" + "-" * 70)
                answer = session.chat(question)
                print(f"\nAssistant: {answer}\n")
                print("-" * 70 + "\n")

            except KeyboardInterrupt:
                print("\n\nSession interrupted")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}\n")

        session.close()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
