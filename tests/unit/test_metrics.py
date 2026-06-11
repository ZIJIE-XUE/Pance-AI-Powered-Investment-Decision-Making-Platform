"""Unit tests for financial metrics calculations."""

import numpy as np
import pytest
from src.engine.metrics import (
    annualized_return,
    annualized_volatility,
    sharpe_ratio,
    max_drawdown,
    portfolio_expected_return,
    portfolio_volatility,
)


class TestAnnualizedReturn:
    def test_zero_returns(self):
        """Zero daily returns should give zero annualized return."""
        ret = annualized_return(np.array([0.0, 0.0, 0.0]))
        assert ret == pytest.approx(0.0)

    def test_positive_returns(self):
        """Positive daily returns should give positive annualized."""
        ret = annualized_return(np.array([0.001] * 252))
        assert ret > 0.0

    def test_empty_array(self):
        """Empty array should return 0."""
        ret = annualized_return(np.array([]))
        assert ret == 0.0


class TestAnnualizedVolatility:
    def test_constant_prices_no_volatility(self):
        """No change should give zero volatility."""
        vol = annualized_volatility(np.array([0.001, 0.001, 0.001]))
        assert vol == pytest.approx(0.0)

    def test_volatile_returns(self):
        """Variable returns should give positive volatility."""
        vol = annualized_volatility(np.array([0.01, -0.02, 0.015, -0.005, 0.03]))
        assert vol > 0.0


class TestSharpeRatio:
    def test_zero_volatility(self):
        """Zero volatility should give zero Sharpe."""
        sr = sharpe_ratio(0.05, 0.0)
        assert sr == 0.0

    def test_positive_sharpe(self):
        """Returns above risk-free should give positive Sharpe."""
        sr = sharpe_ratio(0.10, 0.15, risk_free_rate=0.03)
        assert sr > 0.0

    def test_negative_sharpe(self):
        """Returns below risk-free should give negative Sharpe."""
        sr = sharpe_ratio(0.02, 0.15, risk_free_rate=0.03)
        assert sr < 0.0


class TestMaxDrawdown:
    def test_increasing_values(self):
        """Continuously increasing should have zero drawdown."""
        cum = np.array([1.0, 1.1, 1.2, 1.3, 1.4])
        mdd = max_drawdown(cum)
        assert mdd == pytest.approx(0.0)

    def test_declining_values(self):
        """Declining values should have positive drawdown."""
        cum = np.array([1.0, 0.9, 0.8, 0.7, 0.75])
        mdd = max_drawdown(cum)
        assert mdd > 0.0

    def test_peak_to_trough(self):
        """Should capture the largest peak-to-trough decline."""
        cum = np.array([1.0, 1.2, 1.1, 0.8, 1.3])
        mdd = max_drawdown(cum)
        # Max drawdown = (1.2 - 0.8) / 1.2 = 0.3333
        assert mdd == pytest.approx(0.3333, abs=0.01)


class TestPortfolioMetrics:
    def test_expected_return(self):
        """Portfolio expected return should be weighted average."""
        weights = np.array([0.5, 0.3, 0.2])
        returns = np.array([0.10, 0.05, 0.02])
        port_ret = portfolio_expected_return(weights, returns)
        expected = 0.5 * 0.10 + 0.3 * 0.05 + 0.2 * 0.02
        assert port_ret == pytest.approx(expected)

    def test_volatility_from_covariance(self):
        """Should compute portfolio volatility from covariance."""
        weights = np.array([0.5, 0.5])
        cov = np.array([[0.04, 0.01], [0.01, 0.09]])
        vol = portfolio_volatility(weights, cov)
        assert vol > 0.0
