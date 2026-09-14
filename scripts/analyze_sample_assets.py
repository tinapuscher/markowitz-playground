"""Diagnostic view of the cached sample assets."""

from pathlib import Path

import pandas as pd


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

DATA_DIR = Path(__file__).parent.parent / "backend" / "data" / "sample_prices"

RISK_FREE_RATE = 0.02
TRADING_DAYS = 252


def load_prices() -> pd.DataFrame:
    series = []

    for wkn, _name in SAMPLE_ASSETS:
        frame = pd.read_csv(
            DATA_DIR / f"{wkn}.csv",
            parse_dates=["date"],
        )

        series.append(
            frame
            .set_index("date")["close"]
            .rename(wkn)
        )

    return pd.concat(
        series,
        axis=1,
        join="inner",
    ).sort_index()


def run():
    prices = load_prices()

    returns = prices.pct_change(
        fill_method=None
    ).dropna()

    annual_returns = returns.mean() * TRADING_DAYS
    annual_volatility = returns.std() * (TRADING_DAYS ** 0.5)

    correlations = returns.corr()

    print("\nAsset diagnostics")
    print("-----------------\n")

    for wkn, name in SAMPLE_ASSETS:
        expected_return = annual_returns[wkn]
        volatility = annual_volatility[wkn]

        sharpe = (
            (expected_return - RISK_FREE_RATE) / volatility
            if volatility > 0
            else 0.0
        )

        overnight_corr = correlations.loc[
            wkn,
            "DBX0AN",
        ]

        print(f"{name}")
        print(f"  WKN:                   {wkn}")
        print(f"  Annualized return:     {expected_return * 100:7.2f}%")
        print(f"  Annualized volatility: {volatility * 100:7.2f}%")
        print(f"  Standalone Sharpe:     {sharpe:7.3f}")
        print(f"  Corr. with Overnight:  {overnight_corr:7.3f}")
        print()


if __name__ == "__main__":
    run()