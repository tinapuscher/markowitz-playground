from pathlib import Path

import numpy as np
import pandas as pd

from markowitz import (
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

# Temporary assumption for today's test.
# Later this will use the current €STR.
RISK_FREE_RATE = 0.02


def load_sample_prices() -> pd.DataFrame:
    series = []

    for wkn, _name in SAMPLE_ASSETS:
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

    prices = pd.concat(series, axis=1, join="inner").sort_index()

    return prices


def run():
    prices = load_sample_prices()

    print("\nLoaded sample market data")
    print("-------------------------")
    print(f"Assets: {prices.shape[1]}")
    print(f"Shared trading days: {prices.shape[0]}")
    print(f"From: {prices.index.min().date()}")
    print(f"To:   {prices.index.max().date()}")

    returns = prices.pct_change(fill_method=None).dropna()

    print("\nReturn diagnostics")
    print("------------------")
    print("Rows:", len(returns))
    print("NaN:", returns.isna().sum().to_dict())
    print("Inf:", np.isinf(returns).sum().to_dict())
    print("Zero prices:", (prices == 0).sum().to_dict())

    mu_daily = returns.mean().values
    cov_daily = returns.cov().values

    mu, cov = _annualize(mu_daily, cov_daily)

    weights = _max_sharpe(
        mu,
        cov,
        RISK_FREE_RATE,
    )

    expected_return, volatility = _portfolio_stats(
        weights,
        mu,
        cov,
    )

    sharpe = (
        (expected_return - RISK_FREE_RATE) / volatility
        if volatility > 0
        else 0.0
    )

    frontier = _efficient_frontier(
        mu,
        cov,
        weights,
    )

    print("\nMarkowitz-optimized model allocation")
    print("------------------------------------")

    for (wkn, name), weight in zip(SAMPLE_ASSETS, weights):
        print(
            f"{name:<35} "
            f"{wkn:<8} "
            f"{weight * 100:>7.2f}%"
        )

    print("\nPortfolio metrics")
    print("-----------------")
    print(f"Expected return: {expected_return * 100:.2f}%")
    print(f"Volatility:      {volatility * 100:.2f}%")
    print(f"Sharpe ratio:    {sharpe:.3f}")
    print(f"Risk-free rate:  {RISK_FREE_RATE * 100:.2f}%")
    print(f"Frontier points: {len(frontier)}")

    print(f"\nWeight sum:      {weights.sum() * 100:.2f}%\n")


if __name__ == "__main__":
    run()