"""MCP Bridge (stdio mode) — standard MCP protocol over stdin/stdout."""
import json
import subprocess
import logging
from typing import Optional

from .config import MCP_STDIO_CMD, VERBOSE

logger = logging.getLogger(__name__)


class MCPBridgeStdio:
    """Bridge to MCP server using stdio (standard MCP transport)."""

    def __init__(self, cmd: str = MCP_STDIO_CMD):
        """
        Initialize MCP bridge with stdio server.

        Args:
            cmd: Command to spawn MCP server (e.g., "python3 server.py")
        """
        self.cmd = cmd
        self.process = None
        self._tools_cache = None
        self._request_id = 0
        self._start_server()

    def _start_server(self):
        """Start the MCP server subprocess."""
        if VERBOSE:
            logger.info(f"Starting MCP server: {self.cmd}")

        try:
            self.process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            logger.info("MCP server process started")
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}")

    def _get_request_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    def _send_jsonrpc(self, method: str, params: Optional[dict] = None) -> dict:
        """Send a JSON-RPC 2.0 request to MCP server via stdio."""
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("MCP server process is not running")

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
            # Send request to server stdin
            self.process.stdin.write(json.dumps(payload) + "\n")
            self.process.stdin.flush()

            # Read response from stdout
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("MCP server closed connection")

            data = json.loads(response_line)

            # Check for JSON-RPC error response
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "unknown error")
                raise RuntimeError(f"JSON-RPC error: {error_msg}")

            result = data.get("result", {})

            if VERBOSE:
                logger.info(f"JSON-RPC result: {str(result)[:200]}...")

            return result

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse MCP response: {e}")
        except Exception as e:
            raise RuntimeError(f"MCP communication error: {e}")

    def list_tools(self) -> list[dict]:
        """
        Discover available tools from MCP server.

        Returns:
            List of tool schemas with name, description, inputSchema
        """
        if self._tools_cache is not None:
            return self._tools_cache

        if VERBOSE:
            logger.info("Discovering tools from MCP server")

        try:
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
        """Close MCP server subprocess."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("MCP server process closed")
