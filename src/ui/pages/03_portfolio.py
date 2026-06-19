"""Portfolio Optimization page.

Displays the recommended asset allocation, pie chart, and performance metrics.
"""

import asyncio

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.services.portfolio_service import PortfolioOptimizationService
from src.models.portfolio import PortfolioOptimizationRequest
from src.db.database import async_session_factory
from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _


async def _optimize_portfolio(user_id, risk_profile_id, risk_level, preferred_markets=None):
    """Run portfolio optimization."""
    session = async_session_factory()
    try:
        service = PortfolioOptimizationService(session)
        request = PortfolioOptimizationRequest(
            user_id=user_id,
            risk_profile_id=risk_profile_id,
            risk_level=risk_level,
            preferred_markets=preferred_markets,
        )
        result = await service.optimize(request)
        await session.commit()
        return result
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def show():
    """Display the portfolio optimization page."""
    render_sidebar()
    st.title(t("📊 投资组合配置"))

    # Check prerequisites
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning(t("⚠️ 请先在首页填写基本信息"))
        return

    if "risk_profile" not in st.session_state or st.session_state.risk_profile is None:
        st.warning(t("⚠️ 请先完成风险测评"))
        if st.button(t("前往风险测评")):
            st.switch_page("pages/02_risk_assessment.py")
        return

    user = st.session_state.user
    risk_profile = st.session_state.risk_profile

    # Display risk level context
    risk_level_label = risk_profile["risk_level_label"]
    risk_level = risk_profile["risk_level"]
    st.info(
        t("🎯 您的风险等级：**{label}** | 评分：**{score:.0f}%**").format(
            label=risk_level_label,
            score=risk_profile['total_score'] * 100,
        )
    )

    # Check if portfolio already exists in session
    if st.session_state.get("portfolio") is not None:
        portfolio = st.session_state.portfolio
        _display_portfolio_result(portfolio)

        col_retry, col_next, _ = st.columns([1, 1, 2])
        with col_retry:
            if st.button(t("🔄 重新优化")):
                st.session_state.portfolio = None
                st.rerun()
        with col_next:
            if st.button(t("👉 下一步：Monte Carlo 模拟"), type="primary", use_container_width=True):
                st.switch_page("pages/04_simulation.py")
        return

    # Run optimization button
    if st.button(t("🚀 生成投资组合"), type="primary", use_container_width=True):
        with st.spinner(t("正在进行投资组合优化...（获取市场数据可能需要1-2分钟）")):
            try:
                markets = user.get("preferred_markets", "A股,港股,美股")
                result = asyncio.run(
                    _optimize_portfolio(
                        user_id=user["id"],
                        risk_profile_id=risk_profile["id"],
                        risk_level=risk_level,
                        preferred_markets=markets,
                    )
                )

                # Store in session state
                st.session_state.portfolio = {
                    "id": str(result.id) if result.id else None,
                    "user_id": str(result.user_id),
                    "risk_assessment_id": str(result.risk_assessment_id) if result.risk_assessment_id else None,
                    "risk_level": result.risk_level,
                    "optimization_method": result.optimization_method,
                    "allocations": [
                        {
                            "ticker": a.ticker,
                            "name": a.name,
                            "asset_class": a.asset_class,
                            "weight": a.weight,
                            "expected_return": a.expected_return,
                            "volatility": a.volatility,
                        }
                        for a in result.allocations
                    ],
                    "expected_return": result.expected_return,
                    "volatility": result.volatility,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                }

                st.success(t("✅ 投资组合生成完成！"))
                st.rerun()

            except Exception as e:
                st.error(t("优化失败：{error}").format(error=str(e)))


def _display_portfolio_result(portfolio: dict):
    """Display the portfolio optimization results."""
    st.markdown("---")

    # Create columns for key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            t("预期年化收益"),
            f"{portfolio['expected_return'] * 100:.2f}%",
        )
    with col2:
        st.metric(
            t("年化波动率"),
            f"{portfolio['volatility'] * 100:.2f}%",
        )
    with col3:
        st.metric(
            t("夏普比率"),
            f"{portfolio['sharpe_ratio']:.2f}",
            help=t("Sharpe Ratio > 1 为良好，> 2 为优秀"),
        )
    with col4:
        st.metric(
            t("最大回撤"),
            f"{portfolio['max_drawdown'] * 100:.2f}%",
        )

    st.markdown("---")

    # Pie chart and allocation table side by side
    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.markdown(t("### 资产配置比例"))
        allocations = portfolio["allocations"]

        # Color map by asset class
        class_colors = {
            "equity": px.colors.qualitative.Set1[0],
            "bond": px.colors.qualitative.Set1[1],
            "gold": px.colors.qualitative.Set1[2],
            "real_estate": px.colors.qualitative.Set1[3],
            "cash": px.colors.qualitative.Set1[4],
        }

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=[f"{a['ticker']} ({a['weight']*100:.1f}%)" for a in allocations],
                    values=[a["weight"] for a in allocations],
                    marker=dict(
                        colors=[class_colors.get(a["asset_class"], "#999") for a in allocations]
                    ),
                    textinfo="label+percent",
                    hole=0.35,
                )
            ]
        )
        fig.update_layout(
            height=450,
            margin=dict(l=20, r=20, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Legend
        st.markdown(t("**资产类别图例**"))
        legend_cols = st.columns(4)
        class_names = {
            "equity": t("🟥 股票"),
            "bond": t("🟦 债券"),
            "gold": t("🟩 黄金"),
            "real_estate": t("🟧 地产"),
        }
        for i, (cls, label) in enumerate(class_names.items()):
            with legend_cols[i]:
                st.caption(label)

    with col_table:
        st.markdown(t("### 持仓明细"))
        # Build table data
        table_data = []
        for a in allocations:
            table_data.append({
                t("代码"): a["ticker"],
                t("名称"): a["name"],
                t("资产类别"): a["asset_class"],
                t("配置比例"): f"{a['weight'] * 100:.2f}%",
                t("预期收益"): f"{a['expected_return'] * 100:.2f}%",
                t("年化波动"): f"{a['volatility'] * 100:.2f}%",
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                t("代码"): st.column_config.TextColumn(width="small"),
                t("配置比例"): st.column_config.ProgressColumn(
                    format="%.2f%%",
                    min_value=0,
                    max_value=1,
                ),
            },
        )

    # Asset class summary
    st.markdown(t("### 大类资产汇总"))
    class_summary = {}
    for a in allocations:
        cls = a["asset_class"]
        if cls not in class_summary:
            class_summary[cls] = 0.0
        class_summary[cls] += a["weight"]

    summary_cols = st.columns(len(class_summary))
    class_labels = {
        "equity": t("股票"),
        "bond": t("债券"),
        "gold": t("黄金"),
        "real_estate": t("地产"),
        "cash": t("现金"),
    }
    for i, (cls, weight) in enumerate(class_summary.items()):
        with summary_cols[i]:
            label = class_labels.get(cls, cls)
            st.metric(label, f"{weight * 100:.1f}%")


if __name__ == "__main__":
    show()
