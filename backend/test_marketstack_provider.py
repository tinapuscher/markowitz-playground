"""Test Marketstack provider with XDWT.DE as proof of concept."""

import asyncio

from marketstack_provider import fetch_price_series, MarketstackError


async def main():
    print("\nMarketstack Provider Test: XDWT.DE")
    print("=" * 50)

    symbol = "XDWT.DE"

    try:
        series, result = await fetch_price_series(
            symbol=symbol,
            min_observations=60,
        )

        print(f"\n✅ Successfully fetched data for {symbol}")
        print(f"   Symbol:         {result.symbol}")
        print(f"   Observations:   {result.observations}")
        print(f"   First date:     {result.first_date}")
        print(f"   Last date:      {result.last_date}")
        print(f"   Price field:    {result.price_field}")

        # Validate series properties
        print(f"\nSeries validation:")
        print(f"   Length:         {len(series)}")
        print(f"   DatetimeIndex:  {isinstance(series.index, pd.DatetimeIndex)}")
        print(f"   NaN count:      {series.isna().sum()}")
        print(f"   Min price:      {series.min():.2f}")
        print(f"   Max price:      {series.max():.2f}")

        # Note on adj_close vs close
        if result.price_field == "adj_close":
            print(f"\n   Note: Using adjusted close (adj_close)")
        else:
            print(f"\n   Note: Using raw close (adj_close not sufficiently populated)")

    except MarketstackError as exc:
        print(f"\n❌ MarketstackError [{exc.code}]")
        print(f"   {exc.message}")
    except Exception as exc:
        print(f"\n❌ Unexpected error")
        print(f"   {type(exc).__name__}: {exc}")

    print()


if __name__ == "__main__":
    import pandas as pd  # Import here to avoid unnecessary dependency

    asyncio.run(main())
