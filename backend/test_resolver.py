import asyncio

from asset_resolver import resolve_asset


TEST_WKNS = [
    "A113FM",
    "628930",
    "A2DU5H",
    "593393",
]


async def main() -> None:
    print("\nResolver test\n")

    for wkn in TEST_WKNS:
        try:
            asset = await resolve_asset(wkn)

            print(
                f"{wkn} -> "
                f"{asset.yahoo_symbol} | "
                f"{asset.name} | "
                f"{asset.exchange}"
            )
        except Exception as exc:
            print(f"{wkn} -> ERROR: {exc}")


if __name__ == "__main__":
    asyncio.run(main())