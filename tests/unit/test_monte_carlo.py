"""Unit tests for Monte Carlo simulation engine."""

import pytest
from src.engine.monte_carlo import run_simulation, run_simulation_for_portfolio
from src.utils.exceptions import SimulationError


class TestRunSimulation:
    def test_basic_run(self):
        """Should complete successfully with valid parameters."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=5,
            num_paths=1_000,
        )
        assert result is not None
        assert result.initial_amount == 100_000
        assert result.horizon_years == 5
        assert result.num_paths == 1_000
        assert result.median_final_value > 0
        assert result.percentile_5 > 0
        assert result.percentile_95 > 0
        assert 0.0 <= result.probability_positive <= 1.0

    def test_yearly_projections_count(self):
        """Should return horizon_years + 1 yearly projections (including year 0)."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=10,
            num_paths=500,
        )
        assert len(result.yearly_projections) == 11  # years 0-10

    def test_projections_have_all_percentiles(self):
        """Each projection should have all 5 percentiles."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=5,
            num_paths=500,
        )
        for proj in result.yearly_projections:
            assert proj.percentile_10 is not None
            assert proj.percentile_50 is not None
            assert proj.percentile_90 is not None

    def test_year_zero_equals_initial(self):
        """Year 0 projection median should equal initial amount."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=5,
            num_paths=500,
        )
        assert result.yearly_projections[0].percentile_50 == pytest.approx(100_000)

    def test_negative_initial_raises_error(self):
        """Negative initial amount should raise SimulationError."""
        with pytest.raises(SimulationError):
            run_simulation(
                initial_amount=-1000,
                expected_return=0.08,
                volatility=0.15,
                horizon_years=5,
                num_paths=500,
            )

    def test_zero_horizon_raises_error(self):
        """Zero horizon should raise SimulationError."""
        with pytest.raises(SimulationError):
            run_simulation(
                initial_amount=100_000,
                expected_return=0.08,
                volatility=0.15,
                horizon_years=0,
                num_paths=500,
            )

    def test_negative_volatility_raises_error(self):
        """Negative volatility should raise SimulationError."""
        with pytest.raises(SimulationError):
            run_simulation(
                initial_amount=100_000,
                expected_return=0.08,
                volatility=-0.15,
                horizon_years=5,
                num_paths=500,
            )

    def test_sample_paths_returned(self):
        """Should return sample paths for visualization."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=5,
            num_paths=500,
        )
        assert result.sample_paths is not None
        assert len(result.sample_paths) > 0

    def test_final_values_returned(self):
        """Should return final values for histogram."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=5,
            num_paths=500,
        )
        assert result.final_values is not None
        assert len(result.final_values) > 0

    def test_var_and_cvar_computed(self):
        """VaR and CVaR should be computed."""
        result = run_simulation(
            initial_amount=100_000,
            expected_return=0.08,
            volatility=0.15,
            horizon_years=5,
            num_paths=500,
        )
        assert result.var_95 is not None
        assert result.cvar_95 is not None

    def test_convenience_wrapper(self):
        """The convenience wrapper should work."""
        result = run_simulation_for_portfolio(
            initial_amount=500_000,
            portfolio_expected_return=0.10,
            portfolio_volatility=0.12,
            horizon_years=20,
            num_paths=1_000,
        )
        assert result.horizon_years == 20
        assert result.initial_amount == 500_000

    def test_higher_return_gives_higher_median(self):
        """Higher expected return should lead to higher median final value."""
        result_low = run_simulation(
            initial_amount=100_000,
            expected_return=0.03,
            volatility=0.10,
            horizon_years=10,
            num_paths=500,
        )
        result_high = run_simulation(
            initial_amount=100_000,
            expected_return=0.10,
            volatility=0.10,
            horizon_years=10,
            num_paths=500,
        )
        assert result_high.median_final_value > result_low.median_final_value
