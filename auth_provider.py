"""Authentication providers for Salesforce MCP connector.

Supports multiple authentication methods:
1. SF CLI: Uses sf command-line tool (recommended)
2. Browser Cookie: Uses environment variables (fallback)
3. Direct OAuth: Future implementation

Each provider implements the AuthProvider interface and handles credential
retrieval and optional refresh logic.
"""

import asyncio
import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Credentials:
    """Container for Salesforce authentication credentials."""
    base_url: str
    access_token: str
    username: Optional[str] = None
    org_id: Optional[str] = None
    auth_method: str = "unknown"


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    async def get_credentials(self) -> Credentials:
        """Retrieve Salesforce credentials.
        
        Returns:
            Credentials object with base_url and access_token
            
        Raises:
            Exception: If credentials cannot be obtained
        """
        pass

    @abstractmethod
    async def refresh_if_needed(self) -> bool:
        """Refresh credentials if they have expired.
        
        Returns:
            True if refresh was performed, False if no refresh needed
            
        Raises:
            Exception: If refresh fails
        """
        pass


class BrowserCookieAuthProvider(AuthProvider):
    """Authentication using browser cookie/session token from environment variables.
    
    This is the original method: user authenticates via browser and provides
    the access token via environment variables.
    
    Required environment variables:
        SALESFORCE_BASE_URL: Instance URL (e.g., https://semperis.my.salesforce.com)
        SALESFORCE_ACCESS_TOKEN or SALESFORCE_SID: Access token
    """

    def __init__(self):
        self.base_url = os.getenv("SALESFORCE_BASE_URL")
        self.access_token = os.getenv("SALESFORCE_ACCESS_TOKEN") or os.getenv("SALESFORCE_SID")

    async def get_credentials(self) -> Credentials:
        """Return credentials from environment variables."""
        if not self.base_url or not self.access_token:
            raise Exception(
                "Browser cookie auth requires SALESFORCE_BASE_URL and "
                "(SALESFORCE_ACCESS_TOKEN or SALESFORCE_SID) environment variables"
            )

        logger.info("Using browser cookie authentication")
        return Credentials(
            base_url=self.base_url,
            access_token=self.access_token,
            auth_method="browser_cookie"
        )

    async def refresh_if_needed(self) -> bool:
        """Browser cookies don't auto-refresh; return False."""
        logger.debug("Browser cookie auth: refresh not applicable")
        return False


class SFCliAuthProvider(AuthProvider):
    """Authentication using Salesforce CLI (sf command).
    
    This provider queries the SF CLI for authenticated orgs and retrieves
    access tokens from the CLI's secure storage.
    
    The SF CLI handles token refresh automatically, making this the most
    secure and low-maintenance authentication method.
    
    Optional environment variables:
        SALESFORCE_ORG_USERNAME: Username of the org to use (default: first auth'd org)
        SALESFORCE_CLI_PATH: Path to sf executable (default: 'sf')
    """

    def __init__(self):
        self.cli_path = os.getenv("SALESFORCE_CLI_PATH", "sf")
        self.org_username = os.getenv("SALESFORCE_ORG_USERNAME")
        self._credentials_cache: Optional[Credentials] = None

    async def get_credentials(self) -> Credentials:
        """Retrieve credentials from SF CLI."""
        if self._credentials_cache:
            logger.debug("SF CLI auth: returning cached credentials")
            return self._credentials_cache

        # Get list of authenticated orgs
        org_list = await self._get_org_list()
        if not org_list:
            raise Exception(
                "No authenticated orgs found in SF CLI. "
                "Run 'sf org login web' to authenticate first."
            )

        # Determine which org to use
        target_org = await self._select_org(org_list)

        # Get access token for the selected org
        access_token = await self._get_access_token(target_org["username"])

        # Append REST API path to instance URL if not already present
        instance_url = target_org["instanceUrl"]
        api_version = target_org.get("instanceApiVersion", "59.0")
        if not instance_url.endswith("/services/data"):
            base_url = f"{instance_url}/services/data/v{api_version}"
        else:
            base_url = instance_url

        self._credentials_cache = Credentials(
            base_url=base_url,
            access_token=access_token,
            username=target_org["username"],
            org_id=target_org["orgId"],
            auth_method="sf_cli"
        )

        logger.info(f"SF CLI auth: using org {target_org['username']} ({target_org['orgId']})")
        return self._credentials_cache

    async def _get_org_list(self) -> list[dict]:
        """Get list of authenticated orgs from SF CLI."""
        try:
            result = await self._run_command([self.cli_path, "org", "list", "--json"])
            data = json.loads(result)

            if data.get("status") != 0:
                error_msg = data.get("result", [{}])[0].get("message", "Unknown error")
                raise Exception(f"SF CLI error: {error_msg}")

            # Collect all orgs from different categories
            orgs = []
            org_data = data.get("result", {})

            for category in ["nonScratchOrgs", "scratchOrgs", "other"]:
                if category in org_data:
                    orgs.extend(org_data[category])

            if not orgs:
                devhubs = org_data.get("devHubs", [])
                if devhubs:
                    orgs.extend(devhubs)

            return orgs

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse SF CLI output: {e}")
        except subprocess.TimeoutExpired:
            raise Exception("SF CLI command timed out")
        except FileNotFoundError:
            raise Exception(
                f"SF CLI not found at '{self.cli_path}'. "
                "Install Salesforce CLI: https://developer.salesforce.com/tools/salesforcecli"
            )

    async def _select_org(self, orgs: list[dict]) -> dict:
        """Select an org to use.
        
        If SALESFORCE_ORG_USERNAME is set, use that org.
        Otherwise, use the first available org.
        """
        if self.org_username:
            for org in orgs:
                if org.get("username") == self.org_username:
                    return org
            raise Exception(f"Org '{self.org_username}' not found in SF CLI")

        if not orgs:
            raise Exception("No authenticated orgs found")

        # Use first org
        selected = orgs[0]
        logger.debug(f"Using first available org: {selected.get('username')}")
        return selected

    async def _get_access_token(self, username: str) -> str:
        """Get access token for a specific org."""
        try:
            # Run command with stdin='y' to auto-confirm the prompt
            result = await self._run_command_with_input(
                [self.cli_path, "org", "auth", "show-access-token", "-o", username],
                input_text="y\n"
            )

            # Parse the output to extract the token
            # Output format is a table with token in the second cell
            # Line format: │ Access Token │ <token> │
            for line in result.split("\n"):
                if "Access Token" in line and "│" in line:
                    # Split by │ and get the token (should be the 3rd field)
                    parts = [p.strip() for p in line.split("│")]
                    # parts[0] = '', parts[1] = 'Access Token', parts[2] = token, parts[3] = ''
                    if len(parts) >= 3 and parts[1] == "Access Token":
                        token = parts[2]
                        if token and not token.startswith("[") and token != "Access Token":
                            return token

            raise Exception(f"Could not parse access token from SF CLI output")

        except subprocess.TimeoutExpired:
            raise Exception("SF CLI command timed out while getting access token")

    async def _run_command(self, cmd: list[str]) -> str:
        """Run a shell command asynchronously."""
        try:
            # Use run_in_executor with current event loop
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._run_subprocess, cmd),
                timeout=30.0  # Increased timeout for slower systems/CI
            )
            return result
        except asyncio.TimeoutError:
            raise Exception(f"SF CLI command timed out after 30 seconds: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Command failed: {e.stderr or e.stdout}")

    async def _run_command_with_input(self, cmd: list[str], input_text: str) -> str:
        """Run a shell command with stdin asynchronously."""
        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None, self._run_subprocess_with_input, cmd, input_text
                ),
                timeout=30.0
            )
            return result
        except asyncio.TimeoutError:
            raise Exception(f"SF CLI command timed out after 30 seconds: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Command failed: {e.stderr or e.stdout}")

    async def refresh_if_needed(self) -> bool:
        """SF CLI handles token refresh automatically; return False."""
        logger.debug("SF CLI auth: refresh not applicable (handled by SF CLI)")
        # Invalidate cache to force refresh on next get_credentials call
        self._credentials_cache = None
        return False

    @staticmethod
    def _run_subprocess(cmd: list[str]) -> str:
        """Synchronous subprocess wrapper."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0 and "Error" in result.stdout:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result.stdout

    @staticmethod
    def _run_subprocess_with_input(cmd: list[str], input_text: str) -> str:
        """Synchronous subprocess wrapper with stdin."""
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0 and "Error" in result.stdout:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result.stdout


class DirectOAuthAuthProvider(AuthProvider):
    """Direct OAuth 2.0 authentication (Future implementation).
    
    This will implement the OAuth Web Server Flow, allowing users to
    authenticate once and get automatic token refresh.
    
    Status: NOT YET IMPLEMENTED
    """

    async def get_credentials(self) -> Credentials:
        raise NotImplementedError(
            "Direct OAuth authentication is not yet implemented. "
            "Use SF CLI or browser cookie authentication for now."
        )

    async def refresh_if_needed(self) -> bool:
        raise NotImplementedError("Direct OAuth not implemented")


def create_auth_provider(auth_method: Optional[str] = None) -> AuthProvider:
    """Factory function to create appropriate authentication provider.
    
    Args:
        auth_method: Explicit auth method to use. If None, auto-detect.
                    Options: "sf_cli", "browser_cookie", "direct_oauth", "auto"
    
    Returns:
        AuthProvider instance
        
    Raises:
        Exception: If no valid auth method can be determined
    """
    # Determine which auth method to use
    if not auth_method:
        auth_method = os.getenv("SALESFORCE_AUTH_METHOD", "auto")

    auth_method = auth_method.lower().strip()

    # Handle auto-detection
    if auth_method == "auto":
        logger.debug("Auth method set to auto-detect")
        # Try SF CLI first (more secure)
        if _is_sf_cli_available():
            logger.debug("SF CLI detected, using SF CLI authentication")
            return SFCliAuthProvider()
        # Fall back to browser cookie
        elif _are_browser_cookie_env_vars_set():
            logger.debug("SF CLI not available, falling back to browser cookie authentication")
            return BrowserCookieAuthProvider()
        else:
            raise Exception(
                "No valid authentication method available.\n\n"
                "Option 1 (Recommended): Use SF CLI\n"
                "  1. Install: https://developer.salesforce.com/tools/salesforcecli\n"
                "  2. Authenticate: sf org login web\n"
                "  3. Set: export SALESFORCE_AUTH_METHOD=sf_cli\n\n"
                "Option 2 (Fallback): Use Browser Cookie\n"
                "  1. Get token from browser console\n"
                "  2. Set: export SALESFORCE_BASE_URL=<instance_url>\n"
                "  3. Set: export SALESFORCE_ACCESS_TOKEN=<token>\n"
                "  4. Set: export SALESFORCE_AUTH_METHOD=browser_cookie\n"
            )

    # Explicit auth method selection
    if auth_method == "sf_cli":
        return SFCliAuthProvider()
    elif auth_method == "browser_cookie":
        return BrowserCookieAuthProvider()
    elif auth_method == "direct_oauth":
        return DirectOAuthAuthProvider()
    else:
        raise Exception(
            f"Unknown authentication method: '{auth_method}'. "
            "Valid options: sf_cli, browser_cookie, direct_oauth, auto"
        )


def _is_sf_cli_available() -> bool:
    """Check if SF CLI is installed and available."""
    cli_path = os.getenv("SALESFORCE_CLI_PATH", "sf")
    try:
        result = subprocess.run(
            [cli_path, "--version"],
            capture_output=True,
            timeout=5,
            check=False
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _are_browser_cookie_env_vars_set() -> bool:
    """Check if browser cookie environment variables are set."""
    base_url = os.getenv("SALESFORCE_BASE_URL")
    token = os.getenv("SALESFORCE_ACCESS_TOKEN") or os.getenv("SALESFORCE_SID")
    return bool(base_url and token)
