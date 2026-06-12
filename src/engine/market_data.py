"""Market data provider for the dashboard.

Fetches real-time and historical market data from AKShare (primary)
and Yahoo Finance (fallback for US/Korea indices).

All fetch functions return None on individual failure — the caller
handles graceful degradation. The coordinator never raises.
"""

import concurrent.futures
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


# ── Index definitions ────────────────────────────────────────────────────────

_DASHBOARD_INDICES = [
    # A-share indices
    {"name": "沪深300",   "ticker": "000300", "market": "china_a",     "ak_symbol": "000300", "yahoo_symbol": "000300.SS"},
    {"name": "上证指数",  "ticker": "000001", "market": "china_a",     "ak_symbol": "000001", "yahoo_symbol": "000001.SS"},
    {"name": "创业板指",  "ticker": "399006", "market": "china_a",     "ak_symbol": "399006", "yahoo_symbol": "399006.SZ"},
    {"name": "科创50",    "ticker": "000688", "market": "china_a",     "ak_symbol": "000688", "yahoo_symbol": "000688.SS"},
    {"name": "中证500",   "ticker": "000905", "market": "china_a",     "ak_symbol": "000905", "yahoo_symbol": "000905.SS"},
    # Global indices
    {"name": "恒生指数",  "ticker": "HSI",    "market": "global_index","ak_symbol": "HSI",    "yahoo_symbol": "^HSI"},
    {"name": "恒生科技",  "ticker": "HSTECH", "market": "global_index","ak_symbol": "HSTECH", "yahoo_symbol": "3067.HK"},
    {"name": "标普500",   "ticker": "SPX",    "market": "global_index","ak_symbol": "SPX",    "yahoo_symbol": "^GSPC"},
    {"name": "纳斯达克",  "ticker": "NDX",    "market": "global_index","ak_symbol": "NDX",    "yahoo_symbol": "^IXIC"},
    {"name": "韩国KOSPI", "ticker": "KS11",   "market": "global_index","ak_symbol": "KS11",   "yahoo_symbol": "^KS11"},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _compute_change(current: float, previous: float) -> tuple[float, float]:
    """Return (change_amount, change_pct) between current and previous close."""
    if previous is None or previous == 0:
        return 0.0, 0.0
    change = current - previous
    change_pct = (change / previous) * 100
    return change, change_pct


def _standardize_df(df: pd.DataFrame, date_col: str, close_col: str) -> pd.DataFrame:
    """Standardize a raw DataFrame to [date, close] format.

    Args:
        df: Raw DataFrame from AKShare or yfinance.
        date_col: Name of the date column in df.
        close_col: Name of the close/price column in df.

    Returns:
        DataFrame with columns ['date', 'close'], sorted by date, NaN dropped.
    """
    result = pd.DataFrame({
        "date": pd.to_datetime(df[date_col]),
        "close": pd.to_numeric(df[close_col], errors="coerce"),
    })
    result = result.dropna(subset=["close"])
    result = result.sort_values("date")
    return result


# ── A-share index fetcher ────────────────────────────────────────────────────

def _fetch_china_index(symbol: str, days: int = 45) -> Optional[pd.DataFrame]:
    """Fetch A-share index history via AKShare.

    Uses ak.index_zh_a_hist() which returns daily OHLCV data.

    Args:
        symbol: Index code (e.g. '000300' for CSI 300).
        days: Number of calendar days to look back.

    Returns:
        DataFrame with ['date', 'close'] or None on failure.
    """
    try:
        import akshare as ak
    except ImportError:
        logger.warning("akshare_not_installed")
        return None

    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        df = ak.index_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
        )

        if df is None or df.empty:
            logger.warning("china_index_empty", symbol=symbol)
            return None

        return _standardize_df(df, date_col="日期", close_col="收盘")

    except Exception as e:
        logger.warning("china_index_failed", symbol=symbol, error=str(e)[:100])
        return None


# ── Global index fetcher ─────────────────────────────────────────────────────

def _fetch_global_index(symbol: str, yahoo_symbol: str, days: int = 45) -> Optional[pd.DataFrame]:
    """Fetch global index history via AKShare, with Yahoo Finance fallback.

    Args:
        symbol: AKShare symbol (e.g. 'HSI', 'SPX').
        yahoo_symbol: Yahoo Finance ticker (e.g. '^HSI', '^GSPC').
        days: Number of calendar days to look back.

    Returns:
        DataFrame with ['date', 'close'] or None on failure.
    """
    df = None

    # Try AKShare first
    try:
        import akshare as ak
        df = ak.index_global_hist_em(symbol=symbol)

        if df is not None and not df.empty:
            df = _standardize_df(df, date_col="日期", close_col="收盘")
            # Filter to requested date range (global API returns all history)
            if df is not None:
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
                df = df[df["date"] >= cutoff]
    except ImportError:
        pass
    except Exception as e:
        logger.warning("global_index_akshare_failed", symbol=symbol, error=str(e)[:100])

    # Fallback to Yahoo Finance
    if df is None or df.empty:
        try:
            import yfinance as yf
            ticker = yf.Ticker(yahoo_symbol)
            yf_df = ticker.history(period="1mo")
            if yf_df is not None and not yf_df.empty:
                yf_df = yf_df.reset_index()
                yf_df = yf_df.rename(columns={"Date": "date", "Close": "close"})
                df = yf_df[["date", "close"]].copy()
                df["date"] = pd.to_datetime(df["date"])
        except Exception as e:
            logger.warning("global_index_yahoo_failed", symbol=yahoo_symbol, error=str(e)[:100])
            return None

    if df is None or df.empty:
        return None

    return df.sort_values("date")


# ── Public: Index quotes ─────────────────────────────────────────────────────

def fetch_index_quotes() -> list[dict]:
    """Fetch current quotes and 30-day sparkline data for all dashboard indices.

    Returns:
        List of dicts, each containing name, ticker, price, change, change_pct,
        sparkline (list of 30 close values), market, and optional error.
        On individual failure, price/change are None and error is set.
    """

    def _fetch_one(idx_def: dict) -> dict:
        """Fetch a single index and return the formatted result."""
        name = idx_def["name"]
        market = idx_def["market"]
        symbol = idx_def["ak_symbol"]
        yahoo = idx_def["yahoo_symbol"]

        result = {
            "name": name,
            "ticker": idx_def["ticker"],
            "price": None,
            "change": None,
            "change_pct": None,
            "sparkline": [],
            "market": market,
            "error": None,
        }

        # Fetch history
        if market == "china_a":
            df = _fetch_china_index(symbol)
        else:
            df = _fetch_global_index(symbol, yahoo)

        if df is None or df.empty or len(df) < 2:
            result["error"] = "数据获取失败"
            return result

        # Extract latest close and sparkline
        closes = df["close"].tolist()
        if len(closes) < 2:
            result["error"] = "数据不足"
            return result

        current = closes[-1]
        previous = closes[-2]
        change, change_pct = _compute_change(current, previous)

        # Use last 30 points for sparkline
        sparkline = closes[-30:] if len(closes) >= 30 else closes

        result["price"] = round(float(current), 4)
        result["change"] = round(float(change), 4)
        result["change_pct"] = round(float(change_pct), 2)
        result["sparkline"] = [round(float(v), 4) for v in sparkline]

        return result

    # Fetch all indices in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_one, idx): idx for idx in _DASHBOARD_INDICES}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result(timeout=30))
            except Exception as e:
                idx = futures[future]
                results.append({
                    "name": idx["name"],
                    "ticker": idx["ticker"],
                    "price": None, "change": None, "change_pct": None,
                    "sparkline": [], "market": idx["market"],
                    "error": f"超时: {str(e)[:80]}",
                })

    # Restore original order
    ticker_order = {idx["ticker"]: i for i, idx in enumerate(_DASHBOARD_INDICES)}
    results.sort(key=lambda r: ticker_order.get(r["ticker"], 999))

    return results


# ── Public: Fast index snapshots (Yahoo Finance, no sparklines) ──────────────

def fetch_index_snapshots() -> list[dict]:
    """Fetch index snapshots (price + change, NO sparklines) via Yahoo Finance.

    Uses batch download (yf.download) for all 10 indices in ONE call — avoids
    rate limiting and is much faster (~2-3 seconds total).

    Returns list of dicts with name, ticker, price, change, change_pct, market, error.
    """
    try:
        import yfinance as yf

        yahoo_symbols = [idx["yahoo_symbol"] for idx in _DASHBOARD_INDICES]
        ticker_to_idx = {idx["yahoo_symbol"]: idx for idx in _DASHBOARD_INDICES}

        # Batch download: one API call for all tickers, 5 days of data
        hist = yf.download(yahoo_symbols, period="5d", progress=False, auto_adjust=True)

        results = []
        for idx in _DASHBOARD_INDICES:
            yahoo = idx["yahoo_symbol"]
            result = {
                "name": idx["name"],
                "ticker": idx["ticker"],
                "price": None,
                "change": None,
                "change_pct": None,
                "sparkline": [],
                "market": idx.get("market", ""),
                "error": None,
            }

            try:
                # yf.download returns multi-level columns: ('Close', 'TICKER')
                if yahoo in hist.get("Close", hist):
                    closes = hist["Close"][yahoo].dropna()
                    if len(closes) >= 1:
                        current = float(closes.iloc[-1])
                        if len(closes) >= 2:
                            previous = float(closes.iloc[-2])
                            change, change_pct = _compute_change(current, previous)
                        else:
                            change, change_pct = 0.0, 0.0
                        result["price"] = round(current, 4)
                        result["change"] = round(change, 4)
                        result["change_pct"] = round(change_pct, 2)
                    else:
                        result["error"] = "数据不足"
                else:
                    result["error"] = "数据不足"
            except (KeyError, IndexError, TypeError):
                result["error"] = "数据获取失败"

            results.append(result)

        return results

    except Exception as e:
        logger.warning("yahoo_batch_snapshot_failed", error=str(e)[:100])
        # Fallback: return all with error
        return [
            {"name": idx["name"], "ticker": idx["ticker"],
             "price": None, "change": None, "change_pct": None,
             "sparkline": [], "market": idx.get("market", ""),
             "error": "数据获取失败"}
            for idx in _DASHBOARD_INDICES
        ]


# ── Public: Slow index sparklines (Yahoo Finance, 1-month history) ───────────

def fetch_index_sparklines() -> dict[str, list[float]]:
    """Fetch 30-day sparkline data for all dashboard indices via Yahoo Finance.

    Uses batch download for all indices in one call.

    Returns dict mapping ticker -> list of close values.
    """
    try:
        import yfinance as yf

        yahoo_symbols = [idx["yahoo_symbol"] for idx in _DASHBOARD_INDICES]
        ticker_map = {idx["yahoo_symbol"]: idx["ticker"] for idx in _DASHBOARD_INDICES}

        hist = yf.download(yahoo_symbols, period="1mo", progress=False, auto_adjust=True)

        results: dict[str, list[float]] = {}
        for yahoo, ticker_key in ticker_map.items():
            try:
                if yahoo in hist.get("Close", hist):
                    closes = hist["Close"][yahoo].dropna().tolist()
                    if len(closes) >= 2:
                        sparkline = closes[-30:] if len(closes) >= 30 else closes
                        results[ticker_key] = [round(float(v), 4) for v in sparkline]
                        continue
            except (KeyError, IndexError, TypeError):
                pass
            results[ticker_key] = []

        return results

    except Exception as e:
        logger.warning("yahoo_batch_sparklines_failed", error=str(e)[:100])
        return {idx["ticker"]: [] for idx in _DASHBOARD_INDICES}


# ── Public: Fast market snapshot coordinator ──────────────────────────────────

def fetch_market_snapshot(asset_universe: list[dict] = None) -> dict:
    """Fetch fast market data: index prices, sectors, macro indicators.

    All three categories fetch in parallel.
    Target: < 5 seconds total.

    Returns dict with keys: indices, sectors, macro, timestamp.
    """
    results = {
        "indices": [],
        "sectors": None,
        "macro": {},
        "timestamp": datetime.now(),
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_indices = executor.submit(fetch_index_snapshots)
        future_sectors = executor.submit(fetch_sector_performance)
        future_macro = executor.submit(fetch_macro_indicators)

        try:
            results["indices"] = future_indices.result(timeout=30)
        except Exception as e:
            logger.warning("snapshot_indices_failed", error=str(e)[:100])

        try:
            results["sectors"] = future_sectors.result(timeout=15)
        except Exception as e:
            logger.warning("snapshot_sectors_failed", error=str(e)[:100])

        try:
            results["macro"] = future_macro.result(timeout=20)
        except Exception as e:
            logger.warning("snapshot_macro_failed", error=str(e)[:100])

    return results


# ── Public: Slow market history coordinator ───────────────────────────────────

def fetch_market_history(asset_universe: list[dict]) -> dict:
    """Fetch slow market data: sparklines and ETF movers.

    Both categories fetch in parallel.
    Target: < 15 seconds. Cached separately (ttl=3600).

    Returns dict with keys: sparklines, etf_movers, timestamp.
    """
    results = {
        "sparklines": {},
        "etf_movers": [],
        "timestamp": datetime.now(),
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_sparklines = executor.submit(fetch_index_sparklines)
        future_etf = executor.submit(fetch_etf_movers, asset_universe)

        try:
            results["sparklines"] = future_sparklines.result(timeout=30)
        except Exception as e:
            logger.warning("history_sparklines_failed", error=str(e)[:100])

        try:
            results["etf_movers"] = future_etf.result(timeout=60)
        except Exception as e:
            logger.warning("history_etf_failed", error=str(e)[:100])

    return results


# ── Public: Sector performance ───────────────────────────────────────────────

def fetch_sector_performance() -> Optional[pd.DataFrame]:
    """Fetch industry sector performance from AKShare (同花顺板块数据).

    Returns:
        DataFrame with columns: name, change_pct, price, volume, turnover.
        Returns None on failure.
    """
    try:
        import akshare as ak
    except ImportError:
        logger.warning("akshare_not_installed_for_sectors")
        return None

    try:
        df = ak.stock_board_industry_summary_ths()

        if df is None or df.empty:
            logger.warning("sector_data_empty")
            return None

        # Standardize column names — only map first match to avoid duplicates
        col_map = {}
        targets_mapped = set()
        for col in df.columns:
            col_str = str(col)

            if "name" not in targets_mapped and any(kw in col_str for kw in ["板块", "名称", "行业"]):
                col_map[col] = "name"
                targets_mapped.add("name")
            elif "change_pct" not in targets_mapped and "涨跌幅" in col_str:
                col_map[col] = "change_pct"
                targets_mapped.add("change_pct")
            elif "price" not in targets_mapped and any(kw in col_str for kw in ["最新价", "收盘价"]):
                col_map[col] = "price"
                targets_mapped.add("price")
            elif "volume" not in targets_mapped and "成交量" in col_str:
                col_map[col] = "volume"
                targets_mapped.add("volume")
            elif "turnover" not in targets_mapped and "成交额" in col_str:
                col_map[col] = "turnover"
                targets_mapped.add("turnover")
            elif "market_cap" not in targets_mapped and any(kw in col_str for kw in ["总市值", "市值"]):
                col_map[col] = "market_cap"
                targets_mapped.add("market_cap")

        if col_map:
            result = df.rename(columns=col_map)
        else:
            result = df.copy()

        # Drop duplicate columns (keep first occurrence)
        result = result.loc[:, ~result.columns.duplicated(keep="first")]

        # Ensure required columns exist — if name not found, use positional fallback
        if "name" not in result.columns:
            cols = list(result.columns)
            if len(cols) >= 1:
                result = result.rename(columns={cols[0]: "name"})
            if len(cols) >= 2 and "change_pct" not in result.columns:
                result["change_pct"] = pd.to_numeric(df.iloc[:, 1], errors="coerce")
            if len(cols) >= 3 and "price" not in result.columns:
                result["price"] = pd.to_numeric(df.iloc[:, 2], errors="coerce")

        # Select and clean
        keep_cols = ["name"]
        for c in ["change_pct", "price", "volume", "turnover", "market_cap"]:
            if c in result.columns:
                keep_cols.append(c)

        result = result[keep_cols].copy()

        # Convert numeric columns (handle potential duplicate column names)
        for c in keep_cols:
            if c != "name" and c in result.columns:
                # If column name appears multiple times, take first
                col_data = result[c]
                if isinstance(col_data, pd.DataFrame):
                    col_data = col_data.iloc[:, 0]
                result[c] = pd.to_numeric(col_data, errors="coerce")

        result = result.dropna(subset=["name"])
        result = result.sort_values("change_pct", ascending=False, na_position="last")

        result = result.dropna(subset=["name"])
        result = result.sort_values("change_pct", ascending=False, na_position="last")

        return result

    except Exception as e:
        logger.warning("sector_fetch_failed", error=str(e)[:100])
        return None


# ── Public: Macro indicators ─────────────────────────────────────────────────

def _fetch_gold_price() -> Optional[dict]:
    """Fetch latest gold price. Yahoo Finance first (fast), AKShare fallback."""
    # Yahoo Finance — fast (~1s)
    try:
        import yfinance as yf
        gc = yf.Ticker("GC=F")
        hist = gc.history(period="5d")
        if hist is not None and not hist.empty:
            closes = hist["Close"].dropna()
            if len(closes) >= 2:
                current = float(closes.iloc[-1])
                previous = float(closes.iloc[-2])
                change = current - previous
                change_pct = (change / previous * 100) if previous != 0 else 0
                return {
                    "value": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "unit": "美元/盎司",
                }
    except Exception:
        pass

    # AKShare fallback
    try:
        import akshare as ak
        df = ak.futures_foreign_hist(symbol="GC")
        if df is not None and not df.empty:
            close_col = None
            for col in df.columns:
                col_str = str(col)
                if any(kw in col_str for kw in ["收盘", "close", "Close", "最新"]):
                    close_col = col
                    break
            if close_col is None:
                for col in reversed(df.columns):
                    try:
                        pd.to_numeric(df[col])
                        close_col = col
                        break
                    except (ValueError, TypeError):
                        continue
            if close_col:
                price = float(pd.to_numeric(df[close_col]).dropna().iloc[-1])
                if price > 0:
                    return {"value": round(price, 2), "unit": "美元/盎司"}
    except Exception:
        pass

    return None


def _fetch_oil_price() -> Optional[dict]:
    """Fetch latest WTI crude oil price. Yahoo Finance first (fast), AKShare fallback."""
    # Yahoo Finance — fast (~1s)
    try:
        import yfinance as yf
        cl = yf.Ticker("CL=F")
        hist = cl.history(period="5d")
        if hist is not None and not hist.empty:
            closes = hist["Close"].dropna()
            if len(closes) >= 2:
                current = float(closes.iloc[-1])
                previous = float(closes.iloc[-2])
                change = current - previous
                change_pct = (change / previous * 100) if previous != 0 else 0
                return {
                    "value": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "unit": "美元/桶",
                }
    except Exception:
        pass

    # AKShare fallback
    try:
        import akshare as ak
        df = ak.futures_foreign_hist(symbol="CL")
        if df is not None and not df.empty:
            close_col = None
            for col in df.columns:
                col_str = str(col)
                if any(kw in col_str for kw in ["收盘", "close", "Close", "最新"]):
                    close_col = col
                    break
            if close_col is None:
                for col in reversed(df.columns):
                    try:
                        pd.to_numeric(df[col])
                        close_col = col
                        break
                    except (ValueError, TypeError):
                        continue
            if close_col:
                price = float(pd.to_numeric(df[close_col]).dropna().iloc[-1])
                if price > 0:
                    return {"value": round(price, 2), "unit": "美元/桶"}
    except Exception:
        pass

    return None


def _fetch_us10y_yield() -> Optional[dict]:
    """Fetch US 10-year treasury yield. Yahoo first (fast), AKShare fallback."""
    # Yahoo Finance — fast (~1s)
    try:
        import yfinance as yf
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        if hist is not None and not hist.empty:
            closes = hist["Close"].dropna()
            if len(closes) >= 2:
                current = float(closes.iloc[-1])
                previous = float(closes.iloc[-2])
                change = current - previous
                change_pct = (change / previous * 100) if previous != 0 else 0
                return {
                    "value": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "unit": "%",
                }
    except Exception:
        pass

    # AKShare fallback
    try:
        import akshare as ak
        df = ak.bond_zh_us_rate()
        if df is not None and not df.empty:
            for col in df.columns:
                col_str = str(col).lower()
                if "美国" in str(col) and "10" in str(col):
                    val = float(df[col].dropna().iloc[-1])
                    return {"value": round(val, 2), "unit": "%"}
                if "us" in col_str and "10" in col_str:
                    val = float(df[col].dropna().iloc[-1])
                    return {"value": round(val, 2), "unit": "%"}
    except Exception:
        pass

    return None


def _fetch_usdcny() -> Optional[dict]:
    """Fetch USD/CNY exchange rate. Yahoo first (fast), AKShare fallback."""
    # Yahoo Finance — fast (~1s)
    try:
        import yfinance as yf
        cny = yf.Ticker("CNY=X")
        hist = cny.history(period="5d")
        if hist is not None and not hist.empty:
            closes = hist["Close"].dropna()
            if len(closes) >= 2:
                current = float(closes.iloc[-1])
                previous = float(closes.iloc[-2])
                change = current - previous
                change_pct = (change / previous * 100) if previous != 0 else 0
                return {
                    "value": round(current, 4),
                    "change": round(change, 4),
                    "change_pct": round(change_pct, 4),
                    "unit": "",
                }
            elif len(closes) >= 1:
                return {"value": round(float(closes.iloc[-1]), 4), "unit": ""}
    except Exception:
        pass

    # AKShare fallback
    try:
        import akshare as ak
        df = ak.currency_boc_sina()
        if df is not None and not df.empty:
            usd_row = None
            for _, row in df.iterrows():
                row_str = str(row.to_dict())
                if "美元" in row_str or "USD" in row_str.upper():
                    usd_row = row
                    break
            if usd_row is not None:
                for col in df.columns:
                    col_str = str(col)
                    if "折算" in col_str or "中间价" in col_str or "中行" in col_str:
                        val = float(usd_row[col])
                        return {"value": round(val, 4), "unit": ""}
                for col in df.columns:
                    try:
                        val = float(usd_row[col])
                        return {"value": round(val, 4), "unit": ""}
                    except (ValueError, TypeError):
                        continue
    except Exception:
        pass

    return None


def _fetch_vix() -> Optional[dict]:
    """Fetch CBOE VIX (volatility index)."""
    # AKShare doesn't have a direct VIX API — use Yahoo Finance
    try:
        import yfinance as yf
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            latest = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else latest
            change = latest - prev
            change_pct = (change / prev * 100) if prev != 0 else 0
            return {
                "value": round(latest, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "unit": "",
            }
    except Exception as e:
        logger.warning("vix_fetch_failed", error=str(e)[:100])
    return None


def fetch_macro_indicators() -> dict[str, dict]:
    """Fetch all macro indicators in parallel.

    Returns:
        Dict keyed by indicator id: {name, value, change, change_pct, unit, error}.
    """
    indicators = {
        "gold":   {"name": "黄金 (Au99.99)", "unit": "元/克"},
        "oil":    {"name": "WTI 原油", "unit": "美元/桶"},
        "us10y":  {"name": "美国 10Y 国债", "unit": "%"},
        "usdcny": {"name": "美元 / 人民币", "unit": ""},
        "vix":    {"name": "VIX 恐慌指数", "unit": ""},
    }

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_fetch_gold_price): "gold",
            executor.submit(_fetch_oil_price): "oil",
            executor.submit(_fetch_us10y_yield): "us10y",
            executor.submit(_fetch_usdcny): "usdcny",
            executor.submit(_fetch_vix): "vix",
        }

        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                data = future.result(timeout=20)
                if data:
                    results[key] = {**indicators[key], **data}
                else:
                    results[key] = {**indicators[key], "value": None, "error": "数据获取失败"}
            except Exception as e:
                results[key] = {**indicators[key], "value": None, "error": str(e)[:80]}

    return results


# ── Public: ETF movers ───────────────────────────────────────────────────────

def _fetch_etf_return(asset: dict) -> Optional[dict]:
    """Fetch 5-day return for a single ETF.

    Args:
        asset: Asset info dict from risk_weights.yaml with keys:
               ticker, name, market, ak_symbol, yahoo_symbol, _class.

    Returns:
        Dict with ticker, name, asset_class, price, change_pct, or None on failure.
    """
    ticker = asset.get("ticker", "")
    name = asset.get("name", ticker)
    asset_class = asset.get("_class", "unknown")
    market = asset.get("market", "")
    ak_symbol = asset.get("ak_symbol", ticker)
    yahoo_symbol = asset.get("yahoo_symbol", ticker)

    df = None

    # Try AKShare based on market type
    if market in ("a_share", "us_cross"):
        try:
            import akshare as ak
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=14)).strftime("%Y%m%d")
            df = ak.fund_etf_hist_em(
                symbol=ak_symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            )
            if df is not None and not df.empty:
                df = _standardize_df(df, date_col="日期", close_col="收盘")
        except ImportError:
            pass
        except Exception:
            pass
    elif market == "hk":
        try:
            import akshare as ak
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=14)).strftime("%Y%m%d")
            df = ak.stock_hk_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            )
            if df is not None and not df.empty:
                df = _standardize_df(df, date_col="日期", close_col="收盘")
        except ImportError:
            pass
        except Exception:
            pass

    # Fallback to Yahoo Finance
    if df is None or df.empty:
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(yahoo_symbol)
            yf_df = ticker_obj.history(period="5d")
            if yf_df is not None and not yf_df.empty:
                yf_df = yf_df.reset_index()
                yf_df = yf_df.rename(columns={"Date": "date", "Close": "close"})
                df = yf_df[["date", "close"]].copy()
                df["date"] = pd.to_datetime(df["date"])
        except Exception:
            pass

    if df is None or df.empty or len(df) < 2:
        return None

    closes = df["close"].tolist()
    current = closes[-1]
    oldest = closes[0]
    change_pct = ((current - oldest) / oldest * 100) if oldest != 0 else 0

    return {
        "ticker": ticker,
        "name": name,
        "asset_class": asset_class,
        "price": round(float(current), 4),
        "change_pct": round(float(change_pct), 2),
    }


def fetch_etf_movers(asset_universe: list[dict]) -> list[dict]:
    """Fetch recent performance for all ETFs in the asset universe.

    Args:
        asset_universe: List of asset dicts from risk_weights.yaml,
                        each with _class key added.

    Returns:
        List of dicts with ticker, name, asset_class, price, change_pct,
        sorted by change_pct descending. Failed tickers are excluded.
    """
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_fetch_etf_return, asset) for asset in asset_universe]
        for future in concurrent.futures.as_completed(futures):
            try:
                data = future.result(timeout=20)
                if data is not None:
                    results.append(data)
            except Exception:
                pass

    results.sort(key=lambda x: x["change_pct"], reverse=True)
    return results


# ── Public: Coordinator ──────────────────────────────────────────────────────

def fetch_market_dashboard(asset_universe: list[dict]) -> dict:
    """Fetch all market dashboard data in parallel.

    This is the main entry point for the dashboard page. All four data
    categories are fetched concurrently via ThreadPoolExecutor.

    Args:
        asset_universe: List of asset dicts from risk_weights.yaml.

    Returns:
        Dict with keys: indices, sectors, macro, etf_movers, timestamp.
        Individual values may be None/empty on failure — the UI layer
        handles graceful degradation.
    """
    results = {
        "indices": [],
        "sectors": None,
        "macro": {},
        "etf_movers": [],
        "timestamp": datetime.now(),
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_indices = executor.submit(fetch_index_quotes)
        future_sectors = executor.submit(fetch_sector_performance)
        future_macro = executor.submit(fetch_macro_indicators)
        future_etf = executor.submit(fetch_etf_movers, asset_universe)

        try:
            results["indices"] = future_indices.result(timeout=60)
        except Exception as e:
            logger.warning("dashboard_indices_failed", error=str(e)[:100])

        try:
            results["sectors"] = future_sectors.result(timeout=30)
        except Exception as e:
            logger.warning("dashboard_sectors_failed", error=str(e)[:100])

        try:
            results["macro"] = future_macro.result(timeout=30)
        except Exception as e:
            logger.warning("dashboard_macro_failed", error=str(e)[:100])

        try:
            results["etf_movers"] = future_etf.result(timeout=60)
        except Exception as e:
            logger.warning("dashboard_etf_failed", error=str(e)[:100])

    return results
