"""JobSpy MCP client for multi-platform job search.

Uses JobSpy to aggregate jobs from LinkedIn, Indeed, Glassdoor, ZipRecruiter.
MIT licensed, no authentication required.
"""

import asyncio
import json
import logging
from typing import Any

from .base import MCPClient, MCPToolError, MCPToolResult
from .job_schema import generate_job_id

try:
    from jobspy.model import Country

    _JOBSPY_AVAILABLE = True
except ImportError:
    _JOBSPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class JobSpyMCPClient(MCPClient):
    """JobSpy MCP client for aggregated job search.

    This client uses the python-jobspy library directly rather than
    spawning an MCP server process. This is simpler and more reliable.

    Supported sites: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs
    """

    SUPPORTED_SITES = ["linkedin", "indeed", "glassdoor", "zip_recruiter", "google"]

    def __init__(self) -> None:
        self._connected = False
        self._jobspy_available = False

    async def connect(self) -> None:
        """Check if jobspy is available."""
        self._jobspy_available = _JOBSPY_AVAILABLE
        self._connected = True

    async def disconnect(self) -> None:
        """No cleanup needed."""
        self._connected = False

    def is_connected(self) -> bool:
        """Check if client is ready."""
        return self._connected

    async def list_tools(self) -> list[str]:
        """List available tools."""
        return [
            "search_jobs",
            "search_jobs_multi_site",
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        """Call a job search tool."""
        if not self.is_connected():
            raise MCPToolError("Client not connected")

        if not self._jobspy_available:
            raise MCPToolError(
                "JobSpy not installed. Install with: pip install python-jobspy"
            )

        try:
            if tool_name == "search_jobs":
                return await self._search_jobs(
                    search_term=arguments.get("search_term", ""),
                    location=arguments.get("location", ""),
                    site_names=arguments.get("sites", ["linkedin", "indeed"]),
                    results_wanted=arguments.get("results_wanted", 20),
                    remote=arguments.get("remote", False),
                )
            elif tool_name == "search_jobs_multi_site":
                return await self._search_jobs(
                    search_term=arguments.get("search_term", ""),
                    location=arguments.get("location", ""),
                    site_names=self.SUPPORTED_SITES,
                    results_wanted=arguments.get("results_wanted", 50),
                    remote=arguments.get("remote", False),
                )
            else:
                raise MCPToolError(f"Unknown tool: {tool_name}")
        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Tool call failed: {e}") from e

    # City → country mapping for common cities
    _CITY_TO_COUNTRY: dict[str, str] = {
        "paris": "france",
        "london": "uk",
        "berlin": "germany",
        "munich": "germany",
        "amsterdam": "netherlands",
        "barcelona": "spain",
        "madrid": "spain",
        "malaga": "spain",
        "valencia": "spain",
        "seville": "spain",
        "bilbao": "spain",
        "lisbon": "portugal",
        "milan": "italy",
        "rome": "italy",
        "vienna": "austria",
        "zurich": "switzerland",
        "geneva": "switzerland",
        "brussels": "belgium",
        "copenhagen": "denmark",
        "stockholm": "sweden",
        "oslo": "norway",
        "helsinki": "finland",
        "dublin": "ireland",
        "prague": "czech republic",
        "warsaw": "poland",
        "bucharest": "romania",
        "budapest": "hungary",
        "buenos aires": "argentina",
        "sydney": "australia",
        "melbourne": "australia",
        "toronto": "canada",
        "vancouver": "canada",
        "tokyo": "japan",
        "singapore": "singapore",
        "dubai": "united arab emirates",
    }

    @classmethod
    def _resolve_country(cls, location: str) -> str:
        """Resolve location to a JobSpy country_indeed value.

        Indeed/Glassdoor/Google use country-specific domains, so passing the
        right country is critical for relevant results. Tries:
        1. Direct match against JobSpy's Country enum
        2. City → country lookup
        3. Falls back to "worldwide"
        """
        if not location or location.lower() == "remote":
            return "worldwide"

        # Try direct country match
        try:
            Country.from_string(location)  # type: ignore[name-defined]
            return location.lower()
        except ValueError:
            pass

        # Try city → country mapping
        loc_lower = location.lower().strip()
        if loc_lower in cls._CITY_TO_COUNTRY:
            return cls._CITY_TO_COUNTRY[loc_lower]

        return "worldwide"

    async def _run_scrape(self, search_params: dict[str, Any]):
        """Run JobSpy's synchronous scraper in a worker thread."""
        from jobspy import scrape_jobs  # type: ignore[import-not-found]

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: scrape_jobs(**search_params),
        )

    async def _search_jobs(
        self,
        search_term: str,
        location: str = "",
        site_names: list[str] | None = None,
        results_wanted: int = 20,
        remote: bool = False,
    ) -> MCPToolResult:
        """Search for jobs across multiple platforms."""
        if not self._jobspy_available:
            raise MCPToolError("JobSpy not available")

        sites = site_names or ["linkedin", "indeed"]

        # Resolve country for Indeed/Glassdoor/Google (they use country-specific
        # domains)
        country = self._resolve_country(location)

        # Exclude Glassdoor for unsupported countries (avoids noisy errors)
        if "glassdoor" in sites:
            try:
                c = Country.from_string(country)  # type: ignore[name-defined]
                c.glassdoor_domain_value  # raises if unsupported
            except Exception:
                sites = [s for s in sites if s != "glassdoor"]

        # Build search parameters
        search_params: dict[str, Any] = {
            "site_name": sites,
            "search_term": search_term,
            "results_wanted": results_wanted,
            "country_indeed": country,
        }

        if location:
            search_params["location"] = location

        if remote:
            search_params["is_remote"] = True

        try:
            try:
                jobs_df = await self._run_scrape(search_params)
            except Exception as e:
                if "linkedin" in sites and len(sites) > 1:
                    logger.warning(
                        (
                            "JobSpy search failed with linkedin included; "
                            "retrying without linkedin: %s"
                        ),
                        e,
                    )
                    retry_params = {
                        **search_params,
                        "site_name": [s for s in sites if s != "linkedin"],
                    }
                    jobs_df = await self._run_scrape(retry_params)
                    sites = retry_params["site_name"]
                else:
                    raise

            # Convert DataFrame to list of dicts
            if jobs_df is not None and not jobs_df.empty:
                jobs = jobs_df.to_dict("records")

                # Clean up the results
                cleaned_jobs = []
                for job in jobs:
                    # Handle NaN values from pandas (they come as float)
                    desc = job.get("description")
                    if desc is None or (isinstance(desc, float) and str(desc) == "nan"):
                        desc = ""
                    else:
                        desc = str(desc)[:500]

                    # Generate unique ID from site + job_url
                    job_url = job.get("job_url", "") or ""
                    site = job.get("site", "") or ""
                    job_id = generate_job_id(site, job_url)

                    cleaned_jobs.append(
                        {
                            "id": job_id,
                            "title": job.get("title", "") or "",
                            "company": job.get("company", "") or "",
                            "location": job.get("location", "") or "",
                            "job_url": job.get("job_url", "") or "",
                            "site": job.get("site", "") or "",
                            "date_posted": str(job.get("date_posted", "") or ""),
                            "salary_min": job.get("min_amount"),
                            "salary_max": job.get("max_amount"),
                            "salary_currency": job.get("currency", "") or "",
                            "description": desc,
                        }
                    )

                return MCPToolResult(
                    content=json.dumps(
                        {
                            "search_term": search_term,
                            "location": location,
                            "sites": sites,
                            "total_results": len(cleaned_jobs),
                            "jobs": cleaned_jobs,
                        },
                        indent=2,
                    ),
                    raw_response=jobs,
                    tool_name="search_jobs",
                )
            else:
                return MCPToolResult(
                    content=json.dumps(
                        {
                            "search_term": search_term,
                            "location": location,
                            "sites": sites,
                            "total_results": 0,
                            "jobs": [],
                        },
                        indent=2,
                    ),
                    tool_name="search_jobs",
                )

        except Exception as e:
            raise MCPToolError(f"Job search failed: {e}") from e
