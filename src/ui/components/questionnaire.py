"""Risk assessment questionnaire Streamlit component."""

import streamlit as st

from src.models.risk import Answer, Question, QuestionnaireDefinition
from src.ui.i18n import t, _


def render_questionnaire(questionnaire: QuestionnaireDefinition) -> list[Answer]:
    """Render the risk assessment questionnaire form.

    Args:
        questionnaire: The questionnaire definition with questions and options.

    Returns:
        List of Answer objects with user selections, or empty list if not submitted.
    """
    st.markdown("---")
    st.subheader("📋 " + t(questionnaire.title))
    st.markdown(t(questionnaire.description))
    st.markdown("---")

    answers: list[Answer] = []

    # Category labels for display
    category_labels = {
        "time_horizon": t("⏰ 投资期限"),
        "financial_situation": t("💰 财务状况"),
        "risk_tolerance": t("🎯 风险承受"),
        "investment_preference": t("📈 投资偏好"),
        "knowledge_experience": t("📚 知识与经验"),
    }

    current_category = None
    for i, question in enumerate(questionnaire.questions):
        # Display category header when category changes
        if question.category != current_category:
            current_category = question.category
            cat_label = category_labels.get(current_category, current_category)
            st.markdown(f"### {cat_label}")

        # Build options list for radio
        # Translate option labels for display
        options = [t(opt.label) for opt in question.options]
        values = [opt.value for opt in question.options]

        # Render radio button
        selected_label = st.radio(
            f"**Q{question.id}.** {t(question.text)}",
            options=options,
            key=f"q_{question.id}",
            index=None,  # No default selection
        )

        # Record answer if selected
        if selected_label is not None:
            idx = options.index(selected_label)
            answers.append(
                Answer(
                    question_id=question.id,
                    selected_value=values[idx],
                )
            )

    return answers


def render_risk_result(risk_profile) -> None:
    """Display the risk assessment result."""
    # Risk level colors
    level_colors = {
        "conservative": ["#2196F3", "🛡️"],
        "moderate": ["#4CAF50", "🌿"],
        "balanced": ["#FF9800", "⚖️"],
        "growth": ["#F44336", "🚀"],
        "aggressive": ["#9C27B0", "🔥"],
    }

    risk_level = risk_profile["risk_level"] if isinstance(risk_profile, dict) else risk_profile.risk_level.value
    color, emoji = level_colors.get(risk_level, ["#757575", "📊"])

    st.markdown("---")
    st.markdown(t("## 测评结果"))

    # Score gauge
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        total_score = risk_profile["total_score"] if isinstance(risk_profile, dict) else risk_profile.total_score
        risk_label = risk_profile["risk_level_label"] if isinstance(risk_profile, dict) else risk_profile.risk_level_label
        risk_desc = risk_profile["risk_level_description"] if isinstance(risk_profile, dict) else risk_profile.risk_level_description
        score_pct = total_score * 100
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h3 style="color: {color};">{emoji} {t(risk_label)}</h3>
                <p style="font-size: 48px; font-weight: bold; color: {color};">{score_pct:.0f}%</p>
                <p style="color: #666;">{t('风险承受能力评分')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Progress bar as gauge
        st.progress(total_score)

    # Description
    st.markdown(
        f"""
        <div style="
            padding: 20px;
            border-radius: 10px;
            background-color: {color}15;
            border-left: 4px solid {color};
            margin: 20px 0;
        ">
            <strong>{t('风险等级解读：')}</strong><br/>
            {t(risk_desc)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Category breakdown
    category_scores = risk_profile.get("category_scores", {}) if isinstance(risk_profile, dict) else getattr(risk_profile, "category_scores", {})
    if category_scores:
        st.markdown(t("### 各维度得分明细"))
        cat_labels_zh = {
            "time_horizon": t("投资期限"),
            "financial_situation": t("财务状况"),
            "risk_tolerance": t("风险承受"),
            "investment_preference": t("投资偏好"),
            "knowledge_experience": t("知识经验"),
        }

        for cat, score in category_scores.items():
            cat_label = cat_labels_zh.get(cat, cat)
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**{cat_label}**")
            with col2:
                st.progress(score)
                st.caption(f"{score * 100:.0f}%")
