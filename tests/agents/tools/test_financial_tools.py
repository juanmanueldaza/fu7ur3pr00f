"""Tests for financial tools."""

from unittest.mock import patch

import pytest

from fu7ur3pr00f.agents.tools.financial import compare_salary_ppp, convert_currency

pytestmark = pytest.mark.unit


class TestConvertCurrency:
    """Test convert_currency tool."""

    def test_converts_successfully(self) -> None:
        mock_result = {"converted": 100.0, "rate": 0.01, "date": "2024-01-01"}

        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            return_value=mock_result,
        ):
            result = convert_currency.invoke(
                {"amount": 10000, "from_currency": "ARS", "to_currency": "USD"}
            )

        assert "10,000.00" in result
        assert "100.00" in result
        assert "0.01" in result
        assert "2024-01-01" in result

    def test_returns_error_on_failure(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            return_value={"error": "Rate not found"},
        ):
            result = convert_currency.invoke(
                {"amount": 100, "from_currency": "XYZ", "to_currency": "USD"}
            )

        assert "Currency conversion error" in result

    def test_rejects_negative_amount(self) -> None:
        result = convert_currency.invoke(
            {"amount": -100, "from_currency": "ARS", "to_currency": "USD"}
        )
        assert "Invalid amount" in result

    def test_rejects_zero_amount(self) -> None:
        result = convert_currency.invoke(
            {"amount": 0, "from_currency": "ARS", "to_currency": "USD"}
        )
        assert "Invalid amount" in result

    def test_rejects_infinite_amount(self) -> None:
        result = convert_currency.invoke(
            {"amount": float("inf"), "from_currency": "ARS", "to_currency": "USD"}
        )
        assert "Invalid amount" in result


class TestCompareSalaryPpp:
    """Test compare_salary_ppp tool."""

    def test_compares_single_country(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            side_effect=[
                {"converted": 50000, "rate": 0.5},
                {"ppp_ratio": 0.6, "year": "2023"},
                {"ppp_ratio": 1.0, "year": "2023"},
            ],
        ):
            result = compare_salary_ppp.invoke(
                {
                    "salary": 100000,
                    "currency": "ARS",
                    "country": "Argentina",
                    "target_countries": ["United States"],
                }
            )

        assert "50,000" in result
        assert "United States" in result
        assert "Purchasing power equivalents" in result

    def test_compares_multiple_countries(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            side_effect=[
                {"converted": 50000, "rate": 0.5},
                {"ppp_ratio": 0.6, "year": "2023"},
                {"ppp_ratio": 1.0, "year": "2023"},
                {"ppp_ratio": 0.8, "year": "2023"},
            ],
        ):
            result = compare_salary_ppp.invoke(
                {
                    "salary": 100000,
                    "currency": "ARS",
                    "country": "Argentina",
                    "target_countries": ["United States", "Spain"],
                }
            )

        assert "United States" in result
        assert "Spain" in result

    def test_defaults_to_us_when_no_targets(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            side_effect=[
                {"converted": 50000, "rate": 0.5},
                {"ppp_ratio": 0.6, "year": "2023"},
                {"ppp_ratio": 1.0, "year": "2023"},
            ],
        ):
            result = compare_salary_ppp.invoke(
                {"salary": 100000, "currency": "ARS", "country": "Argentina"}
            )

        assert "United States" in result

    def test_handles_missing_source_ppp(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            side_effect=[
                {"converted": 50000, "rate": 0.5},
                {"error": "No data"},
            ],
        ):
            result = compare_salary_ppp.invoke(
                {
                    "salary": 100000,
                    "currency": "ARS",
                    "country": "Unknown",
                    "target_countries": ["United States"],
                }
            )

        assert "PPP data not available" in result
        assert "50,000" in result

    def test_handles_missing_target_ppp(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            side_effect=[
                {"converted": 50000, "rate": 0.5},
                {"ppp_ratio": 0.6, "year": "2023"},
                {"error": "No data"},
            ],
        ):
            result = compare_salary_ppp.invoke(
                {
                    "salary": 100000,
                    "currency": "ARS",
                    "country": "Argentina",
                    "target_countries": ["Unknown"],
                }
            )

        assert "No PPP data available" in result
        assert "Unknown" in result

    def test_rejects_negative_salary(self) -> None:
        result = compare_salary_ppp.invoke(
            {"salary": -100000, "currency": "ARS", "country": "Argentina"}
        )
        assert "Invalid salary" in result

    def test_rejects_zero_salary(self) -> None:
        result = compare_salary_ppp.invoke(
            {"salary": 0, "currency": "ARS", "country": "Argentina"}
        )
        assert "Invalid salary" in result

    def test_returns_error_on_forex_failure(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.financial._financial",
            return_value={"error": "API down"},
        ):
            result = compare_salary_ppp.invoke(
                {"salary": 100000, "currency": "ARS", "country": "Argentina"}
            )

        assert "Currency conversion error" in result
