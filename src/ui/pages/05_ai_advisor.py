"""AI Advisor page.

Displays AI-generated portfolio analysis, risk assessment,
market scenarios, and investment recommendations.
"""

import asyncio

import streamlit as st

from src.services.advisor_service import AdvisorService
from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _, get_lang


async def _get_advisor_response(user, risk_profile, portfolio, simulation, lang="zh"):
    """Get AI advisor analysis."""
    service = AdvisorService()
    return await service.get_explanation(
        user=user,
        risk_profile=risk_profile,
        portfolio=portfolio,
        simulation=simulation,
        lang=lang,
    )


def show():
    """Display the AI Advisor page."""
    render_sidebar()
    st.title(t("🤖 AI 投资顾问分析"))

    # Check prerequisites
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning(t("⚠️ 请先在首页填写基本信息"))
        return

    if "risk_profile" not in st.session_state or st.session_state.risk_profile is None:
        st.warning(t("⚠️ 请先完成风险测评"))
        return

    if "portfolio" not in st.session_state or st.session_state.portfolio is None:
        st.warning(t("⚠️ 请先完成投资组合优化"))
        return

    if "simulation" not in st.session_state or st.session_state.simulation is None:
        st.warning(t("⚠️ 请先完成 Monte Carlo 模拟"))
        return

    # Display context summary
    st.markdown(
        t("**风险等级：** {risk_label} | "
          "**组合预期收益：** {expected_return:.2f}% | "
          "**Sharpe Ratio：** {sharpe:.2f}").format(
            risk_label=t(st.session_state.risk_profile['risk_level_label']),
            expected_return=st.session_state.portfolio['expected_return'] * 100,
            sharpe=st.session_state.portfolio['sharpe_ratio'],
        )
    )

    # Check if advisor response already cached in session
    if st.session_state.get("advisor_response") is not None:
        response = st.session_state.advisor_response
        _display_advisor_response(response)

        col_retry, col_next, _ = st.columns([1, 1, 2])
        with col_retry:
            if st.button(t("🔄 重新分析")):
                st.session_state.advisor_response = None
                st.rerun()
        with col_next:
            if st.button(t("👉 下一步：下载报告"), type="primary", use_container_width=True):
                st.switch_page("pages/06_report.py")
        return

    # Generate analysis button
    st.markdown("---")
    st.markdown(
        t("""
        ### 📋 AI 投资分析内容

        点击下方按钮，AI 将为您生成：
        - 🎯 投资组合概述与配置理由
        - ⚠️ 主要风险识别与分析
        - 📈 不同市场情景下的表现预测
        - 💡 具体可操作的投资建议
        - 🛡️ 风险提示

        *本地 AI 引擎，无需联网，即时生成分析结果。*
        """)
    )

    if st.button(t("🤖 生成 AI 分析"), type="primary", use_container_width=True):
        with st.spinner(t("AI 正在分析您的投资组合...")):
            try:
                response = asyncio.run(
                    _get_advisor_response(
                        user=st.session_state.user,
                        risk_profile=st.session_state.risk_profile,
                        portfolio=st.session_state.portfolio,
                        simulation=st.session_state.simulation,
                        lang=get_lang(),
                    )
                )

                # Store in session state
                st.session_state.advisor_response = {
                    "summary": response.summary,
                    "allocation_rationale": response.allocation_rationale,
                    "key_risks": [
                        {
                            "risk_name": r.risk_name,
                            "severity": r.severity,
                            "description": r.description,
                            "mitigation": r.mitigation,
                        }
                        for r in response.key_risks
                    ],
                    "market_scenarios": [
                        {
                            "scenario": s.scenario,
                            "probability": s.probability,
                            "description": s.description,
                            "projected_impact": s.projected_impact,
                        }
                        for s in response.market_scenarios
                    ],
                    "investment_recommendations": response.investment_recommendations,
                    "disclaimer_note": response.disclaimer_note,
                }

                st.success(t("✅ AI 分析生成完成！"))
                st.rerun()

            except Exception as e:
                st.error(t("AI 分析生成失败：{error}").format(error=str(e)))
                st.info(t("💡 提示：请确认前面的步骤（风险测评、组合优化、模拟）均已完成。"))


def _display_advisor_response(response: dict):
    """Display the structured AI advisor response."""
    st.markdown("---")

    # Section 1: Summary
    with st.container():
        st.markdown(t("## 📝 投资组合概述"))
        st.markdown(
            f"""
            <div style="padding: 20px; border-radius: 10px;
                 background-color: #f0f7ff; border-left: 4px solid #4285f4;">
                {response['summary']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Section 2: Allocation Rationale
    with st.container():
        st.markdown(t("## 🎯 配置理由"))
        st.markdown(response["allocation_rationale"])

    # Section 3: Key Risks
    st.markdown(t("## ⚠️ 主要风险分析"))

    severity_colors = {
        "high": ("#f44336", t("🔴 高风险")),
        "medium": ("#ff9800", t("🟡 中风险")),
        "low": ("#4caf50", t("🟢 低风险")),
    }

    for i, risk in enumerate(response.get("key_risks", [])):
        severity = risk.get("severity", "medium")
        color, label = severity_colors.get(severity, severity_colors["medium"])

        with st.expander(t("{label} - {risk_name}").format(label=label, risk_name=risk['risk_name']), expanded=(i == 0)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(t("**风险描述**"))
                st.markdown(risk["description"])
            with col2:
                st.markdown(t("**缓解建议**"))
                st.markdown(risk.get("mitigation", t("无特定建议")))

    # Section 4: Market Scenarios
    st.markdown(t("## 📈 市场情景分析"))

    scenario_cols = st.columns(len(response.get("market_scenarios", [])))
    scenario_icons = {"牛市": "🐂", "熊市": "🐻", "震荡市": "📊"}

    for i, scenario in enumerate(response.get("market_scenarios", [])):
        scenario_name = scenario.get("scenario", "")
        icon = scenario_icons.get(scenario_name, "📈")

        with scenario_cols[i]:
            st.markdown(
                t("""
                <div style="padding: 15px; border-radius: 10px;
                     background-color: #f9f9f9; border: 1px solid #e0e0e0;
                     height: 100%;">
                    <h4 style="text-align: center;">{icon} {scenario_name}</h4>
                    <p><strong>发生概率：</strong>{probability}</p>
                    <p>{description}</p>
                    <p><strong>组合影响：</strong>{projected_impact}</p>
                </div>
                """).format(
                    icon=icon,
                    scenario_name=scenario_name,
                    probability=scenario.get('probability', ''),
                    description=scenario.get('description', ''),
                    projected_impact=scenario.get('projected_impact', ''),
                ),
                unsafe_allow_html=True,
            )

    # Section 5: Investment Recommendations
    with st.container():
        st.markdown(t("## 💡 投资建议"))
        st.markdown(
            f"""
            <div style="padding: 20px; border-radius: 10px;
                 background-color: #f0fff4; border-left: 4px solid #4caf50;">
                {response['investment_recommendations']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Section 6: Disclaimer
    with st.container():
        st.markdown("---")
        st.markdown(
            t("""
            <div style="padding: 15px; border-radius: 8px;
                 background-color: #fff3e0; border: 1px solid #ff9800;
                 font-size: 0.9em; color: #666;">
                ⚠️ <strong>风险提示：</strong>{disclaimer}
            </div>
            """).format(
                disclaimer=response.get('disclaimer_note', t('投资有风险，过往表现不代表未来收益。本报告仅供参考，不构成投资建议。'))
            ),
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    show()
