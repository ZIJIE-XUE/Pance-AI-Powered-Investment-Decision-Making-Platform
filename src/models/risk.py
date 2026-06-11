"""Risk assessment Pydantic models."""

from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Five risk tolerance levels."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    BALANCED = "balanced"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"

    @property
    def label_zh(self) -> str:
        labels = {
            "conservative": "保守型",
            "moderate": "稳健型",
            "balanced": "平衡型",
            "growth": "成长型",
            "aggressive": "激进型",
        }
        return labels[self.value]


class QuestionOption(BaseModel):
    """A single option in a risk questionnaire question."""

    label: str
    value: int


class Question(BaseModel):
    """A single question in the risk assessment questionnaire."""

    id: int
    text: str
    category: str
    options: list[QuestionOption]


class QuestionnaireDefinition(BaseModel):
    """Full questionnaire definition."""

    version: str
    title: str
    description: str
    questions: list[Question]


class Answer(BaseModel):
    """User's answer to a single questionnaire question."""

    question_id: int
    selected_value: int


class RiskAssessmentRequest(BaseModel):
    """Request to submit risk assessment answers."""

    user_id: UUID
    answers: list[Answer]


class RiskProfile(BaseModel):
    """Complete risk profile returned after assessment."""

    id: UUID | None = None
    user_id: UUID
    total_score: float = Field(..., ge=0, le=1, description="Normalized risk score 0-1")
    max_possible_score: float
    risk_level: RiskLevel
    risk_level_label: str
    risk_level_description: str
    category_scores: dict[str, float] = Field(
        default_factory=dict, description="Scores by question category"
    )
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
