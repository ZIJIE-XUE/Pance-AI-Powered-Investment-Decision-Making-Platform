"""Multi-market data provider.

Primary: AKShare (free, no VPN, covers A-share / HK / cross-border US)
Fallback: Yahoo Finance (for markets AKShare doesn't cover well, e.g. Korea ETFs)

Unified interface: fetch adjusted close prices → DataFrame indexed by date, columns = tickers.
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.exceptions import PortfolioOptimizationError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# ── AKShare symbol format by market ───────────────────────────────────────

# AKShare API → (function name, column name for close price, column name for date)
_MARKET_CONFIG = {
    "a_share": {
        "api": "fund_etf_hist_em",
        "close_col": "收盘",
        "date_col": "日期",
        "desc": "A股 / 沪深ETF（通过东方财富）",
    },
    "hk": {
        "api": "stock_hk_hist",
        "close_col": "收盘",
        "date_col": "日期",
        "desc": "港股（通过东方财富）",
    },
    "us_cross": {
        "api": "fund_etf_hist_em",
        "close_col": "收盘",
        "date_col": "日期",
        "desc": "跨境美股ETF（中国上市，跟踪美股指数）",
    },
    "global_index": {
        "api": "index_global_hist_em",
        "close_col": "收盘",
        "date_col": "日期",
        "desc": "全球指数（KOSPI, 恒生, 标普500等）",
    },
}


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convert a yfinance-style period string to start/end dates.

    Args:
        period: e.g. '1y', '5y', '10y', '3mo', '6mo'.

    Returns:
        (start_date_str, end_date_str) in YYYYMMDD format.
    """
    end = datetime.now()

    period_map = {
        "1mo": 30,
        "3mo": 91,
        "6mo": 182,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
        "10y": 3650,
        "max": 7300,  # ~20 years
    }

    # Parse numeric + unit
    period = period.lower().strip()
    if period in period_map:
        days = period_map[period]
    else:
        # Try to parse e.g. "3y" -> 3*365
        import re
        m = re.match(r"(\d+)\s*y", period)
        if m:
            days = int(m.group(1)) * 365
        else:
            days = 365  # default 1y

    start = end - timedelta(days=days)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _fetch_akshare(symbol: str, market: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Fetch historical data from AKShare for a single ticker.

    Args:
        symbol: AKShare symbol (e.g. '510300' for A-share ETF).
        market: One of 'a_share', 'hk', 'us_cross', 'global_index'.
        start: Start date YYYYMMDD.
        end: End date YYYYMMDD.

    Returns:
        DataFrame with columns [date, close] or None on failure.
    """
    import akshare as ak

    config = _MARKET_CONFIG.get(market)
    if config is None:
        return None

    api_name = config["api"]
    close_col = config["close_col"]
    date_col = config["date_col"]

    try:
        if market in ("a_share", "us_cross"):
            # Chinese-listed ETFs use fund_etf_hist_em
            df = ak.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",  # 前复权
            )
        elif market == "hk":
            df = ak.stock_hk_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            )
        elif market == "global_index":
            df = ak.index_global_hist_em(symbol=symbol)
            # Global index API doesn't support date filtering — filter after
            if df is not None and not df.empty:
                df[date_col] = pd.to_datetime(df[date_col])
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end)
                df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]
        else:
            return None

        if df is None or df.empty:
            logger.warning("akshare_empty", symbol=symbol, market=market)
            return None

        # Standardize to [date, close]
        result = pd.DataFrame({
            "date": pd.to_datetime(df[date_col]),
            "close": pd.to_numeric(df[close_col], errors="coerce"),
        })
        result = result.dropna(subset=["close"])
        result = result.sort_values("date")

        if result.empty:
            return None

        logger.info("akshare_ok", symbol=symbol, market=market, rows=len(result))
        return result

    except Exception as e:
        logger.warning("akshare_failed", symbol=symbol, market=market, error=str(e)[:100])
        return None


def _fetch_yahoo(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Fallback: fetch from Yahoo Finance.

    Args:
        ticker: Yahoo Finance ticker (e.g. 'SPY', 'EWY').
        start: Start date YYYY-MM-DD.
        end: End date YYYY-MM-DD.

    Returns:
        DataFrame with columns [date, close] or None on failure.
    """
    import yfinance as yf

    try:
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:8]}"

        data = yf.download(
            ticker,
            start=start_fmt,
            end=end_fmt,
            auto_adjust=True,
            progress=False,
        )

        if data.empty:
            return None

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        result = pd.DataFrame({
            "date": pd.to_datetime(close.index),
            "close": pd.to_numeric(close.values, errors="coerce"),
        })
        result = result.dropna(subset=["close"])
        result = result.sort_values("date")

        logger.info("yahoo_ok", ticker=ticker, rows=len(result))
        return result

    except Exception as e:
        logger.warning("yahoo_failed", ticker=ticker, error=str(e)[:100])
        return None


def fetch_single_ticker(ticker: str, asset_info: dict, period: str = "5y") -> pd.DataFrame:
    """Fetch historical close prices for a single ticker.

    Uses AKShare first, falls back to Yahoo Finance.

    Args:
        ticker: Display ticker (e.g. '510300', 'SPY', '02800').
        asset_info: Asset metadata dict with optional keys:
            - market: 'a_share' | 'hk' | 'us_cross' | 'global_index' | None
            - ak_symbol: Override AKShare symbol (if different from ticker)
            - yahoo_symbol: Yahoo Finance fallback symbol
        period: e.g. '1y', '5y'.

    Returns:
        DataFrame with columns [date, close]. The close column is renamed
        to the ticker for downstream compatibility.
    """
    start, end = _period_to_dates(period)
    market = asset_info.get("market", "")
    ak_symbol = asset_info.get("ak_symbol", ticker)
    yahoo_symbol = asset_info.get("yahoo_symbol", ticker)

    result = None

    # Try AKShare first (for supported markets)
    if market in _MARKET_CONFIG:
        result = _fetch_akshare(ak_symbol, market, start, end)

    # Fallback to Yahoo Finance
    if result is None:
        logger.info("fallback_to_yahoo", ticker=ticker, yahoo_symbol=yahoo_symbol)
        result = _fetch_yahoo(yahoo_symbol, start, end)

    if result is None or result.empty:
        logger.warning("ticker_fetch_failed", ticker=ticker, name=asset_info.get("name", ticker))
        return pd.DataFrame()  # Return empty DataFrame — caller will skip this ticker

    # Rename close column to ticker for compatibility
    result = result.rename(columns={"close": ticker})
    return result


def fetch_historical_prices(
    tickers: list[str],
    period: str = "5y",
    asset_info_map: Optional[dict] = None,
) -> pd.DataFrame:
    """Fetch historical adjusted close prices for multiple tickers.

    Each ticker is fetched independently (different sources), then merged
    on date into a single DataFrame.

    Args:
        tickers: List of ticker symbols.
        period: e.g. '1y', '5y', '10y'.
        asset_info_map: Optional dict mapping ticker → asset metadata dict.
            If None, all tickers are treated as Yahoo Finance tickers.

    Returns:
        DataFrame indexed by date, columns = tickers, values = close prices.
        Dropped rows where >30% of tickers are NaN, forward-filled, then
        any remaining NaN rows dropped.
    """
    if asset_info_map is None:
        asset_info_map = {}

    all_series = []
    skipped = []

    for ticker in tickers:
        info = asset_info_map.get(ticker, {})
        try:
            df_single = fetch_single_ticker(ticker, info, period)
            if df_single is None or df_single.empty:
                skipped.append(ticker)
                continue
            df_single = df_single.set_index("date")
            all_series.append(df_single[ticker])
        except Exception as e:
            logger.warning("fetch_skipped", ticker=ticker, error=str(e)[:100])
            skipped.append(ticker)
            continue

    if not all_series:
        raise PortfolioOptimizationError(
            f"没有成功获取任何资产的历史数据。跳过的资产: {skipped}"
        )

    if skipped:
        logger.info("tickers_skipped", skipped=skipped, reason="数据源不可用（国内网络可能无法访问Yahoo Finance）")

    # Merge all series on date index
    prices = pd.concat(all_series, axis=1, join="outer")

    # Drop columns where >70% of data is NaN
    threshold = int(len(prices) * 0.7)
    prices = prices.dropna(axis=1, thresh=threshold)

    # Forward-fill missing values
    prices = prices.ffill()

    # Drop rows that still have NaN (beginning of series)
    prices = prices.dropna()

    if prices.empty:
        raise PortfolioOptimizationError("合并后没有足够的历史价格数据")

    logger.info("prices_combined", tickers=list(prices.columns), rows=len(prices))
    return prices
