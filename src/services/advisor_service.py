"""AI Advisor service.

Orchestrates context building, agent invocation, response caching,
and result validation.
"""

import hashlib
import json
from uuid import UUID

from src.agents.advisor_agent import AdvisorAgent
from src.models.advisor import AdvisorContext, AdvisorResponse
from src.services.cache_service import cache_service
from src.utils.exceptions import AdvisorError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AdvisorService:
    """Service for the AI-powered investment advisor."""

    def __init__(self):
        self.agent = AdvisorAgent()
        self._advice_cache_ttl = 86400  # 24 hours

    def _build_context(
        self, user: dict, risk_profile: dict, portfolio: dict, simulation: dict
    ) -> AdvisorContext:
        """Build the structured context for the AI advisor from session data."""

        # Format numbers for display
        allocations = []
        class_weights_map = {}
        for a in portfolio["allocations"]:
            allocations.append({
                "ticker": a["ticker"],
                "name": a["name"],
                "asset_class": a["asset_class"],
                "weight_pct": f"{a['weight'] * 100:.1f}",
                "return_pct": f"{a['expected_return'] * 100:.2f}",
                "vol_pct": f"{a['volatility'] * 100:.2f}",
            })
            cls = a["asset_class"]
            class_weights_map[cls] = class_weights_map.get(cls, 0) + a["weight"]

        class_labels = {
            "equity": "股票",
            "bond": "债券",
            "gold": "黄金",
            "real_estate": "房地产",
            "cash": "现金",
        }
        class_weights_display = {}
        for cls, weight in class_weights_map.items():
            label = class_labels.get(cls, cls)
            class_weights_display[label] = f"{weight * 100:.1f}"

        return AdvisorContext(
            risk_level=risk_profile["risk_level"],
            risk_level_label=risk_profile["risk_level_label"],
            risk_score_pct=f"{risk_profile['total_score'] * 100:.0f}",
            investment_goal=user.get("investment_goal", "未指定"),
            allocations=allocations,
            expected_return_pct=f"{portfolio['expected_return'] * 100:.2f}",
            volatility_pct=f"{portfolio['volatility'] * 100:.2f}",
            sharpe_ratio=f"{portfolio['sharpe_ratio']:.2f}",
            max_drawdown_pct=f"{portfolio['max_drawdown'] * 100:.2f}",
            horizon_years=simulation["horizon_years"],
            initial_amount=f"{simulation['initial_amount']:,.0f}",
            median_final=f"{simulation['median_final_value']:,.0f}",
            percentile_5=f"{simulation['percentile_5']:,.0f}",
            percentile_95=f"{simulation['percentile_95']:,.0f}",
            var_95=f"{simulation['var_95']:,.0f}",
            probability_positive_pct=f"{simulation['probability_positive'] * 100:.1f}",
            class_weights=class_weights_display,
        )

    def _cache_key(self, portfolio_id: str, simulation_id: str) -> str:
        """Generate a cache key for advisor responses."""
        combined = f"{portfolio_id}:{simulation_id}"
        hashed = hashlib.md5(combined.encode()).hexdigest()[:16]
        return f"advisor:{hashed}"

    async def get_explanation(
        self,
        user: dict,
        risk_profile: dict,
        portfolio: dict,
        simulation: dict,
    ) -> AdvisorResponse:
        """Generate AI investment analysis for the user's portfolio.

        Args:
            user: User info dict from session state.
            risk_profile: Risk assessment result dict.
            portfolio: Portfolio optimization result dict.
            simulation: Monte Carlo simulation result dict.

        Returns:
            AdvisorResponse with structured analysis.

        Raises:
            AdvisorError: If AI call fails.
        """
        # Check cache
        cache_key = self._cache_key(
            portfolio.get("id", ""),
            simulation.get("id", ""),
        )
        cached = cache_service.get(cache_key)
        if cached is not None:
            logger.info("advisor_cache_hit")
            try:
                return AdvisorResponse(**cached)
            except Exception:
                # Cache data may be stale, continue with fresh call
                pass

        # Build context
        context = self._build_context(user, risk_profile, portfolio, simulation)

        # Call agent
        response = await self.agent.run(context)

        # Cache response
        cache_service.set(
            cache_key,
            response.model_dump(),
            ttl_seconds=86400,  # 24h
        )

        return response
