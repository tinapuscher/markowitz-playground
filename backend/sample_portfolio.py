"""Optimization of cached sample assets."""

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

DATA_DIR = Path(__file__).parent / "data" / "sample_prices"


def _load_sample_prices(
    selected_wkns: list[str],
) -> pd.DataFrame:
    series = []

    for wkn, _name in SAMPLE_ASSETS:
        if wkn not in selected_wkns:
            continue

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

    if len(series) < 2:
        raise ValueError(
            "At least two cached sample assets are required."
        )

    return pd.concat(
        series,
        axis=1,
        join="inner",
    ).sort_index()


def optimize_sample_portfolio(
    selected_wkns: list[str],
    risk_free_rate: float = 0.02,
) -> OptimizationResult:
    available_wkns = {
        wkn
        for wkn, _name in SAMPLE_ASSETS
    }

    unknown_wkns = [
        wkn
        for wkn in selected_wkns
        if wkn not in available_wkns
    ]

    if unknown_wkns:
        raise ValueError(
            f"No cached sample data for: {', '.join(unknown_wkns)}"
        )

    prices = _load_sample_prices(selected_wkns)

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

    selected_assets = [
        (wkn, name)
        for wkn, name in SAMPLE_ASSETS
        if wkn in selected_wkns
    ]

    tickers = [
        wkn
        for wkn, _name in selected_assets
    ]

    names = [
        name
        for _wkn, name in selected_assets
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

    return OptimizationResult(
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