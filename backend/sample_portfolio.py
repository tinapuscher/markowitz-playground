"""Optimization of cached sample and custom Marketstack portfolios."""

from pathlib import Path

import pandas as pd

from markowitz import (
    OptimizationResult,
    _annualize,
    _efficient_frontier,
    _max_sharpe,
    _portfolio_stats,
)


SAMPLE_ASSETS = [
    ("A0RPWH", "MSCI World"),
    ("A0YEDL", "Nasdaq-100"),
    ("593393", "DAX"),
    ("A111X9", "Emerging Markets"),
    ("A2DWBY", "World Small Cap"),
    ("A0YBRY", "Euro Government Bonds 5-7yr"),
    ("A0S9GB", "Gold"),
    ("DBX0AN", "EUR Overnight"),
]

SAMPLE_WKNS = frozenset(wkn for wkn, _name in SAMPLE_ASSETS)

# Proof-of-concept mapping for custom assets to Marketstack symbols
# In production, this would be resolved via a proper ticker/exchange mapping system
CUSTOM_MARKETSTACK_SYMBOLS = {
    "A113FM": "XDWT.DE",  # X MSCI WORLD INFO TECH 1C
}

DATA_DIR = Path(__file__).parent / "data" / "sample_prices"


def _load_sample_prices(
    selected_wkns: list[str],
) -> pd.DataFrame:
    series = []

    for wkn in selected_wkns:
        file_path = DATA_DIR / f"{wkn}.csv"

        frame = pd.read_csv(
            file_path,
            parse_dates=["date"],
        )

        price_series = (
            frame
            .set_index("date")["close"]
            .rename(wkn)
        )

        series.append(price_series)

    return pd.concat(
        series,
        axis=1,
        join="inner",
    ).sort_index()


def optimize_sample_portfolio(
    selected_wkns: list[str],
    risk_free_rate: float = 0.02,
) -> OptimizationResult:
    unknown = [wkn for wkn in selected_wkns if wkn not in SAMPLE_WKNS]

    if unknown:
        raise ValueError(
            "Selected assets are not in the cached sample universe: "
            + ", ".join(unknown)
        )

    if len(selected_wkns) < 2:
        raise ValueError(
            "At least two cached sample assets are required."
        )

    prices = _load_sample_prices(selected_wkns)

    data_start = prices.index.min().date().isoformat()
    data_end = prices.index.max().date().isoformat()

    returns = prices.pct_change(
        fill_method=None
    ).dropna()

    mu_daily = returns.mean().values
    cov_daily = returns.cov().values

    mu, cov = _annualize(
        mu_daily,
        cov_daily,
    )

    weights = _max_sharpe(
        mu,
        cov,
        risk_free_rate,
    )

    expected_return, volatility = _portfolio_stats(
        weights,
        mu,
        cov,
    )

    sharpe = (
        (expected_return - risk_free_rate) / volatility
        if volatility > 0
        else 0.0
    )

    frontier = _efficient_frontier(
        mu,
        cov,
        weights,
    )

    asset_names = dict(SAMPLE_ASSETS)

    tickers = selected_wkns
    names = [
        asset_names[wkn]
        for wkn in selected_wkns
    ]

    annual_returns = {
        ticker: round(
            float(returns[ticker].mean() * 252 * 100),
            2,
        )
        for ticker in tickers
    }

    correlation_matrix = (
        returns
        .corr()
        .round(3)
        .values
        .tolist()
    )

    result = OptimizationResult(
        tickers=tickers,
        names=names,
        weights=[
            round(float(weight), 4)
            for weight in weights
        ],
        expected_return=round(
            expected_return * 100,
            2,
        ),
        volatility=round(
            volatility * 100,
            2,
        ),
        sharpe_ratio=round(
            float(sharpe),
            3,
        ),
        efficient_frontier=frontier,
        correlation_matrix=correlation_matrix,
        annual_returns=annual_returns,
    )

    assumptions = {
        "data_start": data_start,
        "data_end": data_end,
        "risk_free_rate": risk_free_rate,
        "objective": "maximum_sharpe",
        "constraints": "long_only",
    }

    return result, assumptions


async def _load_custom_prices(
    custom_wkns: list[str],
) -> dict[str, pd.Series]:
    """Load custom asset prices from Marketstack."""
    from marketstack_provider import fetch_price_series, MarketstackError

    custom_prices = {}
    errors = []

    for wkn in custom_wkns:
        if wkn not in CUSTOM_MARKETSTACK_SYMBOLS:
            errors.append(f"{wkn}: no Marketstack symbol mapping configured")
            continue

        symbol = CUSTOM_MARKETSTACK_SYMBOLS[wkn]
        try:
            series, _ = await fetch_price_series(symbol, min_observations=60)
            custom_prices[wkn] = series.rename(wkn)
        except MarketstackError as exc:
            errors.append(f"{wkn} ({symbol}): {exc.message}")

    if errors:
        raise ValueError(
            "Failed to fetch custom asset prices: " + "; ".join(errors)
        )

    return custom_prices


def _align_price_series(
    sample_prices: pd.DataFrame | None,
    custom_prices: dict[str, pd.Series],
    min_common_observations: int = 60,
) -> tuple[pd.DataFrame, str, str]:
    """
    Align sample and custom price series by common trading dates.

    Returns:
        Tuple of (aligned_prices, data_start, data_end)
    """
    all_series = []

    if sample_prices is not None and not sample_prices.empty:
        all_series.append(sample_prices)

    for wkn, series in custom_prices.items():
        all_series.append(series)

    if not all_series:
        raise ValueError("No price series provided for alignment")

    # Concatenate all series with inner join to get common dates
    aligned = pd.concat(all_series, axis=1, join="inner").sort_index()

    if len(aligned) < min_common_observations:
        raise ValueError(
            f"Insufficient common observations after alignment: {len(aligned)} "
            f"(minimum {min_common_observations})"
        )

    data_start = aligned.index.min().date().isoformat()
    data_end = aligned.index.max().date().isoformat()

    return aligned, data_start, data_end


async def optimize_mixed_portfolio(
    selected_wkns: list[str],
    selected_names: list[str],
    risk_free_rate: float = 0.02,
) -> tuple[OptimizationResult, dict]:
    """
    Optimize a portfolio combining cached sample and custom Marketstack assets.

    Args:
        selected_wkns: List of WKNs to optimize (can include sample and custom)
        selected_names: List of asset names corresponding to the WKNS
        risk_free_rate: Risk-free rate for Sharpe ratio calculation

    Returns:
        Tuple of (OptimizationResult, assumptions)
    """
    if len(selected_wkns) < 2:
        raise ValueError("At least two assets are required for optimization.")

    # Separate sample and custom assets
    sample_wkns = [wkn for wkn in selected_wkns if wkn in SAMPLE_WKNS]
    custom_wkns = [wkn for wkn in selected_wkns if wkn not in SAMPLE_WKNS]

    # Load sample prices if any
    sample_prices = None
    if sample_wkns:
        sample_prices = _load_sample_prices(sample_wkns)

    # Load custom prices if any
    custom_prices = {}
    if custom_wkns:
        custom_prices = await _load_custom_prices(custom_wkns)

    # Align all series by common dates
    prices, data_start, data_end = _align_price_series(
        sample_prices, custom_prices, min_common_observations=60
    )

    # Calculate returns
    returns = prices.pct_change(fill_method=None).dropna()

    if returns.shape[1] < 2:
        raise ValueError(
            "Insufficient assets with valid returns after alignment"
        )

    # Markowitz optimization
    mu_daily = returns.mean().values
    cov_daily = returns.cov().values

    mu, cov = _annualize(mu_daily, cov_daily)

    weights = _max_sharpe(mu, cov, risk_free_rate)

    expected_return, volatility = _portfolio_stats(weights, mu, cov)

    sharpe = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0.0

    frontier = _efficient_frontier(mu, cov, weights)

    # Build result
    tickers = list(returns.columns)
    names = [selected_names[selected_wkns.index(t)] for t in tickers]

    annual_returns = {
        ticker: round(float(returns[ticker].mean() * 252 * 100), 2)
        for ticker in tickers
    }

    correlation_matrix = (
        returns.corr().round(3).values.tolist()
    )

    result = OptimizationResult(
        tickers=tickers,
        names=names,
        weights=[round(float(w), 4) for w in weights],
        expected_return=round(expected_return * 100, 2),
        volatility=round(volatility * 100, 2),
        sharpe_ratio=round(float(sharpe), 3),
        efficient_frontier=frontier,
        correlation_matrix=correlation_matrix,
        annual_returns=annual_returns,
    )

    # Build assumptions with data source information
    data_sources = []
    if sample_wkns:
        data_sources.append(f"cached sample ({len(sample_wkns)} assets)")
    if custom_wkns:
        data_sources.append(f"Marketstack ({len(custom_wkns)} assets)")

    assumptions = {
        "data_start": data_start,
        "data_end": data_end,
        "risk_free_rate": risk_free_rate,
        "objective": "maximum_sharpe",
        "constraints": "long_only",
        "data_sources": ", ".join(data_sources),
    }

    return result, assumptions