"""DCA (Dollar Cost Averaging) Calculator Engine.

Two modes:
1. Forward: given monthly investment → project future value
2. Reverse: given target amount → calculate required monthly investment

Pure computation — no I/O, no external dependencies.
"""

import math


def _monthly_rate(annual_return: float) -> float:
    """Convert annual return to monthly rate."""
    return (1 + annual_return) ** (1 / 12) - 1


def calculate_dca_forward(
    monthly_amount: float,
    years: int,
    annual_return: float,
) -> dict:
    """Project future value of a monthly DCA plan.

    Args:
        monthly_amount: Fixed monthly investment (¥).
        years: Investment horizon in years.
        annual_return: Expected annualized return (e.g. 0.08 for 8%).

    Returns:
        Dict with yearly breakdown, totals, and summary.
    """
    r = _monthly_rate(annual_return)
    total_months = years * 12

    yearly_data = []
    cumulative_principal = 0.0
    cumulative_value = 0.0

    for year in range(1, years + 1):
        year_principal = monthly_amount * 12
        cumulative_principal += year_principal

        # FV = PMT * ((1+r)^n - 1) / r  for months elapsed so far
        months_elapsed = year * 12
        if r == 0:
            cumulative_value = cumulative_principal
        else:
            cumulative_value = monthly_amount * ((1 + r) ** months_elapsed - 1) / r

        year_earnings = cumulative_value - cumulative_principal

        yearly_data.append({
            "year": year,
            "year_principal": round(year_principal, 2),
            "cumulative_principal": round(cumulative_principal, 2),
            "year_earnings": round(year_earnings, 2),
            "cumulative_value": round(cumulative_value, 2),
        })

    total_invested = monthly_amount * total_months
    final_value = yearly_data[-1]["cumulative_value"] if yearly_data else 0
    total_earnings = final_value - total_invested

    return {
        "mode": "forward",
        "monthly_amount": monthly_amount,
        "years": years,
        "annual_return": annual_return,
        "total_invested": round(total_invested, 2),
        "total_earnings": round(total_earnings, 2),
        "final_value": round(final_value, 2),
        "earnings_ratio": round(total_earnings / total_invested * 100, 1) if total_invested > 0 else 0,
        "yearly_data": yearly_data,
    }


def calculate_dca_reverse(
    target_amount: float,
    years: int,
    annual_return: float,
) -> dict:
    """Calculate required monthly investment to reach a target amount.

    Solves: FV = PMT * ((1+r)^n - 1) / r  →  PMT = FV * r / ((1+r)^n - 1)

    Args:
        target_amount: Target future value (¥).
        years: Investment horizon in years.
        annual_return: Expected annualized return (e.g. 0.08 for 8%).

    Returns:
        Dict with required monthly amount and forward projection.
    """
    r = _monthly_rate(annual_return)
    total_months = years * 12

    if r == 0:
        monthly_needed = target_amount / total_months
    else:
        monthly_needed = target_amount * r / ((1 + r) ** total_months - 1)

    monthly_needed = math.ceil(monthly_needed * 100) / 100  # Round up to cents

    # Also run the forward projection with the calculated amount
    forward = calculate_dca_forward(monthly_needed, years, annual_return)

    return {
        "mode": "reverse",
        "target_amount": target_amount,
        "years": years,
        "annual_return": annual_return,
        "monthly_needed": round(monthly_needed, 2),
        "total_invested": forward["total_invested"],
        "total_earnings": forward["total_earnings"],
        "final_value": forward["final_value"],
        "shortfall": round(target_amount - forward["final_value"], 2),
        "yearly_data": forward["yearly_data"],
    }
