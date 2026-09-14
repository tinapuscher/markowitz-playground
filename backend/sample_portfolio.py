"""Optimization of the cached sample portfolio."""

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