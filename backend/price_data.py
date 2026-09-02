"""Historische Kurse – Yahoo Chart API (robust) mit yfinance als Fallback."""

from __future__ import annotations

import pandas as pd
import httpx

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

PERIOD_TO_RANGE = {
    "1y": "1y",
    "2y": "2y",
    "3y": "3y",
    "5y": "5y",
    "max": "max",
}


def _fetch_yahoo_chart(symbol: str, period: str = "3y") -> pd.Series | None:
    range_param = PERIOD_TO_RANGE.get(period, "3y")
    url = YAHOO_CHART.format(symbol=symbol)
    params = {"range": range_param, "interval": "1d", "events": "div,splits"}

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None

    chart = payload.get("chart") or {}
    if chart.get("error"):
        return None
    results = chart.get("result")
    if not results:
        return None

    block = results[0]
    timestamps = block.get("timestamp") or []
    quotes = (block.get("indicators") or {}).get("quote") or []
    if not timestamps or not quotes:
        return None

    q = quotes[0]
    closes = q.get("close") or []
    rows: list[tuple[pd.Timestamp, float]] = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        rows.append((pd.Timestamp(ts, unit="s", tz="UTC").tz_convert(None), float(close)))

    if len(rows) < 60:
        return None

    series = pd.Series(
        [v for _, v in rows],
        index=pd.DatetimeIndex([t for t, _ in rows]),
        name=symbol,
    )
    return series.sort_index()


def _fetch_yfinance(symbol: str, period: str = "3y") -> pd.Series | None:
    try:
        import yfinance as yf
    except ImportError:
        return None

    data = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if data is None or data.empty:
        return None

    if "Close" in data.columns:
        s = data["Close"]
    elif isinstance(data.columns, pd.MultiIndex):
        lvl0 = data.columns.get_level_values(0)
        if "Close" in lvl0:
            s = data["Close"].iloc[:, 0]
        else:
            s = data.iloc[:, 0]
    else:
        s = data.iloc[:, 0]

    s = s.dropna()
    s.name = symbol
    return s if len(s) >= 60 else None


def fetch_price_series(symbol: str, period: str = "3y") -> pd.Series | None:
    series = _fetch_yahoo_chart(symbol, period)
    if series is not None:
        return series
    return _fetch_yfinance(symbol, period)


def fetch_prices(tickers: list[str], period: str = "3y") -> pd.DataFrame:
    """Lädt Schlusskurse für alle Symbole; wirft ValueError bei Fehlschlag."""
    series_list: list[pd.Series] = []
    failed: list[str] = []

    for ticker in tickers:
        s = fetch_price_series(ticker, period)
        if s is not None and len(s) >= 60:
            series_list.append(s)
        else:
            failed.append(ticker)

    if len(series_list) < 2:
        failed_txt = ", ".join(failed) if failed else ", ".join(tickers)
        raise ValueError(
            f"Keine Kursdaten verfügbar für: {failed_txt}. "
            "Prüfen Sie die Ticker (z. B. auf finance.yahoo.com) oder starten Sie das "
            "Backend neu nach: pip install -U 'yfinance>=1.0'"
        )

    prices = pd.concat(series_list, axis=1).sort_index()
    prices = prices.ffill().dropna(how="any")

    if prices.shape[0] < 60:
        raise ValueError("Zu wenig historische Daten (mindestens ~60 Handelstage).")

    return prices
