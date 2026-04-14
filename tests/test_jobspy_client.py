"""Tests for JobSpy client resilience."""

import pandas as pd
import pytest

from fu7ur3pr00f.mcp.jobspy_client import JobSpyMCPClient

pytestmark = pytest.mark.unit


class TestJobSpyClient:
    @pytest.mark.asyncio
    async def test_retries_without_linkedin_when_initial_scrape_fails(
        self, monkeypatch
    ):
        client = JobSpyMCPClient()
        client._jobspy_available = True
        client._connected = True

        calls = []

        async def fake_run_scrape(params):
            calls.append(params["site_name"])
            if "linkedin" in params["site_name"]:
                raise Exception("LinkedInException: Invalid country string: 'liberia'")
            return pd.DataFrame(
                [
                    {
                        "title": "AI Engineer",
                        "company": "Acme",
                        "location": "Remote",
                        "job_url": "https://example.com/job",
                        "site": "indeed",
                        "date_posted": "2026-03-30",
                        "min_amount": None,
                        "max_amount": None,
                        "currency": None,
                        "description": "test",
                    }
                ]
            )

        monkeypatch.setattr(client, "_run_scrape", fake_run_scrape)

        result = await client._search_jobs(
            search_term="AI Engineer",
            location="Europe",
            site_names=["linkedin", "indeed"],
            results_wanted=5,
        )

        assert calls == [["linkedin", "indeed"], ["indeed"]]
        assert result.is_error is False
        assert "AI Engineer" in result.content
