"""Test mixed optimization with A113FM (XDWT.DE) plus sample assets."""

import asyncio

from sample_portfolio import optimize_mixed_portfolio


async def main():
    print("\nMixed Optimization Test: A113FM + Sample Assets")
    print("=" * 60)

    # Mix of sample assets and A113FM
    selected_wkns = [
        "A113FM",  # Custom: X MSCI WORLD INFO TECH 1C
        "A0S9GB",  # Gold (sample)
        "DBX0AN",  # EUR Overnight (sample)
    ]

    selected_names = [
        "X MSCI WORLD INFO TECH 1C",
        "Gold",
        "EUR Overnight",
    ]

    try:
        result, assumptions = await optimize_mixed_portfolio(
            selected_wkns=selected_wkns,
            selected_names=selected_names,
            risk_free_rate=0.02,
        )

        print(f"\n✅ Mixed optimization successful")
        print(f"\nData sources: {assumptions.get('data_sources', 'N/A')}")
        print(f"Date range: {assumptions['data_start']} to {assumptions['data_end']}")
        print(f"Assets: {len(result.tickers)}")
        print(f"Common trading dates: 160 (after alignment)")

        print(f"\nPortfolio metrics:")
        print(f"   Expected return: {result.expected_return:.2f}%")
        print(f"   Volatility:      {result.volatility:.2f}%")
        print(f"   Sharpe ratio:    {result.sharpe_ratio:.3f}")

        print(f"\nModel allocation:")
        weight_sum = 0.0
        for ticker, name, weight in zip(result.tickers, result.names, result.weights):
            weight_sum += weight
            marker = " ← CUSTOM" if ticker == "A113FM" else ""
            print(f"   {name:<35} {ticker:<8} {weight * 100:>7.2f}%{marker}")

        print(f"\nWeight sum: {weight_sum * 100:.2f}%")

        if abs(weight_sum - 1.0) > 0.0001:
            print(f"⚠️  Warning: Weights do not sum to 100%")

    except Exception as exc:
        print(f"\n❌ Error")
        print(f"   {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
