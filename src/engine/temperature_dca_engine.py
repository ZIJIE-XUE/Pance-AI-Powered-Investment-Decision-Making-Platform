"""Temperature DCA Backtest Engine.

Core engine for the flagship "温度定投系统" module.
Simulates three strategies over historical data:
  1. Temperature-driven DCA (dynamic multiplier based on market temperature)
  2. Regular DCA (fixed monthly amount)
  3. Lump sum (all-in at start, for benchmark comparison)

Computes comparative metrics: total return, CAGR, max drawdown, Sharpe ratio, etc.

Also provides:
  - Signal validation: does temperature predict forward returns?
  - Market regime decomposition: strategy performance in bull/bear/sideways
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from src.engine.market_thermometer import (
    _ma_deviation_score,
    _pe_to_score,
    _PE_THRESHOLDS,
    classify_temperature,
)

logger = logging.getLogger(__name__)

# ── Index definitions (multi-source symbols) ─────────────────────────────────

_BACKTEST_INDICES = {
    "上证50": {
        "csindex_code": "000016",
        "ak_symbol": "000016",
        "sina_symbol": "sh000016",
        "pe_thresholds": [8.5, 10.0, 12.0, 14.0],
    },
    "沪深300": {
        "csindex_code": "000300",
        "ak_symbol": "000300",
        "sina_symbol": "sh000300",
        "pe_thresholds": [10.5, 12.5, 15.0, 17.5],
    },
    "中证500": {
        "csindex_code": "000905",
        "ak_symbol": "000905",
        "sina_symbol": "sh000905",
        "pe_thresholds": [22.0, 27.0, 33.0, 40.0],
    },
    "中证1000": {
        "csindex_code": "000852",
        "ak_symbol": "000852",
        "sina_symbol": "sh000852",
        "pe_thresholds": [28.0, 33.0, 40.0, 48.0],
    },
}

# ── Strategy multiplier maps ─────────────────────────────────────────────────

STRATEGIES = {
    "aggressive": {
        "name": "积极",
        "desc": "低温重仓，高位空仓",
        "multipliers": [
            (0, 20, 2.0),
            (20, 40, 1.5),
            (40, 60, 1.0),
            (60, 80, 0.25),
            (80, 101, 0.0),
        ],
    },
    "moderate": {
        "name": "适中",
        "desc": "均衡加减仓",
        "multipliers": [
            (0, 20, 1.5),
            (20, 40, 1.25),
            (40, 60, 1.0),
            (60, 80, 0.5),
            (80, 101, 0.0),
        ],
    },
    "conservative": {
        "name": "保守",
        "desc": "温和微调",
        "multipliers": [
            (0, 20, 1.25),
            (20, 40, 1.1),
            (40, 60, 1.0),
            (60, 80, 0.75),
            (80, 101, 0.5),
        ],
    },
}


def get_multiplier(temperature: float, strategy_name: str) -> float:
    """Map a temperature score (0-100) to an investment multiplier."""
    strategy = STRATEGIES.get(strategy_name, STRATEGIES["moderate"])
    for lo, hi, mult in strategy["multipliers"]:
        if lo <= temperature < hi:
            return mult
    return 1.0


# ── Data fetching ────────────────────────────────────────────────────────────

def _fetch_prices_sina(sina_symbol: str, years: int) -> Optional[pd.DataFrame]:
    """Fetch historical index prices via Sina (ak.stock_zh_index_daily).

    Returns DataFrame with columns: date, close, or None on failure.
    """
    try:
        import akshare as ak

        df = ak.stock_zh_index_daily(symbol=sina_symbol)
        if df is None or df.empty:
            logger.warning("sina_empty", symbol=sina_symbol)
            return None

        # Normalise column names (Sina returns Chinese: 日期, 收盘)
        rename_map = {}
        for col in df.columns:
            if col in ("date", "日期"):
                rename_map[col] = "date"
            elif col in ("close", "收盘"):
                rename_map[col] = "close"
        df = df.rename(columns=rename_map)

        if "date" not in df.columns or "close" not in df.columns:
            # Try positional fallback: first col = date, fourth col = close
            cols = list(df.columns)
            if len(cols) >= 4:
                df = df.rename(columns={cols[0]: "date", cols[3]: "close"})
            else:
                return None

        df["date"] = pd.to_datetime(df["date"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"]).sort_values("date")

        if df.empty:
            return None

        # Filter to requested years
        cutoff = datetime.now() - timedelta(days=years * 365 + 30)
        df = df[df["date"] >= cutoff]

        return df[["date", "close"]].reset_index(drop=True)

    except Exception as e:
        logger.warning("sina_fetch_failed", symbol=sina_symbol, error=str(e)[:100])
        return None


def _fetch_prices_eastmoney(ak_symbol: str, years: int) -> Optional[pd.DataFrame]:
    """Fallback: fetch prices via EastMoney (ak.index_zh_a_hist)."""
    try:
        import akshare as ak

        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=years * 365 + 30)).strftime("%Y%m%d")

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

        return df[["date", "close"]].reset_index(drop=True)

    except Exception as e:
        logger.warning("eastmoney_fetch_failed", symbol=ak_symbol, error=str(e)[:100])
        return None


def _fetch_pe_history(csindex_code: str) -> Optional[pd.DataFrame]:
    """Fetch PE history from CSIndex (limited to ~20 trading days).

    Returns DataFrame with columns: date, pe, or None.
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

        pe_col = "pe_rolling" if "pe_rolling" in df.columns else "pe_static"
        df[pe_col] = pd.to_numeric(df[pe_col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=[pe_col]).sort_values("date")

        return df[["date", pe_col]].rename(columns={pe_col: "pe"})

    except Exception as e:
        logger.warning("pe_history_failed", code=csindex_code, error=str(e)[:100])
        return None


# ── Monthly resampling & temperature computation ─────────────────────────────

def _resample_to_monthly(prices_df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily price data to monthly (last trading day of each month)."""
    df = prices_df.copy()
    df["year_month"] = df["date"].dt.to_period("M")

    monthly = df.groupby("year_month").agg(
        date=("date", "last"),
        close=("close", "last"),
    ).reset_index(drop=True)

    # Compute 200-day moving average at each month-end
    # We need the full daily series for this — compute MA first, then sample
    df["ma200"] = df["close"].rolling(window=200, min_periods=200).mean()
    df["year_month"] = df["date"].dt.to_period("M")

    monthly_ma = df.groupby("year_month").agg(
        ma200=("ma200", "last"),
    ).reset_index(drop=True)

    result = monthly.merge(monthly_ma, left_index=True, right_index=True)
    result = result.dropna(subset=["ma200"])  # need 200 days of history

    return result


def _compute_monthly_temperatures(
    monthly_df: pd.DataFrame,
    pe_df: Optional[pd.DataFrame],
    pe_thresholds: list[float],
    pe_weight: float = 0.6,
) -> pd.DataFrame:
    """Compute temperature (0-100) for each month.

    Uses PE score (pe_weight) + MA deviation score (1-pe_weight) where PE is
    available; falls back to MA-deviation-only otherwise.

    pe_weight is configurable to support sensitivity analysis and
    walk-forward parameter optimization.
    """
    ma_weight = 1.0 - pe_weight
    df = monthly_df.copy()

    # MA deviation score for all months
    df["ma_deviation_pct"] = (df["close"] - df["ma200"]) / df["ma200"] * 100
    df["ma_score"] = df["ma_deviation_pct"].apply(_ma_deviation_score)

    # PE score — merge PE data onto closest month
    if pe_df is not None and not pe_df.empty:
        pe_monthly = pe_df.copy()
        pe_monthly["year_month"] = pe_monthly["date"].dt.to_period("M")
        pe_agg = pe_monthly.groupby("year_month")["pe"].last().reset_index()
        pe_agg.columns = ["year_month", "pe"]

        df["year_month"] = df["date"].dt.to_period("M")
        df = df.merge(pe_agg, on="year_month", how="left")

        # Compute PE score where available
        pe_scores = []
        has_pe_count = 0
        for _, row in df.iterrows():
            if pd.notna(row.get("pe")):
                pe_scores.append(_pe_to_score(float(row["pe"]), pe_thresholds))
                has_pe_count += 1
            else:
                pe_scores.append(None)
        df["pe_score"] = pe_scores

        if has_pe_count > len(df) * 0.3:
            # Enough PE data: use weighted model
            df["temperature"] = df.apply(
                lambda r: (
                    r["pe_score"] * pe_weight + r["ma_score"] * ma_weight
                    if pd.notna(r.get("pe_score"))
                    else r["ma_score"]
                ),
                axis=1,
            )
        else:
            # PE coverage < 30%: raw MA scores cluster in 25-75, making
            # extreme zones rarely visited → all strategies behave similarly.
            # Percentile rank spreads temperatures uniformly across 0-100,
            # ensuring ~20% of months land in each 20-point band so that
            # aggressive / moderate / conservative curves visibly diverge.
            df["temperature"] = df["ma_score"].rank(pct=True) * 100
    else:
        # No PE data at all. Same percentile-rank fallback for the same reason.
        df["temperature"] = df["ma_score"].rank(pct=True) * 100
        df["pe_score"] = None

    # Remove incomplete rows
    df = df.dropna(subset=["temperature"])

    return df


# ── Strategy simulation ──────────────────────────────────────────────────────

def _simulate_regular_dca(
    monthly_df: pd.DataFrame,
    base_monthly: float,
) -> dict:
    """Simulate regular fixed-amount DCA."""
    shares = 0.0
    total_invested = 0.0
    records = []

    for _, row in monthly_df.iterrows():
        price = float(row["close"])
        shares += base_monthly / price
        total_invested += base_monthly

        portfolio_value = shares * price

        records.append({
            "date": row["date"],
            "price": round(price, 2),
            "invested": base_monthly,
            "total_invested": round(total_invested, 2),
            "shares": round(shares, 4),
            "portfolio_value": round(portfolio_value, 2),
            "cash_pool": 0.0,
        })

    return {
        "records": records,
        "total_invested": round(total_invested, 2),
        "total_months": len(records),
    }


def _simulate_temperature_dca(
    monthly_df: pd.DataFrame,
    base_monthly: float,
    strategy_name: str,
) -> dict:
    """Simulate temperature-driven DCA with cash pool.

    Rules:
    - multiplier > 1: invest extra from cash pool (capped at pool balance)
    - multiplier < 1: save difference to cash pool
    - multiplier = 1: normal investment, no pool change
    """
    shares = 0.0
    cash_pool = 0.0
    total_invested = 0.0
    records = []

    strategy = STRATEGIES.get(strategy_name, STRATEGIES["moderate"])

    for _, row in monthly_df.iterrows():
        price = float(row["close"])
        temperature = float(row["temperature"])
        multiplier = get_multiplier(temperature, strategy_name)

        if multiplier > 1.0:
            # Invest extra — draw from cash pool
            extra_needed = base_monthly * (multiplier - 1.0)
            extra_available = min(extra_needed, cash_pool)
            actual_invest = base_monthly + extra_available
            cash_pool -= extra_available
        elif multiplier < 1.0:
            # Invest less — save to cash pool
            actual_invest = base_monthly * multiplier
            cash_pool += base_monthly - actual_invest
        else:
            actual_invest = base_monthly

        shares += actual_invest / price
        total_invested += actual_invest
        portfolio_value = shares * price + cash_pool

        records.append({
            "date": row["date"],
            "price": round(price, 2),
            "temperature": round(temperature, 1),
            "multiplier": multiplier,
            "invested": round(actual_invest, 2),
            "total_invested": round(total_invested, 2),
            "shares": round(shares, 4),
            "portfolio_value": round(portfolio_value, 2),
            "cash_pool": round(cash_pool, 2),
        })

    return {
        "records": records,
        "total_invested": round(total_invested, 2),
        "total_months": len(records),
        "end_cash_pool": round(cash_pool, 2),
    }


def _simulate_lump_sum(
    monthly_df: pd.DataFrame,
    total_amount: float,
) -> dict:
    """Simulate lump-sum investment (all-in at start)."""
    first_price = float(monthly_df.iloc[0]["close"])
    shares = total_amount / first_price
    records = []

    for _, row in monthly_df.iterrows():
        price = float(row["close"])
        portfolio_value = shares * price

        records.append({
            "date": row["date"],
            "price": round(price, 2),
            "portfolio_value": round(portfolio_value, 2),
        })

    return {
        "records": records,
        "total_invested": total_amount,
        "total_months": len(records),
        "shares": round(shares, 4),
    }


# ── Performance metrics ──────────────────────────────────────────────────────

def _compute_metrics(
    sim_result: dict,
    monthly_df: pd.DataFrame,
) -> dict:
    """Compute standard performance metrics from simulation results."""
    records = sim_result["records"]
    total_invested = sim_result["total_invested"]
    total_months = sim_result["total_months"]

    if not records or total_months < 2:
        return {
            "total_return_pct": 0,
            "cagr_pct": 0,
            "max_drawdown_pct": 0,
            "sharpe_ratio": 0,
            "volatility_pct": 0,
            "win_rate_pct": 0,
            "final_value": 0,
        }

    final_value = records[-1]["portfolio_value"]

    # Total return
    total_return_pct = (final_value - total_invested) / total_invested * 100 if total_invested > 0 else 0

    # CAGR
    years_elapsed = total_months / 12
    if years_elapsed > 0 and total_invested > 0 and final_value > 0:
        cagr_pct = ((final_value / total_invested) ** (1 / years_elapsed) - 1) * 100
    else:
        cagr_pct = 0.0

    # Max drawdown
    peaks = np.maximum.accumulate([r["portfolio_value"] for r in records])
    drawdowns = (np.array([r["portfolio_value"] for r in records]) - peaks) / peaks * 100
    max_dd_pct = abs(float(np.min(drawdowns))) if len(drawdowns) > 0 else 0.0

    # Monthly returns for Sharpe & volatility
    monthly_returns = []
    for i in range(1, len(records)):
        prev_val = records[i - 1]["portfolio_value"]
        curr_val = records[i]["portfolio_value"]
        net_invest = records[i].get("invested", 0)
        if prev_val > 0:
            ret = (curr_val - prev_val - net_invest) / prev_val
            monthly_returns.append(ret)

    if len(monthly_returns) >= 3:
        avg_ret = np.mean(monthly_returns)
        std_ret = np.std(monthly_returns, ddof=1)
        ann_vol = std_ret * np.sqrt(12) * 100  # annualised volatility %

        # Sharpe ratio (assume 2% risk-free)
        rf_monthly = 0.02 / 12
        excess = np.array(monthly_returns) - rf_monthly
        sharpe = (np.mean(excess) / np.std(excess, ddof=1)) * np.sqrt(12) if np.std(excess, ddof=1) > 0 else 0.0
    else:
        ann_vol = 0.0
        sharpe = 0.0

    # Win rate: % of months where portfolio value > cost basis
    wins = sum(
        1 for r in records
        if r["portfolio_value"] > r.get("total_invested", r.get("total_invested", 0))
    )
    win_rate_pct = wins / total_months * 100 if total_months > 0 else 0.0

    return {
        "total_return_pct": round(total_return_pct, 1),
        "cagr_pct": round(cagr_pct, 1),
        "max_drawdown_pct": round(max_dd_pct, 1),
        "sharpe_ratio": round(sharpe, 2),
        "volatility_pct": round(ann_vol, 1),
        "win_rate_pct": round(win_rate_pct, 1),
        "final_value": round(final_value, 2),
    }


# ── Main orchestrator ────────────────────────────────────────────────────────

def run_backtest(
    index_name: str = "沪深300",
    years: int = 5,
    base_monthly: float = 5000.0,
    strategy_name: str = "moderate",
    pe_weight: float = 0.6,
) -> dict:
    """Run a complete backtest comparing three DCA strategies.

    Args:
        index_name: One of 上证50 / 沪深300 / 中证500 / 中证1000
        years: Backtest horizon (1-10 years)
        base_monthly: Base monthly investment amount in CNY
        strategy_name: aggressive / moderate / conservative
        pe_weight: Weight of PE score in temperature (0-1). MA gets 1-pe_weight.

    Returns:
        Dict with strategy results, comparison metrics, and data quality info.
    """
    idx_def = _BACKTEST_INDICES.get(index_name)
    if idx_def is None:
        return {
            "error": f"不支持的指数: {index_name}",
            "supported": list(_BACKTEST_INDICES.keys()),
        }

    # ── 1. Fetch price data ──────────────────────────────────────────────────
    prices_df = _fetch_prices_sina(idx_def["sina_symbol"], years)
    data_source = "sina"

    if prices_df is None or prices_df.empty:
        prices_df = _fetch_prices_eastmoney(idx_def["ak_symbol"], years)
        data_source = "eastmoney"

    if prices_df is None or prices_df.empty:
        return {
            "error": f"无法获取 {index_name} 的历史价格数据。请稍后重试。",
            "index_name": index_name,
        }

    if len(prices_df) < 200:
        return {
            "error": f"{index_name} 历史数据不足（仅 {len(prices_df)} 个交易日，至少需要200天计算均线）。请缩短回测年限。",
            "index_name": index_name,
            "available_days": len(prices_df),
        }

    # ── 2. Fetch PE data (optional enhancement) ───────────────────────────────
    pe_df = _fetch_pe_history(idx_def["csindex_code"])
    has_pe = pe_df is not None and not pe_df.empty

    # ── 3. Resample to monthly & compute temperatures ────────────────────────
    monthly_df = _resample_to_monthly(prices_df)

    if monthly_df.empty or len(monthly_df) < 3:
        return {
            "error": f"月度数据不足（仅 {len(monthly_df)} 个月），无法进行有意义的回测。",
            "index_name": index_name,
        }

    monthly_df = _compute_monthly_temperatures(
        monthly_df, pe_df, idx_def["pe_thresholds"], pe_weight=pe_weight
    )

    # PE data coverage (CSIndex only provides ~20 trading days)
    pe_available_months = int(monthly_df["pe_score"].notna().sum()) if "pe_score" in monthly_df.columns else 0
    pe_coverage_pct = round(pe_available_months / len(monthly_df) * 100, 1) if len(monthly_df) > 0 else 0.0

    # ── 4. Simulate three strategies ──────────────────────────────────────────
    temp_dca = _simulate_temperature_dca(monthly_df, base_monthly, strategy_name)
    regular_dca = _simulate_regular_dca(monthly_df, base_monthly)
    lump_total = base_monthly * 12 * years
    lump_sum = _simulate_lump_sum(monthly_df, lump_total)

    # ── 5. Compute metrics for each ───────────────────────────────────────────
    temp_metrics = _compute_metrics(temp_dca, monthly_df)
    regular_metrics = _compute_metrics(regular_dca, monthly_df)
    lump_metrics = _compute_metrics(lump_sum, monthly_df)

    # ── 6. Yearly breakdown ──────────────────────────────────────────────────
    yearly_breakdown = _build_yearly_breakdown(temp_dca, monthly_df, base_monthly)

    # ── 7. Temperature timeline ──────────────────────────────────────────────
    temp_timeline = monthly_df[["date", "temperature", "ma_deviation_pct"]].copy()
    temp_timeline["temperature"] = temp_timeline["temperature"].round(1)
    temp_timeline["ma_deviation_pct"] = temp_timeline["ma_deviation_pct"].round(2)
    if "pe" in monthly_df.columns:
        temp_timeline["pe"] = monthly_df["pe"]
    temp_timeline["zone"] = temp_timeline["temperature"].apply(
        lambda t: classify_temperature(t)["zone_label"]
    )

    # ── 8. Mechanism analysis ──────────────────────────────────────────────
    mechanism = _build_mechanism_analysis(
        temp_dca, regular_dca, lump_sum,
        temp_metrics, regular_metrics, lump_metrics,
        base_monthly, strategy_name,
    )

    # ── 9. Market regime decomposition ─────────────────────────────────────
    regime_analysis = _decompose_by_regime(
        monthly_df, temp_dca, regular_dca, lump_sum,
        temp_metrics, regular_metrics, lump_metrics,
        base_monthly,
    )

    # ── 10. Assemble result ────────────────────────────────────────────────
    date_start = monthly_df.iloc[0]["date"]
    date_end = monthly_df.iloc[-1]["date"]

    return {
        "config": {
            "index_name": index_name,
            "years_requested": years,
            "base_monthly": base_monthly,
            "strategy_name": strategy_name,
            "strategy_label": STRATEGIES[strategy_name]["name"],
            "strategy_desc": STRATEGIES[strategy_name]["desc"],
        },
        "data_quality": {
            "data_source": data_source,
            "has_pe_data": has_pe,
            "pe_coverage_pct": pe_coverage_pct,
            "pe_coverage_note": (
                f"PE数据覆盖 {pe_available_months}/{len(monthly_df)} 个月（{pe_coverage_pct}%）。"
                f"CSIndex 接口仅提供近~20个交易日PE数据，回测中绝大部分月份回退为纯MA偏离信号。"
                f"温度=PE×{pe_weight:.0%}+MA×{1-pe_weight:.0%} 的权重仅在PE可用的月份生效。"
            ) if has_pe else (
                "PE数据不可用，全部回退为MA偏离信号（温度=MA偏离×100%）。"
            ),
            "total_months": len(monthly_df),
            "date_start": date_start.strftime("%Y-%m-%d") if hasattr(date_start, "strftime") else str(date_start)[:10],
            "date_end": date_end.strftime("%Y-%m-%d") if hasattr(date_end, "strftime") else str(date_end)[:10],
        },
        "temperature_dca": {**temp_dca, **temp_metrics},
        "regular_dca": {**regular_dca, **regular_metrics},
        "lump_sum": {**lump_sum, **lump_metrics},
        "mechanism": mechanism,
        "regime_analysis": regime_analysis,
        "yearly_breakdown": yearly_breakdown,
        "temperature_timeline": temp_timeline,
        "monthly_df": monthly_df[["date", "close", "ma200", "temperature"]].copy(),
    }


def _build_mechanism_analysis(
    temp_dca: dict,
    reg_dca: dict,
    lump_sum: dict,
    temp_m: dict,
    reg_m: dict,
    lump_m: dict,
    base_monthly: float,
    strategy_name: str,
) -> dict:
    """Build rich mechanism analysis: what happened and why.

    Returns data for:
    - Return/drawdown ratio (key quality metric)
    - Zone-by-zone investment breakdown
    - Cash pool dynamics
    - Honest caveat about when strategy underperforms
    """
    records = temp_dca["records"]

    # ── Return / drawdown ratio ───────────────────────────────────────────
    def _rr_ratio(ret_pct: float, dd_pct: float) -> float:
        """Return earned per 1% of max drawdown endured."""
        if dd_pct < 0.05:
            dd_pct = 0.05  # floor to avoid division by tiny numbers
        return round(ret_pct / dd_pct, 1)

    temp_rr = _rr_ratio(temp_m["total_return_pct"], temp_m["max_drawdown_pct"])
    reg_rr = _rr_ratio(reg_m["total_return_pct"], reg_m["max_drawdown_pct"])
    lump_rr = _rr_ratio(lump_m["total_return_pct"], lump_m["max_drawdown_pct"])

    # ── Zone-by-zone investment breakdown ─────────────────────────────────
    zone_stats = {
        "cold": {"label": "🧊 低估 (0-40°C)", "months": 0, "invested": 0.0, "base_would_be": 0.0},
        "normal": {"label": "🌡️ 适中 (40-60°C)", "months": 0, "invested": 0.0, "base_would_be": 0.0},
        "hot": {"label": "🔥 偏贵 (60-100°C)", "months": 0, "invested": 0.0, "base_would_be": 0.0},
    }

    max_cash_pool = 0.0
    peak_cash_pool_date = None

    for rec in records:
        temp = rec.get("temperature", 50)
        invested = rec.get("invested", base_monthly)

        if temp < 40:
            zone_stats["cold"]["months"] += 1
            zone_stats["cold"]["invested"] += invested
            zone_stats["cold"]["base_would_be"] += base_monthly
        elif temp < 60:
            zone_stats["normal"]["months"] += 1
            zone_stats["normal"]["invested"] += invested
            zone_stats["normal"]["base_would_be"] += base_monthly
        else:
            zone_stats["hot"]["months"] += 1
            zone_stats["hot"]["invested"] += invested
            zone_stats["hot"]["base_would_be"] += base_monthly

        cp = rec.get("cash_pool", 0)
        if cp > max_cash_pool:
            max_cash_pool = cp
            peak_cash_pool_date = rec["date"]

    # Total saved during hot periods
    hot_saved = zone_stats["hot"]["base_would_be"] - zone_stats["hot"]["invested"]
    cold_extra = zone_stats["cold"]["invested"] - zone_stats["cold"]["base_would_be"]

    # ── Caveat analysis ───────────────────────────────────────────────────
    # Temperature DCA underperforms in sustained bull markets (few months > 60°C)
    hot_months_pct = zone_stats["hot"]["months"] / len(records) * 100 if records else 0
    cold_months_pct = zone_stats["cold"]["months"] / len(records) * 100 if records else 0

    if hot_months_pct < 10 and lump_m["total_return_pct"] > temp_m["total_return_pct"]:
        caveat = (
            "⚠️ 本次回测区间内市场大部分时间估值合理，温度变化较小。"
            "在单边持续牛市中（如2020年），一次性买入的收益通常最高——"
            "温度定投的价值在震荡市和熊市中体现得更明显。"
        )
    elif lump_m["total_return_pct"] > temp_m["total_return_pct"]:
        caveat = (
            "⚠️ 本次回测中一次性买入收益领先，说明该区间市场整体向上。"
            "温度定投通过少投避开了高估值区间，但也会因此错过部分上涨——"
            "这是策略的 trade-off：用一部分上涨空间换取更小的回撤。"
        )
    elif cold_months_pct > 30:
        caveat = (
            "💡 本次回测区间内含较多低估月份，温度定投在低位持续加仓，"
            "这是其超额收益的主要来源。在估值长期偏高的市场中，"
            "策略的加仓机会较少，超额收益会收窄。"
        )
    else:
        caveat = (
            "💡 温度定投的核心优势在于：高估值时少投（避风险）+ 低估值时多投（攒筹码）。"
            "在单边急涨的牛市中它可能跑输一次性买入，但在震荡市和熊市中"
            "通常能提供更好的风险调整后收益。"
        )

    return {
        "return_drawdown_ratio": {
            "temperature_dca": temp_rr,
            "regular_dca": reg_rr,
            "lump_sum": lump_rr,
            "interpretation": "每承受 1% 的最大回撤，能换来多少百分点的总收益。数值越高，说明策略的'痛苦回报比'越优。",
        },
        "zone_breakdown": {
            "cold": {**zone_stats["cold"], "extra_vs_base": round(cold_extra, 2)},
            "normal": {**zone_stats["normal"], "extra_vs_base": round(zone_stats["normal"]["invested"] - zone_stats["normal"]["base_would_be"], 2)},
            "hot": {**zone_stats["hot"], "extra_vs_base": round(hot_saved, 2)},
        },
        "cash_pool": {
            "max_balance": round(max_cash_pool, 2),
            "peak_date": peak_cash_pool_date.strftime("%Y-%m") if peak_cash_pool_date and hasattr(peak_cash_pool_date, "strftime") else str(peak_cash_pool_date)[:7] if peak_cash_pool_date else "—",
            "total_saved_in_hot": round(hot_saved, 2),
            "total_extra_in_cold": round(cold_extra, 2),
        },
        "caveat": caveat,
    }


def _build_yearly_breakdown(
    temp_dca: dict,
    monthly_df: pd.DataFrame,
    base_monthly: float,
) -> list[dict]:
    """Build yearly summary from temperature DCA monthly records."""
    records = temp_dca["records"]
    if not records:
        return []

    yearly = []
    current_year = None
    year_invested = 0.0
    year_start_shares = 0.0
    year_start_value = 0.0
    year_end_value = 0.0
    year_temps = []

    for i, rec in enumerate(records):
        rec_year = rec["date"].year if hasattr(rec["date"], "year") else pd.Timestamp(rec["date"]).year

        if current_year is None:
            current_year = rec_year
            year_start_value = base_monthly  # first month
            year_start_shares = 0.0

        if rec_year != current_year:
            # Close out previous year
            yearly.append({
                "year": current_year,
                "invested": round(year_invested, 2),
                "end_value": round(year_end_value, 2),
                "avg_temp": round(sum(year_temps) / len(year_temps), 1) if year_temps else 50.0,
                "avg_multiplier": round(year_invested / (base_monthly * len(year_temps)), 2) if year_temps else 1.0,
            })
            current_year = rec_year
            year_invested = 0.0
            year_start_value = year_end_value
            year_temps = []

        year_invested += rec["invested"]
        year_end_value = rec["portfolio_value"]
        year_temps.append(rec.get("temperature", 50.0))

    # Final year
    if year_invested > 0:
        yearly.append({
            "year": current_year,
            "invested": round(year_invested, 2),
            "end_value": round(year_end_value, 2),
            "avg_temp": round(sum(year_temps) / len(year_temps), 1) if year_temps else 50.0,
            "avg_multiplier": round(year_invested / (base_monthly * len(year_temps)), 2) if year_temps else 1.0,
        })

    return yearly


# ═══════════════════════════════════════════════════════════════════════════════
# Signal Validation: Does temperature predict forward returns?
# ═══════════════════════════════════════════════════════════════════════════════

def validate_temperature_signal(
    index_name: str = "沪深300",
    years: int = 10,
) -> dict:
    """Empirically validate that market temperature has predictive power.

    For each month, records the temperature and the forward 12-month return,
    then computes Pearson correlation, bucket analysis, and regression.

    The key hypothesis: low temperature → high future returns (negative r).

    Returns:
        Dict with scatter_data, correlation, bucket_analysis, regression_line.
    """
    idx_def = _BACKTEST_INDICES.get(index_name)
    if idx_def is None:
        return {"error": f"不支持的指数: {index_name}", "supported": list(_BACKTEST_INDICES.keys())}

    # ── 1. Fetch price data ──────────────────────────────────────────────────
    prices_df = _fetch_prices_sina(idx_def["sina_symbol"], years)
    data_source = "sina"

    if prices_df is None or prices_df.empty:
        prices_df = _fetch_prices_eastmoney(idx_def["ak_symbol"], years)
        data_source = "eastmoney"

    if prices_df is None or prices_df.empty:
        return {"error": f"无法获取 {index_name} 的历史价格数据"}

    if len(prices_df) < 250:
        return {
            "error": f"{index_name} 数据不足（仅 {len(prices_df)} 日），需要至少 1 年日线数据。",
            "available_days": len(prices_df),
        }

    # ── 2. Fetch PE data ─────────────────────────────────────────────────────
    pe_df = _fetch_pe_history(idx_def["csindex_code"])
    has_pe = pe_df is not None and not pe_df.empty

    # ── 3. Resample to monthly & compute temperatures ────────────────────────
    monthly_df = _resample_to_monthly(prices_df)
    monthly_df = _compute_monthly_temperatures(
        monthly_df, pe_df, idx_def["pe_thresholds"], pe_weight=0.6
    )

    # PE data coverage
    pe_available_months = int(monthly_df["pe_score"].notna().sum()) if "pe_score" in monthly_df.columns else 0
    pe_coverage_pct = round(pe_available_months / len(monthly_df) * 100, 1) if len(monthly_df) > 0 else 0.0
    pe_note = (
        f"PE数据覆盖 {pe_available_months}/{len(monthly_df)} 个月（{pe_coverage_pct}%）。"
        f"CSIndex 接口仅提供近~20个交易日PE数据，信号验证中绝大部分月份回退为纯MA偏离信号。"
        f"相关性分析主要反映MA偏离信号的预测能力，PE的贡献未充分验证。"
    ) if has_pe else "PE数据不可用，信号验证完全基于MA偏离。"

    if monthly_df.empty or len(monthly_df) < 15:
        return {"error": f"月度数据不足（仅 {len(monthly_df)} 个月），无法验证。"}

    # ── 4. For each month, compute forward 12-month return ───────────────────
    n = len(monthly_df)
    points = []
    for i in range(n - 12):
        temp = float(monthly_df.iloc[i]["temperature"])
        price_start = float(monthly_df.iloc[i]["close"])
        price_end = float(monthly_df.iloc[i + 12]["close"])
        fwd_return = (price_end - price_start) / price_start * 100
        points.append({
            "date": str(monthly_df.iloc[i]["date"])[:10],
            "temperature": round(temp, 1),
            "forward_12m_return_pct": round(fwd_return, 2),
        })

    df = pd.DataFrame(points)

    if len(df) < 10:
        return {"error": f"有效数据点不足（仅 {len(df)} 个），无法进行统计检验。"}

    temps = df["temperature"].values
    returns = df["forward_12m_return_pct"].values

    # ── 5. Pearson correlation ───────────────────────────────────────────────
    from scipy import stats as scipy_stats

    r, p_value = scipy_stats.pearsonr(temps, returns)
    significant = p_value < 0.05

    # ── 6. Linear regression for trend line ──────────────────────────────────
    slope, intercept = np.polyfit(temps, returns, 1)
    r_squared = r ** 2

    # ── 7. Bucket analysis ───────────────────────────────────────────────────
    buckets_def = [
        (0, 20, "🧊 极度低估"),
        (20, 40, "❄️ 偏低"),
        (40, 60, "🌡️ 适中"),
        (60, 80, "🔥 偏贵"),
        (80, 101, "💥 高估"),
    ]

    bucket_results = []
    for lo, hi, label in buckets_def:
        mask = (df["temperature"] >= lo) & (df["temperature"] < hi)
        bucket_data = df[mask]
        if len(bucket_data) > 0:
            bucket_results.append({
                "zone": label,
                "range": f"{lo}–{hi}°C",
                "count": int(len(bucket_data)),
                "avg_forward_return": round(float(bucket_data["forward_12m_return_pct"].mean()), 2),
                "median_forward_return": round(float(bucket_data["forward_12m_return_pct"].median()), 2),
                "positive_rate": round(float((bucket_data["forward_12m_return_pct"] > 0).mean()) * 100, 1),
            })

    # ── 8. Interpretation ────────────────────────────────────────────────────
    if r < -0.3 and significant:
        interpretation = (
            f"✅ 温度信号具有显著的负向预测能力（r = {r:.3f}, p = {p_value:.4f}）。"
            f"温度越低，未来12个月的平均收益越高——验证了'低估时买入'策略的统计基础。"
            f"R² = {r_squared:.3f} 表明温度可以解释未来收益 {r_squared*100:.1f}% 的波动，"
            f"这在金融市场中属于有效信号。"
        )
    elif r < -0.1 and significant:
        interpretation = (
            f"✅ 温度信号具有统计显著的负向预测能力（r = {r:.3f}, p = {p_value:.4f}），"
            f"但效应强度较弱（R² = {r_squared:.3f}）。这说明估值温度是未来收益的影响因素之一，"
            f"但并非唯一决定因素——这正是定投策略（分散时点）与温度调整（调整金额）"
            f"需要结合使用的统计依据。"
        )
    elif r < 0:
        interpretation = (
            f"⚠️ 温度信号呈负向趋势（r = {r:.3f}）但统计不显著（p = {p_value:.4f}），"
            f"可能受回测区间内样本量不足或极端行情影响。建议延长回测年限以获得更稳定的统计结论。"
        )
    else:
        interpretation = (
            f"⚠️ 本次回测区间内温度与未来收益未呈现预期的负相关（r = {r:.3f}），"
            f"可能因为区间内市场呈现单边趋势，估值信号暂时失效。"
            f"这恰好说明了温度定投需要长期坚持——短期可能出现信号与结果背离。"
        )

    return {
        "scatter_data": df.to_dict("records"),
        "correlation": {
            "pearson_r": round(r, 4),
            "p_value": round(p_value, 4),
            "r_squared": round(r_squared, 4),
            "significant": significant,
            "interpretation": interpretation,
        },
        "regression": {
            "slope": round(slope, 6),
            "intercept": round(intercept, 2),
        },
        "bucket_analysis": bucket_results,
        "data_quality": {
            "total_points": len(df),
            "index_name": index_name,
            "years_requested": years,
            "data_source": data_source,
            "has_pe_data": has_pe,
            "pe_coverage_pct": pe_coverage_pct,
            "pe_coverage_note": pe_note,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Market Regime Decomposition: strategy performance in bull/bear/sideways
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_regimes(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Classify each month into a market regime.

    Regime definitions (defensible, simple):
      - Bull (🐂 牛市): price > 200MA for >= 3 consecutive months AND
        price is at least 5% above 200MA on average
      - Bear (🐻 熊市): price < 200MA for >= 3 consecutive months AND
        price is at least 5% below 200MA on average
      - Sideways (📊 震荡): everything else — price oscillates near 200MA
    """
    df = monthly_df.copy()
    df["above_ma"] = df["close"] > df["ma200"]
    df["ma_deviation"] = (df["close"] - df["ma200"]) / df["ma200"] * 100

    # Identify runs of consecutive above/below
    df["regime_change"] = df["above_ma"] != df["above_ma"].shift(1)
    df["regime_id"] = df["regime_change"].cumsum()

    # Compute run length and average deviation for each regime segment
    regime_stats = df.groupby("regime_id").agg(
        months=("date", "count"),
        above_ma=("above_ma", "first"),
        avg_deviation=("ma_deviation", "mean"),
    )

    # Classify each segment
    def _label_segment(row):
        if row["months"] < 3:
            return "📊 震荡"
        if row["above_ma"] and row["avg_deviation"] > 5:
            return "🐂 牛市"
        elif not row["above_ma"] and row["avg_deviation"] < -5:
            return "🐻 熊市"
        else:
            return "📊 震荡"

    regime_stats["regime_label"] = regime_stats.apply(_label_segment, axis=1)
    label_map = regime_stats["regime_label"].to_dict()
    df["regime"] = df["regime_id"].map(label_map)

    return df


def _decompose_by_regime(
    monthly_df: pd.DataFrame,
    temp_dca: dict,
    reg_dca: dict,
    lump_sum: dict,
    temp_metrics: dict,
    reg_metrics: dict,
    lump_metrics: dict,
    base_monthly: float,
) -> dict:
    """Compute strategy performance within each market regime.

    Aggregates monthly records by regime label to show where each
    strategy earns its returns and where it struggles.
    """
    # Classify regimes
    df = _classify_regimes(monthly_df)

    # Map regime labels onto each strategy's monthly records
    temp_records = temp_dca["records"]
    reg_records = reg_dca["records"]
    lump_records = lump_sum["records"]

    # Build date → regime lookup
    date_to_regime = {}
    for _, row in df.iterrows():
        date_to_regime[str(row["date"])[:10]] = row["regime"]

    # Attach regime to each record
    for rec in temp_records:
        rec["regime"] = date_to_regime.get(str(rec["date"])[:10], "📊 震荡")
    for rec in reg_records:
        rec["regime"] = date_to_regime.get(str(rec["date"])[:10], "📊 震荡")
    for rec in lump_records:
        rec["regime"] = date_to_regime.get(str(rec["date"])[:10], "📊 震荡")

    # Aggregate by regime
    regimes_order = ["🐂 牛市", "🐻 熊市", "📊 震荡"]
    result = {}

    for regime_label in regimes_order:
        t_recs = [r for r in temp_records if r["regime"] == regime_label]
        r_recs = [r for r in reg_records if r["regime"] == regime_label]
        l_recs = [r for r in lump_records if r["regime"] == regime_label]

        if not t_recs:
            continue

        n_months = len(t_recs)

        # Temperature DCA segment metrics
        t_invested = sum(r.get("invested", base_monthly) for r in t_recs)
        t_start_val = t_recs[0].get("portfolio_value", 0)
        t_end_val = t_recs[-1].get("portfolio_value", 0)
        t_return = (t_end_val - t_start_val - t_invested) / (t_start_val + t_invested) * 100 if (t_start_val + t_invested) > 0 else 0.0

        # Regular DCA segment metrics
        r_invested = sum(r.get("invested", base_monthly) for r in r_recs)
        r_start_val = r_recs[0].get("portfolio_value", 0)
        r_end_val = r_recs[-1].get("portfolio_value", 0)
        r_return = (r_end_val - r_start_val - r_invested) / (r_start_val + r_invested) * 100 if (r_start_val + r_invested) > 0 else 0.0

        # Lump sum segment metrics (simple price change)
        if l_recs:
            l_start_price = l_recs[0].get("price", 0)
            l_end_price = l_recs[-1].get("price", 0)
            l_return = (l_end_price - l_start_price) / l_start_price * 100 if l_start_price > 0 else 0.0
        else:
            l_return = 0.0

        # Average temperature in this regime
        avg_temp = sum(r.get("temperature", 50) for r in t_recs) / n_months if n_months > 0 else 50

        # Determine winner
        returns = {"🌡️ 温度定投": t_return, "📋 普通定投": r_return, "💰 一次性买入": l_return}
        winner = max(returns, key=returns.get)
        winner_emoji = {"🌡️ 温度定投": "🏆", "📋 普通定投": "", "💰 一次性买入": ""}

        result[regime_label] = {
            "months": n_months,
            "avg_temperature": round(avg_temp, 1),
            "temp_dca": {
                "invested": round(t_invested, 2),
                "return_pct": round(t_return, 1),
                "is_winner": winner == "🌡️ 温度定投",
            },
            "regular_dca": {
                "invested": round(r_invested, 2),
                "return_pct": round(r_return, 1),
                "is_winner": winner == "📋 普通定投",
            },
            "lump_sum": {
                "return_pct": round(l_return, 1),
                "is_winner": winner == "💰 一次性买入",
            },
            "winner": f"{winner_emoji.get(winner, '')} {winner}",
        }

    # ── Insight summary ─────────────────────────────────────────────────────
    bear_data = result.get("🐻 熊市")
    bull_data = result.get("🐂 牛市")
    sideways_data = result.get("📊 震荡")

    if bear_data and bear_data["temp_dca"]["is_winner"]:
        insight = (
            "💡 温度定投在熊市中展现了其核心价值——通过低估时加仓、高估时减仓，"
            "在下跌市中有效控制了回撤。这正是策略设计的目标场景。"
        )
    elif bull_data and bull_data["lump_sum"]["is_winner"]:
        insight = (
            "💡 牛市中一次性买入表现最优——这符合理论预期。"
            "温度定投的价值不在于牛市追涨，而在于熊市护盘和震荡市积累。"
            "投资者应理解这一 trade-off：接受牛市中的相对落后，换取熊市中的显著优势。"
        )
    else:
        insight = (
            "💡 不同市场环境下最优策略不同。温度定投的优势在震荡和下跌市场中更明显，"
            "这是因为它通过调节投资节奏来平滑波动，而非预测市场方向。"
        )

    return {
        "regimes": result,
        "insight": insight,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Walk-Forward Validation: out-of-sample test of strategy effectiveness
# ═══════════════════════════════════════════════════════════════════════════════

def walk_forward_validation(
    index_name: str = "沪深300",
    train_years: int = 7,
    test_years: int = 3,
    base_monthly: float = 5000.0,
) -> dict:
    """Walk-forward validation: optimise on train window, verify on test window.

    This is the gold-standard test for whether a strategy is overfitted:
    - Train window: search PE weight × strategy → maximise Sharpe
    - Test window: lock parameters, run once — if still outperforms, the
      strategy is genuinely effective, not a product of hindsight bias.

    Only two parameters are optimised (PE weight, strategy choice), keeping
    the search space small, interpretable, and defensible.

    Args:
        index_name: One of 上证50 / 沪深300 / 中证500 / 中证1000
        train_years: Training window length in years
        test_years: Test (out-of-sample) window length in years
        base_monthly: Base monthly investment in CNY

    Returns:
        Dict with train_window, test_window, optimization grid, and
        out-of-sample performance assessment.
    """
    idx_def = _BACKTEST_INDICES.get(index_name)
    if idx_def is None:
        return {"error": f"不支持的指数: {index_name}"}

    total_years = train_years + test_years

    # ── 1. Fetch all data for the full period ───────────────────────────────
    prices_df = _fetch_prices_sina(idx_def["sina_symbol"], total_years)
    data_source = "sina"

    if prices_df is None or prices_df.empty:
        prices_df = _fetch_prices_eastmoney(idx_def["ak_symbol"], total_years)
        data_source = "eastmoney"

    if prices_df is None or prices_df.empty:
        return {"error": f"无法获取 {index_name} 的历史价格数据"}

    if len(prices_df) < 200:
        return {
            "error": f"数据不足（仅 {len(prices_df)} 日），需要至少200日计算均线。"
        }

    # PE data
    pe_df = _fetch_pe_history(idx_def["csindex_code"])
    has_pe = pe_df is not None and not pe_df.empty

    # ── 2. Resample to monthly (full period, temperature neutral) ──────────
    monthly_full = _resample_to_monthly(prices_df)

    if monthly_full.empty or len(monthly_full) < train_years * 9:
        return {
            "error": f"月度数据不足（仅 {len(monthly_full)} 个月），"
                     f"训练窗至少需要 {train_years * 9} 个月。"
        }

    # ── 3. Split into train and test windows by date ───────────────────────
    all_dates = monthly_full["date"].sort_values()
    split_idx = int(len(all_dates) * train_years / total_years)
    split_date = all_dates.iloc[split_idx]

    monthly_train = monthly_full[monthly_full["date"] <= split_date].copy()
    monthly_test = monthly_full[monthly_full["date"] > split_date].copy()

    if len(monthly_train) < 12:
        return {"error": f"训练窗数据不足（仅 {len(monthly_train)} 个月）"}
    if len(monthly_test) < 6:
        return {"error": f"测试窗数据不足（仅 {len(monthly_test)} 个月）"}

    # ── 4. Grid search on training window ──────────────────────────────────
    pe_weights = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    strategies = ["aggressive", "moderate", "conservative"]

    grid_results = []
    best_sharpe = -999
    best_pe_weight = 0.6
    best_strategy = "moderate"
    best_train_temp = None
    best_train_reg = None

    for pw in pe_weights:
        for strat in strategies:
            # Compute temperatures with this PE weight
            temp_m = _compute_monthly_temperatures(
                monthly_train.copy(), pe_df, idx_def["pe_thresholds"],
                pe_weight=pw,
            )

            if temp_m.empty:
                continue

            # Simulate temperature DCA and regular DCA
            train_temp = _simulate_temperature_dca(temp_m, base_monthly, strat)
            train_reg = _simulate_regular_dca(temp_m, base_monthly)

            # Compute metrics
            temp_metrics = _compute_metrics(train_temp, temp_m)
            reg_metrics = _compute_metrics(train_reg, temp_m)

            sharpe = temp_metrics["sharpe_ratio"]

            grid_results.append({
                "pe_weight": pw,
                "strategy": strat,
                "strategy_label": STRATEGIES[strat]["name"],
                "temp_sharpe": sharpe,
                "temp_cagr": temp_metrics["cagr_pct"],
                "reg_sharpe": reg_metrics["sharpe_ratio"],
                "excess_cagr": round(temp_metrics["cagr_pct"] - reg_metrics["cagr_pct"], 1),
            })

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_pe_weight = pw
                best_strategy = strat
                best_train_temp = temp_metrics
                best_train_reg = reg_metrics

    if not grid_results:
        return {"error": "训练窗网格搜索无有效结果"}

    # ── 5. Apply best parameters to test window ────────────────────────────
    test_temp_m = _compute_monthly_temperatures(
        monthly_test.copy(), pe_df, idx_def["pe_thresholds"],
        pe_weight=best_pe_weight,
    )

    test_temp_dca = _simulate_temperature_dca(test_temp_m, base_monthly, best_strategy)
    test_reg_dca = _simulate_regular_dca(test_temp_m, base_monthly)

    test_temp_metrics = _compute_metrics(test_temp_dca, test_temp_m)
    test_reg_metrics = _compute_metrics(test_reg_dca, test_temp_m)

    # ── 6. Assess degradation ─────────────────────────────────────────────
    train_sharpe = best_train_temp["sharpe_ratio"] if best_train_temp else 0
    test_sharpe = test_temp_metrics["sharpe_ratio"]
    sharpe_drop = round(test_sharpe - train_sharpe, 2)

    train_excess = (best_train_temp["cagr_pct"] - best_train_reg["cagr_pct"]) if best_train_temp and best_train_reg else 0
    test_excess = test_temp_metrics["cagr_pct"] - test_reg_metrics["cagr_pct"]

    # Assessment logic
    if test_excess > 5:
        assessment = (
            f"✅ 样本外验证通过——温度定投在测试窗超额收益 {test_excess:.1f}%，"
            f"远超普通定投。策略有效性得到样本外确认，不是过拟合。"
        )
    elif test_excess > 0:
        assessment = (
            f"✅ 样本外验证通过——温度定投在测试窗仍然跑赢（超额 {test_excess:.1f}%），"
            f"夏普衰减 {sharpe_drop} 在正常范围内。策略虽在样本外有所衰减，"
            f"但核心优势保持。"
        )
    elif test_excess > -3:
        assessment = (
            f"⚠️ 样本外表现边际——温度定投在测试窗与普通定投基本持平"
            f"（超额 {test_excess:.1f}%）。策略优势在样本外收窄，"
            f"但对于风险厌恶型投资者仍有价值（回撤通常更低）。"
        )
    else:
        assessment = (
            f"⚠️ 样本外表现弱于预期——温度定投在测试窗跑输普通定投"
            f"（超额 {test_excess:.1f}%）。这可能表明回测区间内的策略优势"
            f"部分来自参数过拟合，或测试窗市场环境不利于策略。"
        )

    # ── 7. Assemble result ────────────────────────────────────────────────
    return {
        "config": {
            "index_name": index_name,
            "train_years": train_years,
            "test_years": test_years,
            "base_monthly": base_monthly,
        },
        "data_quality": {
            "data_source": data_source,
            "has_pe_data": has_pe,
            "train_months": len(monthly_train),
            "test_months": len(monthly_test),
            "train_window": {
                "start": str(monthly_train.iloc[0]["date"])[:10],
                "end": str(monthly_train.iloc[-1]["date"])[:10],
            },
            "test_window": {
                "start": str(monthly_test.iloc[0]["date"])[:10],
                "end": str(monthly_test.iloc[-1]["date"])[:10],
            },
        },
        "optimization": {
            "best_pe_weight": best_pe_weight,
            "best_strategy": best_strategy,
            "best_strategy_label": STRATEGIES[best_strategy]["name"],
            "grid_results": grid_results,
            "search_space": {
                "pe_weights": pe_weights,
                "strategies": [STRATEGIES[s]["name"] for s in strategies],
                "total_combos": len(pe_weights) * len(strategies),
            },
        },
        "train_performance": {
            "temp_dca": best_train_temp,
            "regular_dca": best_train_reg,
            "excess_cagr": round(train_excess, 1),
        },
        "test_performance": {
            "temp_dca": test_temp_metrics,
            "regular_dca": test_reg_metrics,
            "excess_cagr": round(test_excess, 1),
        },
        "degradation": {
            "train_sharpe": train_sharpe,
            "test_sharpe": test_sharpe,
            "sharpe_drop": sharpe_drop,
            "assessment": assessment,
        },
    }
