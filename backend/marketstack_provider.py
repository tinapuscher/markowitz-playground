"""Marketstack market data provider for custom assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx
import pandas as pd


class MarketstackError(Exception):
    """Base exception for Marketstack provider errors."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class FetchResult:
    """Result of a Marketstack price fetch."""

    symbol: str
    observations: int
    first_date: str
    last_date: str
    price_field: Literal["adj_close", "close"]


def _load_api_key() -> str:
    """Load Marketstack API key from environment."""
    from pathlib import Path

    env_path = Path(__file__).parent.parent / ".env"
    try:
        env_content = env_path.read_text()
    except FileNotFoundError:
        raise MarketstackError(
            code="ENV_NOT_FOUND",
            message="MARKETSTACK_API_KEY not found: .env file missing",
        )

    for line in env_content.split("\n"):
        if line.startswith("MARKETSTACK_API_KEY="):
            return line[len("MARKETSTACK_API_KEY=") :].strip()

    raise MarketstackError(
        code="API_KEY_MISSING",
        message="MARKETSTACK_API_KEY not found in .env file",
    )


async def fetch_price_series(
    symbol: str,
    date_from: str | None = None,
    date_to: str | None = None,
    min_observations: int = 60,
) -> tuple[pd.Series, FetchResult]:
    """
    Fetch historical daily prices from Marketstack.

    Args:
        symbol: Marketstack symbol (e.g., "XDWT.DE")
        date_from: Optional start date in YYYY-MM-DD format
        date_to: Optional end date in YYYY-MM-DD format
        min_observations: Minimum number of valid price observations required

    Returns:
        Tuple of (price_series, fetch_result) where price_series is a pandas Series
        with DatetimeIndex and fetch_result contains metadata.

    Raises:
        MarketstackError: If the fetch fails or data is invalid.
    """
    api_key = _load_api_key()

    url = "https://api.marketstack.com/v2/eod"
    params = {
        "access_key": api_key,
        "symbols": symbol,
        "limit": 1000,
    }

    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise MarketstackError(
            code="HTTP_ERROR",
            message=f"Marketstack API request failed: {exc}",
        ) from exc

    if "error" in payload:
        error = payload["error"]
        raise MarketstackError(
            code=error.get("code", "API_ERROR"),
            message=error.get("message", "Unknown Marketstack API error"),
        )

    data = payload.get("data", [])

    if not data:
        raise MarketstackError(
            code="NO_DATA",
            message=f"No price data returned for symbol {symbol}",
        )

    # Build price series using close as base (all rows must have valid close)
    rows = []
    for row in data:
        close = row.get("close")
        if close is None or not isinstance(close, (int, float)) or close <= 0:
            continue

        date_str = row.get("date", "")
        if not date_str:
            continue

        # Parse ISO date (may include time component)
        date_str_clean = date_str[:10] if "T" in date_str else date_str
        rows.append((date_str_clean, float(close), row.get("adj_close")))

    if len(rows) < min_observations:
        raise MarketstackError(
            code="INSUFFICIENT_DATA",
            message=f"Insufficient valid price observations: {len(rows)} (minimum {min_observations})",
        )

    # Determine which price field to use based on filtered data
    price_field: Literal["adj_close", "close"] = "close"

    # Check if adj_close is sufficiently populated in the filtered data
    adj_close_valid_count = sum(
        1
        for _, _, adj_close in rows
        if adj_close is not None
        and isinstance(adj_close, (int, float))
        and adj_close > 0
    )

    # Use adj_close if it's available in at least 90% of the filtered data
    if adj_close_valid_count >= len(rows) * 0.9:
        price_field = "adj_close"
        # Rebuild rows using adj_close
        rows = [
            (date, adj_close)
            for date, close, adj_close in rows
            if adj_close is not None
            and isinstance(adj_close, (int, float))
            and adj_close > 0
        ]
    else:
        # Use close, remove adj_close from tuples
        rows = [(date, close) for date, close, _ in rows]

    # Re-check minimum observations after potential filtering
    if len(rows) < min_observations:
        raise MarketstackError(
            code="INSUFFICIENT_DATA",
            message=f"Insufficient valid price observations: {len(rows)} (minimum {min_observations})",
        )

    # Create pandas Series
    df = pd.DataFrame(rows, columns=["date", "close"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    series = df["close"]

    # Validate no NaN values
    if series.isna().any():
        raise MarketstackError(
            code="INVALID_DATA",
            message="Price series contains NaN values after normalization",
        )

    # Create result metadata
    fetch_result = FetchResult(
        symbol=symbol,
        observations=len(series),
        first_date=series.index.min().strftime("%Y-%m-%d"),
        last_date=series.index.max().strftime("%Y-%m-%d"),
        price_field=price_field,
    )

    return series, fetch_result
