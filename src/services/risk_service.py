"""Risk assessment service.

Orchestrates questionnaire loading, answer validation, scoring,
and persistence.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import RiskAssessment
from src.db.repository import RiskAssessmentRepository
from src.engine.risk_engine import (
    calculate_category_scores,
    calculate_score,
    load_questionnaire,
    map_score_to_risk_level,
)
from src.models.risk import (
    Answer,
    QuestionnaireDefinition,
    RiskAssessmentRequest,
    RiskProfile,
    RiskLevel,
)
from src.utils.exceptions import RiskAssessmentError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RiskAssessmentService:
    """Service for risk assessment questionnaire and scoring."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RiskAssessmentRepository(session)

    async def get_questionnaire(self) -> QuestionnaireDefinition:
        """Get the active questionnaire with all questions."""
        return load_questionnaire()

    async def submit_assessment(
        self, request: RiskAssessmentRequest
    ) -> RiskProfile:
        """Process user answers and return a risk profile.

        Args:
            request: Contains user_id and list of answers.

        Returns:
            RiskProfile with risk level, scores, and category breakdown.

        Raises:
            RiskAssessmentError: If answers are invalid or incomplete.
        """
        # Load questionnaire for validation
        questionnaire = load_questionnaire()

        # Validate all questions are answered
        question_ids = {q.id for q in questionnaire.questions}
        answered_ids = {a.question_id for a in request.answers}

        if answered_ids != question_ids:
            missing = question_ids - answered_ids
            raise RiskAssessmentError(f"未回答的问题ID: {sorted(missing)}")

        # Validate answer values
        question_map = {q.id: q for q in questionnaire.questions}
        for answer in request.answers:
            question = question_map[answer.question_id]
            valid_values = {opt.value for opt in question.options}
            if answer.selected_value not in valid_values:
                raise RiskAssessmentError(
                    f"问题 {answer.question_id} 的无效答案值: {answer.selected_value}"
                )

        # Calculate scores
        total_score = calculate_score(request.answers, questionnaire.questions)
        max_possible = float(len(questionnaire.questions) * 5)  # Max value per question
        category_scores = calculate_category_scores(
            request.answers, questionnaire.questions
        )

        # Map to risk level
        risk_level, description = map_score_to_risk_level(total_score)

        # Persist
        assessment = RiskAssessment(
            user_id=request.user_id,
            questionnaire_version=questionnaire.version,
            answers_json={
                "answers": [
                    {"question_id": a.question_id, "selected_value": a.selected_value}
                    for a in request.answers
                ]
            },
            total_score=total_score,
            max_possible_score=max_possible,
            risk_level=risk_level.value,
            category_scores_json=category_scores,
        )
        assessment = await self.repo.create(assessment)

        logger.info(
            "risk_assessment_completed",
            user_id=str(request.user_id),
            risk_level=risk_level.value,
            score=total_score,
        )

        return RiskProfile(
            id=assessment.id,
            user_id=assessment.user_id,
            total_score=total_score,
            max_possible_score=max_possible,
            risk_level=risk_level,
            risk_level_label=risk_level.label_zh,
            risk_level_description=description,
            category_scores=category_scores,
            created_at=assessment.created_at,
        )

    async def get_user_history(self, user_id: UUID, limit: int = 10) -> list[RiskProfile]:
        """Get historical risk assessments for a user."""
        assessments = await self.repo.get_by_user(user_id, limit=limit)

        return [
            RiskProfile(
                id=a.id,
                user_id=a.user_id,
                total_score=a.total_score,
                max_possible_score=a.max_possible_score,
                risk_level=RiskLevel(a.risk_level),
                risk_level_label=RiskLevel(a.risk_level).label_zh,
                risk_level_description="",
                category_scores=a.category_scores_json or {},
                created_at=a.created_at,
            )
            for a in assessments
        ]

    async def get_latest(self, user_id: UUID) -> RiskProfile | None:
        """Get the most recent risk assessment for a user."""
        assessments = await self.repo.get_by_user(user_id, limit=1)
        if not assessments:
            return None

        a = assessments[0]
        risk_level = RiskLevel(a.risk_level)
        return RiskProfile(
            id=a.id,
            user_id=a.user_id,
            total_score=a.total_score,
            max_possible_score=a.max_possible_score,
            risk_level=risk_level,
            risk_level_label=risk_level.label_zh,
            risk_level_description="",
            category_scores=a.category_scores_json or {},
            created_at=a.created_at,
        )
