"""Report generation Pydantic models."""

from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportRequest(BaseModel):
    """Request to generate a PDF report."""

    user_id: UUID
    risk_assessment_id: UUID | None = None
    portfolio_id: UUID | None = None
    simulation_id: UUID | None = None
    advisor_text: str | None = Field(
        default=None, description="AI advisor analysis text (optional)"
    )


class ReportMetadata(BaseModel):
    """Report metadata returned after generation."""

    id: UUID | None = None
    user_id: UUID
    status: ReportStatus = ReportStatus.PENDING
    pdf_path: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
