"""Portfolio optimization service.

Orchestrates data fetching, optimization, metric calculation, and persistence.
"""

import hashlib
import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AssetAllocation, Portfolio as PortfolioORM
from src.db.repository import PortfolioRepository
from src.engine.optimizer import (
    fetch_historical_prices,
    get_asset_universe,
    optimize_portfolio,
)
from src.models.portfolio import (
    AssetAllocation as AssetAllocationModel,
    PortfolioConstraints,
    PortfolioOptimizationRequest,
    PortfolioResult,
)
from src.models.risk import RiskLevel
from src.services.cache_service import cache_service
from src.utils.exceptions import PortfolioOptimizationError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PortfolioOptimizationService:
    """Service for portfolio optimization and management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PortfolioRepository(session)

    def _cache_key(self, risk_level: str, constraints_hash: str) -> str:
        """Generate a cache key for optimization results."""
        return f"portfolio_opt:{risk_level}:{constraints_hash}"

    @staticmethod
    def _hash_constraints(constraints: PortfolioConstraints | None) -> str:
        """Generate a deterministic hash of portfolio constraints."""
        if constraints is None:
            return "default"
        data = json.dumps(
            {
                "excluded": sorted(constraints.excluded_tickers),
                "min_w": dict(sorted(constraints.min_weights.items())),
                "max_w": dict(sorted(constraints.max_weights.items())),
            },
            sort_keys=True,
        )
        return hashlib.md5(data.encode()).hexdigest()[:12]

    async def get_asset_universe(self) -> list[dict]:
        """Get the full investment asset universe."""
        return get_asset_universe()

    async def optimize(
        self,
        request: PortfolioOptimizationRequest,
    ) -> PortfolioResult:
        """Generate an optimized portfolio based on risk level.

        Args:
            request: Optimization request with user_id, risk_level, and optional constraints.

        Returns:
            PortfolioResult with allocations and performance metrics.

        Raises:
            PortfolioOptimizationError: If optimization fails or data is insufficient.
        """
        risk_level = request.risk_level
        constraints = request.constraints

        # Check cache for optimization computation (but always create a new DB record)
        constraints_hash = self._hash_constraints(constraints)
        cache_key = self._cache_key(risk_level, constraints_hash)
        cached_opt = cache_service.get(cache_key)

        # Get asset universe
        asset_universe = get_asset_universe()

        # ── Market filter: only filter equity assets by user's preferred markets ──
        if request.preferred_markets:
            selected_markets = [m.strip() for m in request.preferred_markets.split(",") if m.strip()]
            region_map = {"A股": "china_a", "港股": "hk", "美股": "us", "韩国": "korea"}
            allowed_regions = {region_map[m] for m in selected_markets if m in region_map}

            if allowed_regions:
                asset_universe = [
                    a for a in asset_universe
                    if a["asset_class"] != "equity"  # Keep all non-equity assets
                    or a.get("region", "") in allowed_regions  # Filter equity by region
                ]
                logger.info(
                    "market_filter", markets=selected_markets,
                    equity_assets=[a["ticker"] for a in asset_universe if a["asset_class"] == "equity"],
                )

        tickers = [a["ticker"] for a in asset_universe]

        # Exclude tickers if specified
        if constraints and constraints.excluded_tickers:
            tickers = [t for t in tickers if t not in constraints.excluded_tickers]
            asset_universe = [a for a in asset_universe if a["ticker"] in tickers]

        if len(tickers) < 3:
            raise PortfolioOptimizationError(
                "可用资产数量不足，至少需要3个资产进行优化"
            )

        # Use cached optimization result if available, otherwise compute fresh
        if cached_opt is not None:
            logger.info("portfolio_cache_hit", risk_level=risk_level)
            opt_result = cached_opt
        else:
            # Fetch historical prices
            logger.info("fetching_historical_prices", tickers=tickers)
            try:
                prices = fetch_historical_prices(tickers, asset_info=asset_universe)
            except Exception as e:
                raise PortfolioOptimizationError(str(e))

            if prices.empty or len(prices.columns) < 3:
                raise PortfolioOptimizationError("无法获取足够的历史价格数据")

            # Run optimization
            opt_result = optimize_portfolio(
                prices,
                risk_level,
                asset_universe,
            )

        # Persist to database
        portfolio = PortfolioORM(
            user_id=request.user_id,
            risk_assessment_id=request.risk_profile_id,
            risk_level=risk_level,
            optimization_method=opt_result["optimization_method"],
            expected_return=opt_result["expected_return"],
            volatility=opt_result["volatility"],
            sharpe_ratio=opt_result["sharpe_ratio"],
            max_drawdown=opt_result["max_drawdown"],
            constraints_json=(
                {
                    "excluded": constraints.excluded_tickers,
                    "min_weights": constraints.min_weights,
                    "max_weights": constraints.max_weights,
                }
                if constraints
                else None
            ),
        )
        portfolio = await self.repo.create(portfolio)

        # Persist allocations
        for alloc in opt_result["allocations"]:
            asset_alloc = AssetAllocation(
                portfolio_id=portfolio.id,
                ticker=alloc["ticker"],
                asset_name=alloc["name"],
                asset_class=alloc["asset_class"],
                weight=alloc["weight"],
                expected_return=alloc["expected_return"],
                volatility=alloc["volatility"],
            )
            self.session.add(asset_alloc)

        await self.session.flush()

        # Cache the result
        cache_service.set(cache_key, {
            "optimization_method": opt_result["optimization_method"],
            "allocations": opt_result["allocations"],
            "expected_return": opt_result["expected_return"],
            "volatility": opt_result["volatility"],
            "sharpe_ratio": opt_result["sharpe_ratio"],
            "max_drawdown": opt_result["max_drawdown"],
        }, ttl_seconds=3600)

        logger.info(
            "portfolio_optimization_complete",
            risk_level=risk_level,
            num_assets=len(opt_result["allocations"]),
            expected_return=opt_result["expected_return"],
        )

        return PortfolioResult(
            id=portfolio.id,
            user_id=portfolio.user_id,
            risk_assessment_id=portfolio.risk_assessment_id,
            risk_level=risk_level,
            optimization_method=opt_result["optimization_method"],
            allocations=[
                AssetAllocationModel(**a) for a in opt_result["allocations"]
            ],
            expected_return=opt_result["expected_return"],
            volatility=opt_result["volatility"],
            sharpe_ratio=opt_result["sharpe_ratio"],
            max_drawdown=opt_result["max_drawdown"],
            created_at=portfolio.created_at,
        )

    async def get_user_portfolios(
        self, user_id: UUID, limit: int = 10
    ) -> list[PortfolioResult]:
        """Get historical portfolios for a user."""
        portfolios = await self.repo.get_by_user(user_id, limit=limit)

        results = []
        for p in portfolios:
            allocations = [
                AssetAllocationModel(
                    ticker=a.ticker,
                    name=a.asset_name,
                    asset_class=a.asset_class,
                    weight=a.weight,
                    expected_return=a.expected_return,
                    volatility=a.volatility,
                )
                for a in p.allocations
            ]

            results.append(
                PortfolioResult(
                    id=p.id,
                    user_id=p.user_id,
                    risk_assessment_id=p.risk_assessment_id,
                    risk_level=p.risk_level,
                    optimization_method=p.optimization_method,
                    allocations=allocations,
                    expected_return=p.expected_return,
                    volatility=p.volatility,
                    sharpe_ratio=p.sharpe_ratio,
                    max_drawdown=p.max_drawdown,
                    created_at=p.created_at,
                )
            )

        return results
