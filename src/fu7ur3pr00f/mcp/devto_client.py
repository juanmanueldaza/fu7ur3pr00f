"""Dev.to MCP client for tech content trends.

Uses the free Dev.to API (no auth required).
https://dev.to/ - Developer community with trending articles.
"""

from typing import Any

from fu7ur3pr00f.constants import DEVTO_API_BASE

from .base import MCPToolResult
from .http_client import HTTPMCPClient


class DevToMCPClient(HTTPMCPClient):
    """Dev.to MCP client for tech articles and trends.

    Free API, no authentication required.
    Returns trending articles from dev.to.
    """

    BASE_URL = DEVTO_API_BASE

    async def list_tools(self) -> list[str]:
        """List available tools."""
        return ["search_articles", "get_trending", "get_by_tag"]

    async def _tool_search_articles(self, args: dict[str, Any]) -> MCPToolResult:
        """Search Dev.to articles."""
        return await self._get_top_articles(per_page=args.get("per_page", 30))

    async def _tool_get_trending(self, args: dict[str, Any]) -> MCPToolResult:
        """Get trending Dev.to articles."""
        return await self._get_top_articles(per_page=args.get("per_page", 30))

    async def _tool_get_by_tag(self, args: dict[str, Any]) -> MCPToolResult:
        """Get Dev.to articles by tag."""
        return await self._get_by_tag(
            tag=args.get("tag", ""),
            per_page=args.get("per_page", 30),
        )

    async def _get_top_articles(self, per_page: int = 30) -> MCPToolResult:
        """Get top Dev.to articles from the last 7 days."""
        articles, data = await self._api_request(
            "",
            params={"per_page": min(per_page, 100), "top": 7},
        )
        return self._format_articles(articles, "get_trending", data)

    async def _get_by_tag(self, tag: str, per_page: int = 30) -> MCPToolResult:
        """Get Dev.to articles by tag."""
        articles, data = await self._api_request(
            "",
            params={"tag": tag.lower(), "per_page": min(per_page, 100), "top": 30},
        )
        return self._format_articles(articles, "get_by_tag", data, tag=tag)

    def _format_articles(
        self,
        articles: list[dict[str, Any]],
        tool_name: str,
        raw_data: Any,
        tag: str | None = None,
    ) -> MCPToolResult:
        """Format articles into consistent structure."""
        formatted = []
        for article in articles:
            user = article.get("user", {})
            formatted.append(
                {
                    "id": article.get("id"),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "canonical_url": article.get("canonical_url", ""),
                    "cover_image": article.get("cover_image"),
                    "author": user.get("name", ""),
                    "author_username": user.get("username", ""),
                    "author_github": user.get("github_username"),
                    "author_twitter": user.get("twitter_username"),
                    "tags": article.get("tag_list", []),
                    "reading_time_minutes": article.get("reading_time_minutes", 0),
                    "language": article.get("language", "en"),
                    "reactions_count": article.get("public_reactions_count", 0),
                    "comments_count": article.get("comments_count", 0),
                    "created_at": article.get("created_at", ""),
                    "published_at": article.get("published_timestamp", ""),
                    "edited_at": article.get("edited_at"),
                    "last_comment_at": article.get("last_comment_at"),
                    "source": "devto",
                }
            )

        extra = {"tag": tag} if tag else {}
        return self._format_items(formatted, tool_name, raw_data, **extra)
