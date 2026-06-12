"""SQLAlchemy ORM models for the AI Robo Advisor.

Defines the database schema: users, risk_assessments, portfolios,
asset_allocations, simulations, projection_paths, reports, and cache_entries.
"""

import uuid as _uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, new_uuid, utcnow


class User(Base, TimestampMixin):
    """User profile table."""

    __tablename__ = "users"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    income: Mapped[float] = mapped_column(Float, nullable=False)
    asset_size: Mapped[float] = mapped_column(Float, nullable=False)
    investment_horizon: Mapped[int] = mapped_column(Integer, nullable=False)
    investment_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_markets: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Relationships
    risk_assessments = relationship("RiskAssessment", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    simulations = relationship("Simulation", back_populates="user")
    reports = relationship("Report", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class RiskAssessment(Base, TimestampMixin):
    """Risk assessment results table."""

    __tablename__ = "risk_assessments"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    questionnaire_version: Mapped[str] = mapped_column(
        String(16), nullable=False
    )
    answers_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_possible_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # conservative, moderate, balanced, growth, aggressive
    category_scores_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="risk_assessments")
    portfolios = relationship("Portfolio", back_populates="risk_assessment")

    def __repr__(self) -> str:
        return f"<RiskAssessment(id={self.id}, level={self.risk_level})>"


class Portfolio(Base, TimestampMixin):
    """Portfolio optimization results table."""

    __tablename__ = "portfolios"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    risk_assessment_id: Mapped[_uuid.UUID | None] = mapped_column(
        ForeignKey("risk_assessments.id"), nullable=True
    )
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    optimization_method: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_return: Mapped[float] = mapped_column(Float, nullable=False)
    volatility: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    constraints_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    risk_assessment = relationship("RiskAssessment", back_populates="portfolios")
    allocations = relationship(
        "AssetAllocation",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    simulations = relationship("Simulation", back_populates="portfolio")

    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, risk={self.risk_level})>"


class AssetAllocation(Base):
    """Individual asset allocations within a portfolio."""

    __tablename__ = "asset_allocations"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    portfolio_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_name: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return: Mapped[float] = mapped_column(Float, nullable=False)
    volatility: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="allocations")

    def __repr__(self) -> str:
        return f"<AssetAllocation(ticker={self.ticker}, weight={self.weight:.2%})>"


class Simulation(Base, TimestampMixin):
    """Monte Carlo simulation results table."""

    __tablename__ = "simulations"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    portfolio_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False
    )
    initial_amount: Mapped[float] = mapped_column(Float, nullable=False)
    horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)
    num_paths: Mapped[int] = mapped_column(Integer, nullable=False)
    median_final_value: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_5: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_95: Mapped[float] = mapped_column(Float, nullable=False)
    var_95: Mapped[float] = mapped_column(Float, nullable=False)
    cvar_95: Mapped[float] = mapped_column(Float, nullable=False)
    probability_positive: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    user = relationship("User", back_populates="simulations")
    portfolio = relationship("Portfolio", back_populates="simulations")
    projection_paths = relationship(
        "ProjectionPath",
        back_populates="simulation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Simulation(id={self.id}, horizon={self.horizon_years}y)>"


class ProjectionPath(Base):
    """Downsampled yearly percentile paths for a simulation."""

    __tablename__ = "projection_paths"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    simulation_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("simulations.id"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    percentile_10: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_25: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_50: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_75: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_90: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    simulation = relationship("Simulation", back_populates="projection_paths")


class Report(Base, TimestampMixin):
    """PDF report generation tracking table."""

    __tablename__ = "reports"

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    risk_assessment_id: Mapped[_uuid.UUID | None] = mapped_column(
        ForeignKey("risk_assessments.id"), nullable=True
    )
    portfolio_id: Mapped[_uuid.UUID | None] = mapped_column(
        ForeignKey("portfolios.id"), nullable=True
    )
    simulation_id: Mapped[_uuid.UUID | None] = mapped_column(
        ForeignKey("simulations.id"), nullable=True
    )
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="reports")


# Note: Indexes are defined inline on columns via index=True.
# Additional indexes can be added here if needed.
# Index("ix_reports_status", Report.status)
