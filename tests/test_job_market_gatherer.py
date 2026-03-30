"""Tests for job market gatherer summary behavior."""

import pytest

from fu7ur3pr00f.gatherers.market.job_market_gatherer import JobMarketGatherer


class TestJobMarketGatherer:
    @pytest.mark.asyncio
    async def test_remote_only_sources_count_as_remote_positions(self, monkeypatch):
        gatherer = JobMarketGatherer()

        async def fake_gather_from_source(
            self,
            source_name,
            tool_name,
            tool_args,
            results,
            extractor=None,
            source_label=None,
        ):
            if source_name == "remoteok":
                return [
                    {
                        "title": "AI Engineer",
                        "company": "Acme",
                        "location": "Europe",
                        "site": "remoteok",
                    }
                ]
            return []

        monkeypatch.setattr(
            JobMarketGatherer,
            "_gather_from_source",
            fake_gather_from_source,
        )

        data = await gatherer.gather(
            role="AI Engineer",
            location="Europe",
            include_salary=False,
            limit=5,
        )
        assert data["summary"]["remote_positions"] == 1
