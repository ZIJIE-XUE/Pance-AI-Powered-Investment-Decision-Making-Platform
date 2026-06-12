"""Market Dashboard page.

Third independent module of 磐策 PánCè.
Displays real-time market data: index quotes, sector heatmap,
macro indicators, and ETF movers — broker-app quality.

Uses split caching: price data refreshes every 2 min (fast via Yahoo),
sparklines and ETF movers cache for 1 hour (slow via AKShare).
"""

import logging
import yaml
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.ui.components.sidebar import render_sidebar

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

RED_UP = "#e74c3c"      # Chinese convention: red = up
GREEN_DOWN = "#27ae60"  # Chinese convention: green = down
CARD_BG = "#fafbfc"


# ── Data loading ─────────────────────────────────────────────────────────────

def _load_asset_universe() -> list[dict]:
    """Load asset universe from risk_weights.yaml."""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "risk_weights.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assets = []
    for cls_name, items in config.get("asset_universe", {}).items():
        for item in items:
            item["_class"] = cls_name
            assets.append(item)
    return assets


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_snapshot_cached() -> dict:
    """Fast cache: index prices, sectors, macro indicators.

    TTL = 2 minutes. Cleared on refresh button.
    Uses Yahoo Finance for index prices (~2-3 seconds).
    """
    from src.engine.market_data import fetch_market_snapshot

    assets = _load_asset_universe()
    try:
        return fetch_market_snapshot(assets)
    except Exception as e:
        logger.error("snapshot_fetch_failed", error=str(e))
        return {
            "indices": [],
            "sectors": None,
            "macro": {},
            "timestamp": datetime.now(),
        }


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_history_cached() -> dict:
    """Slow cache: sparklines and ETF movers.

    TTL = 1 hour. NOT cleared on refresh button.
    Sparklines and 5-day ETF returns don't need real-time updates.
    """
    from src.engine.market_data import fetch_market_history

    assets = _load_asset_universe()
    try:
        return fetch_market_history(assets)
    except Exception as e:
        logger.error("history_fetch_failed", error=str(e))
        return {
            "sparklines": {},
            "etf_movers": [],
            "timestamp": datetime.now(),
        }


# ── Mini sparkline ───────────────────────────────────────────────────────────

def _create_sparkline(values: list[float], is_positive: bool) -> go.Figure:
    """Create a tiny sparkline chart (60px, no axes, no interactivity).

    Args:
        values: List of close prices.
        is_positive: True for upward trend (red), False for downward (green).

    Returns:
        Plotly Figure configured as a sparkline.
    """
    if not values or len(values) < 2:
        return go.Figure()

    color = RED_UP if is_positive else GREEN_DOWN
    fill_rgba = "rgba(231,76,60,0.12)" if is_positive else "rgba(39,174,96,0.12)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode="lines",
        line=dict(color=color, width=1.4),
        fill="tozeroy",
        fillcolor=fill_rgba,
        hoverinfo="none",
    ))
    fig.update_layout(
        height=55,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, showgrid=False, fixedrange=True),
        yaxis=dict(visible=False, showgrid=False, fixedrange=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        dragmode=False,
    )
    return fig


# ── Header ───────────────────────────────────────────────────────────────────

def _render_header():
    """Render the page header with title, refresh button, and timestamp."""
    col_title, col_btn, col_time = st.columns([3, 1, 1.5])

    with col_title:
        st.title("📊 市场仪表盘")
        st.caption("实时市场数据概览 · 数据来源：AKShare & Yahoo Finance")

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)  # vertical alignment spacer
        if st.button("🔄 刷新行情", type="primary", use_container_width=True,
                     help="立即更新指数价格和宏观指标（走势图和ETF涨跌榜每小时更新一次）"):
            _fetch_snapshot_cached.clear()
            st.rerun()

    with col_time:
        st.markdown("<br>", unsafe_allow_html=True)
        data = _fetch_snapshot_cached()
        ts = data.get("timestamp")
        if ts:
            time_str = ts.strftime("%H:%M:%S") if isinstance(ts, datetime) else str(ts)
            st.markdown(
                f"<div style='text-align:right;padding-top:8px;color:#888;font-size:0.85em'>"
                f"🕐 行情更新于 {time_str}</div>",
                unsafe_allow_html=True,
            )


# ── Row 1: Index ticker cards ────────────────────────────────────────────────

def _render_index_cards(indices: list[dict]):
    """Render a responsive grid of index ticker cards with sparklines.

    Each card shows: name, price, change (colored), mini sparkline.
    Layout: 5 cards per row (A-share) then 5 cards (global) on desktop.
    """
    st.markdown("---")
    st.markdown("### 🏛️ 主要指数")

    if not indices:
        st.info("📡 指数数据暂不可用，请点击刷新按钮重试")
        return

    # Split into rows of 5
    cards_per_row = 5
    for row_start in range(0, len(indices), cards_per_row):
        row_indices = indices[row_start:row_start + cards_per_row]
        cols = st.columns(cards_per_row, gap="small")

        for i, idx in enumerate(row_indices):
            with cols[i]:
                _render_single_card(idx)


def _render_single_card(idx: dict):
    """Render a single index card using st.container with border.

    Args:
        idx: Dict with name, price, change, change_pct, sparkline, error.
    """
    with st.container(border=True):
        # Index name
        st.markdown(
            f"<div style='font-size:0.8em;color:#888;margin-bottom:2px'>{idx['name']}</div>",
            unsafe_allow_html=True,
        )

        error = idx.get("error")
        if error or idx.get("price") is None:
            st.markdown(
                f"<div style='font-size:1.1em;font-weight:bold;color:#999'>--</div>"
                f"<div style='font-size:0.7em;color:#bbb'>数据获取失败</div>",
                unsafe_allow_html=True,
            )
            return

        # Price
        price = idx["price"]
        if price >= 100:
            price_str = f"{price:,.2f}"
        else:
            price_str = f"{price:,.4f}"

        st.markdown(
            f"<div style='font-size:1.2em;font-weight:bold;margin:4px 0'>{price_str}</div>",
            unsafe_allow_html=True,
        )

        # Change (colored — Chinese convention)
        change = idx.get("change") or 0
        change_pct = idx.get("change_pct") or 0
        is_up = change >= 0
        color = RED_UP if is_up else GREEN_DOWN
        arrow = "▲" if is_up else "▼"

        st.markdown(
            f"<div style='font-size:0.85em;color:{color};margin-bottom:6px'>"
            f"{arrow} {abs(change):,.2f} ({abs(change_pct):.2f}%)</div>",
            unsafe_allow_html=True,
        )

        # Sparkline
        sparkline = idx.get("sparkline", [])
        if sparkline and len(sparkline) >= 2:
            fig = _create_sparkline(sparkline, is_up)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Row 2: Sector heatmap ────────────────────────────────────────────────────

def _render_sector_heatmap(sectors: pd.DataFrame):
    """Render sector performance as a treemap + optional detail table.

    Args:
        sectors: DataFrame with columns name, change_pct, price, volume, etc.
    """
    st.markdown("---")
    st.markdown("### 🏭 行业板块表现")

    if sectors is None or sectors.empty:
        st.info("📡 行业板块数据暂不可用")
        return

    # Prepare data
    df = sectors.copy()
    # Limit to top 40 sectors for readability
    if len(df) > 40:
        df = df.head(40)

    # Ensure we have the needed columns
    if "name" not in df.columns or "change_pct" not in df.columns:
        st.info("📡 行业数据格式异常，请稍后重试")
        return

    # Treemap
    volume_col = "volume" if "volume" in df.columns else None

    fig = px.treemap(
        df,
        path=[px.Constant("全部板块"), "name"],
        values=volume_col,
        color="change_pct",
        color_continuous_scale=[
            [0.0, GREEN_DOWN],
            [0.35, "#e8e8e8"],
            [0.5, "#f5f5f5"],
            [0.65, "#e8e8e8"],
            [1.0, RED_UP],
        ],
        color_continuous_midpoint=0,
        range_color=[-5, 5],
        hover_data={"change_pct": ":.2f%", "price": ":.2f"} if "price" in df.columns else {"change_pct": ":.2f%"},
    )

    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[0]:+.2f}%",
        textposition="middle center",
        textfont_size=14,
        hovertemplate="<b>%{label}</b><br>涨跌幅: %{color:+.2f}%<br>最新价: %{customdata[1]:.2f}<extra></extra>",
        marker=dict(cornerradius=4),
    )

    fig.update_layout(
        height=450,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="涨跌幅 %",
            tickformat="+.1f",
            len=0.5,
            y=0.5,
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Expandable detail table
    with st.expander("📋 查看全部行业排名"):
        display_cols = ["name", "change_pct"]
        if "price" in df.columns:
            display_cols.append("price")
        if "volume" in df.columns:
            display_cols.append("volume")

        display_df = df[display_cols].copy()
        col_labels = {"name": "板块名称", "change_pct": "涨跌幅 (%)", "price": "最新价", "volume": "成交量"}
        display_df = display_df.rename(columns=col_labels)

        # Format percentages
        if "涨跌幅 (%)" in display_df.columns:
            display_df["涨跌幅 (%)"] = display_df["涨跌幅 (%)"].apply(
                lambda x: f"{x:+.2f}%" if pd.notna(x) else "--"
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400,
        )


# ── Row 3: Macro indicator cards ─────────────────────────────────────────────

def _render_macro_cards(macro: dict):
    """Render macro indicator cards in a single row.

    Args:
        macro: Dict keyed by indicator id, each with name, value, change,
               change_pct, unit, error.
    """
    st.markdown("---")
    st.markdown("### 🌍 宏观指标")

    if not macro:
        st.info("📡 宏观数据暂不可用")
        return

    # Define display order
    order = ["gold", "oil", "us10y", "usdcny", "vix"]
    cols = st.columns(5, gap="small")

    for i, key in enumerate(order):
        data = macro.get(key, {})
        with cols[i]:
            _render_macro_card(data)


def _render_macro_card(data: dict):
    """Render a single macro indicator card."""
    with st.container(border=True):
        name = data.get("name", "--")
        value = data.get("value")
        unit = data.get("unit", "")
        change = data.get("change")
        change_pct = data.get("change_pct")

        # Name
        st.markdown(
            f"<div style='font-size:0.75em;color:#888;margin-bottom:4px'>{name}</div>",
            unsafe_allow_html=True,
        )

        if value is None:
            st.markdown(
                f"<div style='font-size:1.1em;font-weight:bold;color:#999'>--</div>",
                unsafe_allow_html=True,
            )
            return

        # Value
        st.markdown(
            f"<div style='font-size:1.3em;font-weight:bold;margin:2px 0'>{value}{unit}</div>",
            unsafe_allow_html=True,
        )

        # Change
        if change is not None and change_pct is not None:
            is_up = change >= 0
            color = RED_UP if is_up else GREEN_DOWN
            arrow = "▲" if is_up else "▼"
            st.markdown(
                f"<div style='font-size:0.85em;color:{color}'>"
                f"{arrow} {abs(change):.2f} ({abs(change_pct):.2f}%)</div>",
                unsafe_allow_html=True,
            )
        elif data.get("error"):
            st.markdown(
                f"<div style='font-size:0.7em;color:#bbb'>加载失败</div>",
                unsafe_allow_html=True,
            )


# ── Row 4: ETF movers ────────────────────────────────────────────────────────

def _render_etf_movers(movers: list[dict]):
    """Render ETF top gainers and losers side by side.

    Args:
        movers: List of dicts with ticker, name, asset_class, price, change_pct.
    """
    st.markdown("---")
    st.markdown("### 📈 ETF 涨跌榜")
    st.caption("基于5日累计收益排名")

    if not movers:
        st.info("📡 ETF 数据暂不可用")
        return

    # Separate gainers and losers
    gainers = [m for m in movers if m["change_pct"] > 0][:8]
    losers = [m for m in movers if m["change_pct"] < 0][:8]
    losers = sorted(losers, key=lambda x: x["change_pct"])  # worst first

    col_g, col_l = st.columns(2)

    with col_g:
        st.markdown("#### 🔴 涨幅榜")
        if not gainers:
            st.caption("暂无上涨ETF")
        for rank, etf in enumerate(gainers, 1):
            _render_mover_row(rank, etf)

    with col_l:
        st.markdown("#### 🟢 跌幅榜")
        if not losers:
            st.caption("暂无下跌ETF")
        for rank, etf in enumerate(losers, 1):
            _render_mover_row(rank, etf)


def _render_mover_row(rank: int, etf: dict):
    """Render a single row in the ETF movers list.

    Args:
        rank: Rank number (1-8).
        etf: Dict with ticker, name, change_pct, asset_class.
    """
    change_pct = etf.get("change_pct", 0) or 0
    is_up = change_pct >= 0
    color = RED_UP if is_up else GREEN_DOWN
    arrow = "▲" if is_up else "▼"

    asset_class = etf.get("asset_class", "")
    class_emoji = {
        "equity": "📈",
        "bond": "📊",
        "gold": "🥇",
        "real_estate": "🏠",
    }.get(asset_class, "💹")

    with st.container():
        c_rank, c_name, c_change = st.columns([0.5, 3, 1.5])

        with c_rank:
            st.markdown(
                f"<div style='font-size:0.9em;color:#888;text-align:center;padding-top:4px'>#{rank}</div>",
                unsafe_allow_html=True,
            )

        with c_name:
            st.markdown(
                f"<div style='font-size:0.9em'>{class_emoji} <strong>{etf['ticker']}</strong>"
                f"<span style='font-size:0.8em;color:#888'> {etf['name']}</span></div>",
                unsafe_allow_html=True,
            )

        with c_change:
            st.markdown(
                f"<div style='font-size:0.95em;font-weight:bold;color:{color};text-align:right'>"
                f"{arrow} {abs(change_pct):.2f}%</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div style='margin:0;padding:0;border-bottom:1px solid #f0f0f0'></div>",
            unsafe_allow_html=True,
        )


# ── Main entry ───────────────────────────────────────────────────────────────

def show():
    """Display the Market Dashboard page with progressive loading.

    Fast data (prices, sectors, macro) loads first (~3s).
    Slow data (sparklines, ETF movers) follows from 1-hour cache or loads progressively.
    """
    render_sidebar()

    _render_header()

    # ── Phase 1: Fast data (prices, sectors, macro) ──────────────────────
    with st.spinner("⚡ 正在获取实时行情...（约2-3秒）"):
        snapshot = _fetch_snapshot_cached()

    indices = snapshot.get("indices", [])

    # ── Phase 2: Slow data (sparklines, ETF movers) ─────────────────────
    with st.spinner("📈 正在加载走势图和ETF数据...（首次约10-15秒，后续从缓存秒出）"):
        history = _fetch_history_cached()

    # Merge sparklines into index data
    sparklines_map = history.get("sparklines", {})
    for idx in indices:
        ticker = idx.get("ticker", "")
        if ticker in sparklines_map and sparklines_map[ticker]:
            idx["sparkline"] = sparklines_map[ticker]

    # Row 1: Index cards
    _render_index_cards(indices)

    # Row 2: Sector heatmap
    _render_sector_heatmap(snapshot.get("sectors"))

    # Row 3: Macro indicators
    _render_macro_cards(snapshot.get("macro", {}))

    # Row 4: ETF movers
    _render_etf_movers(history.get("etf_movers", []))

    # Footer
    st.markdown("---")
    st.caption(
        "⚠️ 数据仅供参考，不构成投资建议。指数和ETF价格可能存在15-30分钟延迟。"
        "数据来源：Yahoo Finance（实时行情）、AKShare（走势图及ETF数据）。"
        "点击「刷新行情」仅更新价格数据；走势图和ETF涨跌榜每小时自动更新。"
    )


if __name__ == "__main__":
    show()
