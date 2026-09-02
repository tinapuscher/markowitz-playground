"""Resolve German WKNs to instrument and listing candidates via OpenFIGI."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx


OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"

GERMAN_EXCHANGES = {"GY", "GR", "GF", "GS", "GM", "GT"}


@dataclass
class ListingCandidate:
    name: str
    ticker: str
    exchange: str
    security_type: str | None
    market_sector: str | None


@dataclass
class AssetInfo:
    wkn: str
    name: str
    candidates: list[ListingCandidate]


def normalize_wkn(wkn: str) -> str:
    cleaned = re.sub(r"[\s-]", "", wkn.strip().upper())

    if not re.fullmatch(r"[A-Z0-9]{6}", cleaned):
        raise ValueError("WKN muss genau 6 alphanumerische Zeichen haben.")

    return cleaned


async def lookup_wkn(wkn: str) -> AssetInfo:
    normalized = normalize_wkn(wkn)

    payload = [
        {
            "idType": "ID_WERTPAPIER",
            "idValue": normalized,
        }
    ]

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(OPENFIGI_URL, json=payload)
        response.raise_for_status()
        data = response.json()

    if not data or not isinstance(data, list):
        raise ValueError(f"Keine Daten für WKN {normalized} gefunden.")

    entry = data[0]

    if entry.get("error"):
        raise ValueError(entry["error"])

    results = entry.get("data") or []

    if not results:
        raise ValueError(
            f"WKN {normalized} ist unbekannt oder nicht auffindbar."
        )

    german_results = [
        item
        for item in results
        if (item.get("exchCode") or "").upper() in GERMAN_EXCHANGES
        and item.get("ticker")
    ]

    if not german_results:
        raise ValueError(
            f"Für WKN {normalized} wurde kein deutsches Listing gefunden."
        )

    candidates = [
        ListingCandidate(
            name=item.get("name")
            or item.get("securityDescription")
            or item["ticker"],
            ticker=item["ticker"].strip().upper(),
            exchange=(item.get("exchCode") or "").upper(),
            security_type=item.get("securityType"),
            market_sector=item.get("marketSector"),
        )
        for item in german_results
    ]

    # Remove exact duplicates while preserving OpenFIGI order.
    unique_candidates = list(
        dict.fromkeys(
            (
                c.name,
                c.ticker,
                c.exchange,
                c.security_type,
                c.market_sector,
            )
            for c in candidates
        )
    )

    candidates = [
        ListingCandidate(*candidate)
        for candidate in unique_candidates
    ]

    return AssetInfo(
        wkn=normalized,
        name=candidates[0].name,
        candidates=candidates,
    )