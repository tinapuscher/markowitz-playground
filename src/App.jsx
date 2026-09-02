import { useState } from "react";
import { en } from "./locales/en";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [identifier, setIdentifier] = useState("");
  const [assets, setAssets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCode, setErrorCode] = useState(null);

  const text = en;

  async function handleSubmit(event) {
    event.preventDefault();

    const cleanIdentifier = identifier.trim();

    if (!cleanIdentifier || isLoading) {
      return;
    }

    if (assets.length >= text.assetInput.maximum) {
      return;
    }

    setIsLoading(true);
    setErrorCode(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/resolve/${encodeURIComponent(
          cleanIdentifier
        )}`
      );

      const data = await response.json();

      if (!response.ok || data.status !== "resolved") {
        setErrorCode(data.code || "INTERNAL_ERROR");
        return;
      }

      const alreadyAdded = assets.some(
        (asset) => asset.wkn === data.asset.wkn
      );

      if (!alreadyAdded) {
        setAssets((currentAssets) => [
          ...currentAssets,
          data.asset,
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
            <div>
              <p className="section-label">
                {text.assetInput.label}
              </p>

              <p className="asset-counter">
                {assets.length} / {text.assetInput.maximum}{" "}
                {text.assetInput.counter}
              </p>
            </div>
          </div>

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
              {isLoading ? "Looking up..." : text.assetInput.button}
            </button>
          </form>

          {errorText && (
            <div className="error-message" role="alert">
              <strong>{errorText.title}</strong>
              <p>{errorText.message}</p>
            </div>
          )}

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
                  <div>
                    <strong>{asset.name}</strong>

                    <p>
                      WKN {asset.wkn} · {asset.yahoo_symbol}
                    </p>
                  </div>

                  <button
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

          <button
            className="optimize-button"
            type="button"
            disabled={assets.length < 2}
          >
            {text.actions.optimize}
          </button>
        </section>
      </main>

      <footer>
        {text.footer.disclaimer}
      </footer>
    </div>
  );
}

export default App;