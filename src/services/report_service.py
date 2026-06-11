"""Report generation service.

Orchestrates report building, status tracking, and file management.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Report
from src.db.repository import ReportRepository
from src.models.report import ReportMetadata, ReportRequest, ReportStatus
from src.reports.report_builder import ReportBuilder
from src.utils.exceptions import ReportGenerationError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ReportService:
    """Service for generating and managing investment reports."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReportRepository(session)
        self.builder = ReportBuilder()

    async def generate(
        self,
        user_info: dict,
        risk_profile: dict | None,
        portfolio: dict | None,
        simulation: dict | None,
        advisor_response: dict | None = None,
    ) -> ReportMetadata:
        """Generate a PDF investment report.

        Args:
            user_info: User profile dict from session state.
            risk_profile: Risk assessment result dict.
            portfolio: Portfolio optimization result dict.
            simulation: Monte Carlo simulation result dict.
            advisor_response: AI advisor analysis dict.

        Returns:
            ReportMetadata with file path and status.

        Raises:
            ReportGenerationError: If generation fails.
        """
        user_id = UUID(user_info["id"])

        # Create report record
        report = Report(
            user_id=user_id,
            status=ReportStatus.GENERATING.value,
        )
        report = await self.repo.create(report)
        report_id = report.id

        try:
            # Build the PDF
            pdf_path = self.builder.build_report(
                user_info=user_info,
                risk_profile=risk_profile or {},
                portfolio=portfolio or {},
                simulation=simulation or {},
                advisor_response=advisor_response,
            )

            # Update record
            file_size = os.path.getsize(pdf_path)

            report.pdf_path = pdf_path
            report.file_size_bytes = file_size
            report.status = ReportStatus.COMPLETED.value
            report.completed_at = datetime.now(timezone.utc)

            await self.repo.update(report)

            logger.info(
                "report_completed",
                report_id=str(report_id),
                size=file_size,
            )

            return ReportMetadata(
                id=report.id,
                user_id=report.user_id,
                status=ReportStatus.COMPLETED,
                pdf_path=pdf_path,
                file_size_bytes=file_size,
                created_at=report.created_at,
                completed_at=report.completed_at,
            )

        except Exception as e:
            # Update report status to failed
            report.status = ReportStatus.FAILED.value
            report.error_message = str(e)
            await self.repo.update(report)

            logger.error(
                "report_failed",
                report_id=str(report_id),
                error=str(e),
            )
            raise ReportGenerationError(str(e))

    async def get_report(self, report_id: UUID) -> ReportMetadata | None:
        """Get report metadata by ID."""
        report = await self.repo.get_by_id(report_id)
        if report is None:
            return None

        return ReportMetadata(
            id=report.id,
            user_id=report.user_id,
            status=ReportStatus(report.status),
            pdf_path=report.pdf_path,
            file_size_bytes=report.file_size_bytes,
            error_message=report.error_message,
            created_at=report.created_at,
            completed_at=report.completed_at,
        )

    async def get_user_reports(
        self, user_id: UUID, limit: int = 10
    ) -> list[ReportMetadata]:
        """Get all reports for a user."""
        reports = await self.repo.get_by_user(user_id, limit=limit)

        return [
            ReportMetadata(
                id=r.id,
                user_id=r.user_id,
                status=ReportStatus(r.status),
                pdf_path=r.pdf_path,
                file_size_bytes=r.file_size_bytes,
                error_message=r.error_message,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in reports
        ]

    @staticmethod
    def get_report_bytes(pdf_path: str) -> bytes | None:
        """Read the PDF file bytes for download."""
        if not pdf_path or not os.path.exists(pdf_path):
            return None

        with open(pdf_path, "rb") as f:
            return f.read()
