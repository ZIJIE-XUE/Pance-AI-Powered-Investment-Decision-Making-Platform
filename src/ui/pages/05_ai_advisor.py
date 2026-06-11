"""AI Advisor page.

Displays AI-generated portfolio analysis, risk assessment,
market scenarios, and investment recommendations.
"""

import asyncio

import streamlit as st

from src.services.advisor_service import AdvisorService


async def _get_advisor_response(user, risk_profile, portfolio, simulation):
    """Get AI advisor analysis."""
    service = AdvisorService()
    return await service.get_explanation(
        user=user,
        risk_profile=risk_profile,
        portfolio=portfolio,
        simulation=simulation,
    )


def show():
    """Display the AI Advisor page."""
    st.title("🤖 AI 投资顾问分析")

    # Check prerequisites
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("⚠️ 请先在首页填写基本信息")
        return

    if "risk_profile" not in st.session_state or st.session_state.risk_profile is None:
        st.warning("⚠️ 请先完成风险测评")
        return

    if "portfolio" not in st.session_state or st.session_state.portfolio is None:
        st.warning("⚠️ 请先完成投资组合优化")
        return

    if "simulation" not in st.session_state or st.session_state.simulation is None:
        st.warning("⚠️ 请先完成 Monte Carlo 模拟")
        return

    # Display context summary
    st.markdown(
        f"""
        **风险等级：** {st.session_state.risk_profile['risk_level_label']} |
        **组合预期收益：** {st.session_state.portfolio['expected_return'] * 100:.2f}% |
        **Sharpe Ratio：** {st.session_state.portfolio['sharpe_ratio']:.2f}
        """
    )

    # Check if advisor response already cached in session
    if st.session_state.get("advisor_response") is not None:
        response = st.session_state.advisor_response
        _display_advisor_response(response)

        if st.button("🔄 重新分析"):
            st.session_state.advisor_response = None
            st.rerun()
        return

    # Generate analysis button
    st.markdown("---")
    st.markdown(
        """
        ### 📋 AI 投资分析内容

        点击下方按钮，AI 将为您生成：
        - 🎯 投资组合概述与配置理由
        - ⚠️ 主要风险识别与分析
        - 📈 不同市场情景下的表现预测
        - 💡 具体可操作的投资建议
        - 🛡️ 风险提示

        *本地 AI 引擎，无需联网，即时生成分析结果。*
        """
    )

    if st.button("🤖 生成 AI 分析", type="primary", use_container_width=True):
        with st.spinner("AI 正在分析您的投资组合..."):
            try:
                response = asyncio.run(
                    _get_advisor_response(
                        user=st.session_state.user,
                        risk_profile=st.session_state.risk_profile,
                        portfolio=st.session_state.portfolio,
                        simulation=st.session_state.simulation,
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

                st.success("✅ AI 分析生成完成！")
                st.rerun()

            except Exception as e:
                st.error(f"AI 分析生成失败：{str(e)}")
                st.info("💡 提示：请确认前面的步骤（风险测评、组合优化、模拟）均已完成。")


def _display_advisor_response(response: dict):
    """Display the structured AI advisor response."""
    st.markdown("---")

    # Section 1: Summary
    with st.container():
        st.markdown("## 📝 投资组合概述")
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
        st.markdown("## 🎯 配置理由")
        st.markdown(response["allocation_rationale"])

    # Section 3: Key Risks
    st.markdown("## ⚠️ 主要风险分析")

    severity_colors = {
        "high": ("#f44336", "🔴 高风险"),
        "medium": ("#ff9800", "🟡 中风险"),
        "low": ("#4caf50", "🟢 低风险"),
    }

    for i, risk in enumerate(response.get("key_risks", [])):
        severity = risk.get("severity", "medium")
        color, label = severity_colors.get(severity, severity_colors["medium"])

        with st.expander(f"{label} - {risk['risk_name']}", expanded=(i == 0)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**风险描述**")
                st.markdown(risk["description"])
            with col2:
                st.markdown(f"**缓解建议**")
                st.markdown(risk.get("mitigation", "无特定建议"))

    # Section 4: Market Scenarios
    st.markdown("## 📈 市场情景分析")

    scenario_cols = st.columns(len(response.get("market_scenarios", [])))
    scenario_icons = {"牛市": "🐂", "熊市": "🐻", "震荡市": "📊"}

    for i, scenario in enumerate(response.get("market_scenarios", [])):
        scenario_name = scenario.get("scenario", "")
        icon = scenario_icons.get(scenario_name, "📈")

        with scenario_cols[i]:
            st.markdown(
                f"""
                <div style="padding: 15px; border-radius: 10px;
                     background-color: #f9f9f9; border: 1px solid #e0e0e0;
                     height: 100%;">
                    <h4 style="text-align: center;">{icon} {scenario_name}</h4>
                    <p><strong>发生概率：</strong>{scenario.get('probability', '')}</p>
                    <p>{scenario.get('description', '')}</p>
                    <p><strong>组合影响：</strong>{scenario.get('projected_impact', '')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Section 5: Investment Recommendations
    with st.container():
        st.markdown("## 💡 投资建议")
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
            f"""
            <div style="padding: 15px; border-radius: 8px;
                 background-color: #fff3e0; border: 1px solid #ff9800;
                 font-size: 0.9em; color: #666;">
                ⚠️ <strong>风险提示：</strong>{response.get('disclaimer_note', '投资有风险，过往表现不代表未来收益。本报告仅供参考，不构成投资建议。')}
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    show()
