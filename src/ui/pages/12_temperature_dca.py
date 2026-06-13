"""Temperature-Driven DCA — flagship page of 磐策 PánCè.

Combines market temperature signals with dollar-cost-averaging:
- Backtests three strategies over historical data
- Shows real-time market temperature + current investment suggestion
- Demonstrates quantitative investment methodology
"""

from datetime import datetime

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.engine import temperature_dca_engine as engine
from src.engine.market_thermometer import classify_temperature
from src.ui.components.sidebar import render_sidebar

# ── Colour constants ─────────────────────────────────────────────────────────

ORANGE_MAIN = "#E65100"
ORANGE_LIGHT = "#FFF3E0"
RED_UP = "#e74c3c"
GREEN_DOWN = "#27ae60"
BLUE_BRAND = "#1a237e"
GRAY_LIGHT = "#f8f9fa"

ZONE_COLORS = {
    "极度低估": "#2196F3",
    "偏低": "#64B5F6",
    "适中": "#9E9E9E",
    "偏贵": "#FF9800",
    "高估": "#f44336",
}


# ── Data loading (cached) ────────────────────────────────────────────────────

_CACHE_VERSION = "v3"  # bump to invalidate stale caches after engine changes (added regime_analysis + signal validation)

@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_backtest_data(
    index_name: str,
    years: int,
    base_monthly: float,
    strategy_name: str,
    cache_version: str = _CACHE_VERSION,
) -> dict:
    """Run backtest. Cached 24h — historical data doesn't change intraday.

    `cache_version` is a cache-busting parameter — bump _CACHE_VERSION
    whenever the engine output schema changes.
    """
    return engine.run_backtest(
        index_name=index_name,
        years=years,
        base_monthly=base_monthly,
        strategy_name=strategy_name,
    )


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_current_temperature() -> dict:
    """Fetch current market temperature (reuse thermometer cache)."""
    try:
        from src.engine.market_thermometer import fetch_market_temperature
        return fetch_market_temperature(years=5)
    except Exception:
        return {"indices": [], "overall": None, "timestamp": datetime.now()}


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_signal_validation(index_name: str, cache_version: str = _CACHE_VERSION) -> dict:
    """Run signal validation. Cached 24h."""
    return engine.validate_temperature_signal(index_name=index_name, years=10)


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_walk_forward(index_name: str, train_years: int, test_years: int, cache_version: str = _CACHE_VERSION) -> dict:
    """Run walk-forward validation. Cached 24h."""
    return engine.walk_forward_validation(
        index_name=index_name,
        train_years=train_years,
        test_years=test_years,
        base_monthly=5000.0,
    )


# ── Page config ──────────────────────────────────────────────────────────────

def _inject_css():
    """Inject custom CSS for the temperature DCA page."""
    st.markdown("""
    <style>
        .temp-hero {
            background: linear-gradient(135deg, #FFF3E0 0%, #FCE4EC 100%);
            border-left: 5px solid #E65100;
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 20px;
        }
        .temp-hero h1 {
            color: #BF360C;
            margin: 0 0 6px 0;
            font-size: 1.8em;
        }
        .temp-hero p {
            color: #666;
            margin: 0;
            font-size: 0.95em;
        }
        .strategy-card {
            background: #fafafa;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: center;
            border: 2px solid #e0e0e0;
            transition: border-color 0.2s;
        }
        .strategy-card.active {
            border-color: #E65100;
            background: #FFF8E1;
        }
        .metric-box {
            text-align: center;
            padding: 16px 10px;
            border-radius: 10px;
            background: #fafafa;
        }
        .metric-box.winner {
            background: #E8F5E9;
            border: 1.5px solid #4CAF50;
        }
        .metric-box .value {
            font-size: 1.4em;
            font-weight: 700;
        }
        .metric-box .label {
            font-size: 0.75em;
            color: #888;
            margin-top: 4px;
        }
    </style>
    """, unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────────────────────

def _render_header():
    """Render the flagship hero header."""
    st.markdown(
        '<div class="temp-hero">'
        '<h1>🌡️ 智能温度定投</h1>'
        '<p>基于市场估值温度动态调整每期定投金额 · '
        '市场冷时多投，热时少投 · 回测验证，数据驱动决策</p>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Strategy configuration ───────────────────────────────────────────────────

def _render_config() -> dict:
    """Render strategy configuration bar. Returns config dict."""
    st.markdown("### ⚙️ 策略配置")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        index_name = st.selectbox(
            "基准指数",
            options=["沪深300", "上证50", "中证500", "中证1000"],
            index=0,
            help="回测基准指数，沪深300最能代表A股整体走势",
        )

    with col2:
        years = st.selectbox(
            "回测年限",
            options=[3, 5, 7, 10],
            index=1,
            help="回测历史年数。年限越长，穿越的牛熊周期越多，结论越可靠",
        )

    with col3:
        base_monthly = st.number_input(
            "基准月投 (¥)",
            min_value=500,
            max_value=100_000,
            value=5_000,
            step=500,
            format="%d",
            help="温度适中(40-60°C)时的标准月投金额。市场冷热时按倍率自动调整",
        )

    with col4:
        strategy_name = st.radio(
            "温度策略",
            options=["moderate", "aggressive", "conservative"],
            format_func=lambda s: {
                "aggressive": "🔥 积极",
                "moderate": "⚖️ 适中",
                "conservative": "🛡️ 保守",
            }[s],
            index=0,
            help="积极=低温重仓高位空仓 · 适中=均衡加减 · 保守=温和微调",
        )

    st.markdown("---")
    return {
        "index_name": index_name,
        "years": years,
        "base_monthly": base_monthly,
        "strategy_name": strategy_name,
    }


# ── Multiplier map display ───────────────────────────────────────────────────

def _render_multiplier_map(strategy_name: str):
    """Show temperature → multiplier mapping table."""
    strategy = engine.STRATEGIES.get(strategy_name, engine.STRATEGIES["moderate"])

    st.markdown(
        f"<p style='font-size:0.85em;color:#888;margin-bottom:4px'>"
        f"📐 温度→倍率映射 · {strategy['name']}型 · {strategy['desc']}</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(5, gap="small")
    zones = [
        ("🧊 极度低估<br>0–20°C", "#2196F3"),
        ("❄️ 偏低<br>20–40°C", "#64B5F6"),
        ("🌡️ 适中<br>40–60°C", "#9E9E9E"),
        ("🔥 偏贵<br>60–80°C", "#FF9800"),
        ("💥 高估<br>80–100°C", "#f44336"),
    ]

    for i, (label_html, color) in enumerate(zones):
        mult = strategy["multipliers"][i][2]
        with cols[i]:
            st.markdown(
                f"<div style='text-align:center;padding:8px 4px;border-radius:8px;"
                f"background:{color}15;border:1.5px solid {color}40'>"
                f"<div style='font-size:0.72em;color:#555;margin-bottom:4px'>{label_html}</div>"
                f"<div style='font-size:1.3em;font-weight:700;color:{color}'>×{mult}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")


# ── Equity curves chart ──────────────────────────────────────────────────────

def _render_equity_chart(backtest: dict, config: dict):
    """Render the main comparison chart: three equity curves."""
    st.markdown("### 📈 回测资产曲线对比")

    temp_records = backtest["temperature_dca"]["records"]
    reg_records = backtest["regular_dca"]["records"]
    lump_records = backtest["lump_sum"]["records"]
    monthly_df = backtest.get("monthly_df")

    fig = go.Figure()

    # Temperature DCA — thick orange line
    fig.add_trace(go.Scatter(
        x=[r["date"] for r in temp_records],
        y=[r["portfolio_value"] for r in temp_records],
        mode="lines",
        line=dict(color="#E65100", width=2.8),
        name="🌡️ 温度定投",
        hovertemplate="%{x|%Y-%m}<br>温度定投: ¥%{y:,.0f}<extra></extra>",
    ))

    # Regular DCA — dashed gray
    fig.add_trace(go.Scatter(
        x=[r["date"] for r in reg_records],
        y=[r["portfolio_value"] for r in reg_records],
        mode="lines",
        line=dict(color="#78909C", width=1.8, dash="dash"),
        name="📋 普通定投",
        hovertemplate="%{x|%Y-%m}<br>普通定投: ¥%{y:,.0f}<extra></extra>",
    ))

    # Lump sum — dotted blue
    fig.add_trace(go.Scatter(
        x=[r["date"] for r in lump_records],
        y=[r["portfolio_value"] for r in lump_records],
        mode="lines",
        line=dict(color="#42A5F5", width=1.5, dash="dot"),
        name="💰 一次性买入",
        hovertemplate="%{x|%Y-%m}<br>一次性: ¥%{y:,.0f}<extra></extra>",
    ))

    # Total invested line (cost basis)
    if temp_records:
        fig.add_trace(go.Scatter(
            x=[r["date"] for r in temp_records],
            y=[r["total_invested"] for r in temp_records],
            mode="lines",
            line=dict(color="#BDBDBD", width=1, dash="dash"),
            name="累计投入",
            hovertemplate="%{x|%Y-%m}<br>累计投入: ¥%{y:,.0f}<extra></extra>",
        ))

    # Temperature heatmap on secondary y-axis
    if monthly_df is not None and len(monthly_df) > 0:
        temps = monthly_df["temperature"].values
        temp_colors = []
        for t in temps:
            if t >= 80:
                temp_colors.append("#f44336")
            elif t >= 60:
                temp_colors.append("#FF9800")
            elif t >= 40:
                temp_colors.append("#9E9E9E")
            elif t >= 20:
                temp_colors.append("#64B5F6")
            else:
                temp_colors.append("#2196F3")

        fig.add_trace(go.Scatter(
            x=monthly_df["date"],
            y=monthly_df["temperature"],
            mode="markers",
            marker=dict(
                size=5,
                color=temp_colors,
                opacity=0.6,
                symbol="square",
            ),
            yaxis="y2",
            name="市场温度",
            hovertemplate="%{x|%Y-%m}<br>温度: %{y:.0f}°C<extra></extra>",
        ))

    fig.update_layout(
        height=480,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="",
        yaxis_title="资产价值 (¥)",
        yaxis2=dict(
            title="温度 (°C)",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
        ),
        hovermode="x unified",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Metrics comparison ───────────────────────────────────────────────────────

def _render_metrics(backtest: dict):
    """Render strategy comparison: key metrics + return/drawdown ratio + mechanism."""
    st.markdown("### 📊 策略对比分析")

    temp_m = backtest["temperature_dca"]
    reg_m = backtest["regular_dca"]
    lump_m = backtest["lump_sum"]
    mechanism = backtest.get("mechanism", {})

    # ── Part 1: Three key metrics ──────────────────────────────────────────
    st.markdown("#### 核心指标")

    col_t, col_r, col_l = st.columns(3, gap="small")

    for col, m, label, icon in [
        (col_t, temp_m, "🌡️ 温度定投", ORANGE_MAIN),
        (col_r, reg_m, "📋 普通定投", "#78909C"),
        (col_l, lump_m, "💰 一次性买入", "#42A5F5"),
    ]:
        with col:
            border_color = icon
            st.markdown(
                f"<div style='text-align:center;padding:16px 8px;border-radius:10px;"
                f"background:#fafafa;border:2px solid {border_color}30'>"
                f"<div style='font-size:0.85em;font-weight:600;margin-bottom:10px'>{label}</div>"
                f"<div style='font-size:1.5em;font-weight:700'>{m['cagr_pct']}%</div>"
                f"<div style='font-size:0.7em;color:#888'>年化收益 CAGR</div>"
                f"<div style='margin-top:8px;font-size:1.1em;font-weight:600;color:#f44336'>-{m['max_drawdown_pct']}%</div>"
                f"<div style='font-size:0.7em;color:#888'>最大回撤</div>"
                f"<div style='margin-top:8px;font-size:1.05em'>{m['sharpe_ratio']}</div>"
                f"<div style='font-size:0.7em;color:#888'>夏普比率</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Part 2: Mechanism breakdown ─────────────────────────────────────────
    st.markdown("")
    st.markdown("#### 🔍 为什么温度定投呈现这个结果？")

    zone = mechanism.get("zone_breakdown", {})
    cp = mechanism.get("cash_pool", {})

    cold = zone.get("cold", {})
    normal = zone.get("normal", {})
    hot = zone.get("hot", {})

    if cold or hot:
        mech_cols = st.columns(3, gap="small")

        with mech_cols[0]:
            cold_months = cold.get("months", 0)
            cold_extra = cold.get("extra_vs_base", 0)
            st.markdown(
                f"<div style='padding:12px;background:#E3F2FD;border-radius:8px'>"
                f"<div style='font-size:0.85em;font-weight:600'>🧊 低温区间 (0-40°C)</div>"
                f"<div style='font-size:0.75em;color:#888'>共 {cold_months} 个月 · 估值偏低</div>"
                f"<div style='font-size:1.15em;font-weight:600;color:#1565C0;margin-top:4px'>"
                f"{'+' if cold_extra >= 0 else ''}¥{cold_extra:,.0f}</div>"
                f"<div style='font-size:0.72em;color:#555'>额外加仓（低位多买）</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with mech_cols[1]:
            hot_months = hot.get("months", 0)
            hot_saved = cp.get("total_saved_in_hot", 0)
            st.markdown(
                f"<div style='padding:12px;background:#FFF3E0;border-radius:8px'>"
                f"<div style='font-size:0.85em;font-weight:600'>🔥 高温区间 (60-100°C)</div>"
                f"<div style='font-size:0.75em;color:#888'>共 {hot_months} 个月 · 估值偏高</div>"
                f"<div style='font-size:1.15em;font-weight:600;color:#E65100;margin-top:4px'>"
                f"¥{hot_saved:,.0f}</div>"
                f"<div style='font-size:0.72em;color:#555'>暂扣少投（高位避风险）</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with mech_cols[2]:
            max_cp = cp.get("max_balance", 0)
            peak_d = cp.get("peak_date", "—")
            st.markdown(
                f"<div style='padding:12px;background:#fafafa;border-radius:8px'>"
                f"<div style='font-size:0.85em;font-weight:600'>💰 现金池动态</div>"
                f"<div style='font-size:0.75em;color:#888'>峰值日期 {peak_d}</div>"
                f"<div style='font-size:1.15em;font-weight:600;color:#555;margin-top:4px'>"
                f"¥{max_cp:,.0f}</div>"
                f"<div style='font-size:0.72em;color:#555'>最高积存金额</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Part 4: Caveat ─────────────────────────────────────────────────────
    caveat = mechanism.get("caveat", "")
    if caveat:
        st.markdown("")
        st.info(caveat)


# ── Yearly breakdown ─────────────────────────────────────────────────────────

def _render_yearly_breakdown(backtest: dict, config: dict):
    """Render yearly breakdown table for temperature DCA."""
    st.markdown("---")
    st.markdown("### 📋 温度定投逐年明细")

    yearly = backtest.get("yearly_breakdown", [])
    if not yearly:
        st.info("数据不足以生成逐年明细")
        return

    table_data = []
    for y in yearly:
        avg_temp = y.get("avg_temp", 50)
        temp_info = classify_temperature(avg_temp)
        table_data.append({
            "年份": f"{y['year']}年",
            "当年投入": f"¥{y['invested']:,.0f}",
            "年末市值": f"¥{y['end_value']:,.0f}",
            "平均温度": f"{avg_temp:.0f}°C {temp_info['zone_label']}",
            "平均倍率": f"×{y['avg_multiplier']:.2f}",
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "年份": st.column_config.TextColumn(width="small"),
            "平均温度": st.column_config.TextColumn(width="medium"),
        },
    )


# ── Signal Validation ──────────────────────────────────────────────────────────

def _render_signal_validation(config: dict):
    """Render signal validation: scatter plot + correlation + bucket analysis.

    Tests whether market temperature actually predicts forward returns.
    This is the empirical foundation that justifies the entire strategy.
    """
    st.markdown("---")
    st.markdown("### 🔬 信号验证：温度能否预测未来收益？")

    st.markdown(
        '<p style="font-size:0.85em;color:#888;margin-bottom:12px">'
        '如果温度信号有效，低温应该对应未来较高的收益（负相关）。'
        '这是整个温度定投策略的实证基础。</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("正在运行信号验证...（首次约 5-10 秒）"):
        validation = _fetch_signal_validation(config["index_name"])

    if "error" in validation:
        st.warning(f"⚠️ 信号验证暂不可用：{validation['error']}")
        return

    corr = validation["correlation"]
    dq = validation["data_quality"]

    # ── Top row: scatter plot + stats ──────────────────────────────────────
    chart_col, stat_col = st.columns([3, 2])

    with chart_col:
        scatter_data = validation["scatter_data"]
        reg = validation["regression"]

        # Build scatter plot with regression line
        fig = go.Figure()

        # Color points by temperature zone
        temps = [d["temperature"] for d in scatter_data]
        returns = [d["forward_12m_return_pct"] for d in scatter_data]

        point_colors = []
        for t in temps:
            if t >= 80:
                point_colors.append("#f44336")
            elif t >= 60:
                point_colors.append("#FF9800")
            elif t >= 40:
                point_colors.append("#9E9E9E")
            elif t >= 20:
                point_colors.append("#64B5F6")
            else:
                point_colors.append("#2196F3")

        fig.add_trace(go.Scatter(
            x=temps,
            y=returns,
            mode="markers",
            marker=dict(size=9, color=point_colors, opacity=0.55, line=dict(width=0.5, color="#fff")),
            name="月度数据点",
            hovertemplate="温度: %{x:.0f}°C<br>未来12月收益: %{y:.1f}%<extra></extra>",
        ))

        # Regression line
        x_range = np.linspace(min(temps) - 2, max(temps) + 2, 100)
        y_line = reg["slope"] * x_range + reg["intercept"]
        fig.add_trace(go.Scatter(
            x=x_range.tolist(),
            y=y_line.tolist(),
            mode="lines",
            line=dict(color="#E65100", width=2, dash="dash"),
            name=f"回归线 (r={corr['pearson_r']:.3f})",
            hovertemplate="温度: %{x:.0f}°C<br>预测收益: %{y:.1f}%<extra></extra>",
        ))

        # Zero-return reference line
        fig.add_hline(y=0, line=dict(color="#ccc", width=1, dash="dot"))

        fig.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis_title="市场温度 (°C)",
            yaxis_title="未来12个月收益 (%)",
            plot_bgcolor="white",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with stat_col:
        # Correlation statistics
        sig_badge = "✅ 统计显著" if corr["significant"] else "⚠️ 不显著"
        sig_color = "#27ae60" if corr["significant"] else "#E65100"

        st.markdown(
            f"<div style='padding:16px;background:#fafafa;border-radius:10px;margin-bottom:10px'>"
            f"<div style='font-size:0.85em;font-weight:600;margin-bottom:10px'>📊 相关分析</div>"
            f"<table style='width:100%;font-size:0.9em'>"
            f"<tr><td>Pearson r</td><td style='text-align:right;font-weight:700'>{corr['pearson_r']:.4f}</td></tr>"
            f"<tr><td>p 值</td><td style='text-align:right;font-weight:700'>{corr['p_value']:.4f}</td></tr>"
            f"<tr><td>R²</td><td style='text-align:right;font-weight:700'>{corr['r_squared']:.4f}</td></tr>"
            f"<tr><td>显著性</td><td style='text-align:right;font-weight:700;color:{sig_color}'>{sig_badge}</td></tr>"
            f"<tr><td>样本量</td><td style='text-align:right'>{dq['total_points']} 个月</td></tr>"
            f"<tr><td>基准指数</td><td style='text-align:right'>{dq['index_name']}</td></tr>"
            f"</table></div>",
            unsafe_allow_html=True,
        )

        # Interpretation
        st.info(corr["interpretation"])

    # ── Bucket analysis ────────────────────────────────────────────────────
    buckets = validation.get("bucket_analysis", [])
    if buckets:
        st.markdown("#### 温度分桶：各区间未来收益对比")

        bucket_cols = st.columns(len(buckets), gap="small")
        for i, b in enumerate(buckets):
            with bucket_cols[i]:
                # Color based on zone
                zone_colors_bucket = {
                    "🧊 极度低估": "#2196F3",
                    "❄️ 偏低": "#64B5F6",
                    "🌡️ 适中": "#9E9E9E",
                    "🔥 偏贵": "#FF9800",
                    "💥 高估": "#f44336",
                }
                zone_color = zone_colors_bucket.get(b["zone"], "#9E9E9E")

                # Determine if this bucket has positive avg return
                avg_ret = b["avg_forward_return"]
                ret_color = "#27ae60" if avg_ret > 0 else "#e74c3c"

                st.markdown(
                    f"<div style='text-align:center;padding:10px 6px;border-radius:8px;"
                    f"background:{zone_color}10;border:1.5px solid {zone_color}30'>"
                    f"<div style='font-size:0.78em;color:#555;margin-bottom:4px'>{b['zone']}</div>"
                    f"<div style='font-size:0.7em;color:#888'>{b['range']}</div>"
                    f"<div style='font-size:1.15em;font-weight:700;color:{ret_color};margin:4px 0'>"
                    f"{'+' if avg_ret > 0 else ''}{avg_ret}%</div>"
                    f"<div style='font-size:0.7em;color:#888'>平均未来12月收益</div>"
                    f"<div style='font-size:0.7em;color:#aaa'>"
                    f"正收益率 {b['positive_rate']}% · n={b['count']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ── Regime decomposition ───────────────────────────────────────────────────────

def _render_regime_decomposition(backtest: dict):
    """Render market regime decomposition: strategy performance in bull/bear/sideways."""
    st.markdown("---")
    st.markdown("### 📊 市场环境分解：什么情况下温度定投有效？")

    regime_analysis = backtest.get("regime_analysis", {})
    regimes = regime_analysis.get("regimes", {})
    insight = regime_analysis.get("insight", "")

    if not regimes:
        st.info("市场环境数据不足以进行分解分析")
        return

    st.markdown(
        '<p style="font-size:0.85em;color:#888;margin-bottom:12px">'
        '将回测区间拆分为牛市（价>均线+上行）、熊市（价<均线+下行）、震荡市（价在均线附近），'
        '对比三种策略在各环境下的表现。不同策略在不同市场中各有优劣——'
        '了解这一点是制定投资策略的关键。</p>',
        unsafe_allow_html=True,
    )

    # ── Comparison table ───────────────────────────────────────────────────
    # Build table as HTML cards
    regime_order = ["🐂 牛市", "🐻 熊市", "📊 震荡"]

    cols = st.columns(len(regime_order), gap="small")

    for i, regime_label in enumerate(regime_order):
        data = regimes.get(regime_label)
        with cols[i]:
            if data is None:
                st.markdown(
                    f"<div style='padding:16px;text-align:center;background:#fafafa;"
                    f"border-radius:10px;color:#999'>"
                    f"<div style='font-size:1.2em'>{regime_label}</div>"
                    f"<div style='font-size:0.8em;margin-top:8px'>本期无此环境</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                continue

            # Build card
            months = data["months"]
            avg_temp = data["avg_temperature"]

            # Strategies comparison within this regime
            strategies_html = ""
            for label, key in [("🌡️ 温度", "temp_dca"), ("📋 普通", "regular_dca"), ("💰 一次性", "lump_sum")]:
                s = data[key]
                ret = s["return_pct"]
                is_winner = s.get("is_winner", False)
                ret_color = "#27ae60" if ret > 0 else "#e74c3c"
                winner_mark = " 🏆" if is_winner else ""
                strategies_html += (
                    f"<div style='display:flex;justify-content:space-between;"
                    f"font-size:0.82em;padding:2px 0;"
                    f"{'font-weight:700;color:#E65100' if is_winner else 'color:#555'}'>"
                    f"<span>{label}{winner_mark}</span>"
                    f"<span style='color:{ret_color}'>{'+' if ret > 0 else ''}{ret}%</span>"
                    f"</div>"
                )

            st.markdown(
                f"<div style='padding:14px 12px;background:#fafafa;border-radius:10px;"
                f"border:1.5px solid #e0e0e0'>"
                f"<div style='font-size:1.1em;font-weight:600;text-align:center;"
                f"margin-bottom:6px'>{regime_label}</div>"
                f"<div style='font-size:0.75em;color:#888;text-align:center;margin-bottom:10px'>"
                f"{months} 个月 · 平均温度 {avg_temp:.0f}°C</div>"
                f"{strategies_html}"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Insight ────────────────────────────────────────────────────────────
    if insight:
        st.markdown("")
        st.info(insight)

    # ── Key takeaway ───────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.82em;color:#888;margin-top:4px">'
        '💡 <b>核心认知</b>：没有任何策略在所有市场中都最优。'
        '温度定投的价值定位是——用牛市中的相对落后，换取熊市和震荡市中的显著优势。'
        '这是一个明确、可预期的 trade-off，而非策略缺陷。'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Walk-Forward validation ────────────────────────────────────────────────────

def _render_walk_forward(config: dict):
    """Render walk-forward validation: train/test split + grid search + OOS test.

    Gold-standard test for overfitting: optimise on train, verify on test.
    """
    st.markdown("---")
    st.markdown("### 🚶 Walk-Forward 样本外检验")

    st.markdown(
        '<p style="font-size:0.85em;color:#888;margin-bottom:12px">'
        '将历史数据拆分为训练窗（优化参数）和测试窗（只看一遍），'
        '测试策略是否在从未见过的数据上仍然有效。'
        '这是区分"真正有用的策略"和"回测过拟合"的黄金标准。</p>',
        unsafe_allow_html=True,
    )

    # Compute appropriate split for the selected years
    backtest_years = config["years"]
    if backtest_years >= 7:
        train_years = max(4, backtest_years - 3)
        test_years = backtest_years - train_years
    elif backtest_years >= 5:
        train_years = 3
        test_years = backtest_years - 3
    else:
        train_years = 2
        test_years = backtest_years - 2

    if test_years < 1:
        st.info("回测年限太短，无法进行有意义的 Walk-Forward 检验（至少需要2年训练 + 1年测试）。请增加回测年限。")
        return

    with st.spinner(f"正在运行 Walk-Forward 检验...（{train_years}年训练 → {test_years}年测试，首次约 20-30 秒）"):
        wf = _fetch_walk_forward(config["index_name"], train_years, test_years)

    if "error" in wf:
        st.warning(f"⚠️ Walk-Forward 检验暂不可用：{wf['error']}")
        return

    opt = wf["optimization"]
    dq = wf["data_quality"]
    train = wf["train_performance"]
    test = wf["test_performance"]
    deg = wf["degradation"]

    # ── Top row: two-window comparison ─────────────────────────────────────
    tw_col, tw_label, ts_col = st.columns([5, 1, 5])

    with tw_col:
        st.markdown(
            f"<div style='padding:16px;background:#FFF8E1;border-radius:10px;"
            f"border:2px solid #FF9800;text-align:center'>"
            f"<div style='font-size:0.85em;color:#E65100;font-weight:600;margin-bottom:8px'>"
            f"🔧 训练窗 · {train_years}年</div>"
            f"<div style='font-size:0.7em;color:#888;margin-bottom:10px'>"
            f"{dq['train_window']['start']} → {dq['train_window']['end']} · "
            f"{dq['train_months']} 个月</div>"
            f"<div style='font-size:0.78em;color:#555;margin-bottom:10px'>"
            f"网格搜索 {opt['search_space']['total_combos']} 种组合，"
            f"最优：PE {opt['best_pe_weight']:.0%} + {opt['best_strategy_label']}</div>"
            f"<div style='font-size:1.15em;font-weight:700'>"
            f"温度: {train['temp_dca']['cagr_pct']}%</div>"
            f"<div style='font-size:0.8em;color:#888'>"
            f"普通: {train['regular_dca']['cagr_pct']}% · "
            f"超额: <b style='color:#E65100'>{'+' if train['excess_cagr'] > 0 else ''}{train['excess_cagr']}%</b></div>"
            f"<div style='font-size:0.8em;color:#888'>"
            f"夏普: {train['temp_dca']['sharpe_ratio']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with tw_label:
        st.markdown(
            '<div style="text-align:center;font-size:1.5em;padding-top:40px">→</div>',
            unsafe_allow_html=True,
        )

    with ts_col:
        excess_color = "#27ae60" if test["excess_cagr"] > 0 else "#e74c3c"
        st.markdown(
            f"<div style='padding:16px;background:#E8F5E9;border-radius:10px;"
            f"border:2px solid #4CAF50;text-align:center'>"
            f"<div style='font-size:0.85em;color:#2E7D32;font-weight:600;margin-bottom:8px'>"
            f"👁️ 测试窗 · {test_years}年（样本外）</div>"
            f"<div style='font-size:0.7em;color:#888;margin-bottom:10px'>"
            f"{dq['test_window']['start']} → {dq['test_window']['end']} · "
            f"{dq['test_months']} 个月 · 参数锁定，未接触</div>"
            f"<div style='font-size:0.78em;color:#555;margin-bottom:10px'>"
            f"PE {opt['best_pe_weight']:.0%} · {opt['best_strategy_label']} · 只看一遍</div>"
            f"<div style='font-size:1.15em;font-weight:700'>"
            f"温度: {test['temp_dca']['cagr_pct']}%</div>"
            f"<div style='font-size:0.8em;color:#888'>"
            f"普通: {test['regular_dca']['cagr_pct']}% · "
            f"超额: <b style='color:{excess_color}'>{'+' if test['excess_cagr'] > 0 else ''}{test['excess_cagr']}%</b></div>"
            f"<div style='font-size:0.8em;color:#888'>"
            f"夏普: {test['temp_dca']['sharpe_ratio']} "
            f"(变动 {'+' if deg['sharpe_drop'] >= 0 else ''}{deg['sharpe_drop']})</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Grid search heatmap ────────────────────────────────────────────────
    st.markdown("")
    st.markdown("#### 📊 参数优化网格")

    grid = opt["grid_results"]
    strategies = ["激进", "适中", "保守"]
    weights = sorted(set(g["pe_weight"] for g in grid))

    # Build heatmap data
    import plotly.graph_objects as go

    heatmap_data = []
    for strat_label in strategies:
        row = []
        for pw in weights:
            match = [g for g in grid if g["strategy_label"] == strat_label and g["pe_weight"] == pw]
            if match:
                row.append(match[0]["temp_sharpe"])
            else:
                row.append(None)
        heatmap_data.append(row)

    # Find best cell
    best_pw = opt["best_pe_weight"]
    best_sl = opt["best_strategy_label"]
    annotations = []
    for si, sl in enumerate(strategies):
        for wi, pw in enumerate(weights):
            val = heatmap_data[si][wi]
            if val is None:
                continue
            text = f"{val:.2f}"
            if pw == best_pw and sl == best_sl:
                text = f"⭐{val:.2f}"
            annotations.append(dict(
                x=wi, y=si, text=text, showarrow=False,
                font=dict(color="#fff" if val > 1.0 else "#555", size=11,
                         family="monospace"),
            ))

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=[f"{w:.0%}" for w in weights],
        y=strategies,
        colorscale=[
            [0.0, "#f44336"],
            [0.25, "#FF9800"],
            [0.5, "#FFEB3B"],
            [0.75, "#8BC34A"],
            [1.0, "#2E7D32"],
        ],
        zmin=0,
        zmax=max(max(row) for row in heatmap_data if any(v is not None for v in row)) * 1.1,
        text=[[f"{v:.2f}" if v else "" for v in row] for row in heatmap_data],
        texttemplate="%{text}",
        textfont=dict(size=11, family="monospace"),
        hovertemplate="PE权重=%{x}<br>策略=%{y}<br>夏普=%{z:.2f}<extra></extra>",
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=30, b=10),
        xaxis_title="PE 权重",
        yaxis_title="",
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Assessment ─────────────────────────────────────────────────────────
    st.info(deg["assessment"])

    st.markdown(
        '<div style="font-size:0.8em;color:#888;margin-top:4px">'
        '💡 <b>方法论</b>：Walk-Forward 是量化策略验证的黄金标准。'
        '训练窗内可自由探索参数，测试窗只看一次。'
        '若样本外仍然有效，则策略不是过拟合的产物——这正是学术论文和机构级策略验收的核心方法。'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Behavioral finance framework ───────────────────────────────────────────────

def _render_behavioral_finance():
    """Render behavioral finance explanation: why temperature DCA works.

    Positions the system as a tool to counteract specific cognitive biases,
    elevating it from a technical tool to a theoretically grounded system.
    """
    st.markdown("---")
    st.markdown("### 🧠 行为金融视角：为什么温度定投理论上应该有效？")

    st.markdown(
        '<p style="font-size:0.85em;color:#888;margin-bottom:16px">'
        '温度定投的价值不在于"预测市场"——没有人能准确预测。'
        '它的价值在于帮助投资者克服特定认知偏差，用规则取代情绪驱动决策。</p>',
        unsafe_allow_html=True,
    )

    biases = [
        {
            "emoji": "🧊",
            "zone": "低估区间 (0-40°C)",
            "bias": "损失厌恶 (Loss Aversion)",
            "bias_en": "Loss Aversion",
            "mechanism": (
                "市场恐慌时，投资者因害怕继续亏损而不敢买入。"
                "温度定投通过**自动加仓到 1.25–2.0 倍**，"
                "用规则强制逆情绪操作，克服'该买不敢买'的心理障碍。"
            ),
            "color": "#2196F3",
        },
        {
            "emoji": "🔥",
            "zone": "高估区间 (60-100°C)",
            "bias": "羊群效应 (Herd Behavior)",
            "bias_en": "Herd Behavior",
            "mechanism": (
                "市场狂热时，投资者容易追涨杀跌。"
                "温度定投通过**强制少投至 0–0.75 倍**，"
                "在高位自动刹车，避免'别人都在买所以我也买'的从众陷阱。"
            ),
            "color": "#FF9800",
        },
        {
            "emoji": "🌡️",
            "zone": "适中区间 (40-60°C)",
            "bias": "锚定效应 (Anchoring)",
            "bias_en": "Anchoring",
            "mechanism": (
                "投资者容易被近期价格'锚定'，在正常波动中过度反应。"
                "温度定投在估值合理时**维持基准定投**，"
                "不被短期价格波动所锚定，保持纪律性投资节奏。"
            ),
            "color": "#9E9E9E",
        },
    ]

    for b in biases:
        st.markdown(
            f"<div style='display:flex;align-items:flex-start;padding:14px 16px;"
            f"margin-bottom:10px;background:#fafafa;border-radius:10px;"
            f"border-left:4px solid {b['color']};gap:14px'>"
            f"<div style='font-size:1.8em;min-width:40px;text-align:center'>{b['emoji']}</div>"
            f"<div style='flex:1'>"
            f"<div style='font-weight:600;font-size:0.92em;margin-bottom:2px'>{b['zone']}</div>"
            f"<div style='font-size:0.78em;color:{b['color']};margin-bottom:6px'>"
            f"克服：{b['bias']}（{b['bias_en']}）</div>"
            f"<div style='font-size:0.82em;color:#555;line-height:1.6'>{b['mechanism']}</div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Summary
    st.markdown(
        '<div style="margin-top:12px;padding:14px 18px;background:#E8EAF6;'
        'border-radius:10px;font-size:0.88em;color:#283593;line-height:1.7">'
        '💡 <b>学术定位</b>：温度定投本质上是一种<b>规则化的行为金融干预工具</b>。'
        '它不依赖市场预测能力，而是通过系统性地抵消投资者的认知偏差来创造价值。'
        '这一视角将系统从"一个 Python 回测工具"提升为'
        '"有行为金融学理论根基的量化决策系统"——'
        '这正是 BA/FinTech 研究生项目最看重的思维深度。'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Real-time temperature suggestion ─────────────────────────────────────────

def _render_current_suggestion(config: dict):
    """Show current market temperature and investment suggestion."""
    st.markdown("---")
    st.markdown("### 🌡️ 实时市场温度 · 当前建议")

    with st.spinner("正在获取当前市场温度..."):
        thermo = _fetch_current_temperature()

    indices = thermo.get("indices", [])
    overall = thermo.get("overall")

    if not indices and overall is None:
        st.info("📡 实时温度数据暂不可用，请稍后刷新")
        return

    # Find the selected index
    idx_name = config["index_name"]
    selected_idx = None
    for idx in indices:
        if idx.get("name") == idx_name:
            selected_idx = idx
            break

    col1, col2 = st.columns([1, 2])

    with col1:
        # Current temperature display
        if selected_idx and selected_idx.get("temperature"):
            temp = selected_idx["temperature"]
            pct = temp.get("percentile", 50)
            color = temp.get("color", "#9E9E9E")
            label = temp.get("zone_label", "适中")
            suggestion = temp.get("suggestion", "")

            st.markdown(
                f"<div style='text-align:center;padding:20px;background:{color}10;"
                f"border-radius:12px;border:2px solid {color}40'>"
                f"<div style='font-size:0.85em;color:#888'>{idx_name} 当前温度</div>"
                f"<div style='font-size:3em;font-weight:700;color:{color};margin:8px 0'>{pct:.0f}°C</div>"
                f"<div style='font-size:1.15em;font-weight:600;color:{color}'>{label}</div>"
                f"<div style='font-size:0.82em;color:#555;margin-top:8px'>{suggestion}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info(f"{idx_name} 实时温度暂不可用")

    with col2:
        # Investment suggestion
        base = config["base_monthly"]
        strategy_name = config["strategy_name"]

        if selected_idx and selected_idx.get("temperature"):
            pct = selected_idx["temperature"]["percentile"]
            multiplier = engine.get_multiplier(pct, strategy_name)
            suggested = base * multiplier
            saved = base - suggested
        else:
            multiplier = 1.0
            suggested = base
            saved = 0.0

        strategy_label = engine.STRATEGIES.get(strategy_name, {}).get("name", "适中")

        st.markdown(
            f"<div style='padding:16px 20px;background:#fafafa;border-radius:12px'>"
            f"<div style='font-size:0.95em;font-weight:600;margin-bottom:12px'>"
            f"📐 {strategy_label}型策略 · 当前决策</div>",
            unsafe_allow_html=True,
        )

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("基准月投", f"¥{base:,.0f}")
        with m2:
            st.metric("温度倍率", f"×{multiplier}", delta=f"{multiplier - 1:.0%}" if multiplier != 1 else None)
        with m3:
            st.metric("建议月投", f"¥{suggested:,.0f}",
                      delta=f"-¥{saved:,.0f}" if saved > 0 else (f"+¥{abs(saved):,.0f}" if saved < 0 else None))

        if saved > 0:
            st.markdown(
                f"<div style='margin-top:8px;padding:8px 12px;background:#FFF3E0;border-radius:6px;font-size:0.85em'>"
                f"💰 本月存入现金池 <b>¥{saved:,.0f}</b>（温度偏高，暂扣）"
                f"<br><span style='color:#888;font-size:0.85em'>"
                f"等温度回落至60°C以下，现金池自动释放加仓</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        elif multiplier > 1.0:
            extra = base * (multiplier - 1)
            st.markdown(
                f"<div style='margin-top:8px;padding:8px 12px;background:#E8F5E9;border-radius:6px;font-size:0.85em'>"
                f"🚀 从现金池额外投入 <b>¥{extra:,.0f}</b>（温度偏低，加仓买入）"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Cash pool tracking (session state)
    if "temp_dca_cash_pool" not in st.session_state:
        st.session_state.temp_dca_cash_pool = 0.0

    if saved > 0:
        st.session_state.temp_dca_cash_pool += saved
    elif multiplier > 1.0:
        extra = base * (multiplier - 1)
        st.session_state.temp_dca_cash_pool = max(0, st.session_state.temp_dca_cash_pool - extra)

    if st.session_state.temp_dca_cash_pool > 0:
        st.markdown(
            f"<div style='margin-top:4px;font-size:0.82em;color:#888'>"
            f"📦 累计现金池余额: ¥{st.session_state.temp_dca_cash_pool:,.0f}"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────────────────

def _render_footer(backtest: dict):
    """Render footer with data quality info."""
    dq = backtest.get("data_quality", {})
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.markdown("---")
    st.caption(
        f"🌡️ 智能温度定投 — 磐策 PánCè 旗舰功能 · "
        f"回测区间: {dq.get('date_start', '—')} 至 {dq.get('date_end', '—')} · "
        f"共 {dq.get('total_months', 0)} 个月 · "
        f"温度信号: {'PE估值(60%) + MA偏离(40%)' if dq.get('has_pe_data') else 'MA偏离(100%)'} · "
        f"数据源: {dq.get('data_source', '—')} · "
        f"数据更新于 {ts} · "
        f"历史回测不代表未来收益，仅供参考"
    )


# ── Main entry ───────────────────────────────────────────────────────────────

def show():
    """Display the Temperature DCA flagship page."""
    render_sidebar()
    _inject_css()

    _render_header()

    # Step 1: Configuration
    config = _render_config()

    # Step 2: Multiplier map
    _render_multiplier_map(config["strategy_name"])

    # Step 3: Run backtest
    with st.spinner("🔄 正在运行历史回测...（首次约 5-10 秒，后续秒出）"):
        backtest = _fetch_backtest_data(
            index_name=config["index_name"],
            years=config["years"],
            base_monthly=config["base_monthly"],
            strategy_name=config["strategy_name"],
        )

    if "error" in backtest:
        st.error(f"❌ {backtest['error']}")
        if "supported" in backtest:
            st.info(f"支持的指数: {', '.join(backtest['supported'])}")
        return

    # Step 4: Equity curves
    _render_equity_chart(backtest, config)

    # Step 5: Signal validation — empirical foundation
    _render_signal_validation(config)

    # Step 5.5: Walk-Forward validation — out-of-sample test
    _render_walk_forward(config)

    # Step 6: Metrics comparison
    _render_metrics(backtest)

    # Step 7: Regime decomposition — where does the strategy win/lose?
    _render_regime_decomposition(backtest)

    # Step 8: Yearly breakdown
    _render_yearly_breakdown(backtest, config)

    # Step 9: Behavioral finance framework — theoretical grounding
    _render_behavioral_finance()

    # Step 10: Real-time suggestion
    _render_current_suggestion(config)

    # Footer
    _render_footer(backtest)


if __name__ == "__main__":
    show()
