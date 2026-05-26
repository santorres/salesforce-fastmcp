"""Ollama LLM backend — handles tool calling and reasoning."""
import json
import re
import httpx
import logging
from typing import Optional
from dataclasses import dataclass

from .config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_TEMPERATURE,
    OLLAMA_TOP_P,
    VERBOSE,
    TIMEOUT_SECONDS,
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


class OllamaClient:
    """Ollama LLM client with tool calling support."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=TIMEOUT_SECONDS)

    def _format_tools_for_prompt(self, tools: list[dict]) -> str:
        """Format tool schema for Nous-Hermes tool calling."""
        tools_text = "Available tools:\n"
        for tool in tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "No description")
            params = tool.get("inputSchema", {}).get("properties", {})

            param_list = ", ".join(params.keys()) if params else "none"
            tools_text += f"  - {name}: {desc} (params: {param_list})\n"

        return tools_text

    def _parse_tool_calls(self, text: str) -> list[ToolCall]:
        """Parse tool calls from LLM response (Nous-Hermes format)."""
        calls = []

        # Look for XML-style tool calls: <tool_call name="tool_name">{"param": "value"}</tool_call>
        pattern = r'<tool_call\s+name="([^"]+)">({.*?})</tool_call>'
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2)
            try:
                params = json.loads(params_str)
                calls.append(ToolCall(name=tool_name, parameters=params))
                if VERBOSE:
                    logger.info(f"Parsed tool call: {tool_name}({params})")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool params for {tool_name}: {e}")

        return calls

    def _build_system_prompt(self, tools: list[dict]) -> str:
        """Build system prompt with tool calling instructions."""
        tools_desc = self._format_tools_for_prompt(tools)

        return f"""You are a Salesforce channel analytics assistant. You have access to tools that query sales data.

{tools_desc}

When you need to call a tool, use this format:
<tool_call name="tool_name">{{"param1": "value1", "param2": "value2"}}</tool_call>

You can call multiple tools in sequence. After receiving tool results, analyze them and provide a clear answer to the user's question.

Be concise and focus on business insights relevant to channel directors (revenue, pipeline, partner performance, risk, etc.)."""

    def call(
        self,
        question: str,
        tools: list[dict],
        conversation_history: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """
        Send a question to Ollama with available tools.

        Args:
            question: User's question
            tools: List of MCP tool schemas
            conversation_history: Previous messages for multi-turn

        Returns:
            LLMResponse with text and parsed tool calls
        """
        system_prompt = self._build_system_prompt(tools)

        # Build message history
        messages = conversation_history or []
        messages.append({"role": "user", "content": question})

        if VERBOSE:
            logger.info(f"Calling Ollama ({self.model}) with {len(tools)} tools available")

        try:
            response = self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": OLLAMA_TEMPERATURE,
                        "top_p": OLLAMA_TOP_P,
                        "num_predict": 1024,  # Limit output length
                    },
                },
            )
            response.raise_for_status()

            data = response.json()
            text = data.get("message", {}).get("content", "")

            if VERBOSE:
                logger.info(f"Ollama response: {text[:200]}...")

            tool_calls = self._parse_tool_calls(text)

            return LLMResponse(text=text, tool_calls=tool_calls, raw=data)

        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Try: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.text}")

    def close(self):
        """Close HTTP client."""
        self.client.close()
