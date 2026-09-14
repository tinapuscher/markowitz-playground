# Markowitz Playground

**Explore portfolio optimization with real market data — and the real-world assumptions behind the model.**

Markowitz Playground is an educational application for exploring Modern Portfolio Theory with real financial instruments.

The idea is simple:

1. Select real market instruments.
2. Use historical market data.
3. Calculate returns, risk and correlations.
4. Let the Markowitz model derive a model allocation.
5. Make both the result and its assumptions transparent.

The project combines financial modeling with a practical product question: how do you make a mathematically valid model understandable, reproducible and honest about its data limitations?

---

## Current MVP

The current application implements a complete vertical slice:

`React UI → FastAPI → cached real market data → Markowitz optimization → model allocation`

The playground includes eight real sample instruments covering different markets and asset classes:

- MSCI World
- Nasdaq-100
- DAX
- Emerging Markets
- World Small Cap
- Euro Government Bonds
- Gold
- EUR Overnight / Money Market

Users can remove assets from the sample selection before running the optimization. The selected assets are sent to the backend and only those assets are included in the calculation.

The resulting model allocation is displayed directly on the corresponding asset cards.

---

## Model transparency

A Markowitz result is only meaningful in the context of its inputs and assumptions.

The application therefore displays the assumptions alongside every model result:

- historical data period actually used in the calculation
- risk-free rate
- optimization objective
- portfolio constraints

The current sample uses cached historical market data rather than fetching prices every time the model runs.

This keeps the demo reproducible and independent of temporary third-party API availability.

The current optimization objective is **Maximum Sharpe Ratio**, with **long-only allocations** whose weights sum to 100%.

The risk-free rate is currently an explicit model parameter. A future version may use the latest Euro Short-Term Rate (€STR) as its default while keeping the assumption visible and adjustable.

---

## Why market data became a product problem

A WKN or ISIN identifies a financial instrument. A market-data provider, however, may identify prices through exchange-specific ticker symbols.

Those are not necessarily the same thing.

One ETF can:

- have one WKN and ISIN,
- trade on several exchanges,
- have several listing symbols,
- and be represented differently by different data providers.

This means that a naive pipeline such as

`WKN → ticker → historical prices`

is not reliable enough.

The architecture therefore separates the responsibilities:

`UI → Asset Resolver → Market Data Provider → Markowitz Engine`

OpenFIGI is used to identify instruments and possible listings. Market-data availability is validated separately.

During development, Yahoo Finance also started rate-limiting repeated requests. The application handles this explicitly instead of incorrectly reporting the instrument as unknown.

**An unavailable data source is not the same as unavailable data — and neither means that the financial instrument does not exist.**

---

## Data strategy

Reliable financial market data is a product dependency, not merely an implementation detail.

For the current MVP, a curated set of real instruments is backed by cached historical market data. The sample cache can be refreshed deliberately rather than making the core optimization experience dependent on an external provider on every run.

Marketstack is currently used to refresh the cached sample dataset.

A separate asset-resolution path allows additional instruments to be identified via WKN or ISIN. Full integration of arbitrary user-selected assets into the optimization pipeline is still a future step.

A production-grade version would require a deliberate market-data strategy, potentially including:

- commercial or higher-reliability data sources
- adjusted or total-return price series
- caching and scheduled refreshes
- provider fallbacks
- stronger listing resolution
- data-quality monitoring

The MVP deliberately makes this boundary visible rather than hiding it.

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

The optimizer currently searches for the long-only portfolio with the maximum Sharpe ratio.

This also demonstrates an important property of portfolio optimization: **Markowitz results can be highly sensitive to the observation period, expected-return estimates and other model assumptions.**

A mathematically optimal result under a particular set of historical inputs is not automatically a sensible prediction of future returns.

The results are therefore presented as **model allocations, not investment recommendations**.

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

### Data and instrument resolution

- OpenFIGI
- Marketstack
- Yahoo Finance

The external data-provider layer is intentionally separated from the optimization logic so that providers can be replaced or extended later.

---

## Project structure

```text
markowitz-app/
├── backend/
│   ├── data/
│   │   └── sample_prices/
│   ├── asset_resolver.py
│   ├── main.py
│   ├── markowitz.py
│   ├── price_data.py
│   ├── requirements.txt
│   ├── sample_portfolio.py
│   ├── test_resolver.py
│   ├── test_sample_markowitz.py
│   └── wkn_lookup.py
├── scripts/
│   ├── analyze_sample_assets.py
│   └── update-sample-data.mjs
├── src/
│   ├── locales/
│   │   └── en.js
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
└── README.md
```

---

## Roadmap

Next steps include:

- expose the cache refresh date alongside the historical data period
- use €STR as a transparent default risk-free rate
- integrate custom resolved assets into the optimization pipeline
- visualize the efficient frontier
- improve historical return methodology, including adjusted / total-return data
- expand educational explanations of diversification, risk and correlation

---

## Disclaimer

**For educational purposes only — not investment advice.**

The application demonstrates portfolio-optimization concepts using historical market data and simplified model assumptions. Historical results and model allocations should not be interpreted as predictions or recommendations.

---

## AI-assisted development

Product concept, architecture and implementation were developed with support from generative AI.

The resulting code and product decisions were reviewed during development, but errors may remain.