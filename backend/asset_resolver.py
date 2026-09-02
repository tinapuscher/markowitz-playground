from __future__ import annotations

from dataclasses import dataclass

from price_data import fetch_price_series
from wkn_lookup import AssetInfo, ListingCandidate, lookup_wkn


YAHOO_SUFFIX_BY_EXCHANGE = {
    "GY": ".DE",
    "GR": ".DE",
    "GF": ".F",
    "GS": ".SG",
    "GM": ".MU",
    "GT": ".DE",
}


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


async def resolve_asset(
    wkn: str,
    period: str = "3y",
) -> ResolvedAsset:
    asset: AssetInfo = await lookup_wkn(wkn)

    tried_symbols: set[str] = set()

    for candidate in asset.candidates:
        yahoo_symbol = yahoo_symbol_for_candidate(candidate)

        if yahoo_symbol in tried_symbols:
            continue

        tried_symbols.add(yahoo_symbol)

        series = fetch_price_series(
            yahoo_symbol,
            period=period,
        )

        if series is None:
            continue

        return ResolvedAsset(
            wkn=asset.wkn,
            name=candidate.name,
            yahoo_symbol=yahoo_symbol,
            source_ticker=candidate.ticker,
            exchange=candidate.exchange,
        )

    raise ValueError(
        f"Für WKN {asset.wkn} konnte kein Yahoo-Symbol "
        f"mit ausreichenden Kursdaten gefunden werden."
    )