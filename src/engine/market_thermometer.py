"""Market Thermometer engine.

Computes A-share market "temperature" (0-100C) from two signals:
1. Current PE (via CSIndex / AKShare `stock_zh_index_value_csindex`)
2. Price deviation from 200-day moving average (via AKShare `index_zh_a_hist`)

Combined signal → temperature zone → investment suggestion.
All data sources are free and accessible from within China.
"""

import time
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# ── Index definitions ────────────────────────────────────────────────────────

_THERMOMETER_INDICES = [
    {"name": "上证50",   "csindex_code": "000016", "ak_symbol": "000016", "desc": "大盘蓝筹",  "weight": 0.25},
    {"name": "沪深300",  "csindex_code": "000300", "ak_symbol": "000300", "desc": "核心基准",  "weight": 0.35},
    {"name": "中证500",  "csindex_code": "000905", "ak_symbol": "000905", "desc": "中盘成长",  "weight": 0.25},
    {"name": "中证1000", "csindex_code": "000852", "ak_symbol": "000852", "desc": "小盘风向标", "weight": 0.15},
]

# PE thresholds per index: [极度低估上限, 偏低上限, 适中上限, 偏贵上限]
# Values above the last threshold = 高估
_PE_THRESHOLDS = {
    "000016": [8.5, 10.0, 12.0, 14.0],     # 上证50
    "000300": [10.5, 12.5, 15.0, 17.5],     # 沪深300
    "000905": [22.0, 27.0, 33.0, 40.0],     # 中证500
    "000852": [28.0, 33.0, 40.0, 48.0],     # 中证1000
}

# ── Temperature classification ───────────────────────────────────────────────

_TEMPERATURE_ZONES = [
    (0,   20,  "🧊 极度低估", "#2196F3", "估值处于历史底部区域，可积极加仓"),
    (20,  40,  "❄️ 偏低",    "#64B5F6", "估值低于正常水平，可适当多投"),
    (40,  60,  "🌡️ 适中",    "#9E9E9E", "估值处于合理区间，维持正常定投"),
    (60,  80,  "🔥 偏贵",    "#FF9800", "估值高于正常水平，建议减少定投金额"),
    (80,  101, "💥 高估",    "#f44336", "估值处于历史高位，建议暂停定投并考虑减仓"),
]


def classify_temperature(score: float) -> dict:
    """Classify a temperature score (0-100) into a zone."""
    for low, high, label, color, suggestion in _TEMPERATURE_ZONES:
        if low <= score < high:
            return {
                "percentile": round(score, 1),
                "zone_label": label,
                "color": color,
                "suggestion": suggestion,
            }
    return {
        "percentile": round(score, 1),
        "zone_label": "🌡️ 适中",
        "color": "#9E9E9E",
        "suggestion": "维持正常定投",
    }


def _pe_to_score(pe: float, thresholds: list[float]) -> float:
    """Map a PE value to a 0-100 score using index-specific thresholds.

    Each threshold is a zone boundary. Scores are centered in each zone
    with linear interpolation within zones.
    """
    zones = [10, 30, 50, 70, 90]  # center score for each zone
    boundaries = [0] + thresholds + [float("inf")]

    for i in range(len(boundaries) - 1):
        if pe <= boundaries[i + 1]:
            # Linear interpolate within this zone
            lo = boundaries[i]
            hi = boundaries[i + 1]
            z_lo = zones[i]
            z_hi = zones[i + 1] if i + 1 < len(zones) else zones[i]
            if hi == float("inf"):
                return float(z_hi)
            if hi == lo:
                return float(z_lo)
            fraction = (pe - lo) / (hi - lo)
            return float(z_lo + fraction * (z_hi - z_lo))

    return 90.0


def _ma_deviation_score(pct_deviation: float) -> float:
    """Map price deviation from 200MA to a 0-100 score.

    pct_deviation: e.g. +10 means price is 10% above 200MA.
    Higher deviation → higher score (more expensive).
    """
    # Clamp to reasonable range and map to 0-100
    clamped = max(-30, min(30, pct_deviation))
    # Map [-30, 30] → [0, 100]
    return (clamped + 30) / 60 * 100


# ── Data fetching ────────────────────────────────────────────────────────────

def _fetch_csindex_pe(csindex_code: str) -> Optional[dict]:
    """Fetch current PE from CSIndex via AKShare.

    Returns dict with: pe_current, pe_history_df, or None.
    """
    try:
        import akshare as ak

        df = ak.stock_zh_index_value_csindex(symbol=csindex_code)
        if df is None or df.empty:
            return None

        df = df.rename(columns={
            "日期": "date",
            "市盈率1": "pe_static",
            "市盈率2": "pe_rolling",
        })

        # Use 市盈率2 (rolling/TTM PE) as primary; fall back to 市盈率1 (static)
        pe_col = "pe_rolling" if "pe_rolling" in df.columns else "pe_static"
        df[pe_col] = pd.to_numeric(df[pe_col], errors="coerce")
        df = df.dropna(subset=[pe_col])
        df["date"] = pd.to_datetime(df["date"])

        if df.empty:
            return None

        df = df.sort_values("date")
        current_pe = float(df[pe_col].iloc[-1])

        return {
            "pe_current": round(current_pe, 2),
            "pe_history": df[["date", pe_col]].rename(columns={pe_col: "pe"}),
        }

    except Exception as e:
        logger.warning("csindex_pe_failed", code=csindex_code, error=str(e)[:100])
        return None


def _fetch_price_ma(ak_symbol: str, ma_days: int = 200) -> Optional[dict]:
    """Fetch price data and compute 200MA deviation for an A-share index.

    Returns dict with: ma_deviation_pct, price_history_df, or None.
    """
    try:
        import akshare as ak

        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        df = ak.index_zh_a_hist(
            symbol=ak_symbol,
            period="daily",
            start_date=start,
            end_date=end,
        )

        if df is None or df.empty:
            return None

        df = df.rename(columns={"日期": "date", "收盘": "close"})
        df["date"] = pd.to_datetime(df["date"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"]).sort_values("date")

        if len(df) < ma_days:
            return None

        # Compute 200MA and deviation
        df["ma200"] = df["close"].rolling(window=ma_days, min_periods=ma_days).mean()
        latest_close = float(df["close"].iloc[-1])
        latest_ma = float(df["ma200"].dropna().iloc[-1]) if df["ma200"].dropna().size > 0 else latest_close

        deviation_pct = (latest_close - latest_ma) / latest_ma * 100 if latest_ma != 0 else 0.0

        return {
            "ma_deviation_pct": round(deviation_pct, 2),
            "price_history": df[["date", "close", "ma200"]].copy(),
            "latest_close": round(latest_close, 2),
        }

    except Exception as e:
        logger.warning("price_ma_failed", symbol=ak_symbol, error=str(e)[:100])
        return None


def _fetch_single_index(idx_def: dict) -> dict:
    """Fetch all data for one index and compute temperature."""
    ak_symbol = idx_def["ak_symbol"]
    csindex_code = idx_def["csindex_code"]

    result = {
        **idx_def,
        "pe_current": None,
        "pe_history": None,
        "ma_deviation_pct": None,
        "price_history": None,
        "temperature": None,
        "error": None,
    }

    # Fetch PE and price data sequentially (reliable + avoids concurrency issues)
    pe_data = _fetch_csindex_pe(csindex_code)
    price_data = _fetch_price_ma(ak_symbol)

    if pe_data is None and price_data is None:
        result["error"] = "数据暂不可用"
        return result

    # ── Compute PE-based score ──────────────────────────────────────────────
    pe_score = None
    if pe_data:
        result["pe_current"] = pe_data["pe_current"]
        result["pe_history"] = pe_data["pe_history"]

        thresholds = _PE_THRESHOLDS.get(csindex_code)
        if thresholds:
            pe_score = _pe_to_score(pe_data["pe_current"], thresholds)

    # ── Compute MA deviation score ──────────────────────────────────────────
    ma_score = None
    if price_data:
        result["ma_deviation_pct"] = price_data["ma_deviation_pct"]
        result["price_history"] = price_data["price_history"]
        ma_score = _ma_deviation_score(price_data["ma_deviation_pct"])

    # ── Combined temperature ────────────────────────────────────────────────
    if pe_score is not None and ma_score is not None:
        combined = pe_score * 0.6 + ma_score * 0.4
    elif pe_score is not None:
        combined = pe_score
    elif ma_score is not None:
        combined = ma_score
    else:
        combined = 50.0

    result["temperature"] = classify_temperature(combined)
    result["pe_score"] = round(pe_score, 1) if pe_score is not None else None
    result["ma_score"] = round(ma_score, 1) if ma_score is not None else None

    return result


# ── Public: Main coordinator ─────────────────────────────────────────────────

def fetch_market_temperature(years: int = 5) -> dict:
    """Fetch market temperature data for all tracked indices.

    Uses CSIndex for PE + AKShare index_zh_a_hist for price/MA.
    All requests are sequential to avoid rate limiting.

    Returns dict with: indices, overall, timestamp.
    """
    results = {"indices": [], "overall": None, "timestamp": datetime.now()}

    for idx_def in _THERMOMETER_INDICES:
        try:
            results["indices"].append(_fetch_single_index(idx_def))
        except Exception as e:
            results["indices"].append({
                **idx_def,
                "pe_current": None,
                "pe_history": None,
                "ma_deviation_pct": None,
                "price_history": None,
                "temperature": None,
                "error": f"获取失败: {str(e)[:80]}",
            })
        time.sleep(0.3)

    # Compute overall temperature
    overall = _compute_overall(results["indices"])
    results["overall"] = overall

    return results


def _compute_overall(indices: list[dict]) -> dict:
    """Weighted average temperature across all indices."""
    weighted_sum = 0.0
    total_weight = 0.0

    for idx in indices:
        weight = idx.get("weight", 0.25)
        temp = idx.get("temperature")
        if temp:
            weighted_sum += temp["percentile"] * weight
        else:
            weighted_sum += 50.0 * weight  # neutral fallback
        total_weight += weight

    overall_pct = weighted_sum / total_weight if total_weight > 0 else 50.0
    return {"percentile": round(overall_pct, 1), **classify_temperature(overall_pct)}
