const testAssets = [
  { wkn: "A113FM", expected: "Xtrackers MSCI World Information Technology" },
  { wkn: "628930", expected: "iShares EURO STOXX Banks" },
  { wkn: "A2DU5H", expected: "BNP Paribas Easy Dividend Europe" },
  { wkn: "A0RPWH", expected: "iShares Core MSCI World" },
  { wkn: "A111X9", expected: "iShares Core MSCI Emerging Markets IMI" },
  { wkn: "A2DWBY", expected: "iShares MSCI World Small Cap" },
  { wkn: "A1CYW7", expected: "Invesco S&P 500" },
  { wkn: "593393", expected: "iShares Core DAX" },
  { wkn: "DBX0AN", expected: "Xtrackers EUR Overnight Rate Swap" },
  { wkn: "A0S9GB", expected: "Xetra-Gold" },
];

const OPENFIGI_URL = "https://api.openfigi.com/v3/mapping";

async function resolveWkns() {
  const payload = testAssets.map((asset) => ({
    idType: "ID_WERTPAPIER",
    idValue: asset.wkn,
  }));

  const response = await fetch(OPENFIGI_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`OpenFIGI request failed: ${response.status}`);
  }

  const results = await response.json();

  return testAssets.map((asset, index) => {
    const result = results[index];

    if (result?.error || !result?.data?.length) {
      return {
        wkn: asset.wkn,
        expected: asset.expected,
        status: "❌",
        matches: 0,
        name: "-",
        ticker: "-",
        exchange: "-",
        type: "-",
      };
    }

    const matches = result.data;

    const preferred =
      matches.find((m) => m.exchCode === "GR") ??
      matches.find((m) => m.exchCode === "GY") ??
      matches[0];

    return {
      wkn: asset.wkn,
      expected: asset.expected,
      status: "✅",
      matches: matches.length,
      name: preferred.name ?? "-",
      ticker: preferred.ticker ?? "-",
      exchange: preferred.exchCode ?? "-",
      type: preferred.securityType ?? "-",
    };
  });
}

async function testYahooSymbol(asset) {
  if (!asset.ticker || asset.ticker === "-") {
    return {
      ...asset,
      yahooSymbol: "-",
      yahooStatus: "❌",
      yahooName: "-",
      pricePoints: 0,
    };
  }

  const yahooSymbol = `${asset.ticker}.DE`;

  const period2 = Math.floor(Date.now() / 1000);
  const period1 = period2 - 60 * 60 * 24 * 365 * 5;

  const url =
    `https://query1.finance.yahoo.com/v8/finance/chart/` +
    `${encodeURIComponent(yahooSymbol)}` +
    `?period1=${period1}&period2=${period2}&interval=1d`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      return {
        ...asset,
        yahooSymbol,
        yahooStatus: `❌ HTTP ${response.status}`,
        yahooName: "-",
        pricePoints: 0,
      };
    }

    const data = await response.json();

    const result = data?.chart?.result?.[0];

    if (!result) {
      return {
        ...asset,
        yahooSymbol,
        yahooStatus: "❌ No data",
        yahooName: "-",
        pricePoints: 0,
      };
    }

    const timestamps = result.timestamp ?? [];
    const yahooName =
      result.meta?.longName ??
      result.meta?.shortName ??
      result.meta?.symbol ??
      "-";

    return {
      ...asset,
      yahooSymbol,
      yahooStatus: timestamps.length > 0 ? "✅" : "❌ No prices",
      yahooName,
      pricePoints: timestamps.length,
    };
  } catch (error) {
    return {
      ...asset,
      yahooSymbol,
      yahooStatus: `❌ ${error.message}`,
      yahooName: "-",
      pricePoints: 0,
    };
  }
}

async function run() {
  console.log("\n1) Resolving WKNs via OpenFIGI...\n");

  const resolvedAssets = await resolveWkns();

  console.table(
    resolvedAssets.map((asset) => ({
      WKN: asset.wkn,
      Status: asset.status,
      Matches: asset.matches,
      Name: asset.name,
      Ticker: asset.ticker,
      Exchange: asset.exchange,
      Type: asset.type,
    })),
  );

  console.log("\n2) Testing Yahoo symbols...\n");

  const yahooResults = [];

  for (const asset of resolvedAssets) {
    const result = await testYahooSymbol(asset);
    yahooResults.push(result);

    console.log(
      `${asset.wkn} → ${result.yahooSymbol} → ${result.yahooStatus}`,
    );
  }

  console.log("\nYahoo summary:\n");

  console.table(
    yahooResults.map((asset) => ({
      WKN: asset.wkn,
      OpenFIGI: asset.ticker,
      Yahoo: asset.yahooSymbol,
      Status: asset.yahooStatus,
      "Yahoo Name": asset.yahooName,
      "Price Points": asset.pricePoints,
    })),
  );
    await testYahooCandidates([
    "DAXEX.DE",
    "GDAXIEX.DE",
    "EXS1.DE",
  ]);
}

async function testYahooCandidates(symbols) {
  console.log("\n3) Testing fallback symbols for WKN 593393...\n");

  for (const symbol of symbols) {
    const period2 = Math.floor(Date.now() / 1000);
    const period1 = period2 - 60 * 60 * 24 * 365 * 5;

    const url =
      `https://query1.finance.yahoo.com/v8/finance/chart/` +
      `${encodeURIComponent(symbol)}` +
      `?period1=${period1}&period2=${period2}&interval=1d`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        console.log(`${symbol} → ❌ HTTP ${response.status}`);
        continue;
      }

      const data = await response.json();
      const result = data?.chart?.result?.[0];

      if (!result) {
        console.log(`${symbol} → ❌ No data`);
        continue;
      }

      const name =
        result.meta?.longName ??
        result.meta?.shortName ??
        result.meta?.symbol ??
        "-";

      const points = result.timestamp?.length ?? 0;

      console.log(`${symbol} → ✅ ${name} → ${points} price points`);
    } catch (error) {
      console.log(`${symbol} → ❌ ${error.message}`);
    }
  }
}

run().catch((error) => {
  console.error("\n❌ Test failed:");
  console.error(error);
  process.exit(1);
});