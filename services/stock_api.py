"""
股票資料 API 服務
美股：Finnhub API（即時）
台股：Yahoo Finance（yfinance）

優化功能：
- API 快取機制 (30 秒)
- 批次查詢
- 錯誤重試 (最多 3 次)
"""

import os
import time
import requests
import yfinance as yf
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

# ==========================================
# 快取機制
# ==========================================
class SimpleCache:
    """簡單的記憶體快取"""
    def __init__(self, ttl=30):
        self.cache = {}
        self.ttl = ttl  # 快取存活時間（秒）
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()

# 全域快取實例
quote_cache = SimpleCache(ttl=30)  # 報價快取 30 秒
history_cache = SimpleCache(ttl=60)  # 歷史資料快取 60 秒

# ==========================================
# 重試機制
# ==========================================
def retry(max_attempts=3, delay=1):
    """API 呼叫重試裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            # 所有重試都失敗
            raise last_error
        return wrapper
    return decorator

# ==========================================
# 股票 API 服務
# ==========================================
class StockAPIService:
    def __init__(self):
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        self.finnhub_base = "https://finnhub.io/api/v1"
    
    def get_quote(self, symbol: str, market: str = "US") -> dict:
        """
        取得股票報價（含快取）
        market: "US" 使用 Finnhub, "TW" 使用 Yahoo Finance
        """
        cache_key = f"{market}:{symbol}"
        
        # 檢查快取
        cached = quote_cache.get(cache_key)
        if cached:
            cached["from_cache"] = True
            return cached
        
        # 取得新資料
        if market == "US":
            result = self._get_finnhub_quote(symbol)
        else:
            result = self._get_yahoo_quote(symbol)
        
        # 存入快取（只快取成功的結果）
        if result.get("status") == "success":
            result["from_cache"] = False
            quote_cache.set(cache_key, result)
        
        return result
    
    def get_quotes_batch(self, symbols: list, market: str = "US") -> list:
        """
        批次取得多支股票報價
        減少 API 呼叫次數
        """
        results = []
        uncached_symbols = []
        
        # 先從快取取得
        for symbol in symbols:
            cache_key = f"{market}:{symbol}"
            cached = quote_cache.get(cache_key)
            if cached:
                cached["from_cache"] = True
                results.append(cached)
            else:
                uncached_symbols.append(symbol)
        
        # 批次取得未快取的股票
        for symbol in uncached_symbols:
            result = self.get_quote(symbol, market)
            results.append(result)
        
        return results
    
    @retry(max_attempts=3, delay=1)
    def _get_finnhub_quote(self, symbol: str) -> dict:
        """使用 Finnhub API 取得美股即時報價（含重試）"""
        from .us_stock_names import get_us_stock_name
        
        url = f"{self.finnhub_base}/quote"
        params = {"symbol": symbol, "token": self.finnhub_key}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Finnhub 回傳格式: c=現價, pc=昨收, h=最高, l=最低, o=開盤
        if data.get("c") and data.get("pc"):
            price = data["c"]
            prev_close = data["pc"]
            change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0
            
            # 取得股票名稱
            stock_name = get_us_stock_name(symbol)
            
            return {
                "symbol": symbol,
                "name": stock_name,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "high": data.get("h"),
                "low": data.get("l"),
                "source": "finnhub",
                "status": "success"
            }
        else:
            return self._error_response(symbol, "無法取得 Finnhub 資料")
    
    def _get_yahoo_quote(self, symbol: str) -> dict:
        """使用 Yahoo Finance 取得台股報價"""
        from .tw_stock_names import get_tw_stock_name
        
        try:
            ticker = yf.Ticker(symbol)
            
            # 優先使用中文名稱對照表
            stock_name = get_tw_stock_name(symbol)
            
            # 如果對照表沒有，嘗試從 Yahoo 取得（英文）
            if not stock_name:
                try:
                    info = ticker.info
                    stock_name = info.get("shortName") or info.get("longName")
                except:
                    pass
            
            # 嘗試 fast_info
            fi = getattr(ticker, "fast_info", None)
            if fi:
                price = fi.last_price
                prev_close = fi.previous_close
                if price and prev_close and prev_close != 0:
                    change_pct = ((price - prev_close) / prev_close) * 100
                    return {
                        "symbol": symbol,
                        "name": stock_name,
                        "price": round(float(price), 2),
                        "prev_close": round(float(prev_close), 2),
                        "change_pct": round(change_pct, 2),
                        "source": "yahoo",
                        "status": "success"
                    }
            
            # 備用：使用 history
            hist = ticker.history(period="5d")
            if hist is not None and len(hist) >= 2:
                price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2])
                change_pct = ((price - prev_close) / prev_close) * 100
                return {
                    "symbol": symbol,
                    "name": stock_name,
                    "price": round(price, 2),
                    "prev_close": round(prev_close, 2),
                    "change_pct": round(change_pct, 2),
                    "source": "yahoo",
                    "status": "success"
                }
                
            return self._error_response(symbol, "無法取得 Yahoo 資料")
            
        except Exception as e:
            return self._error_response(symbol, str(e))
    
    def _error_response(self, symbol: str, error: str) -> dict:
        return {
            "symbol": symbol,
            "price": None,
            "prev_close": None,
            "change_pct": None,
            "source": "error",
            "status": "error",
            "error": error
        }
    
    def clear_cache(self):
        """清除所有快取"""
        quote_cache.clear()
        history_cache.clear()


# 單例模式
stock_api = StockAPIService()

