"""JavaScript content extraction for portfolio scraping.

Single Responsibility: Fetch and parse JSON content files for portfolio data.

Note: This module requires portfolios to expose structured JSON data files
(e.g., /content.json) instead of parsing JavaScript code. This approach is:
- More secure (no regex parsing of code)
- More reliable (structured data vs fragile pattern matching)
- More maintainable (standard JSON vs custom JS patterns)

For JS-heavy sites without JSON endpoints, consider using a headless browser
or requiring users to provide structured data files.
"""

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ...utils.logging import get_logger

if TYPE_CHECKING:
    from .fetcher import PortfolioFetcher

logger = get_logger(__name__)

# Security limits
MAX_JSON_FILES = 5  # Maximum JSON files to fetch per page
MAX_JSON_SIZE = 1024 * 1024  # 1MB limit for JSON parsing
ALLOWED_CONTENT_TYPES = frozenset({
    "application/json",
    "application/ld+json",
    "text/json",
})


@dataclass
class JSContent:
    """Content extracted from JSON data files.

    Note: Despite the class name, this now extracts from structured JSON files,
    not JavaScript code. The name is preserved for backward compatibility.
    """

    projects: list[dict] = field(default_factory=list)
    socials: list[dict] = field(default_factory=list)
    bio: dict = field(default_factory=dict)
    source_url: str | None = None


class JSExtractor:
    """Extract content from JSON data files.

    Single responsibility: Fetch and parse structured JSON files for portfolio data.

    This extractor looks for:
    1. JSON-LD in HTML (application/ld+json script tags)
    2. Linked JSON content files (e.g., /content.json)
    3. Data attributes in HTML elements

    Security: Only parses validated JSON with size limits and content-type checks.
    """

    # Common JSON content file paths to try
    CONTENT_PATHS = [
        "/content.json",
        "/data/content.json",
        "/api/content",
        "/data.json",
        "/portfolio.json",
    ]

    def extract(
        self,
        html: str,
        base_url: str,
        fetcher: "PortfolioFetcher",
    ) -> JSContent:
        """Find and extract content from JSON files and HTML.

        Args:
            html: HTML containing JSON-LD or references to JSON files
            base_url: Base URL for resolving relative paths
            fetcher: Object implementing fetch() method

        Returns:
            JSContent with extracted projects, socials, bio
        """
        soup = BeautifulSoup(html, "html.parser")

        # First, try extracting from JSON-LD in HTML
        content = self._extract_json_ld(soup)
        if content.projects or content.socials or content.bio:
            logger.debug("Found JSON-LD content in HTML")
            return content

        # Second, try fetching linked JSON content files
        json_files_checked = 0
        for content_path in self.CONTENT_PATHS:
            if json_files_checked >= MAX_JSON_FILES:
                logger.debug("Reached max JSON file limit (%d)", MAX_JSON_FILES)
                break

            json_url = urljoin(base_url, content_path)
            try:
                result = fetcher.fetch(json_url)
                json_files_checked += 1

                content = self._parse_json_file(result.content, json_url)
                if content.projects or content.socials or content.bio:
                    logger.debug("Found JSON content at %s", json_url)
                    return content
            except Exception as e:
                logger.debug("JSON file not found at %s: %s", json_url, e)
                continue

        # Third, try extracting from data attributes in HTML
        content = self._extract_data_attributes(soup, base_url)
        if content.projects or content.socials or content.bio:
            logger.debug("Found data attributes content in HTML")
            return content

        return JSContent()

    def _extract_json_ld(self, soup: BeautifulSoup) -> JSContent:
        """Extract portfolio data from JSON-LD structured data."""
        content = JSContent()

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    data = json.loads(script.string)
                    self._process_json_ld_data(data, content)
            except (json.JSONDecodeError, TypeError):
                continue

        return content

    def _process_json_ld_data(self, data: dict | list, content: JSContent) -> None:
        """Process JSON-LD data and extract portfolio information."""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    self._process_json_ld_item(item, content)
        elif isinstance(data, dict):
            self._process_json_ld_item(data, content)

    def _process_json_ld_item(self, item: dict, content: JSContent) -> None:
        """Process a single JSON-LD item."""
        item_type = item.get("@type", "")

        # Extract Person data for bio
        if item_type == "Person":
            content.bio = {
                "name": item.get("name", ""),
                "jobTitle": item.get("jobTitle", ""),
                "description": item.get("description", ""),
                "email": item.get("email", ""),
            }
            if "sameAs" in item:
                content.socials = [
                    {"name": "Profile", "url": url} for url in item["sameAs"]
                ]

        # Extract CreativeWork or Project for projects
        elif item_type in ("CreativeWork", "Project", "SoftwareApplication"):
            project = {
                "name": item.get("name", "Untitled"),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
            }
            if project["name"] != "Untitled":
                content.projects.append(project)

    def _parse_json_file(self, json_text: str, source_url: str) -> JSContent:
        """Parse a JSON content file.

        Security: Validates size and structure before parsing.
        """
        # Size limit check
        if len(json_text) > MAX_JSON_SIZE:
            logger.warning(
                "JSON file too large: %d bytes (max %d)",
                len(json_text),
                MAX_JSON_SIZE,
            )
            return JSContent()

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.debug("Failed to parse JSON from %s: %s", source_url, e)
            return JSContent()

        content = JSContent(source_url=source_url)

        # Handle different JSON structures
        if isinstance(data, dict):
            # Extract bio
            if "bio" in data and isinstance(data["bio"], dict):
                content.bio = data["bio"]
            elif "person" in data and isinstance(data["person"], dict):
                content.bio = data["person"]
            elif "name" in data and isinstance(data.get("jobTitle"), str):
                # Root-level person data
                content.bio = data

            # Extract projects
            if "projects" in data and isinstance(data["projects"], list):
                content.projects = [
                    p for p in data["projects"] if isinstance(p, dict)
                ]

            # Extract socials
            if "socials" in data and isinstance(data["socials"], list):
                content.socials = [
                    s for s in data["socials"] if isinstance(s, dict)
                ]
            elif "social" in data and isinstance(data["social"], list):
                content.socials = [
                    s for s in data["social"] if isinstance(s, dict)
                ]

        elif isinstance(data, list):
            # Array of items - try to categorize
            for item in data:
                if not isinstance(item, dict):
                    continue
                if "name" in item and ("url" in item or "description" in item):
                    if "jobTitle" in item or "@type" in item:
                        content.bio = item
                    else:
                        content.projects.append(item)

        return content

    def _extract_data_attributes(
        self,
        soup: BeautifulSoup,
        base_url: str,
    ) -> JSContent:
        """Extract portfolio data from HTML data attributes.

        Looks for elements with data-portfolio, data-project, data-social attributes.
        """
        content = JSContent()

        # Extract project data from data attributes
        for elem in soup.find_all(attrs={"data-project": True}):
            try:
                project_data = elem.get("data-project")
                if project_data and isinstance(project_data, str):
                    project = json.loads(project_data)
                    if isinstance(project, dict):
                        content.projects.append(project)
            except json.JSONDecodeError:
                continue

        # Extract social links from data attributes
        for elem in soup.find_all(attrs={"data-social": True}):
            try:
                social_data = elem.get("data-social")
                if social_data and isinstance(social_data, str):
                    social = json.loads(social_data)
                    if isinstance(social, dict):
                        content.socials.append(social)
            except json.JSONDecodeError:
                continue

        # Extract bio from data attributes
        for elem in soup.find_all(attrs={"data-bio": True}):
            try:
                bio_data = elem.get("data-bio")
                if bio_data and isinstance(bio_data, str):
                    bio = json.loads(bio_data)
                    if isinstance(bio, dict):
                        content.bio = bio
            except json.JSONDecodeError:
                continue

        return content
