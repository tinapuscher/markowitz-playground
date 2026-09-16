"""Resolve an asset identifier via OpenFIGI."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from sample_portfolio import SAMPLE_WKNS
from wkn_lookup import AssetInfo, ListingCandidate, lookup_wkn


class ResolverError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ResolvedAsset:
    wkn: str
    name: str
    source_ticker: str
    exchange: str
    in_sample_cache: bool


def select_preferred_candidate(
    asset: AssetInfo,
) -> ListingCandidate:
    """
    Select one preferred German listing candidate.

    MVP decision:
    do not try many possible listings.
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


async def resolve_asset(wkn: str) -> ResolvedAsset:
    """
    Resolve one WKN.

    MVP behaviour:
    - identify the instrument via OpenFIGI
    - choose one preferred German listing
    - mark whether the WKN is in the cached sample universe
    - do not call a live market-data provider
    """

    try:
        asset: AssetInfo = await lookup_wkn(wkn)

    except ValueError as exc:
        raise ResolverError(
            code="INSTRUMENT_NOT_FOUND",
            message=str(exc),
        ) from exc

    except httpx.HTTPError as exc:
        raise ResolverError(
            code="IDENTIFICATION_PROVIDER_UNAVAILABLE",
            message=(
                "OpenFIGI konnte aktuell nicht erreicht werden."
            ),
        ) from exc

    candidate = select_preferred_candidate(asset)

    return ResolvedAsset(
        wkn=asset.wkn,
        name=candidate.name,
        source_ticker=candidate.ticker,
        exchange=candidate.exchange,
        in_sample_cache=asset.wkn in SAMPLE_WKNS,
    )
