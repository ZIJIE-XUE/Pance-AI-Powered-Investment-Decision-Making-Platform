"""Monte Carlo Simulation page.

Displays fan charts, probability distributions, and risk statistics.
"""

import asyncio

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.services.simulation_service import MonteCarloService
from src.models.simulation import MonteCarloRequest
from src.db.database import async_session_factory
from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _


async def _run_simulation(user_id, portfolio_id, initial_amount, horizon_years, num_paths):
    """Execute Monte Carlo simulation."""
    session = async_session_factory()
    try:
        service = MonteCarloService(session)
        request = MonteCarloRequest(
            user_id=user_id,
            portfolio_id=portfolio_id,
            initial_amount=initial_amount,
            horizon_years=horizon_years,
            num_paths=num_paths,
        )
        result = await service.run(request)
        await session.commit()
        return result
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def show():
    """Display the Monte Carlo simulation page."""
    render_sidebar()
    st.title(t("🔮 Monte Carlo 模拟"))

    # Check prerequisites
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning(t("⚠️ 请先在首页填写基本信息"))
        return

    if "portfolio" not in st.session_state or st.session_state.portfolio is None:
        st.warning(t("⚠️ 请先完成投资组合优化"))
        if st.button(t("前往组合优化")):
            st.switch_page("pages/03_portfolio.py")
        return

    user = st.session_state.user
    portfolio = st.session_state.portfolio

    # Simulation parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        initial_amount = st.number_input(
            t("初始投资金额 (¥)"),
            value=float(user.get("asset_size", 100_000)),
            min_value=1000.0,
            step=10_000.0,
            format="%.0f",
        )
    with col2:
        horizon_years = st.selectbox(
            t("投资期限"),
            options=[5, 10, 20],
            index=0,
            help=t("选择模拟的时间跨度"),
        )
    with col3:
        num_paths = st.selectbox(
            t("模拟路径数"),
            options=[1_000, 5_000, 10_000, 50_000],
            index=2,
            help=t("路径越多越精确，但计算时间更长"),
        )

    # Run simulation button
    run_col1, run_col2 = st.columns([1, 2])
    with run_col1:
        run_sim = st.button(
            t("🔮 运行 Monte Carlo 模拟"),
            type="primary",
            use_container_width=True,
        )

    if run_sim:
        with st.spinner(t("正在模拟 {paths} 条收益路径...（可能需要10-30秒）").format(paths=f"{num_paths:,}")):
            try:
                result = asyncio.run(
                    _run_simulation(
                        user_id=user["id"],
                        portfolio_id=portfolio["id"],
                        initial_amount=initial_amount,
                        horizon_years=horizon_years,
                        num_paths=num_paths,
                    )
                )

                # Store in session state
                st.session_state.simulation = {
                    "id": str(result.id) if result.id else None,
                    "initial_amount": result.initial_amount,
                    "horizon_years": result.horizon_years,
                    "num_paths": result.num_paths,
                    "median_final_value": result.median_final_value,
                    "percentile_5": result.percentile_5,
                    "percentile_95": result.percentile_95,
                    "var_95": result.var_95,
                    "cvar_95": result.cvar_95,
                    "probability_positive": result.probability_positive,
                    "yearly_projections": [
                        {
                            "year": p.year,
                            "percentile_10": p.percentile_10,
                            "percentile_25": p.percentile_25,
                            "percentile_50": p.percentile_50,
                            "percentile_75": p.percentile_75,
                            "percentile_90": p.percentile_90,
                        }
                        for p in result.yearly_projections
                    ],
                    "final_values": result.final_values,
                    "sample_paths": result.sample_paths,
                }

                st.success(t("✅ 模拟完成！"))
                st.rerun()

            except Exception as e:
                st.error(t("模拟失败：{error}").format(error=str(e)))

    # Display results if available
    if st.session_state.get("simulation") is not None:
        sim = st.session_state.simulation
        _display_simulation_results(sim)

        col_retry, col_next, _ = st.columns([1, 1, 2])
        with col_retry:
            if st.button(t("🔄 重新模拟")):
                st.session_state.simulation = None
                st.rerun()
        with col_next:
            if st.button(t("👉 下一步：AI 分析"), type="primary", use_container_width=True):
                st.switch_page("pages/05_ai_advisor.py")


def _display_simulation_results(sim: dict):
    """Display Monte Carlo simulation results with charts and stats."""
    st.markdown("---")

    # Key statistics
    total_return = (
        (sim["median_final_value"] / sim["initial_amount"] - 1) * 100
    )
    p5_return = (
        (sim["percentile_5"] / sim["initial_amount"] - 1) * 100
    )
    p95_return = (
        (sim["percentile_95"] / sim["initial_amount"] - 1) * 100
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            t("初始投资"),
            f"¥{sim['initial_amount']:,.0f}",
        )
    with col2:
        st.metric(
            t("预期终值（中位数）"),
            f"¥{sim['median_final_value']:,.0f}",
            delta=f"{total_return:.1f}%",
        )
    with col3:
        st.metric(
            t("悲观情景 (P5)"),
            f"¥{sim['percentile_5']:,.0f}",
            delta=f"{p5_return:.1f}%",
            delta_color="off",
        )
    with col4:
        st.metric(
            t("乐观情景 (P95)"),
            f"¥{sim['percentile_95']:,.0f}",
            delta=f"{p95_return:.1f}%",
        )
    with col5:
        st.metric(
            t("盈利概率"),
            f"{sim['probability_positive'] * 100:.1f}%",
        )

    # Risk metrics
    risk_col1, risk_col2 = st.columns(2)
    with risk_col1:
        st.metric("Value at Risk (95%)", f"¥{sim['var_95']:,.0f}")
    with risk_col2:
        st.metric("Conditional VaR (95%)", f"¥{sim['cvar_95']:,.0f}")

    st.markdown("---")

    # Fan chart
    st.markdown(t("### 📈 收益路径扇形图"))
    _render_fan_chart(sim)

    # Distribution histogram
    col_hist, col_stats = st.columns([2, 1])

    with col_hist:
        st.markdown(t("### 📊 终值概率分布"))
        _render_histogram(sim)

    with col_stats:
        st.markdown(t("### 📋 逐年预测"))
        _render_yearly_table(sim)


def _render_fan_chart(sim: dict):
    """Render fan chart showing percentile bands over time."""
    years = [p["year"] for p in sim["yearly_projections"]]

    fig = go.Figure()

    # P10-P90 band
    p90 = [p["percentile_90"] for p in sim["yearly_projections"]]
    p10 = [p["percentile_10"] for p in sim["yearly_projections"]]
    fig.add_trace(
        go.Scatter(
            x=years + years[::-1],
            y=p90 + p10[::-1],
            fill="toself",
            fillcolor="rgba(66, 133, 244, 0.2)",
            line=dict(color="rgba(255, 255, 255, 0)"),
            name="P10-P90",
            hoverinfo="skip",
        )
    )

    # P25-P75 band
    p75 = [p["percentile_75"] for p in sim["yearly_projections"]]
    p25 = [p["percentile_25"] for p in sim["yearly_projections"]]
    fig.add_trace(
        go.Scatter(
            x=years + years[::-1],
            y=p75 + p25[::-1],
            fill="toself",
            fillcolor="rgba(66, 133, 244, 0.4)",
            line=dict(color="rgba(255, 255, 255, 0)"),
            name="P25-P75",
            hoverinfo="skip",
        )
    )

    # Median line
    p50 = [p["percentile_50"] for p in sim["yearly_projections"]]
    fig.add_trace(
        go.Scatter(
            x=years,
            y=p50,
            mode="lines",
            line=dict(color="#1a73e8", width=3),
            name=t("中位数 (P50)"),
        )
    )

    # Sample paths (faint background lines)
    if sim.get("sample_paths"):
        for i, path in enumerate(sim["sample_paths"][:30]):  # Show 30 paths max
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(path))),
                    y=path,
                    mode="lines",
                    line=dict(color="rgba(150, 150, 150, 0.15)", width=0.5),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # Initial investment line
    fig.add_hline(
        y=sim["initial_amount"],
        line_dash="dash",
        line_color="gray",
        annotation_text=t("初始投资"),
    )

    fig.update_layout(
        height=500,
        xaxis_title=t("年"),
        yaxis_title=t("组合价值 (¥)"),
        hovermode="x unified",
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_histogram(sim: dict):
    """Render histogram of final portfolio values."""
    final_values = sim.get("final_values")
    if not final_values:
        st.info(t("无分布数据"))
        return

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=final_values,
            nbinsx=80,
            marker_color="#4285f4",
            opacity=0.75,
            name=t("终值分布"),
        )
    )

    # Add percentile lines
    p5 = sim["percentile_5"]
    p50 = sim["median_final_value"]
    p95 = sim["percentile_95"]

    for value, color, label in [
        (p5, "red", t("P5 (悲观)")),
        (p50, "blue", t("P50 (中位)")),
        (p95, "green", t("P95 (乐观)")),
    ]:
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=label,
        )

    # Initial investment line
    fig.add_vline(
        x=sim["initial_amount"],
        line_dash="dot",
        line_color="gray",
        annotation_text=t("初始投资"),
    )

    fig.update_layout(
        height=400,
        xaxis_title=t("组合终值 (¥)"),
        yaxis_title=t("频次"),
        showlegend=False,
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_yearly_table(sim: dict):
    """Render yearly projection table."""
    table_data = []
    for p in sim["yearly_projections"]:
        table_data.append({
            t("年份"): t("第{year}年").format(year=p['year']),
            t("悲观(P10)"): f"¥{p['percentile_10']:,.0f}",
            t("保守(P25)"): f"¥{p['percentile_25']:,.0f}",
            t("中位(P50)"): f"¥{p['percentile_50']:,.0f}",
            t("乐观(P75)"): f"¥{p['percentile_75']:,.0f}",
            t("激进(P90)"): f"¥{p['percentile_90']:,.0f}",
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        height=400,
    )


if __name__ == "__main__":
    show()
