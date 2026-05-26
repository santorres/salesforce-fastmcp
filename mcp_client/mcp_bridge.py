"""MCP Bridge — connects to Salesforce FastMCP server via JSON-RPC protocol."""
import json
import httpx
import logging
from typing import Optional
from .config import MCP_SERVER_URL, TIMEOUT_SECONDS, VERBOSE

logger = logging.getLogger(__name__)


class MCPBridge:
    """Bridge to MCP server using JSON-RPC 2.0 protocol."""

    def __init__(self, server_url: str = MCP_SERVER_URL):
        """
        Initialize MCP bridge.

        Args:
            server_url: HTTP URL to MCP server (e.g., http://localhost:8000/mcp)
        """
        self.server_url = server_url.rstrip("/")
        self.client = httpx.Client(timeout=TIMEOUT_SECONDS)
        self._tools_cache = None
        self._request_id = 0
        self._session_id = None
        self._initialized = False

    def _get_request_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    def _parse_sse_response(self, text: str) -> dict:
        """Parse Server-Sent Events (SSE) response format."""
        lines = text.strip().split("\n")
        result = {}

        for line in lines:
            if line.startswith("data: "):
                json_str = line[6:]  # Remove "data: " prefix
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from SSE line: {json_str}")

        return result

    def _send_jsonrpc(self, method: str, params: Optional[dict] = None, retry_count: int = 0) -> dict:
        """Send a JSON-RPC 2.0 request to MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": method,
        }
        if params:
            payload["params"] = params

        if VERBOSE:
            logger.info(f"JSON-RPC request: {method} {params or ''}")

        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            # Include session ID if we have one
            if self._session_id:
                headers["mcp-session-id"] = self._session_id

            response = self.client.post(
                self.server_url,
                json=payload,
                headers=headers,
            )

            # Extract session ID from response headers (even on error)
            if "mcp-session-id" in response.headers:
                self._session_id = response.headers["mcp-session-id"]
                if VERBOSE:
                    logger.info(f"Session ID: {self._session_id}")

            # If we got a 400 "Missing session ID" error but now have a session ID, retry
            if response.status_code == 400 and self._session_id and retry_count == 0:
                if VERBOSE:
                    logger.info("Retrying with session ID...")
                return self._send_jsonrpc(method, params, retry_count=1)

            response.raise_for_status()

            # Parse SSE format if response contains streaming data
            response_text = response.text
            if response_text.startswith("event:"):
                data = self._parse_sse_response(response_text)
            else:
                data = response.json()

            # Check for JSON-RPC error response
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "unknown error")
                raise RuntimeError(f"JSON-RPC error: {error_msg}")

            result = data.get("result", {})

            if VERBOSE:
                logger.info(f"JSON-RPC result: {str(result)[:200]}...")

            return result

        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to MCP server at {self.server_url}. "
                "Is it running? Try: MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py"
            )
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else "unknown"
            error_text = e.response.text if hasattr(e, 'response') and e.response else str(e)
            raise RuntimeError(f"MCP server HTTP error: {status_code} — {error_text}")

    def _initialize(self):
        """Initialize MCP protocol handshake."""
        if self._initialized:
            return

        if VERBOSE:
            logger.info("Initializing MCP protocol")

        try:
            result = self._send_jsonrpc(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "ollama-mcp-client", "version": "1.0.0"},
                },
            )

            if VERBOSE:
                logger.info(f"MCP initialized: {result.get('serverInfo', {}).get('name')}")

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            raise

    def list_tools(self) -> list[dict]:
        """
        Discover available tools from MCP server.

        Returns:
            List of tool schemas with name, description, inputSchema
        """
        if self._tools_cache is not None:
            return self._tools_cache

        if VERBOSE:
            logger.info(f"Discovering tools from {self.server_url}")

        try:
            # Initialize first if not already done
            self._initialize()

            # Then list tools
            result = self._send_jsonrpc("tools/list")
            tools = result.get("tools", [])

            if VERBOSE:
                logger.info(f"Discovered {len(tools)} tools")

            self._tools_cache = tools
            return tools

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool (e.g., "get_revenue")
            arguments: Tool arguments as dict

        Returns:
            Tool result
        """
        if VERBOSE:
            logger.info(f"Calling tool: {tool_name}({arguments})")

        try:
            result = self._send_jsonrpc(
                "tools/call",
                {"name": tool_name, "arguments": arguments},
            )
            return result

        except Exception as e:
            error_detail = str(e)
            logger.error(f"Tool call failed: {tool_name} — {error_detail}")
            return {"error": error_detail, "tool": tool_name}

    def close(self):
        """Close HTTP client."""
        self.client.close()
