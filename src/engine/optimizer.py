"""Portfolio optimization engine.

Two-level optimization:
1. Asset-class weights determined by risk level (from risk_weights.yaml)
2. Within each class, PyPortfolioOpt allocates to individual ETFs

This ensures different risk levels produce truly different portfolios.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import yfinance as yf
from pypfopt import EfficientFrontier, expected_returns, risk_models
from pypfopt.exceptions import OptimizationError as PFPOptError

from src.engine.metrics import (
    portfolio_expected_return,
    portfolio_volatility,
    sharpe_ratio,
    max_drawdown as calc_max_drawdown,
)
from src.utils.exceptions import PortfolioOptimizationError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# ── Config helpers ──────────────────────────────────────────────────────

def _load_config() -> dict:
    config_path = Path(__file__).parent.parent.parent / "config" / "risk_weights.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_risk_level_bounds(risk_level: str) -> dict[str, tuple[float, float]]:
    """Get (min, max) weight bounds for each asset class for a given risk level."""
    config = _load_config()
    levels = config["risk_levels"]
    level_data = levels.get(risk_level)
    if level_data is None:
        level_data = levels["balanced"]

    return {
        "equity": (level_data["equity_range"][0], level_data["equity_range"][1]),
        "bond": (level_data["bond_range"][0], level_data["bond_range"][1]),
        "gold": (level_data["gold_range"][0], level_data["gold_range"][1]),
        "cash": (level_data["cash_range"][0], level_data["cash_range"][1]),
    }


def get_asset_universe() -> list[dict]:
    """Get a flat list of all assets."""
    assets = _load_config()["asset_universe"]
    flat = []
    for asset_class, tickers in assets.items():
        for t in tickers:
            flat.append({
                "ticker": t["ticker"],
                "name": t["name"],
                "asset_class": t["class"],
            })
    return flat


def annualized_return(daily_returns: np.ndarray, trading_days: int = 252) -> float:
    """Compute annualized return from daily returns."""
    if len(daily_returns) == 0:
        return 0.0
    return float(np.mean(daily_returns) * trading_days)


def fetch_historical_prices(tickers: list[str], period: str = "5y") -> pd.DataFrame:
    """Fetch historical adjusted close prices from Yahoo Finance."""
    try:
        data = yf.download(tickers, period=period, auto_adjust=True, progress=False)
        if data.empty:
            raise PortfolioOptimizationError("无法获取历史价格数据")

        if len(tickers) == 1:
            close = data["Close"]
            if isinstance(close, pd.Series):
                return pd.DataFrame({tickers[0]: close})
            return close

        close = data["Close"]
        close = close.dropna(axis=1, thresh=int(len(close) * 0.7))
        close = close.ffill().dropna()

        if close.empty:
            raise PortfolioOptimizationError("没有足够的历史价格数据")

        return close
    except PortfolioOptimizationError:
        raise
    except Exception as e:
        logger.error("fetch_prices_failed", error=str(e))
        raise PortfolioOptimizationError(f"获取历史数据失败: {str(e)}")


# ── Main optimizer ──────────────────────────────────────────────────────

def optimize_portfolio(
    prices: pd.DataFrame,
    risk_level: str,
    asset_info: list[dict],
    risk_free_rate: float = 0.03,
) -> dict:
    """Two-level portfolio optimization with risk-level-aware constraints.

    1. Asset-class weights are bounded by risk level (from risk_weights.yaml)
    2. Within each class, PyPortfolioOpt allocates to the best ETFs
    3. Cash allocation fills any remainder

    Args:
        prices: DataFrame of historical prices (columns=tickers).
        risk_level: conservative | moderate | balanced | growth | aggressive.
        asset_info: List of dicts with ticker, name, asset_class.
        risk_free_rate: Risk-free rate for Sharpe calculation.

    Returns:
        Dict with allocations, metrics, and metadata.
    """
    class_bounds = _get_risk_level_bounds(risk_level)

    # Group assets by class
    class_tickers: dict[str, list[str]] = {}
    ticker_info = {}
    for a in asset_info:
        t = a["ticker"]
        if t not in prices.columns:
            continue
        cls = a.get("asset_class", "equity")
        if cls == "real_estate":
            cls = "equity"  # Treat REIT as equity
        if cls not in class_tickers:
            class_tickers[cls] = []
        class_tickers[cls].append(t)
        ticker_info[t] = a

    if not class_tickers.get("equity") or not class_tickers.get("bond"):
        raise PortfolioOptimizationError("资产类别数据不足，至少需要股票和债券类ETF")

    # ── Step 1: Determine target class weights ──────────────────────────
    # Use the MIDPOINT of the risk-level range as the target
    equity_target = (class_bounds["equity"][0] + class_bounds["equity"][1]) / 2
    bond_target = (class_bounds["bond"][0] + class_bounds["bond"][1]) / 2
    gold_target = (class_bounds["gold"][0] + class_bounds["gold"][1]) / 2
    cash_target = (class_bounds["cash"][0] + class_bounds["cash"][1]) / 2

    # ── Step 2: Within each class, find optimal ETF weights ─────────────
    final_allocations = []

    def _optimize_class(tickers_in_class: list[str], class_name: str) -> list[dict]:
        """Run mean-variance optimization on a subset of assets within one class."""
        if not tickers_in_class:
            return []

        sub_prices = prices[tickers_in_class].dropna()

        if len(tickers_in_class) == 1:
            # Single asset: 100% weight
            t = tickers_in_class[0]
            info = ticker_info.get(t, {"name": t, "asset_class": class_name})
            rets = sub_prices[t].pct_change().dropna().values
            return [{
                "ticker": t,
                "name": info.get("name", t),
                "asset_class": class_name,
                "weight": 1.0,
                "expected_return": round(float(annualized_return(rets)), 4),
                "volatility": round(float(np.std(rets) * np.sqrt(252)), 4),
            }]

        try:
            mu = expected_returns.mean_historical_return(sub_prices)
            S = risk_models.sample_cov(sub_prices)

            ef = EfficientFrontier(mu, S)

            if class_name == "bond":
                # Bonds: prioritize low volatility
                w = ef.min_volatility()
            elif class_name == "gold":
                w = ef.min_volatility()  # Gold is a hedge: minimize vol
            else:
                # Equity: maximize Sharpe
                w = ef.max_sharpe(risk_free_rate=risk_free_rate)

            cleaned = ef.clean_weights(cutoff=0.05)
            cleaned = {k: float(v) for k, v in cleaned.items() if v > 0.01}
            total = sum(cleaned.values())
            if total == 0:
                # Fallback: equal weight
                w_eq = 1.0 / len(tickers_in_class)
                cleaned = {t: w_eq for t in tickers_in_class}
                total = 1.0
            weights = {k: v / total for k, v in cleaned.items()}

        except PFPOptError:
            # Fallback: equal weight within class
            w_eq = 1.0 / len(tickers_in_class)
            weights = {t: w_eq for t in tickers_in_class}
            logger.warning("optimization_fallback", class_name=class_name)

        result = []
        for t, w in weights.items():
            info = ticker_info.get(t, {"name": t, "asset_class": class_name})
            rets = sub_prices[t].pct_change().dropna().values
            result.append({
                "ticker": t,
                "name": info.get("name", t),
                "asset_class": class_name,
                "weight": round(w, 4),
                "expected_return": round(float(annualized_return(rets)), 4),
                "volatility": round(float(np.std(rets) * np.sqrt(252)), 4),
            })
        return result

    equity_allocs = _optimize_class(class_tickers.get("equity", []), "equity")
    bond_allocs = _optimize_class(class_tickers.get("bond", []), "bond")
    gold_allocs = _optimize_class(class_tickers.get("gold", []), "gold")

    # ── Step 3: Scale sub-portfolios to class targets ────────────────────

    for a in equity_allocs:
        a["weight"] = round(a["weight"] * equity_target, 4)
    for a in bond_allocs:
        a["weight"] = round(a["weight"] * bond_target, 4)
    for a in gold_allocs:
        a["weight"] = round(a["weight"] * gold_target, 4)

    all_allocated = equity_allocs + bond_allocs + gold_allocs

    # Remove near-zero allocations
    all_allocated = [a for a in all_allocated if a["weight"] > 0.005]

    # ── Step 4: Compute portfolio-level metrics ──────────────────────────
    tickers = [a["ticker"] for a in all_allocated]
    weights_arr = np.array([a["weight"] for a in all_allocated])

    # Normalize (in case of rounding)
    total_w = weights_arr.sum()
    if total_w > 0 and abs(total_w - 1.0) > 0.001:
        weights_arr = weights_arr / total_w
        for i, a in enumerate(all_allocated):
            a["weight"] = round(float(weights_arr[i]), 4)

    ann_returns = np.array([
        annualized_return(prices[t].pct_change().dropna().values)
        for t in tickers
    ])
    daily_rets = prices[tickers].pct_change().dropna()
    cov = daily_rets.cov().values

    port_return = portfolio_expected_return(weights_arr, ann_returns)
    port_vol = portfolio_volatility(weights_arr, cov)
    port_sharpe = sharpe_ratio(port_return, port_vol, risk_free_rate)

    # Historical max drawdown
    port_daily = (daily_rets @ weights_arr).values
    port_cum = np.cumprod(1 + port_daily)
    port_mdd = calc_max_drawdown(port_cum)

    # Add cash allocation as placeholder
    if cash_target > 0.01:
        all_allocated.append({
            "ticker": "CASH",
            "name": "现金/货币基金",
            "asset_class": "cash",
            "weight": round(float(cash_target), 4),
            "expected_return": round(risk_free_rate, 4),
            "volatility": 0.001,
        })

    # Determine optimization method label
    method_labels = {
        "conservative": "风险优先 (最小波动)",
        "moderate": "稳健优先 (最小波动 + 收益)",
        "balanced": "平衡配置 (风险平价)",
        "growth": "增长优先 (最大夏普)",
        "aggressive": "进取优先 (最大夏普 + 高权益)",
    }

    logger.info(
        "optimization_complete",
        risk_level=risk_level,
        equity_target=f"{equity_target:.1%}",
        bond_target=f"{bond_target:.1%}",
        num_assets=len(all_allocated),
        expected_return=f"{port_return:.4f}",
        sharpe=f"{port_sharpe:.2f}",
    )

    return {
        "allocations": all_allocated,
        "expected_return": round(port_return, 4),
        "volatility": round(port_vol, 4),
        "sharpe_ratio": round(port_sharpe, 4),
        "max_drawdown": round(port_mdd, 4),
        "optimization_method": method_labels.get(risk_level, "优化组合"),
    }
