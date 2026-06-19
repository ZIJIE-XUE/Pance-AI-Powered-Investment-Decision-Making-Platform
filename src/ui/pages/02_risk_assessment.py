"""Risk Assessment page.

Users complete the risk tolerance questionnaire and view their results.
"""

import asyncio

import streamlit as st

from src.engine.risk_engine import load_questionnaire
from src.services.risk_service import RiskAssessmentService
from src.ui.components.questionnaire import render_questionnaire, render_risk_result
from src.db.database import async_session_factory
from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _


def _load_questionnaire_sync():
    """Load the questionnaire directly - no database needed."""
    return load_questionnaire()


async def _submit_assessment(user_id, answers):
    """Submit risk assessment answers."""
    from src.models.risk import RiskAssessmentRequest

    session = async_session_factory()
    try:
        service = RiskAssessmentService(session)
        request = RiskAssessmentRequest(user_id=user_id, answers=answers)
        result = await service.submit_assessment(request)
        await session.commit()
        return result
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def show():
    """Display the risk assessment page."""
    render_sidebar()
    st.title(t("🎯 风险承受能力测评"))

    # Check if user profile exists in session state

    # Check if user profile exists in session state
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning(t("⚠️ 请先在首页填写您的基本信息"))
        if st.button(t("前往首页")):
            st.switch_page("pages/01_home.py")
        return

    user = st.session_state.user
    user_id = user["id"]

    # Load questionnaire (engine has its own internal cache, no need to store in session)
    questionnaire = _load_questionnaire_sync()

    # Check if already completed
    if st.session_state.get("risk_profile") is not None:
        risk_profile = st.session_state.risk_profile
        st.success(t("✅ 测评已完成！"))
        st.markdown(
            t("**风险等级：** {label} （评分：{score:.0f}%）").format(
                label=t(risk_profile['risk_level_label']),
                score=risk_profile['total_score'] * 100,
            )
        )
        render_risk_result(risk_profile)

        col_retry, col_next, _ = st.columns([1, 1, 2])
        with col_retry:
            if st.button(t("🔄 重新测评")):
                st.session_state.risk_profile = None
                keys_to_clear = [k for k in st.session_state.keys() if k.startswith("q_")]
                for k in keys_to_clear:
                    del st.session_state[k]
                st.rerun()
        with col_next:
            if st.button(t("👉 下一步：投资组合"), type="primary", use_container_width=True):
                st.switch_page("pages/03_portfolio.py")
        return

    # Render questionnaire
    answers = render_questionnaire(questionnaire)

    # Submit button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submitted = st.button(
            t("📊 提交测评"),
            type="primary",
            use_container_width=True,
            disabled=len(answers) < len(questionnaire.questions),
        )

    if not submitted:
        # Show progress
        progress = len(answers) / len(questionnaire.questions) if questionnaire.questions else 0
        st.progress(progress, text=t("已完成 {done}/{total} 题").format(
            done=len(answers),
            total=len(questionnaire.questions),
        ))
        return

    # Submit assessment
    with st.spinner(t("正在分析您的风险承受能力...")):
        try:
            risk_profile = asyncio.run(_submit_assessment(user_id, answers))
            st.session_state.risk_profile = {
                "id": str(risk_profile.id),
                "user_id": str(risk_profile.user_id),
                "total_score": risk_profile.total_score,
                "max_possible_score": risk_profile.max_possible_score,
                "risk_level": risk_profile.risk_level.value,
                "risk_level_label": risk_profile.risk_level_label,
                "risk_level_description": risk_profile.risk_level_description,
                "category_scores": risk_profile.category_scores,
                "created_at": str(risk_profile.created_at) if risk_profile.created_at else None,
            }

            st.success(t("✅ 测评完成！"))
            st.rerun()

        except Exception as e:
            st.error(t("测评提交失败：{error}").format(error=str(e)))


if __name__ == "__main__":
    show()
