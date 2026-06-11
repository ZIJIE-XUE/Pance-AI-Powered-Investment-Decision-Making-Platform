"""Generic repository pattern for database CRUD operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic async repository for CRUD operations on a single entity type."""

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> T | None:
        """Get a single entity by its UUID primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[T]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        """Persist a new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Update an existing entity (must be tracked by session)."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete an entity by ID. Returns True if deleted."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == entity_id)
        )
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def find_by(
        self, **kwargs: Any
    ) -> list[T]:
        """Find entities by arbitrary column filters."""
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class UserRepository(BaseRepository["User"]):
    """Specialized repository for User entities."""

    def __init__(self, session: AsyncSession):
        from src.db.models import User

        super().__init__(User, session)

    async def get_by_email(self, email: str) -> "User | None":
        from src.db.models import User

        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


class RiskAssessmentRepository(BaseRepository["RiskAssessment"]):
    """Specialized repository for RiskAssessment entities."""

    def __init__(self, session: AsyncSession):
        from src.db.models import RiskAssessment

        super().__init__(RiskAssessment, session)

    async def get_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> list["RiskAssessment"]:
        from src.db.models import RiskAssessment

        result = await self.session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class PortfolioRepository(BaseRepository["Portfolio"]):
    """Specialized repository for Portfolio entities."""

    def __init__(self, session: AsyncSession):
        from src.db.models import Portfolio

        super().__init__(Portfolio, session)

    async def get_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> list["Portfolio"]:
        from src.db.models import Portfolio

        result = await self.session.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SimulationRepository(BaseRepository["Simulation"]):
    """Specialized repository for Simulation entities."""

    def __init__(self, session: AsyncSession):
        from src.db.models import Simulation

        super().__init__(Simulation, session)

    async def get_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> list["Simulation"]:
        from src.db.models import Simulation

        result = await self.session.execute(
            select(Simulation)
            .where(Simulation.user_id == user_id)
            .order_by(Simulation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ReportRepository(BaseRepository["Report"]):
    """Specialized repository for Report entities."""

    def __init__(self, session: AsyncSession):
        from src.db.models import Report

        super().__init__(Report, session)

    async def get_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> list["Report"]:
        from src.db.models import Report

        result = await self.session.execute(
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
