"""Portfolio optimization Pydantic models."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AssetInfo(BaseModel):
    """Information about an asset in the investment universe."""

    ticker: str
    name: str
    asset_class: str  # equity, bond, gold, real_estate


class AssetAllocation(BaseModel):
    """A single asset allocation within a portfolio."""

    ticker: str
    name: str
    asset_class: str
    weight: float = Field(..., ge=0, le=1)
    expected_return: float
    volatility: float


class PortfolioConstraints(BaseModel):
    """Optional constraints for portfolio optimization."""

    excluded_tickers: list[str] = Field(default_factory=list)
    min_weights: dict[str, float] = Field(default_factory=dict)
    max_weights: dict[str, float] = Field(default_factory=dict)


class PortfolioOptimizationRequest(BaseModel):
    """Request to generate an optimized portfolio."""

    user_id: UUID
    risk_profile_id: UUID
    risk_level: str
    constraints: PortfolioConstraints | None = None
    preferred_markets: str | None = None  # "A股,港股,美股" — comma-separated market labels


class PortfolioResult(BaseModel):
    """Optimized portfolio result."""

    id: UUID | None = None
    user_id: UUID
    risk_assessment_id: UUID | None = None
    risk_level: str
    optimization_method: str
    allocations: list[AssetAllocation]
    expected_return: float = Field(..., description="Annualized expected return")
    volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown estimate")
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
