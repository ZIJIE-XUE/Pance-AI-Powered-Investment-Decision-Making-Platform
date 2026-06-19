"""DCA Calculator page.

Standalone page — no prerequisites. Two modes:
- Forward: monthly amount → future value projection
- Reverse: target amount → required monthly investment
"""

import plotly.graph_objects as go
import streamlit as st

from src.engine.dca_calculator import calculate_dca_forward, calculate_dca_reverse
from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _


def show():
    """Display the DCA calculator page."""
    render_sidebar()
    st.title(t("💰 定投计算器"))
    st.markdown(t("计算每月定额投资的未来收益，或反推达成目标所需的每月投入。"))

    st.markdown("---")

    # ── Common inputs ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        years = st.slider(t("投资年限"), min_value=1, max_value=30, value=10, step=1,
                          help=t("计划持续定投的年数"))
    with col2:
        annual_return = st.slider(
            t("预期年化收益率"), min_value=0.0, max_value=50.0, value=7.0, step=0.5,
            help=t("预期的年均投资回报率（参考：沪深300长期约8-10%，债券约3-5%，上限50%用于极端情景测试）"),
        ) / 100
    with col3:
        mode = st.radio(
            t("计算模式"),
            options=[t("📈 正算：我每月投X，将来能有多少？"), t("🎯 反算：我想攒到Y，每月要投多少？")],
        )

    st.markdown("---")

    # ── Mode-specific input ────────────────────────────────────────────────
    is_reverse = mode.startswith("🎯")

    if is_reverse:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            target_amount = st.number_input(
                t("目标金额 (¥)"),
                min_value=10_000,
                max_value=100_000_000,
                value=1_000_000,
                step=50_000,
                format="%d",
                help=t("你希望到期时攒到的总金额"),
            )
    else:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            monthly_amount = st.number_input(
                t("每月定投金额 (¥)"),
                min_value=100,
                max_value=1_000_000,
                value=5_000,
                step=500,
                format="%d",
                help=t("你计划每个月固定投入的金额"),
            )

    # ── Calculate button ───────────────────────────────────────────────────
    st.markdown("")
    if st.button(t("📊 开始计算"), type="primary", use_container_width=True):
        if is_reverse:
            result = calculate_dca_reverse(target_amount, years, annual_return)
            _display_reverse_result(result)
        else:
            result = calculate_dca_forward(monthly_amount, years, annual_return)
            _display_forward_result(result)

        _display_chart(result)
        _display_table(result)


def _display_forward_result(result: dict):
    """Display forward calculation summary cards."""
    st.markdown(t("### 📈 定投收益预测"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("每月投入"), f"¥{result['monthly_amount']:,.0f}")
    with col2:
        st.metric(t("累计投入"), f"¥{result['total_invested']:,.0f}")
    with col3:
        st.metric(t("投资收益"), f"¥{result['total_earnings']:,.0f}",
                  delta=t("{ratio}% 回报率").format(ratio=result['earnings_ratio']))
    with col4:
        st.metric(t("{years}年后终值").format(years=result['years']), f"¥{result['final_value']:,.0f}")


def _display_reverse_result(result: dict):
    """Display reverse calculation summary cards."""
    st.markdown(t("### 🎯 定投目标规划"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("目标金额"), f"¥{result['target_amount']:,.0f}")
    with col2:
        st.metric(t("每月需投入"), f"¥{result['monthly_needed']:,.0f}",
                  help=t("基于预期收益率反算的每月最低定投额"))
    with col3:
        st.metric(t("累计投入"), f"¥{result['total_invested']:,.0f}")
    with col4:
        gap = result.get("shortfall", 0)
        if abs(gap) < 1:
            st.metric(t("差额"), "≈ ¥0", delta=t("刚好达标 ✅"))
        elif gap > 0:
            st.metric(t("差额"), f"-¥{gap:,.0f}", delta=t("略有不足"))
        else:
            st.metric(t("差额"), f"+¥{abs(gap):,.0f}", delta=t("超额完成 🎉"))

    if result["monthly_needed"] <= 0:
        st.warning(t("目标金额太小或期限太长，每月投入几乎为零。请调整参数。"))


def _display_chart(result: dict):
    """Render area chart: principal vs earnings over time."""
    yearly = result["yearly_data"]

    years_list = [d["year"] for d in yearly]
    principal = [d["cumulative_principal"] for d in yearly]
    values = [d["cumulative_value"] for d in yearly]
    earnings = [v - p for v, p in zip(values, principal)]

    fig = go.Figure()

    # Principal area
    fig.add_trace(go.Scatter(
        x=years_list + years_list[::-1],
        y=principal + [0] * len(years_list),
        fill="toself",
        fillcolor="rgba(66, 133, 244, 0.3)",
        line=dict(color="rgba(66, 133, 244, 0.6)", width=1),
        name=t("累计本金"),
        hovertemplate=t("第 %{x} 年<br>累计本金: ¥%{y:,.0f}<extra></extra>"),
    ))

    # Earnings on top
    fig.add_trace(go.Scatter(
        x=years_list + years_list[::-1],
        y=values + principal[::-1],
        fill="toself",
        fillcolor="rgba(76, 175, 80, 0.3)",
        line=dict(color="rgba(76, 175, 80, 0.6)", width=1),
        name=t("投资收益"),
        hovertemplate=t("第 %{x} 年<br>累计总值: ¥%{y:,.0f}<extra></extra>"),
    ))

    # Total value line
    fig.add_trace(go.Scatter(
        x=years_list,
        y=values,
        mode="lines+markers",
        line=dict(color="#1a237e", width=2),
        marker=dict(size=4, color="#1a237e"),
        name=t("总资产"),
        hovertemplate=t("第 %{x} 年<br>总资产: ¥%{y:,.0f}<extra></extra>"),
    ))

    # Add reference line for target in reverse mode
    if result.get("mode") == "reverse":
        target = result["target_amount"]
        fig.add_hline(
            y=target, line_dash="dash", line_color="#f44336",
            annotation_text=t("目标: ¥{target:,.0f}").format(target=target),
            annotation_position="bottom right",
        )

    fig.update_layout(
        title=t("资产增长曲线"),
        xaxis_title=t("年数"),
        yaxis_title=t("金额 (¥)"),
        hovermode="x unified",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)


def _display_table(result: dict):
    """Display yearly breakdown table."""
    st.markdown(t("### 📋 逐年明细"))

    yearly = result["yearly_data"]

    table_data = []
    for d in yearly:
        table_data.append({
            t("年份"): t("第{year}年").format(year=d['year']),
            t("当年投入"): f"¥{d['year_principal']:,.0f}",
            t("累计投入"): f"¥{d['cumulative_principal']:,.0f}",
            t("累计收益"): f"¥{d['year_earnings']:,.0f}",
            t("总资产"): f"¥{d['cumulative_value']:,.0f}",
            t("收益占比"): round(d['year_earnings'] / d['cumulative_value'] * 100, 1)
            if d['cumulative_value'] > 0 else 0.0,
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            t("年份"): st.column_config.TextColumn(width="small"),
            t("收益占比"): st.column_config.ProgressColumn(
                width="medium",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


if __name__ == "__main__":
    show()
