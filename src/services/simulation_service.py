"""Monte Carlo simulation service.

Orchestrates simulation execution, result persistence, and caching.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProjectionPath, Simulation as SimulationORM
from src.db.repository import SimulationRepository
from src.engine.monte_carlo import run_simulation_for_portfolio
from src.models.simulation import MonteCarloRequest, SimulationResult
from src.services.cache_service import cache_service
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MonteCarloService:
    """Service for Monte Carlo simulation management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SimulationRepository(session)

    async def run(self, request: MonteCarloRequest) -> SimulationResult:
        """Run a Monte Carlo simulation for a portfolio.

        Args:
            request: Simulation parameters (portfolio_id, horizon, amount, etc.).

        Returns:
            SimulationResult with distribution statistics and projection paths.
        """
        # Get portfolio data for simulation parameters
        from src.db.models import Portfolio as PortfolioORM
        from sqlalchemy import select

        result = await self.session.execute(
            select(PortfolioORM).where(PortfolioORM.id == request.portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if portfolio is None:
            from src.utils.exceptions import SimulationError
            raise SimulationError(f"投资组合未找到: {request.portfolio_id}")

        # Check cache
        cache_key = (
            f"monte_carlo:{request.portfolio_id}:"
            f"{request.horizon_years}:{int(request.initial_amount)}"
        )
        cached = cache_service.get(cache_key)
        if cached is not None:
            logger.info(
                "simulation_cache_hit",
                portfolio_id=str(request.portfolio_id),
                horizon=request.horizon_years,
            )
            return SimulationResult(
                user_id=request.user_id,
                portfolio_id=request.portfolio_id,
                **cached,
            )

        # Run simulation
        simulation_result = run_simulation_for_portfolio(
            initial_amount=request.initial_amount,
            portfolio_expected_return=portfolio.expected_return,
            portfolio_volatility=portfolio.volatility,
            horizon_years=request.horizon_years,
            num_paths=request.num_paths,
        )

        # Set IDs
        simulation_result.user_id = request.user_id
        simulation_result.portfolio_id = request.portfolio_id

        # Persist simulation summary
        simulation = SimulationORM(
            user_id=request.user_id,
            portfolio_id=request.portfolio_id,
            initial_amount=request.initial_amount,
            horizon_years=request.horizon_years,
            num_paths=request.num_paths,
            median_final_value=simulation_result.median_final_value,
            percentile_5=simulation_result.percentile_5,
            percentile_95=simulation_result.percentile_95,
            var_95=simulation_result.var_95,
            cvar_95=simulation_result.cvar_95,
            probability_positive=simulation_result.probability_positive,
        )
        simulation = await self.repo.create(simulation)
        simulation_result.id = simulation.id

        # Persist projection paths
        for proj in simulation_result.yearly_projections:
            path = ProjectionPath(
                simulation_id=simulation.id,
                year=proj.year,
                percentile_10=proj.percentile_10,
                percentile_25=proj.percentile_25,
                percentile_50=proj.percentile_50,
                percentile_75=proj.percentile_75,
                percentile_90=proj.percentile_90,
            )
            self.session.add(path)

        await self.session.flush()

        # Cache the result (without large arrays)
        cache_data = {
            "initial_amount": simulation_result.initial_amount,
            "horizon_years": simulation_result.horizon_years,
            "num_paths": simulation_result.num_paths,
            "median_final_value": simulation_result.median_final_value,
            "percentile_5": simulation_result.percentile_5,
            "percentile_95": simulation_result.percentile_95,
            "var_95": simulation_result.var_95,
            "cvar_95": simulation_result.cvar_95,
            "probability_positive": simulation_result.probability_positive,
            "yearly_projections": [
                {
                    "year": p.year,
                    "percentile_10": p.percentile_10,
                    "percentile_25": p.percentile_25,
                    "percentile_50": p.percentile_50,
                    "percentile_75": p.percentile_75,
                    "percentile_90": p.percentile_90,
                }
                for p in simulation_result.yearly_projections
            ],
        }
        cache_service.set(cache_key, cache_data, ttl_seconds=3600)

        logger.info(
            "simulation_persisted",
            simulation_id=str(simulation.id),
            horizon=request.horizon_years,
        )

        return simulation_result

    async def get_user_simulations(
        self, user_id: UUID, limit: int = 10
    ) -> list[SimulationResult]:
        """Get historical simulations for a user."""
        simulations = await self.repo.get_by_user(user_id, limit=limit)

        results = []
        for s in simulations:
            projections = [
                {
                    "year": p.year,
                    "percentile_10": p.percentile_10,
                    "percentile_25": p.percentile_25,
                    "percentile_50": p.percentile_50,
                    "percentile_75": p.percentile_75,
                    "percentile_90": p.percentile_90,
                }
                for p in s.projection_paths
            ]

            results.append(
                SimulationResult(
                    id=s.id,
                    user_id=s.user_id,
                    portfolio_id=s.portfolio_id,
                    initial_amount=s.initial_amount,
                    horizon_years=s.horizon_years,
                    num_paths=s.num_paths,
                    median_final_value=s.median_final_value,
                    percentile_5=s.percentile_5,
                    percentile_95=s.percentile_95,
                    var_95=s.var_95,
                    cvar_95=s.cvar_95,
                    probability_positive=s.probability_positive,
                    yearly_projections=projections,
                    created_at=s.created_at,
                )
            )

        return results
