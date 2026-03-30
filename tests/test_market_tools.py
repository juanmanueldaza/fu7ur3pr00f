"""Tests for market tool heuristics and formatting."""

from unittest.mock import patch

from fu7ur3pr00f.agents.tools.market import get_salary_insights
from fu7ur3pr00f.gatherers.market.source_registry import _build_jobicy_args


class TestJobicyArgs:
    def test_build_jobicy_args_prefers_stable_role_noun(self) -> None:
        args = _build_jobicy_args("AI Engineer", "Spain", 10)
        assert args == {"count": 10, "tag": "engineer"}

    def test_build_jobicy_args_skips_title_prefix_noise(self) -> None:
        args = _build_jobicy_args("Senior Full Stack AI Engineer", "Europe", 10)
        assert args == {"count": 10, "tag": "engineer"}


class TestSalaryInsights:
    def test_filters_out_salary_listings_from_wrong_location(self) -> None:
        fake_data = {
            "salary_data": [{"title": "Full Stack Developer Salary in Spain (2026)"}],
            "job_listings": [
                {
                    "company": "Guidehouse",
                    "salary": "USD 215,000 - 358,000",
                    "location": "Washington, DC, USA",
                },
                {
                    "company": "Remote EU Co",
                    "salary": "EUR 70,000 - 90,000",
                    "location": "Remote - Spain",
                },
            ],
        }

        with patch(
            "fu7ur3pr00f.agents.tools.market.run_async_call", return_value=fake_data
        ):
            output = get_salary_insights.func("Full Stack Engineer", "Spain")

        assert "Remote EU Co (Remote - Spain): EUR 70,000 - 90,000" in output
        assert "Guidehouse" not in output

    def test_reports_when_only_salary_mismatches_exist(self) -> None:
        fake_data = {
            "salary_data": [],
            "job_listings": [
                {
                    "company": "Guidehouse",
                    "salary": "USD 215,000 - 358,000",
                    "location": "Washington, DC, USA",
                }
            ],
        }

        with patch(
            "fu7ur3pr00f.agents.tools.market.run_async_call", return_value=fake_data
        ):
            output = get_salary_insights.func("AI Engineer", "Spain")

        assert "ignoring mismatched locations" in output
        assert "Guidehouse" not in output
