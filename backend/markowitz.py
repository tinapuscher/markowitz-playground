"""Mean-variance (Markowitz) portfolio optimization."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from price_data import fetch_prices


@dataclass
class OptimizationResult:
    tickers: list[str]
    names: list[str]
    weights: list[float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    efficient_frontier: list[dict[str, float]]
    correlation_matrix: list[list[float]]
    annual_returns: dict[str, float]


def _fetch_returns(tickers: list[str], period: str = "3y") -> pd.DataFrame:
    prices = fetch_prices(tickers, period=period)
    returns = prices.pct_change().dropna()
    if returns.shape[1] < 2 and len(tickers) > 1:
        raise ValueError("Kursdaten für mehrere Assets konnten nicht abgeglichen werden.")

    # Drop assets with too many missing values
    missing_frac = returns.isna().mean()
    valid = missing_frac[missing_frac < 0.1].index.tolist()
    if len(valid) < 2:
        raise ValueError("Zu viele fehlende Werte in den Kursreihen.")
    returns = returns[valid].dropna()
    return returns


def _annualize(mu: np.ndarray, cov: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return mu * 252, cov * 252


def _portfolio_stats(weights: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> tuple[float, float]:
    ret = float(weights @ mu)
    vol = float(np.sqrt(weights @ cov @ weights))
    return ret, vol


def _max_sharpe(mu: np.ndarray, cov: np.ndarray, risk_free: float) -> np.ndarray:
    n = len(mu)

    def neg_sharpe(w: np.ndarray) -> float:
        ret, vol = _portfolio_stats(w, mu, cov)
        if vol < 1e-10:
            return 1e6
        return -(ret - risk_free) / vol

    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    bounds = tuple((0.0, 1.0) for _ in range(n))
    x0 = np.full(n, 1.0 / n)

    result = minimize(
        neg_sharpe,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    if not result.success:
        raise ValueError("Optimierung konnte nicht konvergieren.")
    return result.x


def _efficient_frontier(
    mu: np.ndarray, cov: np.ndarray, optimal_weights: np.ndarray, points: int = 25
) -> list[dict[str, float]]:
    n = len(mu)
    opt_ret, _ = _portfolio_stats(optimal_weights, mu, cov)

    # Min-variance portfolio
    def port_var(w: np.ndarray) -> float:
        return float(w @ cov @ w)

    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    bounds = tuple((0.0, 1.0) for _ in range(n))
    x0 = np.full(n, 1.0 / n)
    minvar = minimize(
        port_var, x0, method="SLSQP", bounds=bounds, constraints=constraints
    )
    min_ret, min_vol = _portfolio_stats(minvar.x, mu, cov)

    # Upper return bound: max single-asset return (long-only)
    max_ret = float(np.max(mu))
    target_returns = np.linspace(min_ret, min(max_ret, opt_ret * 1.15), points)

    frontier: list[dict[str, float]] = []
    for target in target_returns:
        def objective(w: np.ndarray) -> float:
            return float(w @ cov @ w)

        ret_constraint = {
            "type": "eq",
            "fun": lambda w, t=target: float(w @ mu) - t,
        }
        sum_constraint = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
        res = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=[sum_constraint, ret_constraint],
            options={"maxiter": 300},
        )
        if res.success:
            ret, vol = _portfolio_stats(res.x, mu, cov)
            frontier.append(
                {
                    "return": round(ret * 100, 2),
                    "volatility": round(vol * 100, 2),
                    "is_optimal": abs(ret - opt_ret) < 1e-4,
                }
            )
    return frontier


def optimize_portfolio(
    tickers: list[str],
    names: list[str],
    risk_free_rate: float = 0.02,
    period: str = "3y",
) -> OptimizationResult:
    if len(tickers) < 2:
        raise ValueError("Mindestens zwei Assets für eine Portfolio-Optimierung nötig.")

    returns = _fetch_returns(tickers, period=period)
    used_tickers = list(returns.columns)
    used_names = [
        names[tickers.index(t)] if t in tickers else t for t in used_tickers
    ]

    mu_daily = returns.mean().values
    cov_daily = returns.cov().values
    mu, cov = _annualize(mu_daily, cov_daily)

    weights = _max_sharpe(mu, cov, risk_free_rate)
    exp_ret, vol = _portfolio_stats(weights, mu, cov)
    sharpe = (exp_ret - risk_free_rate) / vol if vol > 0 else 0.0

    corr = returns.corr().values.tolist()
    annual_ret = {
        t: round(float(returns[t].mean() * 252 * 100), 2) for t in used_tickers
    }

    frontier = _efficient_frontier(mu, cov, weights)

    return OptimizationResult(
        tickers=used_tickers,
        names=used_names,
        weights=[round(float(w), 4) for w in weights],
        expected_return=round(exp_ret * 100, 2),
        volatility=round(vol * 100, 2),
        sharpe_ratio=round(float(sharpe), 3),
        efficient_frontier=frontier,
        correlation_matrix=[[round(c, 3) for c in row] for row in corr],
        annual_returns=annual_ret,
    )
