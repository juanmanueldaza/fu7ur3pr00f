"""Financial data MCP client for currency conversion and PPP comparison.

Uses two free APIs (no authentication required):
- ExchangeRate-API: Real-time exchange rates for 170+ currencies
  https://www.exchangerate-api.com/docs/free
- World Bank: Purchasing Power Parity (PPP) conversion factors
  https://api.worldbank.org/v2/

Uses pycountry for ISO country code resolution.
"""

import time
from typing import Any

import pycountry

from fu7ur3pr00f.constants import FOREX_API_BASE, PPP_API_BASE

from ..config import settings
from .base import MCPToolResult
from .http_client import HTTPMCPClient

# Module-level caches (MCP clients are created/destroyed per tool call)
_forex_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_ppp_cache: dict[str, tuple[float, float, str]] = {}  # code -> (ts, ratio, year)

_PPP_CACHE_TTL = 24 * 3600  # 24 hours (annual data)


def resolve_country_code(country: str) -> str:
    """Resolve country name or code to ISO 3166-1 alpha-3.

    Uses pycountry library for robust country code resolution.
    Handles full names ("Argentina"), alpha-2 ("AR"), and alpha-3 ("ARG").

    Args:
        country: Country name or code

    Returns:
        ISO 3166-1 alpha-3 country code

    Raises:
        ValueError: If country cannot be resolved
    """
    stripped = country.strip()

    # Try alpha-3 first (3 letters)
    if len(stripped) == 3 and stripped.isalpha():
        country_obj = pycountry.countries.get(alpha_3=stripped.upper())
        if country_obj:
            return country_obj.alpha_3

    # Try alpha-2 (2 letters)
    if len(stripped) == 2 and stripped.isalpha():
        country_obj = pycountry.countries.get(alpha_2=stripped.upper())
        if country_obj:
            return country_obj.alpha_3

    # Try by name (case-insensitive)
    country_obj = pycountry.countries.search_fuzzy(stripped)
    if country_obj:
        return country_obj[0].alpha_3

    raise ValueError(f"Cannot resolve country: {country!r}")


class FinancialMCPClient(HTTPMCPClient):
    """Financial data client for forex and PPP.

    Free APIs, no authentication required.
    - Exchange rates: 170+ currencies including ARS, BRL, MXN
    - PPP data: World Bank annual purchasing power parity ratios
    """

    DEFAULT_TIMEOUT = 45.0  # World Bank API can be slow
    BASE_URL = FOREX_API_BASE
    PPP_URL = PPP_API_BASE
    PPP_INDICATOR = "PA.NUS.PPPC.RF"

    async def list_tools(self) -> list[str]:
        """List available tools."""
        return ["convert_currency", "get_ppp_factor"]

    async def _tool_convert_currency(self, args: dict[str, Any]) -> MCPToolResult:
        """Convert between currencies using real-time rates."""
        amount = float(args.get("amount", 1))
        from_cur = args.get("from_currency", "USD").upper()
        to_cur = args.get("to_currency", "USD").upper()

        now = time.time()
        cached = _forex_cache.get(from_cur)

        if cached and (now - cached[0]) < settings.forex_cache_hours * 3600:
            data = cached[1]
        else:
            _, data = await self._api_request(f"/{from_cur}")
            if data.get("result") != "success":
                return self._format_response(
                    {"error": f"Exchange rate API error: {data.get('result')}"},
                    data,
                    "convert_currency",
                )
            _forex_cache[from_cur] = (now, data)

        rates = data.get("rates", {})
        if to_cur not in rates:
            return self._format_response(
                {"error": f"Currency {to_cur!r} not supported"},
                data,
                "convert_currency",
            )

        rate = rates[to_cur]
        output = {
            "from": from_cur,
            "to": to_cur,
            "amount": amount,
            "converted": round(amount * rate, 2),
            "rate": rate,
            "date": data.get("time_last_update_utc", ""),
        }
        return self._format_response(output, data, "convert_currency")

    async def _tool_get_ppp_factor(self, args: dict[str, Any]) -> MCPToolResult:
        """Get PPP conversion factor for a country."""
        country = args.get("country", "")
        code = resolve_country_code(country)
        now = time.time()

        cached = _ppp_cache.get(code)
        if cached and (now - cached[0]) < _PPP_CACHE_TTL:
            ppp_ratio, year = cached[1], cached[2]
            return self._format_ppp_output(country, code, ppp_ratio, year, {})

        # Use PPP_URL for World Bank API (different from BASE_URL)
        _, data = await self._api_request(
            f"/{code}/indicator/{self.PPP_INDICATOR}",
            params={"format": "json", "per_page": 5},
            base_url=self.PPP_URL,
        )

        entries = data[1] if len(data) > 1 and data[1] else []
        ppp_ratio, year = self._find_latest_ppp(entries)

        if ppp_ratio is not None:
            _ppp_cache[code] = (now, ppp_ratio, year or "")

        return self._format_ppp_output(country, code, ppp_ratio, year, data)

    def _find_latest_ppp(self, entries: list) -> tuple[float | None, str | None]:
        """Find most recent non-null PPP value."""
        for entry in entries:
            if entry.get("value") is not None:
                return entry["value"], entry.get("date", "")
        return None, None

    def _format_ppp_output(
        self,
        country: str,
        code: str,
        ppp_ratio: float | None,
        year: str | None,
        raw_data: dict,
    ) -> MCPToolResult:
        """Format PPP output consistently."""
        if ppp_ratio is None:
            output = {
                "country": country,
                "country_code": code,
                "ppp_ratio": None,
                "year": None,
                "interpretation": "No PPP data available",
            }
        else:
            output = {
                "country": country,
                "country_code": code,
                "ppp_ratio": ppp_ratio,
                "year": year,
                "interpretation": f"Price level is {ppp_ratio * 100:.1f}% of the US",
            }
        return self._format_response(output, raw_data, "get_ppp_factor")
