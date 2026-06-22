"""AI Advisor Agent.

Generates professional investment analysis using a local rule-based engine.
No external API calls required — works completely offline.
"""

from src.agents.base_agent import BaseAgent
from src.engine.local_advisor_engine import generate_advisor_response
from src.ui.i18n import get_lang, t
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

    async def run(self, context: AdvisorContext, lang: str = "zh") -> AdvisorResponse:
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
            response = generate_advisor_response(context, lang=lang)
            logger.info("advisor_agent_complete", risk_level=context.risk_level_label)
            return response
        except Exception as e:
            logger.error("advisor_agent_failed", error=str(e))
            # Return a minimal fallback response instead of raising
            lang = get_lang()
            if lang == 'en':
                return AdvisorResponse(
                    summary=f"Based on your {t(context.risk_level_label)} risk profile, the portfolio has an expected annual return of {context.expected_return_pct}% with {context.volatility_pct}% annual volatility.",
                    allocation_rationale="This allocation is based on Modern Portfolio Theory, diversifying across equities, bonds, gold, and other asset classes according to your risk tolerance.",
                    key_risks=[
                        RiskItem(
                            risk_name="Market Risk",
                            severity="medium",
                            description="Portfolio value will fluctuate with market movements.",
                            mitigation="Maintain a long-term perspective and rebalance regularly.",
                        )
                    ],
                    market_scenarios=[
                        ScenarioItem(
                            scenario="Bull Market",
                            probability="Medium-Low",
                            description="Strong returns expected when the economy performs well.",
                            projected_impact="Equity assets perform strongly.",
                        ),
                        ScenarioItem(
                            scenario="Bear Market",
                            probability="Medium-Low",
                            description="Portfolio will incur some losses during market downturns.",
                            projected_impact="Bonds and gold provide downside buffer.",
                        ),
                        ScenarioItem(
                            scenario="Sideways Market",
                            probability="High",
                            description="Returns come from interest and dividends during flat markets.",
                            projected_impact="Rebalancing discipline is key.",
                        ),
                    ],
                    investment_recommendations="Maintain DCA discipline, rebalance regularly, hold for the long term.",
                    disclaimer_note="Investing involves risk. Past performance does not guarantee future results. This analysis is for reference only and does not constitute investment advice.",
                )
            else:
                return AdvisorResponse(
                    summary=f"根据您的{t(context.risk_level_label)}风险等级，投资组合预期年化收益为{context.expected_return_pct}%，"
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
