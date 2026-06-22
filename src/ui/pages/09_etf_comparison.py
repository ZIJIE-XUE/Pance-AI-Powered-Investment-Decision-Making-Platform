"""ETF Comparison page.

Part of the Market Dashboard module (市场仪表盘).
Users select 2 ETFs from the asset universe and get professional-grade
comparison: KPI cards, detailed metrics table, price/drawdown/correlation
charts, and distribution analysis.
"""

import logging
import yaml
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.engine.metrics import (
    annualized_return,
    annualized_volatility,
    sharpe_ratio,
    max_drawdown,
)
from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

RED = "#e74c3c"
BLUE = "#4285f4"
GREEN = "#27ae60"
PERIOD_OPTIONS = {"1年": "1y", "3年": "3y", "5年": "5y", "10年": "10y", "20年": "20y"}


# ── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _load_etf_list() -> list[dict]:
    """Load ETF universe from risk_weights.yaml. Returns list of asset dicts."""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "risk_weights.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assets = []
    for cls_name, items in config.get("asset_universe", {}).items():
        for item in items:
            item["_class"] = cls_name
            assets.append(item)
    return assets


def _build_selector_options(assets: list[dict]) -> dict[str, list[tuple[str, str, dict]]]:
    """Group ETFs by market + asset class for organized selectors.

    Returns dict like:
        {"A股 · 股票": [(label, ticker, asset_info), ...], ...}
    """
    market_labels = {
        "a_share": t("A股"), "hk": t("港股"), "us": t("美股"), "korea": t("韩国"),
        "us_cross": t("A股跨境"),
    }
    class_labels = {
        "equity": t("股票"), "bond": t("债券"), "gold": t("黄金"), "real_estate": t("地产"),
        "sector": t("行业板块"),
    }

    groups: dict[str, list[tuple[str, str, dict]]] = {}

    for a in assets:
        market = a.get("market", "")
        region = a.get("region", "")
        cls = a.get("_class", "")

        # Determine display market
        if market in ("a_share", "us_cross"):
            display_market = market_labels.get(market, market)
        elif region:
            display_market = market_labels.get(region, region.upper())
        elif market == "hk":
            display_market = t("港股")
        else:
            display_market = t("国际")

        display_class = class_labels.get(cls, cls)
        group_key = f"{display_market} · {display_class}"

        if group_key not in groups:
            groups[group_key] = []

        label = f"{a['ticker']} — {t(a['name'])}"
        groups[group_key].append((label, a["ticker"], a))

    return groups


# ── Data fetching + metric computation ────────────────────────────────────────

def _fetch_etf_prices(ticker: str, info: dict, period: str) -> pd.Series:
    """Fetch clean daily close prices for a single ETF.

    Uses Yahoo Finance for speed (batch-compatible).
    Falls back to AKShare if Yahoo fails.
    """
    yahoo_symbol = info.get("yahoo_symbol", ticker)

    # Try Yahoo Finance first (fast)
    try:
        import yfinance as yf
        # Yahoo Finance doesn't support "20y" — map to "max"
        yahoo_period = "max" if period == "20y" else period
        hist = yf.download(yahoo_symbol, period=yahoo_period, progress=False, auto_adjust=True)
        if hist is not None and not hist.empty:
            if "Close" in hist.columns:
                closes = hist["Close"]
                if isinstance(closes, pd.DataFrame):
                    closes = closes.iloc[:, 0]
                closes = closes.dropna()
                if len(closes) >= 10:
                    closes.name = ticker
                    return closes
    except Exception:
        pass

    # Fallback: use data_provider (AKShare + Yahoo)
    try:
        from src.engine.data_provider import fetch_single_ticker
        period_map = {"1y": "1y", "3y": "3y", "5y": "5y", "10y": "10y", "20y": "max"}
        dp_period = period_map.get(period, "5y")
        df = fetch_single_ticker(ticker, info, dp_period)
        if df is not None and not df.empty and ticker in df.columns:
            closes = df.set_index("date")[ticker].dropna()
            if len(closes) >= 10:
                return closes
    except Exception:
        pass

    return pd.Series(dtype=float)


def _compute_metrics(prices: pd.Series) -> dict:
    """Compute all professional metrics for a single ETF price series.

    Args:
        prices: pd.Series of daily close prices, indexed by date.

    Returns:
        Dict of computed metrics.
    """
    daily_rets = prices.pct_change().dropna()
    if len(daily_rets) < 20:
        return {"error": t("数据不足（至少需要20个交易日）")}

    rets_arr = daily_rets.values
    ann_ret = annualized_return(rets_arr)
    ann_vol = annualized_volatility(rets_arr)
    sharpe = sharpe_ratio(rets_arr, ann_vol)
    cum_rets = (1 + daily_rets).cumprod()
    mdd = max_drawdown(cum_rets.values)
    calmar = ann_ret / mdd if mdd > 0 else float("inf")

    # Drawdown dates
    running_max = cum_rets.expanding().max()
    drawdown = (cum_rets - running_max) / running_max
    worst_idx = drawdown.idxmin()
    worst_dd = drawdown.min()

    # Period returns
    def _period_return(days: int) -> float:
        if len(prices) <= days:
            return float((prices.iloc[-1] / prices.iloc[0] - 1) * 100)
        return float((prices.iloc[-1] / prices.iloc[-days-1] - 1) * 100)

    # Monthly returns
    monthly = prices.resample("ME").last().pct_change().dropna()
    best_month = monthly.max() * 100
    worst_month = monthly.min() * 100
    positive_months = (monthly > 0).sum() / len(monthly) * 100 if len(monthly) > 0 else 0

    # Latest price
    latest_price = float(prices.iloc[-1])

    return {
        "latest_price": latest_price,
        "ann_ret": ann_ret * 100,           # %
        "ann_vol": ann_vol * 100,           # %
        "sharpe": sharpe,
        "max_drawdown": mdd * 100,          # %
        "calmar": calmar,
        "return_1m": _period_return(21),
        "return_3m": _period_return(63),
        "return_6m": _period_return(126),
        "return_1y": _period_return(252),
        "return_3y": _period_return(756) if len(prices) >= 756 else None,
        "return_total": float((prices.iloc[-1] / prices.iloc[0] - 1) * 100),
        "best_month": best_month,
        "worst_month": worst_month,
        "positive_months": positive_months,
        "worst_dd_date": str(worst_idx.date()) if hasattr(worst_idx, 'date') else str(worst_idx),
        "worst_dd": worst_dd * 100,
        "daily_rets": daily_rets,
        "cum_rets": cum_rets,
        "drawdown_series": drawdown,
        "prices": prices,
    }


@st.cache_data(ttl=300, show_spinner=t("正在拉取历史数据并计算指标..."))
def _compute_comparison_cached(
    ticker_a: str, yahoo_a: str, market_a: str, ak_a: str,
    ticker_b: str, yahoo_b: str, market_b: str, ak_b: str,
    period: str,
) -> dict:
    """Cached ETF comparison computation.

    Args are all primitive types for hash-based caching.
    Returns dict with keys: metrics_a, metrics_b, correlation, rolling_corr, merged_prices, error.
    """
    info_a = {
        "ticker": ticker_a, "yahoo_symbol": yahoo_a,
        "market": market_a, "ak_symbol": ak_a,
    }
    info_b = {
        "ticker": ticker_b, "yahoo_symbol": yahoo_b,
        "market": market_b, "ak_symbol": ak_b,
    }

    # Fetch prices
    prices_a = _fetch_etf_prices(ticker_a, info_a, period)
    prices_b = _fetch_etf_prices(ticker_b, info_b, period)

    if prices_a.empty and prices_b.empty:
        return {"error": t("两只 ETF 数据均获取失败，请稍后重试")}
    if prices_a.empty:
        return {"error": ticker_a + t(" 数据获取失败")}
    if prices_b.empty:
        return {"error": ticker_b + t(" 数据获取失败")}

    # Compute individual metrics
    metrics_a = _compute_metrics(prices_a)
    metrics_b = _compute_metrics(prices_b)

    if "error" in metrics_a:
        return {"error": f"{ticker_a}: {metrics_a['error']}"}
    if "error" in metrics_b:
        return {"error": f"{ticker_b}: {metrics_b['error']}"}

    # Align dates for correlation analysis
    aligned_a = metrics_a["daily_rets"]
    aligned_b = metrics_b["daily_rets"]
    common_idx = aligned_a.index.intersection(aligned_b.index)
    rets_a = aligned_a[common_idx]
    rets_b = aligned_b[common_idx]

    # Correlation stats
    pearson = rets_a.corr(rets_b)
    r_squared = pearson ** 2
    both_up = ((rets_a > 0) & (rets_b > 0)).sum() / len(rets_a) * 100 if len(rets_a) > 0 else 0
    both_down = ((rets_a < 0) & (rets_b < 0)).sum() / len(rets_a) * 100 if len(rets_a) > 0 else 0

    # Rolling 60-day correlation
    if len(rets_a) >= 60:
        rolling_corr = rets_a.rolling(60).corr(rets_b).dropna()
        rolling_corr_dates = rolling_corr.index.tolist()
        rolling_corr_vals = rolling_corr.values.tolist()
    else:
        rolling_corr_dates = []
        rolling_corr_vals = []

    # Normalized prices for overlay chart (align to 100)
    aligned_prices_a = metrics_a["prices"][common_idx]
    aligned_prices_b = metrics_b["prices"][common_idx]
    norm_a = (aligned_prices_a / aligned_prices_a.iloc[0] * 100).tolist()
    norm_b = (aligned_prices_b / aligned_prices_b.iloc[0] * 100).tolist()
    norm_dates = common_idx.tolist()

    return {
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "correlation": {
            "pearson": pearson,
            "r_squared": r_squared,
            "both_up": both_up,
            "both_down": both_down,
        },
        "rolling_corr": (rolling_corr_dates, rolling_corr_vals),
        "norm_chart": (norm_dates, norm_a, norm_b),
        "ticker_a": ticker_a,
        "ticker_b": ticker_b,
        "name_a": "",
        "name_b": "",
    }


# ── Alipay-style comparison renderer ─────────────────────────────────────────

# Rows definition: (label, key, fmt, higher_is_better)
# higher_is_better: True = 数值大更好 (收益、夏普), False = 数值小更好 (波动率、回撤), None = 不比较
_COMPARE_ROWS = [
    ("最新价格",      "latest_price",    "¥{:,.2f}",   None),
    ("累计收益",      "return_total",    "{:+.2f}%",   True),
    ("年化收益",      "ann_ret",         "{:+.2f}%",   True),
    ("年化波动率",    "ann_vol",         "{:.2f}%",    False),
    ("夏普比率",      "sharpe",          "{:.2f}",     True),
    ("最大回撤",      "max_drawdown",    "{:.2f}%",    False),
    ("Calmar比率",    "calmar",          "{:.2f}",     True),
    ("1个月收益",     "return_1m",       "{:+.2f}%",   True),
    ("3个月收益",     "return_3m",       "{:+.2f}%",   True),
    ("6个月收益",     "return_6m",       "{:+.2f}%",   True),
    ("1年收益",       "return_1y",       "{:+.2f}%",   True),
    ("最佳月份",      "best_month",      "{:+.2f}%",   True),
    ("最差月份",      "worst_month",     "{:+.2f}%",   False),
    ("正收益月份占比", "positive_months", "{:.1f}%",    True),
]


def _winner(val_a, val_b, higher_is_better: bool) -> str:
    """Determine which value wins. Returns 'a', 'b', or 'tie'."""
    if val_a is None or val_b is None:
        return "tie"
    if higher_is_better:
        if val_a > val_b: return "a"
        if val_b > val_a: return "b"
    else:
        if val_a < val_b: return "a"
        if val_b < val_a: return "b"
    return "tie"


def _render_main_chart(result: dict):
    """Render the hero price chart — large, clean, Alipay-style."""
    ticker_a = result["ticker_a"]
    ticker_b = result["ticker_b"]
    dates, norm_a, norm_b = result["norm_chart"]

    if not dates:
        st.info(t("数据不足以绘制走势图"))
        return

    fig = go.Figure()

    # Grid lines for readability (Alipay style)
    fig.add_hline(y=100, line_dash="solid", line_color="#e0e0e0", line_width=1)

    fig.add_trace(go.Scatter(
        x=dates, y=norm_a, mode="lines",
        name=ticker_a,
        line=dict(color=RED, width=2.5),
        hovertemplate=f"{ticker_a}: %{{y:.1f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=norm_b, mode="lines",
        name=ticker_b,
        line=dict(color=BLUE, width=2.5),
        hovertemplate=f"{ticker_b}: %{{y:.1f}}<extra></extra>",
    ))

    # Fill between for visual comparison
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=norm_a + norm_b[::-1],
        fill="toself",
        fillcolor="rgba(180,180,180,0.08)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(size=13)),
        hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", zeroline=False,
                   title=t("起点 = 100")),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_compare_rows(metrics_a: dict, metrics_b: dict, ticker_a: str, ticker_b: str):
    """Render Alipay-style comparison rows — label in center, values on sides, winner highlighted."""
    st.markdown(t("### 指标对比"))
    st.caption(t("🔴 红色 = 更优 —— 绿色 = 较劣"))

    for label, key, fmt, higher_better in _COMPARE_ROWS:
        val_a = metrics_a.get(key)
        val_b = metrics_b.get(key)
        winner = _winner(val_a, val_b, higher_better) if higher_better is not None else "tie"

        str_a = fmt.format(val_a) if val_a is not None else "--"
        str_b = fmt.format(val_b) if val_b is not None else "--"

        # Color the winner red, loser green
        color_a = RED if winner == "a" else (GREEN if winner == "b" else "#333")
        color_b = RED if winner == "b" else (GREEN if winner == "a" else "#333")
        weight_a = "700" if winner == "a" else "400"
        weight_b = "700" if winner == "b" else "400"

        html = (
            f"<div style='display:flex;align-items:center;padding:10px 0;"
            f"border-bottom:1px solid #f0f0f0'>"
            f"<div style='flex:1;text-align:right;padding-right:16px;font-size:1.05em;"
            f"color:{color_a};font-weight:{weight_a}'>{str_a}</div>"
            f"<div style='flex:0 0 auto;text-align:center;min-width:120px;"
            f"color:#888;font-size:0.85em'>{t(label)}</div>"
            f"<div style='flex:1;text-align:left;padding-left:16px;font-size:1.05em;"
            f"color:{color_b};font-weight:{weight_b}'>{str_b}</div>"
            f"</div>"
        )
        st.markdown(html, unsafe_allow_html=True)


def _render_correlation_bar(corr: dict):
    """Render correlation as a simple visual bar + 4 stats."""
    st.markdown("---")
    st.markdown(t("### 🔗 相关性"))

    pearson = corr.get("pearson", 0)
    r2 = corr.get("r_squared", 0)
    both_up = corr.get("both_up", 0)
    both_down = corr.get("both_down", 0)

    # Correlation gauge bar
    abs_p = abs(pearson)
    bar_color = RED if abs_p > 0.7 else ("#f39c12" if abs_p > 0.4 else GREEN)

    st.markdown(
        f"<div style='margin:8px 0'>"
        f"<span style='font-size:0.9em;color:#888'>{t('Pearson 相关系数')}</span><br>"
        f"<span style='font-size:2em;font-weight:bold;color:{bar_color}'>{pearson:+.4f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Visual bar
    bar_html = (
        f"<div style='height:8px;background:#eee;border-radius:4px;margin:8px 0;overflow:hidden'>"
        f"<div style='height:100%;width:{abs_p*100}%;background:{bar_color};border-radius:4px'></div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;font-size:0.7em;color:#bbb'>"
        f"<span>-1.0</span><span>0</span><span>+1.0</span></div>"
    )
    st.markdown(bar_html, unsafe_allow_html=True)

    # Four stat cards
    cols = st.columns(4)
    with cols[0]:
        st.metric(t("判定系数 R²"), f"{r2:.4f}")
    with cols[1]:
        st.metric(t("共同上涨"), f"{both_up:.1f}%")
    with cols[2]:
        st.metric(t("共同下跌"), f"{both_down:.1f}%")
    with cols[3]:
        label = t("高度相关") if abs_p > 0.7 else (t("中度相关") if abs_p > 0.4 else t("低度相关"))
        st.metric(t("相关程度"), label)


def _render_drawdown_chart(metrics_a: dict, metrics_b: dict, ticker_a: str, ticker_b: str):
    """Render drawdown overlay chart, compact size."""
    dd_a = metrics_a.get("drawdown_series")
    dd_b = metrics_b.get("drawdown_series")
    if dd_a is None or dd_b is None:
        return

    common = dd_a.index.intersection(dd_b.index)
    if len(common) < 5:
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=common, y=dd_a[common] * 100, mode="lines",
        name=ticker_a, line=dict(color=RED, width=1.5),
        fill="tozeroy", fillcolor="rgba(231,76,60,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=common, y=dd_b[common] * 100, mode="lines",
        name=ticker_b, line=dict(color=BLUE, width=1.5),
        fill="tozeroy", fillcolor="rgba(66,133,244,0.08)",
    ))
    fig.update_layout(
        height=300, margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified", yaxis=dict(ticksuffix="%"),
        plot_bgcolor="white",
    )
    st.markdown(t("#### 📉 回撤曲线"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_rolling_corr_chart(result: dict):
    """Render rolling correlation chart."""
    corr_dates, corr_vals = result["rolling_corr"]
    if not corr_dates:
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=corr_dates, y=corr_vals, mode="lines",
        line=dict(color="#8e44ad", width=1.5),
        fill="tozeroy", fillcolor="rgba(142,68,173,0.08)",
        name=t("60日滚动相关性"),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        height=300, margin=dict(l=20, r=20, t=10, b=20),
        showlegend=False, hovermode="x unified",
        yaxis=dict(range=[-1, 1]), plot_bgcolor="white",
    )
    st.markdown(t("#### 🟣 60日滚动相关性"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_distribution_chart(metrics_a: dict, metrics_b: dict, ticker_a: str, ticker_b: str):
    """Render daily return distribution histogram."""
    rets_a = metrics_a.get("daily_rets")
    rets_b = metrics_b.get("daily_rets")
    if rets_a is None or rets_b is None:
        return

    common = rets_a.index.intersection(rets_b.index)
    if len(common) < 20:
        return

    r_a = rets_a[common].values * 100
    r_b = rets_b[common].values * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=r_a, nbinsx=50, name=ticker_a,
        marker_color=RED, opacity=0.55, histnorm="probability",
    ))
    fig.add_trace(go.Histogram(
        x=r_b, nbinsx=50, name=ticker_b,
        marker_color=BLUE, opacity=0.55, histnorm="probability",
    ))
    fig.update_layout(
        height=300, margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        barmode="overlay", plot_bgcolor="white",
        xaxis=dict(ticksuffix="%", title=t("日收益率")),
        yaxis=dict(title=t("概率密度")),
    )
    st.markdown(t("#### 📊 日收益分布"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Main entry ───────────────────────────────────────────────────────────────

def show():
    """Display the ETF Comparison page — Alipay fund comparison style."""
    render_sidebar()
    st.title(t("📈 ETF 对比工具"))
    st.caption(t("选两只 ETF，一眼看出谁更强 —— 红色突出优胜方"))

    # Load ETF list
    assets = _load_etf_list()
    groups = _build_selector_options(assets)

    all_options: list[tuple[str, str, dict]] = []
    for group_name, options in groups.items():
        for label, ticker, info in options:
            display = f"[{group_name}] {label}"
            all_options.append((display, ticker, info))

    # Selection UI — compact single row
    st.markdown("---")
    col_a, col_vs, col_b, col_p = st.columns([2.5, 0.5, 2.5, 1])

    option_labels = [opt[0] for opt in all_options]

    with col_a:
        idx_a = st.selectbox(t("ETF A"), range(len(option_labels)),
                             format_func=lambda i: option_labels[i], key="etf_a")

    with col_vs:
        st.markdown("<div style='text-align:center;padding-top:28px;font-size:1.3em;color:#888'>VS</div>",
                    unsafe_allow_html=True)

    with col_b:
        default_b = min(1, len(option_labels) - 1)
        idx_b = st.selectbox(t("ETF B"), range(len(option_labels)),
                             format_func=lambda i: option_labels[i],
                             index=default_b if default_b != idx_a else min(default_b + 1, len(option_labels) - 1),
                             key="etf_b")

    with col_p:
        period_label = st.selectbox(t("周期"), list(PERIOD_OPTIONS.keys()), index=2,
                                     format_func=lambda k: t(k))
        period = PERIOD_OPTIONS[period_label]

    # Compare button
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        compare_clicked = st.button(t("📊 开始对比"), type="primary", use_container_width=True)

    if compare_clicked:
        if idx_a == idx_b:
            st.warning(t("请选择两只不同的 ETF 进行对比"))
            return

        _, ticker_a, info_a = all_options[idx_a]
        _, ticker_b, info_b = all_options[idx_b]

        name_a = info_a.get("name", ticker_a)
        name_b = info_b.get("name", ticker_b)

        with st.spinner(t("正在对比 ") + ticker_a + t(" vs ") + ticker_b + "..."):
            result = _compute_comparison_cached(
                ticker_a, info_a.get("yahoo_symbol", ticker_a),
                info_a.get("market", ""), info_a.get("ak_symbol", ticker_a),
                ticker_b, info_b.get("yahoo_symbol", ticker_b),
                info_b.get("market", ""), info_b.get("ak_symbol", ticker_b),
                period,
            )

        if result.get("error"):
            st.error(result["error"])
            return

        result["name_a"] = name_a
        result["name_b"] = name_b
        result["ticker_a"] = ticker_a
        result["ticker_b"] = ticker_b

        st.markdown("---")

        # ── ETF name headers (side by side) ──
        hcol_a, hcol_vs, hcol_b = st.columns([2, 0.6, 2])
        with hcol_a:
            st.markdown(f"<h3 style='text-align:center;color:{RED}'>{ticker_a}</h3>"
                        f"<p style='text-align:center;color:#888;font-size:0.85em'>{name_a}</p>",
                        unsafe_allow_html=True)
        with hcol_vs:
            st.markdown("<div style='text-align:center;padding-top:12px;font-size:1.2em;color:#bbb'>VS</div>",
                        unsafe_allow_html=True)
        with hcol_b:
            st.markdown(f"<h3 style='text-align:center;color:{BLUE}'>{ticker_b}</h3>"
                        f"<p style='text-align:center;color:#888;font-size:0.85em'>{name_b}</p>",
                        unsafe_allow_html=True)

        st.caption(t("对比周期：") + t(period_label))

        # ── Hero chart: price overlay ──
        _render_main_chart(result)

        # ── Comparison rows (Alipay style) ──
        _render_compare_rows(result["metrics_a"], result["metrics_b"], ticker_a, ticker_b)

        # ── Correlation ──
        _render_correlation_bar(result["correlation"])

        # ── Collapsible: additional charts ──
        with st.expander(t("📉 更多分析图表"), expanded=False):
            _render_drawdown_chart(result["metrics_a"], result["metrics_b"], ticker_a, ticker_b)
            _render_rolling_corr_chart(result)
            _render_distribution_chart(result["metrics_a"], result["metrics_b"], ticker_a, ticker_b)

    else:
        # Show ETF overview table before comparison
        st.markdown("---")
        st.markdown(t("### 📋 可选 ETF 一览"))
        st.caption(t("从下表中选择两只 ETF，点击「开始对比」进行分析"))

        overview = []
        for _, ticker, info in all_options:
            overview.append({
                t("代码"): ticker,
                t("名称"): t(info.get("name", "")),
                t("资产类别"): {"equity": t("股票"), "bond": t("债券"), "gold": t("黄金"), "real_estate": t("地产")}.get(info.get("_class", ""), ""),
                t("市场"): info.get("market", info.get("region", "")),
            })

        st.dataframe(overview, use_container_width=True, hide_index=True, height=350)


if __name__ == "__main__":
    show()
