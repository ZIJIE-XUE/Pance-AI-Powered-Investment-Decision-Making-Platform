"""Market Thermometer page.

Part of the Market Dashboard module (市场仪表盘).
Shows PE valuation + price-MA-deviation temperature for A-share indices,
rendered as intuitive temperature gauges with investment suggestions.
"""

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from src.ui.components.sidebar import render_sidebar

# ── Constants ────────────────────────────────────────────────────────────────

RED_UP = "#e74c3c"
GREEN_DOWN = "#27ae60"


# ── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_temperature_cached() -> dict:
    """Fetch market temperature data. Cached 24 hours (daily update)."""
    from src.engine.market_thermometer import fetch_market_temperature

    try:
        return fetch_market_temperature(years=5)
    except Exception:
        return {"indices": [], "overall": None, "timestamp": datetime.now()}


# ── Header ───────────────────────────────────────────────────────────────────

def _render_header():
    """Render page title and description."""
    st.title("🌡️ 市场温度计")
    st.markdown(
        "<p style='color:#888;font-size:0.95em'>"
        "综合 PE 估值 + 价格偏离均线，判断当前 A 股市场冷热 · "
        "数据每天自动更新 · PE 来源：中证指数官网 · "
        "覆盖上证50 / 沪深300 / 中证500 / 中证1000"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")


# ── Row 1: Index temperature cards ───────────────────────────────────────────

def _render_temperature_cards(indices: list[dict]):
    """Render 4 index temperature cards in a row."""
    st.markdown("### 📊 指数估值温度")

    cols = st.columns(4, gap="small")

    for i, idx in enumerate(indices):
        with cols[i]:
            _render_single_card(idx)


def _render_single_card(idx: dict):
    """Render a single index temperature card."""
    name = idx.get("name", "--")
    desc = idx.get("desc", "")
    error = idx.get("error")
    pe_current = idx.get("pe_current")
    ma_dev = idx.get("ma_deviation_pct")
    temp = idx.get("temperature")
    pe_score = idx.get("pe_score")
    ma_score = idx.get("ma_score")

    with st.container(border=True):
        # Index name + description
        st.markdown(
            f"<div style='font-size:0.9em;font-weight:600'>{name}</div>"
            f"<div style='font-size:0.7em;color:#888;margin-bottom:6px'>{desc}</div>",
            unsafe_allow_html=True,
        )

        if error or temp is None:
            st.markdown(
                "<div style='color:#bbb;font-size:0.85em;padding:12px 0'>"
                "数据暂不可用</div>",
                unsafe_allow_html=True,
            )
            return

        # PE value
        if pe_current is not None:
            st.markdown(
                f"<div style='margin-top:2px'>"
                f"<span style='font-size:0.7em;color:#888'>PE(TTM) </span>"
                f"<span style='font-size:1.05em;font-weight:600'>{pe_current:.1f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # MA deviation
        if ma_dev is not None:
            ma_color = RED_UP if ma_dev > 0 else GREEN_DOWN
            sign = "+" if ma_dev > 0 else ""
            st.markdown(
                f"<div style='margin-bottom:2px'>"
                f"<span style='font-size:0.7em;color:#888'>偏离200日均线 </span>"
                f"<span style='font-size:0.9em;font-weight:600;color:{ma_color}'>{sign}{ma_dev:.1f}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Temperature zone
        color = temp.get("color", "#9E9E9E")
        label = temp.get("zone_label", "--")
        pct_val = temp.get("percentile", 50.0)

        st.markdown(
            f"<div style='font-size:1.1em;font-weight:600;color:{color};margin:6px 0'>"
            f"{label}</div>",
            unsafe_allow_html=True,
        )

        # Progress bar
        _render_temp_bar(pct_val, color)

        st.markdown(
            f"<div style='font-size:0.75em;color:#888;margin-top:2px'>"
            f"综合温度 <b>{pct_val:.0f}°C</b>"
            f"<span style='font-size:0.65em;color:#bbb;margin-left:4px'>"
            f"(PE={pe_score:.0f}° · MA={ma_score:.0f}°)</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Suggestion
        suggestion = temp.get("suggestion", "")
        st.markdown(
            f"<div style='font-size:0.78em;color:#555;margin-top:6px;"
            f"padding:6px 8px;background:#f8f9fa;border-radius:6px'>"
            f"💡 {suggestion}</div>",
            unsafe_allow_html=True,
        )


def _render_temp_bar(pct: float, color: str):
    """Render a custom colored progress bar using HTML/CSS."""
    html = (
        f"<div style='background:#e9ecef;border-radius:4px;height:8px;width:100%'>"
        f"<div style='background:{color};border-radius:4px;height:8px;"
        f"width:{pct:.0f}%;transition:width 0.3s'></div>"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ── Row 2: PE history chart ──────────────────────────────────────────────────

def _render_pe_chart(indices: list[dict]):
    """Render PE history chart with zone bands for a selected index."""
    st.markdown("---")
    st.markdown("### 📈 PE 估值走势")

    valid_indices = [
        idx for idx in indices
        if idx.get("pe_history") is not None
    ]

    if not valid_indices:
        st.info("📡 PE 历史数据暂不可用（中证指数官网仅提供近20个交易日数据）")
        return

    names = [idx["name"] for idx in valid_indices]
    selected_name = st.selectbox(
        "选择指数",
        options=names,
        label_visibility="collapsed",
        key="pe_chart_index",
    )

    selected = next((idx for idx in valid_indices if idx["name"] == selected_name), valid_indices[0])
    pe_df = selected.get("pe_history")

    if pe_df is None or pe_df.empty:
        st.info("📡 该指数 PE 历史数据暂不可用")
        return

    pe_values = pe_df["pe"].dropna()
    if len(pe_values) < 2:
        st.info("📡 PE 数据点不足，无法绘制走势图")
        return

    current_pe = selected.get("pe_current", pe_values.iloc[-1])

    fig = go.Figure()

    # PE history line
    fig.add_trace(go.Scatter(
        x=pe_df["date"],
        y=pe_df["pe"],
        mode="lines+markers",
        line=dict(color="#37474F", width=2),
        marker=dict(size=4),
        name="PE (TTM)",
        hovertemplate="%{x|%Y-%m-%d}<br>PE: %{y:.2f}<extra></extra>",
    ))

    # Current PE annotation
    fig.add_hline(
        y=current_pe,
        line_dash="dash",
        line_color=RED_UP,
        line_width=1.5,
        annotation_text=f"当前: {current_pe:.1f}",
        annotation_position="top right",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="",
        yaxis_title="市盈率 (PE)",
        hovermode="x unified",
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.caption("💡 PE数据来自中证指数官网，每日盘后更新。走势图展示近20个交易日。")


# ── Row 3: Price vs MA chart ─────────────────────────────────────────────────

def _render_price_chart(indices: list[dict]):
    """Render price vs 200MA chart for a selected index."""
    st.markdown("---")
    st.markdown("### 📊 价格偏离均线")

    valid_indices = [
        idx for idx in indices
        if idx.get("price_history") is not None
    ]

    if not valid_indices:
        st.info("📡 价格数据暂不可用")
        return

    names = [idx["name"] for idx in valid_indices]
    selected_name = st.selectbox(
        "选择指数",
        options=names,
        label_visibility="collapsed",
        key="price_chart_index",
    )

    selected = next((idx for idx in valid_indices if idx["name"] == selected_name), valid_indices[0])
    price_df = selected.get("price_history")

    if price_df is None or price_df.empty:
        st.info("📡 该指数价格数据暂不可用")
        return

    # Price line
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=price_df["date"],
        y=price_df["close"],
        mode="lines",
        line=dict(color="#37474F", width=1.5),
        name="收盘价",
        hovertemplate="%{x|%Y-%m-%d}<br>收盘: %{y:.0f}<extra></extra>",
    ))

    # 200MA line
    ma_data = price_df.dropna(subset=["ma200"])
    if not ma_data.empty:
        fig.add_trace(go.Scatter(
            x=ma_data["date"],
            y=ma_data["ma200"],
            mode="lines",
            line=dict(color="#FF9800", width=1.8, dash="dash"),
            name="200日均线",
            hovertemplate="%{x|%Y-%m-%d}<br>200MA: %{y:.0f}<extra></extra>",
        ))

    ma_dev = selected.get("ma_deviation_pct", 0)
    dev_color = RED_UP if ma_dev > 0 else GREEN_DOWN
    sign = "+" if ma_dev > 0 else ""

    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="",
        yaxis_title="指数点位",
        hovermode="x unified",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        f"<p style='font-size:0.85em;color:#888'>"
        f"当前偏离200日均线: <span style='color:{dev_color};font-weight:600'>{sign}{ma_dev:.1f}%</span> · "
        f"价格高于均线 → 可能偏热 · 价格低于均线 → 可能偏冷</p>",
        unsafe_allow_html=True,
    )


# ── Row 4: Overall temperature ──────────────────────────────────────────────

def _render_overall(overall: dict, indices: list[dict]):
    """Render the combined market temperature summary card."""
    st.markdown("---")
    st.markdown("### 📊 A 股综合温度")

    if overall is None:
        st.info("📡 综合温度数据暂不可用")
        return

    pct = overall.get("percentile", 50)
    color = overall.get("color", "#9E9E9E")
    label = overall.get("zone_label", "--")
    suggestion = overall.get("suggestion", "")

    col_vis, col_text = st.columns([1, 2])

    with col_vis:
        _render_gauge(pct, color, label)

    with col_text:
        st.markdown(
            f"<div style='font-size:1.6em;font-weight:700;color:{color};margin-top:12px'>"
            f"综合温度 {pct:.0f}°C — {label}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='font-size:1.05em;color:#555;margin-top:12px;line-height:1.7'>"
            f"💡 {suggestion}</p>",
            unsafe_allow_html=True,
        )

        # Methodology note
        st.markdown(
            "<p style='font-size:0.8em;color:#888;margin-top:8px'>"
            "温度构成：PE估值（权重60%）+ 价格偏离200日均线（权重40%）</p>",
            unsafe_allow_html=True,
        )

        breakdown_parts = []
        for idx in indices:
            temp = idx.get("temperature")
            if temp:
                p = temp.get("percentile", 50)
                tc = temp.get("color", "#888")
                breakdown_parts.append(
                    f"{idx['name']} <span style='color:{tc}'>{p:.0f}°C</span>"
                )
        if breakdown_parts:
            st.markdown(
                "<p style='font-size:0.8em;color:#555'>"
                + " · ".join(breakdown_parts) + "</p>",
                unsafe_allow_html=True,
            )


def _render_gauge(pct: float, color: str, label: str):
    """Render a half-circle gauge chart for overall temperature."""
    # Background arc
    fig = go.Figure()

    # Full background arc
    theta_vals = [i * 1.8 for i in range(101)]
    fig.add_trace(go.Scatterpolar(
        r=[1] * 101,
        theta=theta_vals,
        mode="lines",
        line=dict(color="#e9ecef", width=14),
        hoverinfo="skip",
        showlegend=False,
    ))

    # Filled arc
    filled_steps = max(int(pct), 1)
    if filled_steps > 0:
        fig.add_trace(go.Scatterpolar(
            r=[1] * (filled_steps + 1),
            theta=[i * 1.8 for i in range(filled_steps + 1)],
            mode="lines",
            line=dict(color=color, width=14),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Center text
    fig.add_annotation(
        x=0, y=0.2,
        text=f"<b style='font-size:30px;color:{color}'>{pct:.0f}°C</b><br>"
             f"<span style='font-size:12px;color:#888'>{label}</span>",
        showarrow=False,
    )

    # Cold/Hot labels
    fig.add_annotation(x=-0.65, y=0.95, text="🧊 0°", showarrow=False, font=dict(size=10, color="#2196F3"))
    fig.add_annotation(x=0.65, y=0.95, text="💥 100°", showarrow=False, font=dict(size=10, color="#f44336"))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 1.3]),
            angularaxis=dict(visible=False, direction="clockwise"),
        ),
        height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Main entry ───────────────────────────────────────────────────────────────

def show():
    """Display the Market Thermometer page."""
    render_sidebar()

    _render_header()

    with st.spinner("🌡️ 正在计算市场温度...（首次约 5-10 秒，后续秒出）"):
        data = _fetch_temperature_cached()

    indices = data.get("indices", [])
    overall = data.get("overall")

    # Row 1: Index temperature cards
    _render_temperature_cards(indices)

    # Row 2: PE history chart
    _render_pe_chart(indices)

    # Row 3: Price vs 200MA chart
    _render_price_chart(indices)

    # Row 4: Overall temperature gauge
    _render_overall(overall, indices)

    # Footer
    st.markdown("---")
    ts = data.get("timestamp")
    time_str = ts.strftime("%Y-%m-%d %H:%M") if isinstance(ts, datetime) else ""
    st.caption(
        "🌡️ 市场温度计 — 磐策 PánCè · "
        "温度 = PE估值(60%) + 价格偏离200日均线(40%) · "
        "PE数据来源：中证指数官网 csindex.com.cn · "
        "仅供参考，不构成投资建议。"
        f" · 数据更新于 {time_str}"
    )


if __name__ == "__main__":
    show()
