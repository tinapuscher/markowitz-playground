import fs from "node:fs";
import path from "node:path";

const SAMPLE_ASSETS = [
  { wkn: "A0RPWH", symbol: "EUNL.DE", exposure: "MSCI World" },
  { wkn: "A0YEDL", symbol: "SXRV.DE", exposure: "Nasdaq-100" },
  { wkn: "593393", symbol: "EXS1.DE", exposure: "DAX" },
  { wkn: "A111X9", symbol: "IS3N.DE", exposure: "Emerging Markets" },
  { wkn: "A2DWBY", symbol: "IUSN.DE", exposure: "World Small Cap" },
  {
    wkn: "A0YBRY",
    symbol: "EUN9.DE",
    exposure: "Euro Government Bonds 5-7yr",
  },
  { wkn: "A0S9GB", symbol: "4GLD.DE", exposure: "Gold" },
  { wkn: "DBX0AN", symbol: "XEON.DE", exposure: "EUR Overnight" },
];

const OUTPUT_DIR = path.resolve(
  process.cwd(),
  "backend",
  "data",
  "sample_prices"
);

function loadApiKey() {
  const envPath = path.resolve(process.cwd(), ".env");
  const envContent = fs.readFileSync(envPath, "utf8");

  const line = envContent
    .split("\n")
    .find((entry) => entry.startsWith("MARKETSTACK_API_KEY="));

  if (!line) {
    throw new Error("MARKETSTACK_API_KEY not found in .env");
  }

  return line.slice("MARKETSTACK_API_KEY=".length).trim();
}

const API_KEY = loadApiKey();

async function fetchAsset(asset) {
  const url =
    `https://api.marketstack.com/v2/eod` +
    `?access_key=${encodeURIComponent(API_KEY)}` +
    `&symbols=${encodeURIComponent(asset.symbol)}` +
    `&limit=1000`;

  const response = await fetch(url);
  const body = await response.json();

  if (!response.ok) {
    throw new Error(
      `${asset.wkn} / ${asset.symbol}: HTTP ${response.status}`
    );
  }

  if (!Array.isArray(body?.data) || body.data.length === 0) {
    throw new Error(
      `${asset.wkn} / ${asset.symbol}: no price data returned`
    );
  }

  const rows = body.data
      .filter(
        (row) =>
          row.date &&
          typeof row.close === "number" &&
          Number.isFinite(row.close) &&
          row.close > 0
)
    .map((row) => ({
      date: row.date.slice(0, 10),
      close: row.close,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));

  if (rows.length === 0) {
    throw new Error(
      `${asset.wkn} / ${asset.symbol}: no valid closing prices`
    );
  }

  return rows;
}

function toCsv(rows) {
  const lines = ["date,close"];

  for (const row of rows) {
    lines.push(`${row.date},${row.close}`);
  }

  return `${lines.join("\n")}\n`;
}

async function run() {
  console.log("\nUpdating cached sample market data...\n");

  /*
   * Fetch everything first.
   *
   * We deliberately do not touch existing CSV files until all eight
   * Marketstack requests have succeeded.
   */
  const downloads = [];

  for (const asset of SAMPLE_ASSETS) {
    process.stdout.write(
      `${asset.wkn} → ${asset.symbol} → fetching... `
    );

    const rows = await fetchAsset(asset);

    downloads.push({
      asset,
      rows,
    });

    console.log(`✅ ${rows.length} prices`);
  }

  /*
   * Only after every asset succeeded do we write the new cache.
   */
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  for (const { asset, rows } of downloads) {
    const filePath = path.join(
      OUTPUT_DIR,
      `${asset.wkn}.csv`
    );

    fs.writeFileSync(filePath, toCsv(rows), "utf8");
  }

  console.log(
    `\n✅ ${downloads.length}/${SAMPLE_ASSETS.length} sample datasets updated.`
  );

  console.log(`\nSaved to:\n${OUTPUT_DIR}\n`);
}

run().catch((error) => {
  console.error("\n❌ Sample data update failed.");
  console.error(error.message);
  console.error(
    "\nExisting cached CSV files were not intentionally replaced."
  );
  process.exit(1);
});