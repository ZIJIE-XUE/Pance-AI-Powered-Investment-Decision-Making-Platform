"""Financial metrics calculation engine.

Pure functions for computing expected return, volatility,
Sharpe ratio, and maximum drawdown.
"""

import numpy as np
from config.settings import settings


def annualized_return(daily_returns: np.ndarray, trading_days: int = 252) -> float:
    """Calculate annualized expected return from daily returns.

    Args:
        daily_returns: Array of daily returns.
        trading_days: Number of trading days per year (default 252).

    Returns:
        Annualized return as a decimal (e.g., 0.08 = 8%).
    """
    if len(daily_returns) == 0:
        return 0.0
    avg_daily = float(np.mean(daily_returns))
    return float(avg_daily * trading_days)


def annualized_volatility(daily_returns: np.ndarray, trading_days: int = 252) -> float:
    """Calculate annualized volatility (standard deviation).

    Args:
        daily_returns: Array of daily returns.
        trading_days: Number of trading days per year (default 252).

    Returns:
        Annualized volatility as a decimal.
    """
    if len(daily_returns) < 2:
        return 0.0
    daily_std = float(np.std(daily_returns, ddof=1))
    return float(daily_std * np.sqrt(trading_days))


def sharpe_ratio(
    returns: np.ndarray | float,
    volatility: float,
    risk_free_rate: float | None = None,
) -> float:
    """Calculate the Sharpe ratio.

    Args:
        returns: Annualized expected return or daily returns array.
        volatility: Annualized volatility.
        risk_free_rate: Risk-free rate (default from settings).

    Returns:
        Sharpe ratio.
    """
    if risk_free_rate is None:
        risk_free_rate = settings.DEFAULT_RISK_FREE_RATE

    if volatility == 0:
        return 0.0

    if isinstance(returns, np.ndarray):
        ann_return = annualized_return(returns)
    else:
        ann_return = returns

    return float((ann_return - risk_free_rate) / volatility)


def max_drawdown(cumulative_returns: np.ndarray) -> float:
    """Calculate the maximum drawdown from a cumulative return series.

    Maximum drawdown is the largest peak-to-trough decline.

    Args:
        cumulative_returns: Array of cumulative returns (1 + cumulative).

    Returns:
        Maximum drawdown as a positive decimal (e.g., 0.25 = 25% drawdown).
    """
    if len(cumulative_returns) < 2:
        return 0.0

    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = (running_max - cumulative_returns) / running_max
    return float(np.max(drawdowns))


def portfolio_expected_return(
    weights: np.ndarray, asset_returns: np.ndarray
) -> float:
    """Calculate portfolio expected return from weights and individual returns.

    Args:
        weights: Array of asset weights (sum to 1).
        asset_returns: Array of annualized expected returns per asset.

    Returns:
        Portfolio expected return.
    """
    return float(np.dot(weights, asset_returns))


def portfolio_volatility(
    weights: np.ndarray, cov_matrix: np.ndarray
) -> float:
    """Calculate portfolio volatility from weights and covariance matrix.

    Args:
        weights: Array of asset weights.
        cov_matrix: Covariance matrix of asset returns.

    Returns:
        Portfolio volatility.
    """
    var = weights.T @ cov_matrix @ weights
    return float(np.sqrt(var))
