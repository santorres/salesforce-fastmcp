"""MLX Omni Server LLM backend — handles tool calling and reasoning."""
import json
import logging
from typing import Optional
from dataclasses import dataclass
from openai import OpenAI

from .config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_TEMPERATURE,
    OLLAMA_TOP_P,
    VERBOSE,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool call."""
    name: str
    parameters: dict


@dataclass
class LLMResponse:
    """LLM response with optional tool calls."""
    text: str
    tool_calls: list[ToolCall]
    raw: dict


class MLXOmniClient:
    """MLX Omni Server LLM client with OpenAI-compatible tool calling."""

    def __init__(self, base_url: str = "http://localhost:8000/v1", model: str = "mlx"):
        """
        Initialize MLX Omni client.

        Args:
            base_url: OpenAI-compatible endpoint (MLX Omni Server default: http://localhost:8000/v1)
            model: Model name (MLX Omni uses "mlx" by default)
        """
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key="not-needed", base_url=base_url)

    def _convert_mcp_tools_to_openai(self, tools: list[dict]) -> list[dict]:
        """Convert MCP tool schemas to OpenAI-compatible function calling format."""
        openai_tools = []

        for tool in tools:
            name = tool.get("name", "")
            description = tool.get("description", "No description")

            # Extract parameters from MCP inputSchema
            input_schema = tool.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])

            # Build OpenAI-compatible function schema (same as Ollama format)
            openai_tool = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description.split("\n")[0],  # Use first line only
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            }

            openai_tools.append(openai_tool)

        return openai_tools

    def _format_tools_for_prompt(self, tools: list[dict]) -> str:
        """Format tool schema for display."""
        tools_text = "Available tools:\n"
        for tool in tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "No description")
            params = tool.get("inputSchema", {}).get("properties", {})

            param_list = ", ".join(params.keys()) if params else "none"
            tools_text += f"  - {name}: {desc} (params: {param_list})\n"

        return tools_text



    def call(
        self,
        question: str,
        tools: list[dict],
        conversation_history: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """
        Send a question to MLX Omni Server with available tools using native function calling.

        Args:
            question: User's question
            tools: List of MCP tool schemas
            conversation_history: Previous messages for multi-turn

        Returns:
            LLMResponse with text and parsed tool calls
        """
        # Build message history
        messages = conversation_history or []
        messages.append({"role": "user", "content": question})

        if VERBOSE:
            logger.info(f"Calling MLX Omni Server ({self.model}) with {len(tools)} tools available")

        try:
            # Convert MCP tools to OpenAI format
            openai_tools = self._convert_mcp_tools_to_openai(tools)

            if VERBOSE:
                logger.info(f"Converted {len(openai_tools)} MCP tools to OpenAI format")

            # Use OpenAI SDK with native function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                temperature=OLLAMA_TEMPERATURE,
                max_tokens=1024,
            )

            if VERBOSE:
                logger.info(f"MLX response: {response.choices[0].message.content[:200] if response.choices[0].message.content else '(no text)'}")

            text = response.choices[0].message.content or ""
            tool_calls = []

            # Parse native tool_calls from response
            if response.choices[0].message.tool_calls:
                if VERBOSE:
                    logger.info(f"Tool calls in response: {len(response.choices[0].message.tool_calls)}")

                for call in response.choices[0].message.tool_calls:
                    tool_name = call.function.name
                    # Parse arguments (OpenAI SDK returns as JSON string)
                    try:
                        params = json.loads(call.function.arguments) if isinstance(call.function.arguments, str) else call.function.arguments
                    except json.JSONDecodeError:
                        params = {}

                    if VERBOSE:
                        logger.info(f"Parsed: name='{tool_name}', params={params}")

                    if tool_name:
                        tool_calls.append(ToolCall(name=tool_name, parameters=params))

            return LLMResponse(text=text, tool_calls=tool_calls, raw=response.model_dump())

        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg or "refused" in error_msg.lower():
                raise RuntimeError(
                    f"Cannot connect to MLX Omni Server at {self.base_url}. "
                    "Is it running? Try: `mlx_omni_server` or check localhost:8000"
                )
            raise RuntimeError(f"MLX API error: {error_msg}")

    def close(self):
        """Close HTTP client."""
        self.client.close()
