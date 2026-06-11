"""Pytest fixtures for AI Robo Advisor tests."""

import pytest
import yaml
from pathlib import Path


@pytest.fixture
def sample_risk_config():
    """Load the risk_weights.yaml for test use."""
    config_path = Path(__file__).parent.parent / "config" / "risk_weights.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_questionnaire(sample_risk_config):
    """Get the sample questionnaire from config."""
    return sample_risk_config["questionnaire"]


@pytest.fixture
def sample_questions(sample_questionnaire):
    """Get the list of questions from the questionnaire as Pydantic models."""
    from src.models.risk import Question, QuestionOption

    questions = []
    for q in sample_questionnaire["questions"]:
        options = [
            QuestionOption(label=opt["label"], value=opt["value"])
            for opt in q["options"]
        ]
        questions.append(
            Question(
                id=q["id"],
                text=q["text"],
                category=q["category"],
                options=options,
            )
        )
    return questions


@pytest.fixture
def conservative_answers(sample_questions):
    """Generate answers that result in a conservative risk profile."""
    from src.models.risk import Answer

    answers = []
    for q in sample_questions:
        # Pick the lowest-value option (most conservative)
        min_val = min(opt.value for opt in q.options)
        answers.append(Answer(question_id=q.id, selected_value=min_val))
    return answers


@pytest.fixture
def aggressive_answers(sample_questions):
    """Generate answers that result in an aggressive risk profile."""
    from src.models.risk import Answer

    answers = []
    for q in sample_questions:
        # Pick the highest-value option (most aggressive)
        max_val = max(opt.value for opt in q.options)
        answers.append(Answer(question_id=q.id, selected_value=max_val))
    return answers


@pytest.fixture
def balanced_answers(sample_questions):
    """Generate answers that result in a balanced risk profile."""
    from src.models.risk import Answer

    answers = []
    for q in sample_questions:
        # Pick the middle-value option
        options = q.options
        mid_opt = options[len(options) // 2]
        answers.append(Answer(question_id=q.id, selected_value=mid_opt.value))
    return answers
