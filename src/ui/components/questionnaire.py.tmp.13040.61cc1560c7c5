"""Risk assessment questionnaire Streamlit component."""

import streamlit as st

from src.models.risk import Answer, Question, QuestionnaireDefinition


def render_questionnaire(questionnaire: QuestionnaireDefinition) -> list[Answer]:
    """Render the risk assessment questionnaire form.

    Args:
        questionnaire: The questionnaire definition with questions and options.

    Returns:
        List of Answer objects with user selections, or empty list if not submitted.
    """
    st.markdown("---")
    st.subheader("📋 " + questionnaire.title)
    st.markdown(questionnaire.description)
    st.markdown("---")

    answers: list[Answer] = []

    # Category labels for display
    category_labels = {
        "time_horizon": "⏰ 投资期限",
        "financial_situation": "💰 财务状况",
        "risk_tolerance": "🎯 风险承受",
        "investment_preference": "📈 投资偏好",
        "knowledge_experience": "📚 知识与经验",
    }

    current_category = None
    for i, question in enumerate(questionnaire.questions):
        # Display category header when category changes
        if question.category != current_category:
            current_category = question.category
            cat_label = category_labels.get(current_category, current_category)
            st.markdown(f"### {cat_label}")

        # Build options list for radio
        options = [opt.label for opt in question.options]
        values = [opt.value for opt in question.options]

        # Render radio button
        selected_label = st.radio(
            f"**Q{question.id}.** {question.text}",
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

    color, emoji = level_colors.get(risk_profile.risk_level.value, ["#757575", "📊"])

    st.markdown("---")
    st.markdown("## 测评结果")

    # Score gauge
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        score_pct = risk_profile.total_score * 100
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h3 style="color: {color};">{emoji} {risk_profile.risk_level_label}</h3>
                <p style="font-size: 48px; font-weight: bold; color: {color};">{score_pct:.0f}%</p>
                <p style="color: #666;">风险承受能力评分</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Progress bar as gauge
        st.progress(risk_profile.total_score)

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
            <strong>风险等级解读：</strong><br/>
            {risk_profile.risk_level_description}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Category breakdown
    if risk_profile.category_scores:
        st.markdown("### 各维度得分明细")
        cat_labels_zh = {
            "time_horizon": "投资期限",
            "financial_situation": "财务状况",
            "risk_tolerance": "风险承受",
            "investment_preference": "投资偏好",
            "knowledge_experience": "知识经验",
        }

        for cat, score in risk_profile.category_scores.items():
            cat_label = cat_labels_zh.get(cat, cat)
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**{cat_label}**")
            with col2:
                st.progress(score)
                st.caption(f"{score * 100:.0f}%")
