"""Unit tests for the risk assessment engine."""

import pytest
from src.engine.risk_engine import (
    calculate_score,
    calculate_category_scores,
    map_score_to_risk_level,
    load_questionnaire,
)
from src.models.risk import RiskLevel, Question


class TestCalculateScore:
    """Tests for the risk score calculation function."""

    def test_conservative_score_zero(self, sample_questions, conservative_answers):
        """Conservative (lowest) answers should give score near 0."""
        score = calculate_score(conservative_answers, sample_questions)
        assert score == 0.0

    def test_aggressive_score_one(self, sample_questions, aggressive_answers):
        """Aggressive (highest) answers should give score near 1."""
        score = calculate_score(aggressive_answers, sample_questions)
        assert score == 1.0

    def test_balanced_score_mid(self, sample_questions, balanced_answers):
        """Balanced answers should give roughly 0.5."""
        score = calculate_score(balanced_answers, sample_questions)
        assert 0.3 <= score <= 0.7

    def test_empty_answers_raises_error(self):
        """Empty answer list should raise an error."""
        with pytest.raises(Exception):
            calculate_score([], [])

    def test_invalid_question_id_raises_error(self, sample_questions):
        """Invalid question ID should raise an error."""
        from src.models.risk import Answer

        answers = [Answer(question_id=999, selected_value=3)]
        with pytest.raises(Exception):
            calculate_score(answers, sample_questions)

    def test_score_between_zero_and_one(self, sample_questions, balanced_answers):
        """Score should always be between 0 and 1."""
        score = calculate_score(balanced_answers, sample_questions)
        assert 0.0 <= score <= 1.0


class TestMapScoreToRiskLevel:
    """Tests for risk level mapping."""

    def test_low_score_is_conservative(self):
        """Score < 0.30 should map to conservative."""
        level, _ = map_score_to_risk_level(0.15)
        assert level == RiskLevel.CONSERVATIVE

    def test_mid_score_is_balanced(self):
        """Score ~0.5 should map to balanced."""
        level, _ = map_score_to_risk_level(0.50)
        assert level == RiskLevel.BALANCED

    def test_high_score_is_aggressive(self):
        """Score > 0.80 should map to aggressive."""
        level, _ = map_score_to_risk_level(0.85)
        assert level == RiskLevel.AGGRESSIVE

    def test_boundary_conservative_moderate(self):
        """Boundary 0.30 maps to conservative (first match)."""
        level, _ = map_score_to_risk_level(0.30)
        assert level == RiskLevel.CONSERVATIVE

    def test_boundary_balanced_growth(self):
        """Boundary 0.60 maps to balanced (first match)."""
        level, _ = map_score_to_risk_level(0.60)
        assert level == RiskLevel.BALANCED


class TestLoadQuestionnaire:
    """Tests for questionnaire loading."""

    def test_loads_all_questions(self):
        """Should load all 12 questions."""
        q = load_questionnaire()
        assert len(q.questions) == 12

    def test_each_question_has_options(self):
        """Each question should have options."""
        q = load_questionnaire()
        for question in q.questions:
            assert len(question.options) == 5

    def test_questionnaire_has_title(self):
        """Questionnaire should have a title."""
        q = load_questionnaire()
        assert q.title
        assert q.version


class TestCategoryScores:
    """Tests for category score calculation."""

    def test_returns_dict(self, sample_questions, balanced_answers):
        """Should return a dict of category scores."""
        scores = calculate_category_scores(balanced_answers, sample_questions)
        assert isinstance(scores, dict)
        assert len(scores) > 0

    def test_all_scores_between_zero_and_one(self, sample_questions, balanced_answers):
        """All category scores should be between 0 and 1."""
        scores = calculate_category_scores(balanced_answers, sample_questions)
        for score in scores.values():
            assert 0.0 <= score <= 1.0
