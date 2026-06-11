"""Monte Carlo simulation Pydantic models."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class MonteCarloRequest(BaseModel):
    """Request to run a Monte Carlo simulation."""

    user_id: UUID
    portfolio_id: UUID
    initial_amount: float = Field(..., gt=0)
    horizon_years: int = Field(..., description="5, 10, or 20 years")
    num_paths: int = Field(10_000, ge=100, le=1_000_000)


class ProjectionPercentile(BaseModel):
    """Portfolio value percentiles at a given year."""

    year: int
    percentile_10: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_90: float


class SimulationResult(BaseModel):
    """Complete Monte Carlo simulation result."""

    id: UUID | None = None
    user_id: UUID | None = None
    portfolio_id: UUID | None = None
    initial_amount: float
    horizon_years: int
    num_paths: int
    median_final_value: float = Field(..., description="50th percentile final value")
    percentile_5: float = Field(..., description="5th percentile (downside)")
    percentile_95: float = Field(..., description="95th percentile (upside)")
    var_95: float = Field(..., description="95% Value at Risk")
    cvar_95: float = Field(..., description="95% Conditional Value at Risk")
    probability_positive: float = Field(
        ..., ge=0, le=1, description="Probability of positive return"
    )
    yearly_projections: list[ProjectionPercentile] = Field(default_factory=list)
    # Raw data for charts (stored in-memory, not persisted)
    final_values: list[float] | None = Field(
        default=None, description="Distribution of final portfolio values"
    )
    sample_paths: list[list[float]] | None = Field(
        default=None, description="Sample of simulated paths for fan chart"
    )
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
