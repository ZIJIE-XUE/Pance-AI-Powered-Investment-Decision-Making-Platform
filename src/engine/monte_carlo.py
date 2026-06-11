"""Monte Carlo simulation engine.

Geometric Brownian Motion (GBM) based portfolio projection,
VaR, CVaR, and distribution statistics.
"""

import numpy as np
from numpy.random import default_rng

from config.settings import settings
from src.models.simulation import ProjectionPercentile, SimulationResult
from src.utils.exceptions import SimulationError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_simulation(
    initial_amount: float,
    expected_return: float,
    volatility: float,
    horizon_years: int,
    num_paths: int = 10_000,
    risk_free_rate: float | None = None,
) -> SimulationResult:
    """Run a Monte Carlo simulation using Geometric Brownian Motion.

    GBM model: dS = μ * S * dt + σ * S * dW
    Where:
        S = portfolio value
        μ = expected annual return (drift)
        σ = annual volatility
        dW = Wiener process (random shock)

    Args:
        initial_amount: Initial portfolio value.
        expected_return: Annualized expected return.
        volatility: Annualized volatility.
        horizon_years: Number of years to simulate.
        num_paths: Number of simulation paths.
        risk_free_rate: Risk-free rate for VaR/CVaR calculation.

    Returns:
        SimulationResult with distribution statistics and projection paths.

    Raises:
        SimulationError: If parameters are invalid.
    """
    if initial_amount <= 0:
        raise SimulationError("初始投资金额必须大于0")
    if horizon_years <= 0 or horizon_years > 50:
        raise SimulationError("投资期限必须在1-50年之间")
    if volatility < 0:
        raise SimulationError("波动率不能为负数")
    if num_paths < 100:
        raise SimulationError("模拟路径数至少为100")

    if risk_free_rate is None:
        risk_free_rate = settings.DEFAULT_RISK_FREE_RATE

    # Parameters
    dt = 1.0 / 252  # Daily time step (252 trading days)
    total_steps = horizon_years * 252
    annual_steps = np.arange(0, horizon_years + 1) * 252  # Index for yearly snapshots

    # GBM parameters (daily)
    mu_daily = expected_return / 252 - 0.5 * (volatility ** 2) / 252
    sigma_daily = volatility / np.sqrt(252)

    # Initialize random number generator
    rng = default_rng()

    # Generate random walks for all paths at once (more memory but faster)
    # Using log-return approach for numerical stability
    random_shocks = rng.normal(
        loc=mu_daily,
        scale=sigma_daily,
        size=(num_paths, total_steps),
    )

    # Compute log returns and accumulate
    # log(S_t) = log(S_0) + sum(log_returns)
    log_returns = random_shocks
    log_paths = np.log(initial_amount) + np.cumsum(log_returns, axis=1)

    # Insert initial value at t=0
    log_paths = np.hstack([np.log(initial_amount) * np.ones((num_paths, 1)), log_paths])

    # Extract yearly values
    yearly_indices = np.arange(0, total_steps + 1, 252)  # Every 252 trading days
    # Ensure we include the final step
    if yearly_indices[-1] != total_steps:
        yearly_indices = np.append(yearly_indices, total_steps)

    # Adjust to match horizon_years + 1 points
    yearly_indices = yearly_indices[: horizon_years + 1]
    if len(yearly_indices) < horizon_years + 1:
        yearly_indices = np.linspace(0, total_steps, horizon_years + 1, dtype=int)

    yearly_log_paths = log_paths[:, yearly_indices]
    yearly_paths = np.exp(yearly_log_paths)

    # Final values distribution
    final_values = yearly_paths[:, -1]
    final_returns = (final_values / initial_amount) - 1

    # Compute percentiles
    sorted_final = np.sort(final_values)

    median_final = float(np.percentile(sorted_final, 50))
    p5 = float(np.percentile(sorted_final, 5))
    p95 = float(np.percentile(sorted_final, 95))

    # VaR 95% - the loss at the 5th percentile (relative to initial)
    var_95 = float(initial_amount * (1 + risk_free_rate) ** horizon_years - p5)

    # CVaR 95% - expected loss beyond VaR
    tail_losses = sorted_final[sorted_final <= p5]
    if len(tail_losses) > 0:
        cvar_95 = float(
            initial_amount * (1 + risk_free_rate) ** horizon_years
            - np.mean(tail_losses)
        )
    else:
        cvar_95 = var_95

    # Probability of positive return
    prob_positive = float(np.mean(final_values > initial_amount))

    # Yearly percentile projections
    yearly_projections = []
    for year_idx in range(yearly_paths.shape[1]):
        year_values = yearly_paths[:, year_idx]
        year_num = year_idx  # year 0, 1, 2, ..., horizon_years

        yearly_projections.append(
            ProjectionPercentile(
                year=year_num,
                percentile_10=float(np.percentile(year_values, 10)),
                percentile_25=float(np.percentile(year_values, 25)),
                percentile_50=float(np.percentile(year_values, 50)),
                percentile_75=float(np.percentile(year_values, 75)),
                percentile_90=float(np.percentile(year_values, 90)),
            )
        )

    # Sample paths for visualization (max 100 paths to keep data manageable)
    sample_size = min(100, num_paths)
    sample_indices = np.linspace(0, num_paths - 1, sample_size, dtype=int)
    sample_paths = yearly_paths[sample_indices].tolist()

    # Downsample final values for histogram (max 10000 points)
    if len(final_values) > 10_000:
        hist_indices = np.linspace(0, len(final_values) - 1, 10_000, dtype=int)
        hist_values = final_values[hist_indices].tolist()
    else:
        hist_values = final_values.tolist()

    logger.info(
        "simulation_complete",
        num_paths=num_paths,
        horizon=horizon_years,
        median_final=round(median_final, 2),
        p5=round(p5, 2),
        p95=round(p95, 2),
        prob_positive=round(prob_positive, 4),
    )

    return SimulationResult(
        initial_amount=initial_amount,
        horizon_years=horizon_years,
        num_paths=num_paths,
        median_final_value=round(median_final, 2),
        percentile_5=round(p5, 2),
        percentile_95=round(p95, 2),
        var_95=round(var_95, 2),
        cvar_95=round(cvar_95, 2),
        probability_positive=round(prob_positive, 4),
        yearly_projections=yearly_projections,
        final_values=hist_values,
        sample_paths=sample_paths,
    )


def run_simulation_for_portfolio(
    initial_amount: float,
    portfolio_expected_return: float,
    portfolio_volatility: float,
    horizon_years: int,
    num_paths: int = 10_000,
) -> SimulationResult:
    """Convenience wrapper for running simulation with portfolio-level parameters.

    This is the primary entry point used by the simulation service.
    """
    return run_simulation(
        initial_amount=initial_amount,
        expected_return=portfolio_expected_return,
        volatility=portfolio_volatility,
        horizon_years=horizon_years,
        num_paths=num_paths,
    )
