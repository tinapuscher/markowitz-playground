"""Resolve an asset identifier to a Yahoo Finance market symbol."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from wkn_lookup import AssetInfo, ListingCandidate, lookup_wkn


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

YAHOO_SUFFIX_BY_EXCHANGE = {
    "GY": ".DE",
    "GR": ".DE",
    "GF": ".F",
    "GS": ".SG",
    "GM": ".MU",
    "GT": ".DE",
}


class ResolverError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ResolvedAsset:
    wkn: str
    name: str
    yahoo_symbol: str
    source_ticker: str
    exchange: str


def yahoo_symbol_for_candidate(candidate: ListingCandidate) -> str:
    suffix = YAHOO_SUFFIX_BY_EXCHANGE.get(candidate.exchange, ".DE")
    ticker = candidate.ticker.strip().upper()

    if suffix and not ticker.endswith(suffix):
        return f"{ticker}{suffix}"

    return ticker


def select_preferred_candidate(
    asset: AssetInfo,
) -> ListingCandidate:
    """
    Select one preferred German listing candidate.

    MVP decision:
    do not try many possible listings against Yahoo.
    """

    if not asset.candidates:
        raise ResolverError(
            code="INSTRUMENT_NOT_FOUND",
            message="Keine geeigneten Listings gefunden.",
        )

    exchange_priority = {
        "GY": 0,
        "GR": 1,
        "GT": 2,
        "GF": 3,
        "GS": 4,
        "GM": 5,
    }

    return min(
        asset.candidates,
        key=lambda candidate: exchange_priority.get(
            candidate.exchange,
            99,
        ),
    )


def check_yahoo_symbol(symbol: str) -> bool:
    """
    Check whether Yahoo provides data for one symbol.

    Raises a dedicated error if Yahoo rate-limits the request.
    """

    url = YAHOO_CHART_URL.format(symbol=symbol)

    params = {
        "range": "1mo",
        "interval": "1d",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    try:
        with httpx.Client(
            timeout=5.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = client.get(
                url,
                params=params,
            )

    except httpx.RequestError as exc:
        raise ResolverError(
            code="MARKET_DATA_PROVIDER_UNAVAILABLE",
            message=(
                "Yahoo Finance konnte aktuell nicht erreicht werden."
            ),
        ) from exc

    if response.status_code == 429:
        raise ResolverError(
            code="MARKET_DATA_PROVIDER_UNAVAILABLE",
            message=(
                "Yahoo Finance begrenzt aktuell die Anzahl "
                "der Datenabfragen."
            ),
        )

    if not response.is_success:
        return False

    try:
        payload = response.json()
    except ValueError:
        return False

    chart = payload.get("chart") or {}

    if chart.get("error"):
        return False

    result = chart.get("result") or []

    if not result:
        return False

    timestamps = result[0].get("timestamp") or []

    return len(timestamps) > 0


async def resolve_asset(wkn: str) -> ResolvedAsset:
    """
    Resolve one WKN.

    MVP behaviour:
    - identify the instrument via OpenFIGI
    - choose one preferred German listing
    - validate one Yahoo symbol
    - do not guess through many alternative listings
    """

    try:
        asset: AssetInfo = await lookup_wkn(wkn)

    except ValueError as exc:
        raise ResolverError(
            code="INSTRUMENT_NOT_FOUND",
            message=str(exc),
        ) from exc

    candidate = select_preferred_candidate(asset)

    yahoo_symbol = yahoo_symbol_for_candidate(candidate)

    if not check_yahoo_symbol(yahoo_symbol):
        raise ResolverError(
            code="PRICE_DATA_UNAVAILABLE",
            message=(
                f"Das Instrument {asset.name} wurde erkannt, "
                "konnte aber nicht eindeutig mit historischen "
                "Yahoo-Finance-Kursdaten verknüpft werden."
            ),
        )

    return ResolvedAsset(
        wkn=asset.wkn,
        name=candidate.name,
        yahoo_symbol=yahoo_symbol,
        source_ticker=candidate.ticker,
        exchange=candidate.exchange,
    )