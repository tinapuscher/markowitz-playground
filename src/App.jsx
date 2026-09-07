import { useState } from "react";
import { en } from "./locales/en";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";
const MAX_ASSETS = 20;

const SAMPLE_ASSETS = [
  {
    name: "iShares Core MSCI World UCITS ETF USD (Acc)",
    exposure: "MSCI World",
    type: "ETF",
    wkn: "A0RPWH",
    isin: "IE00B4L5Y983",
    isSample: true,
  },
  {
    name: "iShares Nasdaq 100 UCITS ETF (Acc)",
    exposure: "NASDAQ-100",
    type: "ETF",
    wkn: "A0YEDL",
    isin: "IE00B53SZB19",
    isSample: true,
  },
  {
    name: "iShares Core DAX UCITS ETF (DE) EUR (Acc)",
    exposure: "DAX",
    type: "ETF",
    wkn: "593393",
    isin: "DE0005933931",
    isSample: true,
  },
  {
    name: "iShares Core MSCI Emerging Markets IMI UCITS ETF (Acc)",
    exposure: "Emerging Markets",
    type: "ETF",
    wkn: "A111X9",
    isin: "IE00BKM4GZ66",
    isSample: true,
  },
  {
    name: "iShares MSCI World Small Cap UCITS ETF",
    exposure: "World Small Cap",
    type: "ETF",
    wkn: "A2DWBY",
    isin: "IE00BF4RFH31",
    isSample: true,
  },
  {
    name: "iShares Euro Government Bond 5-7yr UCITS ETF",
    exposure: "Euro Government Bonds",
    type: "ETF",
    wkn: "A0YBRY",
    isin: "DE000A0YBRY0",
    isSample: true,
  },
  {
    name: "Xetra-Gold",
    exposure: "Gold",
    type: "ETC",
    wkn: "A0S9GB",
    isin: "DE000A0S9GB0",
    isSample: true,
  },
  {
    name: "Xtrackers II EUR Overnight Rate Swap UCITS ETF 1C",
    exposure: "EUR Overnight / Money Market",
    type: "ETF",
    wkn: "DBX0AN",
    isin: "LU0290358497",
    isSample: true,
  },
];

function App() {
  const [identifier, setIdentifier] = useState("");
  const [assets, setAssets] = useState(SAMPLE_ASSETS);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCode, setErrorCode] = useState(null);

  const text = en;

  async function handleSubmit(event) {
    event.preventDefault();

    const cleanIdentifier = identifier.trim();

    if (!cleanIdentifier || isLoading) {
      return;
    }

    if (assets.length >= MAX_ASSETS) {
      return;
    }

    setIsLoading(true);
    setErrorCode(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/resolve/${encodeURIComponent(cleanIdentifier)}`
      );

      const data = await response.json();

      if (!response.ok || data.status !== "resolved") {
        setErrorCode(data.code || "INTERNAL_ERROR");
        return;
      }

      const alreadyAdded = assets.some(
        (asset) =>
          asset.wkn === data.asset.wkn ||
          (asset.isin &&
            data.asset.isin &&
            asset.isin === data.asset.isin)
      );

      if (!alreadyAdded) {
        setAssets((currentAssets) => [
          ...currentAssets,
          {
            ...data.asset,
            isSample: false,
          },
        ]);
      }

      setIdentifier("");
    } catch {
      setErrorCode("INTERNAL_ERROR");
    } finally {
      setIsLoading(false);
    }
  }

  function removeAsset(wkn) {
    setAssets((currentAssets) =>
      currentAssets.filter((asset) => asset.wkn !== wkn)
    );
  }

  const errorText = errorCode
    ? text.errors[errorCode] || text.errors.INTERNAL_ERROR
    : null;

  return (
    <div className="app-shell">
      <header className="header">
        <a className="brand" href="/">
          <span className="brand-mark">M</span>
          {text.app.name}
        </a>

        <nav className="navigation">
          <a className="active" href="#optimize">
            {text.app.navigation.optimize}
          </a>
          <a href="#learn">{text.app.navigation.learn}</a>
          <a href="#about">{text.app.navigation.about}</a>
        </nav>
      </header>

      <main>
        <section className="hero" id="optimize">
          <p className="eyebrow">{text.hero.eyebrow}</p>

          <h1>{text.hero.title}</h1>

          <p className="hero-description">
            {text.hero.description}
          </p>
        </section>

       <section className="workspace">
        <div className="workspace-header">
          <p className="section-label">{text.assetInput.label}</p>

          <p className="asset-counter">
            {assets.length} / {MAX_ASSETS} assets
          </p>
        </div>

        <button
          className="optimize-button"
          type="button"
          disabled={assets.length < 2}
        >
          {text.actions.optimize}
        </button>

        {assets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">↗</div>
            <h2>{text.emptyState.title}</h2>
            <p>{text.emptyState.description}</p>
          </div>
        ) : (
          <div className="asset-list">
            {assets.map((asset) => (
              <div
                className="asset-row"
                key={asset.wkn}
              >
                <div className="asset-main">
                  <div className="asset-heading">
                    <strong>{asset.exposure || asset.name}</strong>

                    <span className="asset-type">
                      {asset.type || "ETF"}
                    </span>
                  </div>

                  {asset.exposure && (
                    <p className="asset-name">
                      {asset.name}
                    </p>
                  )}

                  <p className="asset-identifiers">
                    WKN {asset.wkn}
                    {asset.isin && ` · ISIN ${asset.isin}`}
                    {!asset.isin &&
                      asset.yahoo_symbol &&
                      ` · ${asset.yahoo_symbol}`}
                  </p>
                </div>

                <button
                  className="remove-asset"
                  type="button"
                  onClick={() => removeAsset(asset.wkn)}
                  aria-label={`Remove ${asset.name}`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <form
          className="asset-form"
          onSubmit={handleSubmit}
        >
          <input
            value={identifier}
            onChange={(event) =>
              setIdentifier(event.target.value)
            }
            placeholder={text.assetInput.placeholder}
            aria-label={text.assetInput.label}
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={isLoading}
          >
            {isLoading
              ? text.assetInput.loading
              : text.assetInput.button}
          </button>
        </form>

        <div className="sample-note">
          <strong>{text.samples.title}</strong>
          <p>{text.samples.description}</p>
        </div>

        {errorText && (
          <div className="error-message" role="alert">
            <strong>{errorText.title}</strong>
            <p>{errorText.message}</p>
          </div>
        )}
      </section>
      </main>

      <footer>
        {text.footer.disclaimer}
      </footer>
    </div>
  );
}

export default App;