"""AI Advisor response Pydantic models."""

from pydantic import BaseModel, Field


class RiskItem(BaseModel):
    """A single risk identified by the AI advisor."""

    risk_name: str
    severity: str  # high, medium, low
    description: str
    mitigation: str


class ScenarioItem(BaseModel):
    """A market scenario analysis."""

    scenario: str  # 牛市, 熊市, 震荡市
    probability: str
    description: str
    projected_impact: str


class AdvisorResponse(BaseModel):
    """Structured response from the AI advisor agent."""

    summary: str = Field(..., description="投资组合概述")
    allocation_rationale: str = Field(..., description="配置理由")
    key_risks: list[RiskItem] = Field(default_factory=list, description="主要风险")
    market_scenarios: list[ScenarioItem] = Field(
        default_factory=list, description="市场情景分析"
    )
    investment_recommendations: str = Field(..., description="投资建议")
    disclaimer_note: str = Field(..., description="风险提示")


class AdvisorContext(BaseModel):
    """Context data passed to the AI advisor agent."""

    risk_level: str
    risk_level_label: str
    risk_score_pct: str
    investment_goal: str
    allocations: list[dict]
    expected_return_pct: str
    volatility_pct: str
    sharpe_ratio: str
    max_drawdown_pct: str
    horizon_years: int
    initial_amount: str
    median_final: str
    percentile_5: str
    percentile_95: str
    var_95: str
    probability_positive_pct: str
    class_weights: dict[str, str]
