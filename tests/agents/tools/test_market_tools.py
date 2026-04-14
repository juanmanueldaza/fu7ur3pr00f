"""Tests for market intelligence tools."""

from unittest.mock import patch

import pytest

from fu7ur3pr00f.agents.tools.market import (
    _is_location_relevant,
    _normalize_location_tokens,
    analyze_market_fit,
    analyze_market_skills,
    gather_market_data,
    get_salary_insights,
    get_tech_trends,
    search_jobs,
)

pytestmark = pytest.mark.unit


class TestNormalizeLocationTokens:
    """Test _normalize_location_tokens helper."""

    def test_empty_returns_empty(self) -> None:
        assert _normalize_location_tokens("") == set()

    def test_remote_expands(self) -> None:
        tokens = _normalize_location_tokens("remote")
        assert "remote" in tokens
        assert "worldwide" in tokens

    def test_spain_expands(self) -> None:
        tokens = _normalize_location_tokens("spain")
        assert "spain" in tokens
        assert "madrid" in tokens
        assert "barcelona" in tokens

    def test_europe_expands(self) -> None:
        tokens = _normalize_location_tokens("europe")
        assert "europe" in tokens
        assert "spain" in tokens
        assert "germany" in tokens

    def test_strips_special_chars(self) -> None:
        tokens = _normalize_location_tokens("San Francisco, CA!")
        assert "san" in tokens
        assert "francisco" in tokens

    def test_filters_single_char_tokens(self) -> None:
        tokens = _normalize_location_tokens("a b c test")
        assert "a" not in tokens
        assert "test" in tokens


class TestIsLocationRelevant:
    """Test _is_location_relevant helper."""

    def test_empty_requested_matches_all(self) -> None:
        job = {"location": "Madrid"}
        assert _is_location_relevant(job, "") is True

    def test_remote_job_matches_any_request(self) -> None:
        job = {"location": "Remote"}
        assert _is_location_relevant(job, "Spain") is True

    def test_is_remote_flag(self) -> None:
        job = {"location": "", "is_remote": True}
        # Empty location returns True only when "remote" is in requested tokens
        # The is_remote flag is checked AFTER the empty location check
        assert _is_location_relevant(job, "remote") is True
        assert _is_location_relevant(job, "Spain") is False

    def test_location_match(self) -> None:
        job = {"location": "Madrid, Spain"}
        assert _is_location_relevant(job, "Spain") is True

    def test_location_mismatch(self) -> None:
        job = {"location": "New York, USA"}
        assert _is_location_relevant(job, "Spain") is False

    def test_empty_job_location_requires_remote(self) -> None:
        job = {"location": ""}
        assert _is_location_relevant(job, "remote") is True
        assert _is_location_relevant(job, "Spain") is False


class TestSearchJobs:
    """Test search_jobs tool."""

    def test_returns_results(self) -> None:
        mock_data = {
            "job_listings": [
                {
                    "title": "Senior Python Dev",
                    "company": "TechCorp",
                    "location": "Remote",
                    "salary": "$120k-$150k",
                    "url": "https://example.com/job",
                    "site": "remoteok",
                }
            ],
            "summary": {
                "total_jobs": 1,
                "sources": ["remoteok"],
                "remote_positions": 1,
            },
            "errors": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = search_jobs.invoke({"query": "Python Developer"})

        assert "Python Developer" in result
        assert "Senior Python Dev" in result
        assert "TechCorp" in result

    def test_deduplicates_jobs(self) -> None:
        mock_data = {
            "job_listings": [
                {"title": "Dev", "company": "Acme", "location": "Remote"},
                {"title": "Dev", "company": "Acme", "location": "Madrid"},
                {"title": "Dev", "company": "Other", "location": "Remote"},
            ],
            "summary": {"total_jobs": 3, "sources": ["remoteok"]},
            "errors": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = search_jobs.invoke({"query": "Dev"})

        assert "2 found" in result

    def test_reports_errors(self) -> None:
        mock_data = {
            "job_listings": [],
            "summary": {"total_jobs": 0, "sources": []},
            "errors": ["timeout", "rate limit"],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = search_jobs.invoke({"query": "Dev"})

        assert "2 errors" in result

    def test_respects_limit(self) -> None:
        mock_data = {
            "job_listings": [],
            "summary": {"total_jobs": 0, "sources": []},
            "errors": [],
        }

        def capture_gather(*args, **kwargs):
            # Verify gather was called with correct params
            assert args == ()
            assert kwargs == {"role": "Dev", "location": "Berlin", "limit": 10}
            return mock_data

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.side_effect = capture_gather
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                side_effect=lambda fn, **kw: fn(**kw),
            ):
                search_jobs.invoke({"query": "Dev", "location": "Berlin", "limit": 10})

            mock_cls.return_value.gather.assert_called_once_with(
                role="Dev", location="Berlin", limit=10
            )


class TestGetTechTrends:
    """Test get_tech_trends tool."""

    def test_returns_trends(self) -> None:
        mock_data = {
            "trending_stories": [
                {"title": "Rust is taking over", "points": 450},
                {"title": "AI coding assistants", "points": 320},
            ],
            "hiring_trends": {
                "top_technologies": [("Python", 100), ("Rust", 80)],
                "remote_percentage": 75,
            },
            "hn_job_postings": [{"title": "Hiring Dev", "salary_min": 100000}],
            "errors": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.TechTrendsGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_tech_trends.invoke({})

        assert "Rust is taking over" in result
        assert "450 pts" in result
        assert "75%" in result

    def test_filters_stories_to_top_5(self) -> None:
        stories = [{"title": f"Story {i}", "points": i * 10} for i in range(10)]
        mock_data = {
            "trending_stories": stories,
            "hiring_trends": {},
            "hn_job_postings": [],
            "errors": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.TechTrendsGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_tech_trends.invoke({})

        assert "Story 0" in result
        assert "Story 4" in result
        assert "Story 5" not in result

    def test_reports_errors(self) -> None:
        mock_data = {
            "trending_stories": [],
            "hiring_trends": {},
            "hn_job_postings": [],
            "errors": ["HN API down"],
        }

        with patch("fu7ur3pr00f.agents.tools.market.TechTrendsGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_tech_trends.invoke({"topic": "Python"})

        assert "Some data unavailable" in result


class TestGetSalaryInsights:
    """Test get_salary_insights tool."""

    def test_returns_salary_from_listings(self) -> None:
        mock_data = {
            "salary_data": [],
            "job_listings": [
                {
                    "company": "TechCorp",
                    "salary": "$120k",
                    "location": "Remote",
                }
            ],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_salary_insights.invoke({"role": "Developer"})

        assert "TechCorp" in result
        assert "$120k" in result

    def test_returns_salary_research_data(self) -> None:
        mock_data = {
            "salary_data": [
                {
                    "title": "Senior Dev Salary Guide",
                    "description": "Average salary is $130k",
                }
            ],
            "job_listings": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_salary_insights.invoke({"role": "Developer"})

        assert "Salary research" in result
        assert "Senior Dev Salary Guide" in result

    def test_returns_no_data_message(self) -> None:
        mock_data = {
            "salary_data": [],
            "job_listings": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_salary_insights.invoke({"role": "Rare Role"})

        assert "No specific salary data found" in result

    def test_filters_by_location_relevance(self) -> None:
        mock_data = {
            "salary_data": [],
            "job_listings": [
                {
                    "company": "US Corp",
                    "salary": "$120k",
                    "location": "San Francisco",
                },
                {
                    "company": "EU Corp",
                    "salary": "€80k",
                    "location": "Madrid, Spain",
                },
            ],
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_cls:
            mock_cls.return_value.gather.return_value = mock_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=mock_data,
            ):
                result = get_salary_insights.invoke(
                    {"role": "Developer", "location": "Spain"}
                )

        assert "EU Corp" in result


class TestAnalyzeMarketFit:
    """Test analyze_market_fit tool."""

    def test_returns_analysis(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.market.run_market_analysis",
            return_value="Your skills align well with the market.",
        ):
            result = analyze_market_fit.invoke({})

        assert "Your skills align well" in result


class TestAnalyzeMarketSkills:
    """Test analyze_market_skills tool."""

    def test_returns_analysis(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.market.run_market_analysis",
            return_value="Learn Rust and Go.",
        ):
            result = analyze_market_skills.invoke({})

        assert "Learn Rust and Go" in result


class TestGatherMarketData:
    """Test gather_market_data tool."""

    def test_gathers_all_sources(self) -> None:
        trends_data = {
            "trending_stories": [{"title": "AI", "points": 100}],
            "hiring_trends": {"total_job_postings": 50},
            "hn_job_postings": [{"title": "Dev"}],
        }
        jobs_data = {
            "job_listings": [{"title": "Dev"}],
            "summary": {"sources": ["remoteok"], "remote_positions": 10},
        }
        content_data = {
            "devto_articles": [{"title": "Article"}],
            "stackoverflow_trends": {"topic_popularity": ["python", "rust"]},
        }

        with patch("fu7ur3pr00f.agents.tools.market.TechTrendsGatherer") as mock_trends:
            mock_trends.return_value.gather_with_cache.return_value = trends_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.JobMarketGatherer"
            ) as mock_jobs:
                mock_jobs.return_value.gather_with_cache.return_value = jobs_data
                with patch(
                    "fu7ur3pr00f.agents.tools.market.ContentTrendsGatherer"
                ) as mock_content:
                    mock_content.return_value.gather_with_cache.return_value = (
                        content_data
                    )
                    with patch(
                        "fu7ur3pr00f.agents.tools.market.run_async_call",
                        side_effect=[trends_data, jobs_data, content_data],
                    ):
                        result = gather_market_data.invoke({"source": "all"})

        assert "Tech Trends" in result
        assert "Job Market" in result
        assert "Content Trends" in result

    def test_gathers_only_trends(self) -> None:
        trends_data = {
            "trending_stories": [{"title": "AI"}],
            "hiring_trends": {},
            "hn_job_postings": [],
        }

        with patch("fu7ur3pr00f.agents.tools.market.TechTrendsGatherer") as mock_trends:
            mock_trends.return_value.gather_with_cache.return_value = trends_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=trends_data,
            ):
                result = gather_market_data.invoke({"source": "trends"})

        assert "Tech Trends" in result
        assert "Job Market" not in result

    def test_gathers_only_jobs(self) -> None:
        jobs_data = {
            "job_listings": [],
            "summary": {"sources": [], "remote_positions": 0},
        }

        with patch("fu7ur3pr00f.agents.tools.market.JobMarketGatherer") as mock_jobs:
            mock_jobs.return_value.gather_with_cache.return_value = jobs_data
            with patch(
                "fu7ur3pr00f.agents.tools.market.run_async_call",
                return_value=jobs_data,
            ):
                result = gather_market_data.invoke({"source": "jobs"})

        assert "Job Market" in result
        assert "Tech Trends" not in result
