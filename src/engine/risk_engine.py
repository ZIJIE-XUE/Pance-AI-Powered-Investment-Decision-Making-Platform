"""Risk assessment scoring engine.

Pure computation functions: score calculation, risk level mapping,
category breakdowns. No I/O or persistence.
"""

from pathlib import Path

import yaml

from src.models.risk import (
    Answer,
    Question,
    QuestionnaireDefinition,
    RiskLevel,
    RiskProfile,
)
from src.utils.exceptions import RiskAssessmentError


# Cache for loaded config
_config_cache: dict | None = None


def _load_config() -> dict:
    """Load risk_weights.yaml config, caching it in memory."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = Path(__file__).parent.parent.parent / "config" / "risk_weights.yaml"
    with open(config_path, encoding="utf-8") as f:
        _config_cache = yaml.safe_load(f)
    return _config_cache


def load_questionnaire() -> QuestionnaireDefinition:
    """Load the active questionnaire definition from config."""
    config = _load_config()
    q_def = config["questionnaire"]

    questions = [
        Question(
            id=q["id"],
            text=q["text"],
            category=q["category"],
            options=q["options"],
        )
        for q in q_def["questions"]
    ]

    return QuestionnaireDefinition(
        version=q_def["version"],
        title=q_def["title"],
        description=q_def["description"],
        questions=questions,
    )


def calculate_score(answers: list[Answer], questions: list[Question]) -> float:
    """Calculate normalized risk score from user answers.

    Returns a float between 0.0 (most conservative) and 1.0 (most aggressive).
    """
    if not answers:
        raise RiskAssessmentError("答案不能为空")

    question_map = {q.id: q for q in questions}

    total_score = 0.0
    min_possible = 0.0
    max_possible = 0.0

    for answer in answers:
        question = question_map.get(answer.question_id)
        if question is None:
            raise RiskAssessmentError(f"无效的问题ID: {answer.question_id}")

        values = [opt.value for opt in question.options]
        min_val = min(values)
        max_val = max(values)

        min_possible += min_val
        max_possible += max_val
        total_score += answer.selected_value

    if max_possible == min_possible:
        return 0.5  # Fallback for degenerate case

    normalized = (total_score - min_possible) / (max_possible - min_possible)
    return round(normalized, 4)


def calculate_category_scores(
    answers: list[Answer], questions: list[Question]
) -> dict[str, float]:
    """Calculate normalized scores per question category."""
    question_map = {q.id: q for q in questions}

    categories: dict[str, dict[str, float]] = {}
    for q in questions:
        if q.category not in categories:
            categories[q.category] = {"score": 0.0, "min": 0.0, "max": 0.0}

    for answer in answers:
        question = question_map.get(answer.question_id)
        if question is None:
            continue

        values = [opt.value for opt in question.options]
        cat = categories[question.category]
        cat["score"] += answer.selected_value
        cat["min"] += min(values)
        cat["max"] += max(values)

    result = {}
    for cat_name, cat_data in categories.items():
        if cat_data["max"] == cat_data["min"]:
            result[cat_name] = 0.5
        else:
            result[cat_name] = round(
                (cat_data["score"] - cat_data["min"])
                / (cat_data["max"] - cat_data["min"]),
                4,
            )

    return result


def map_score_to_risk_level(score: float) -> tuple[RiskLevel, str]:
    """Map a normalized score to a risk level and description.

    Returns (RiskLevel, description).
    """
    config = _load_config()
    levels = config["risk_levels"]

    for level_key, level_data in levels.items():
        if level_data["min_score"] <= score <= level_data["max_score"]:
            risk_level = RiskLevel(level_key)
            return risk_level, level_data["description"]

    # Fallback (should not reach here)
    return RiskLevel.BALANCED, "平衡型投资者"


def get_risk_level_config(risk_level: RiskLevel) -> dict:
    """Get the full configuration for a given risk level."""
    config = _load_config()
    return config["risk_levels"][risk_level.value]


def get_recommended_allocation_ranges(risk_level: RiskLevel) -> dict[str, tuple[float, float]]:
    """Get recommended asset class allocation ranges for a risk level.

    Returns dict mapping asset class to (min, max) weight.
    """
    level_config = get_risk_level_config(risk_level)
    return {
        "equity": (
            level_config["equity_range"][0],
            level_config["equity_range"][1],
        ),
        "bond": (
            level_config["bond_range"][0],
            level_config["bond_range"][1],
        ),
        "gold": (
            level_config["gold_range"][0],
            level_config["gold_range"][1],
        ),
        "cash": (
            level_config["cash_range"][0],
            level_config["cash_range"][1],
        ),
    }
