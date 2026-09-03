# Markowitz Playground

**Explore portfolio optimization with real market data — and the real-world data problems behind it.**

Markowitz Playground is an educational application for exploring Modern Portfolio Theory with real financial instruments.

The basic idea is simple:

1. Select assets.
2. Retrieve historical market data.
3. Calculate returns, risk and correlations.
4. Let the Markowitz model derive a model allocation.
5. Make the result understandable rather than just displaying numbers.

The project started as a portfolio optimization experiment. While building it, one thing became clear very quickly:

> **The optimization model is not the hardest part. Reliable instrument identification and consistent access to historical market data are.**

That discovery now shapes both the architecture and the MVP.

---

## Current status

**MVP in active development**

Already implemented:

- React/Vite frontend
- FastAPI backend
- WKN-based instrument lookup via OpenFIGI
- separation between instrument identity and market-data listing
- Yahoo Finance listing validation
- structured handling of unavailable or rate-limited market data
- Markowitz optimization engine
- efficient-frontier calculation
- correlation matrix calculation
- frontend/backend integration
- centralized UI copy for future localization

The current UI already communicates with the backend and distinguishes between:

- an unknown instrument
- an identified instrument for which historical price data cannot be resolved reliably
- a temporarily unavailable market-data provider
- internal application errors

The next MVP step is to make the optimization experience reproducible independently of third-party API availability.

---

## Why market data became a product problem

A WKN or ISIN identifies a financial instrument. A market-data provider, however, may identify prices through exchange-specific ticker symbols.

Those are not necessarily the same thing.

For example, one ETF can:

- have one WKN and ISIN,
- trade on several exchanges,
- have several listing symbols,
- and be represented differently by different data providers.

This means that a naive pipeline such as

`WKN → ticker → historical prices`

is not reliable enough.

The current architecture therefore separates the problem into distinct responsibilities:

`UI → Asset Resolver → Market Data Provider → Markowitz Engine`

OpenFIGI is used to identify instruments and possible listings. Market-data availability is validated separately.

During development, Yahoo Finance also started rate-limiting repeated requests. The application handles this explicitly instead of incorrectly reporting the instrument as unknown.

This is an important distinction: **an unavailable data source is not the same as unavailable data, and neither means that the financial instrument does not exist.**

---

## MVP data strategy

Reliable financial market data is a product dependency, not merely an implementation detail.

Free market-data sources are useful for experimentation but cannot necessarily provide the reliability expected from a production application.

For the MVP, the planned approach is therefore hybrid:

### Reproducible demo dataset

A curated set of real instruments with cached historical data will provide a stable path through the complete optimization experience.

This makes the educational model reproducible and keeps the core experience independent of external rate limits.

### External asset lookup

Lookup of additional real instruments can remain available where third-party data sources allow it.

Failures are surfaced transparently rather than silently substituted or interpreted as missing instruments.

### Production perspective

A production-grade version would require a deliberate market-data strategy, potentially including:

- a commercial data provider
- caching
- provider fallbacks
- stronger listing resolution
- data-quality monitoring

The MVP deliberately does not hide this boundary.

---

## The Markowitz model

The optimization engine uses historical asset returns to estimate:

- expected annual return
- annualized volatility
- covariance
- correlation
- Sharpe ratio
- model portfolio weights
- efficient-frontier portfolios

The current optimizer uses long-only allocations whose weights sum to 100%.

The results are intended to demonstrate the mechanics and implications of Modern Portfolio Theory — **not to recommend investments.**

---

## Tech stack

### Frontend

- React
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- NumPy
- pandas
- SciPy
- httpx
- yfinance

### Data / instrument resolution

- OpenFIGI
- Yahoo Finance market data

The external data-provider layer is intentionally separated from the optimization logic so that providers can be replaced or extended later.

---

## Project structure

```text
markowitz-app/
├── backend/
│   ├── asset_resolver.py
│   ├── main.py
│   ├── markowitz.py
│   ├── price_data.py
│   ├── requirements.txt
│   ├── test_resolver.py
│   └── wkn_lookup.py
├── scripts/
├── src/
│   ├── locales/
│   │   └── en.js
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
└── README.md
