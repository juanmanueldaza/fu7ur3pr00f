"""HTTP-based MCP client base class.

Provides a reusable base class for MCP clients that communicate
with HTTP APIs. Eliminates code duplication across 8+ client
implementations by consolidating:
- Connection lifecycle (connect, disconnect, is_connected)
- HTTP client initialization with configurable headers/timeout
- Tool call error handling wrapper
- Common patterns for JSON response formatting

Usage:
    class MyAPIClient(HTTPMCPClient):
        BASE_URL = "https://api.example.com"
        DEFAULT_HEADERS = {"Accept": "application/json"}

        async def list_tools(self) -> list[str]:
            return ["my_tool"]

        async def _tool_my_tool(self, args: dict[str, Any]) -> MCPToolResult:
            # Implementation
            ...
"""

import json
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, cast

import httpx

from .base import MCPClient, MCPConnectionError, MCPToolError, MCPToolResult

# Security limits
_MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB max response size


class ResponseExtractor(Protocol):
    """Protocol for extracting items from API responses."""

    def __call__(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        ...


class HTTPMCPClient(MCPClient):
    """Base class for HTTP API-based MCP clients.

    Subclasses must:
    1. Set BASE_URL class attribute (optional, for documentation)
    2. Override list_tools() to return available tool names
    3. Implement tool methods named _tool_{tool_name}(args) -> MCPToolResult

    Optional overrides:
    - DEFAULT_TIMEOUT: Request timeout in seconds (default: 30.0)
    - DEFAULT_HEADERS: Headers to include in all requests
    - _get_headers(): For dynamic header generation
    - _validate_connection(): For API key or other pre-connection checks
    """

    BASE_URL: str = ""
    DEFAULT_TIMEOUT: float = 30.0
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": "fu7ur3pr00f Career Intelligence/1.0",
        "Accept": "application/json",
    }

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the HTTP MCP client.

        Args:
            api_key: Optional API key for authenticated APIs
        """
        self._api_key = api_key
        self._connected = False
        self._client: httpx.AsyncClient | None = None
        self._tool_handlers: dict[
            str, Callable[[dict[str, Any]], Awaitable[MCPToolResult]]
        ] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Auto-register tool handlers named _tool_*.

        Subclasses define tools via _tool_* methods.
        This is called once in __init__.
        """
        for name in dir(self):
            if name.startswith("_tool_"):
                tool_name = name[6:]  # Strip "_tool_" prefix
                handler = getattr(self, name)
                if callable(handler):
                    self._tool_handlers[tool_name] = cast(
                        Callable[[dict[str, Any]], Awaitable[MCPToolResult]],
                        handler,
                    )

    def _get_headers(self) -> dict[str, str]:
        """Get headers for HTTP requests.

        Override in subclasses for custom headers.
        Default implementation returns DEFAULT_HEADERS.

        Returns:
            Headers dict to use for requests
        """
        return self.DEFAULT_HEADERS.copy()

    def _validate_connection(self) -> None:
        """Validate that connection can be established.

        Override in subclasses to check API keys, etc.
        Raise MCPConnectionError if validation fails.
        """
        pass

    async def connect(self) -> None:
        """Initialize HTTP client.

        Raises:
            MCPConnectionError: If initialization fails
        """
        self._validate_connection()

        try:
            self._client = httpx.AsyncClient(
                timeout=self.DEFAULT_TIMEOUT,
                headers=self._get_headers(),
            )
            self._connected = True
        except Exception as e:
            raise MCPConnectionError(f"Failed to initialize HTTP client: {e}") from e

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        self._connected = False

    def is_connected(self) -> bool:
        """Check if client is connected and ready."""
        return self._connected and self._client is not None

    @abstractmethod
    async def list_tools(self) -> list[str]:
        """List available tools.

        Subclasses must implement this to return their tool names.

        Returns:
            List of tool names
        """
        pass

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        """Call a tool with the given arguments.

        Handles common error patterns and delegates to registered _tool_* methods.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            MCPToolResult with tool output

        Raises:
            MCPToolError: If tool call fails
        """
        if not self.is_connected():
            raise MCPToolError("Client not connected")

        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            raise MCPToolError(f"Unknown tool: {tool_name}")

        try:
            return await handler(arguments)
        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Tool call failed: {e}") from e

    def _ensure_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not initialized.

        Returns:
            The httpx AsyncClient

        Raises:
            MCPToolError: If client is not initialized
        """
        if not self._client:
            raise MCPToolError("Client not initialized")
        return self._client

    def _check_response_size(self, response: httpx.Response) -> None:
        """Validate response size to prevent memory exhaustion.

        Args:
            response: HTTP response to check

        Raises:
            MCPToolError: If response exceeds maximum size
        """
        content_length = len(response.content)
        if content_length > _MAX_RESPONSE_SIZE:
            raise MCPToolError(
                f"Response too large: {content_length / 1024 / 1024:.1f}MB "
                f"(max {_MAX_RESPONSE_SIZE / 1024 / 1024:.0f}MB)"
            )

    def _format_response(
        self,
        output: dict[str, Any],
        raw_response: Any,
        tool_name: str,
    ) -> MCPToolResult:
        """Format response with consistent JSON indentation.

        DRY helper to eliminate repeated json.dumps(indent=2) calls
        across all HTTP MCP clients.

        Args:
            output: Processed output dict to serialize
            raw_response: Original API response for debugging
            tool_name: Name of the tool that was called

        Returns:
            MCPToolResult with formatted JSON content
        """
        return MCPToolResult(
            content=json.dumps(output, indent=2),
            raw_response=raw_response,
            tool_name=tool_name,
        )

    async def _api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        response_extractor: ResponseExtractor | None = None,
        base_url: str | None = None,
    ) -> tuple[list[dict[str, Any]], Any]:
        """Generic API request with configurable extraction.

        DRY helper to eliminate repeated API call patterns across
        all HTTP-based MCP clients.

        Args:
            endpoint: API endpoint path (appended to BASE_URL or base_url)
            method: HTTP method (default: GET)
            params: Query parameters
            json_body: JSON body for POST/PUT requests
            response_extractor: Function to extract items from response.
                              Pass None to return full response as list.
            base_url: Optional override for BASE_URL

        Returns:
            Tuple of (items list, full response data)

        Raises:
            MCPToolError: If request fails
        """
        client = self._ensure_client()

        request_kwargs: dict[str, Any] = {"params": params}
        if json_body:
            request_kwargs["json"] = json_body

        url = base_url + endpoint if base_url else f"{self.BASE_URL}{endpoint}"
        response = await client.request(method, url, **request_kwargs)
        response.raise_for_status()

        data = response.json()
        if response_extractor and isinstance(data, dict):
            items = response_extractor(data)
        else:
            items = data if isinstance(data, list) else []

        return items, data

    def _items_extractor(
        self, key: str = "items"
    ) -> Callable[[dict[str, Any]], list[dict[str, Any]]]:
        """Factory for common item extraction patterns.

        Args:
            key: Key to extract from response dict

        Returns:
            Function that extracts list from response
        """
        return lambda data: data.get(key, [])

    def _format_items(
        self,
        items: list[dict[str, Any]],
        tool_name: str,
        raw_response: Any,
        source: str | None = None,
        **extra: Any,
    ) -> MCPToolResult:
        """Format items with standard structure.

        DRY helper to eliminate repeated output formatting.

        Args:
            items: List of items to format
            tool_name: Name of the tool
            raw_response: Original API response
            source: Optional source name (default: client class name)
            extra: Additional fields to add to output

        Returns:
            MCPToolResult with formatted output
        """
        output: dict[str, Any] = {
            "source": source
            or self.__class__.__name__.replace("MCPClient", "").lower(),
            "total_returned": len(items),
            "items": items,
            **extra,
        }
        return self._format_response(output, raw_response, tool_name)
