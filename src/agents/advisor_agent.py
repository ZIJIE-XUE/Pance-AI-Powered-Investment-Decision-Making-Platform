"""AI Advisor Agent.

Generates professional investment analysis using a local rule-based engine.
No external API calls required — works completely offline.
"""

from src.agents.base_agent import BaseAgent
from src.engine.local_advisor_engine import generate_advisor_response
from src.models.advisor import AdvisorContext, AdvisorResponse, RiskItem, ScenarioItem
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AdvisorAgent(BaseAgent):
    """AI agent that explains portfolio allocation and provides investment advice.

    Uses a local rule-based engine to generate:
    - Portfolio summary and allocation rationale
    - Key risk analysis with severity and mitigation
    - Bull/bear/sideways market scenario analysis
    - Actionable investment recommendations
    - Risk disclaimer

    No external API key required — works entirely offline.
    """

    async def run(self, context: AdvisorContext) -> AdvisorResponse:
        """Generate AI-powered investment analysis using local engine.

        Args:
            context: AdvisorContext with portfolio data, simulation results,
                     and user preferences.

        Returns:
            AdvisorResponse with structured analysis.
        """
        logger.info(
            "advisor_agent_starting",
            risk_level=context.risk_level_label,
        )

        try:
            response = generate_advisor_response(context)
            logger.info("advisor_agent_complete", risk_level=context.risk_level_label)
            return response
        except Exception as e:
            logger.error("advisor_agent_failed", error=str(e))
            # Return a minimal fallback response instead of raising
            return AdvisorResponse(
                summary=f"根据您的{context.risk_level_label}风险等级，投资组合预期年化收益为{context.expected_return_pct}%，"
                       f"年化波动率为{context.volatility_pct}%。",
                allocation_rationale="该配置基于现代投资组合理论，根据您的风险承受能力在股票、债券、黄金等资产类别之间进行了分散化配置。",
                key_risks=[
                    RiskItem(
                        risk_name="市场风险",
                        severity="medium",
                        description="投资组合价值会随市场波动而变化。",
                        mitigation="保持长期投资视角，定期再平衡。",
                    )
                ],
                market_scenarios=[
                    ScenarioItem(
                        scenario="牛市",
                        probability="中低",
                        description="经济向好时组合有望获得较好收益。",
                        projected_impact="权益类资产表现强劲。",
                    ),
                    ScenarioItem(
                        scenario="熊市",
                        probability="中低",
                        description="市场下行时组合会承受一定损失。",
                        projected_impact="债券和黄金提供下行缓冲。",
                    ),
                    ScenarioItem(
                        scenario="震荡市",
                        probability="高",
                        description="市场横盘时依靠利息和股息获取收益。",
                        projected_impact="再平衡纪律是关键。",
                    ),
                ],
                investment_recommendations="保持定投纪律，定期再平衡，长期持有。",
                disclaimer_note="投资有风险，过往表现不代表未来收益。本分析仅供参考，不构成投资建议。",
            )
