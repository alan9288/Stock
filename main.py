"""
股票監控系統 - FastAPI 後端
提供 RESTful API 供 Vue 3 前端使用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import yfinance as yf
import json
import os
from datetime import datetime, time as dtime
import pytz

# ==========================================
# 初始化
# ==========================================
app = FastAPI(
    title="股票監控 API",
    description="美股/台股監控系統後端",
    version="1.0.0"
)

# CORS 設定（允許 Vue 開發伺服器）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_FILE = "config.json"
TZ_TW = pytz.timezone("Asia/Taipei")
TZ_US = pytz.timezone("America/New_York")

# ==========================================
# Pydantic Models
# ==========================================
class GroupCreate(BaseModel):
    market: str  # "TW" or "US"
    name: str
    stocks: list[str]

class ConfigUpdate(BaseModel):
    market: str
    thresholds: str

# ==========================================
# 工具函式
# ==========================================
def load_config() -> dict:
    """載入設定檔"""
    default = {
        "TW": {"thresholds": "+3 +5 -5 -10", "groups": {}},
        "US": {"thresholds": "+5 +10 -5 -10", "groups": {}}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_config(config: dict):
    """儲存設定檔"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_stock_data(symbol: str) -> dict:
    """取得單一股票數據"""
    try:
        ticker = yf.Ticker(symbol)
        
        # 嘗試 fast_info
        fi = getattr(ticker, "fast_info", None)
        if fi:
            price = fi.last_price
            prev_close = fi.previous_close
            if price and prev_close and prev_close != 0:
                change_pct = (price - prev_close) / prev_close
                return {
                    "symbol": symbol,
                    "price": round(float(price), 2),
                    "prev_close": round(float(prev_close), 2),
                    "change_pct": round(change_pct * 100, 2),
                    "status": "success"
                }
        
        # 備用：history
        hist = ticker.history(period="5d")
        if hist is not None and len(hist) >= 2:
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            change_pct = (price - prev_close) / prev_close
            return {
                "symbol": symbol,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct * 100, 2),
                "status": "success"
            }
    except Exception as e:
        pass
    
    return {
        "symbol": symbol,
        "price": None,
        "prev_close": None,
        "change_pct": None,
        "status": "error"
    }

def get_market_status(market: str) -> dict:
    """取得市場開盤狀態"""
    now_utc = datetime.now(pytz.utc)
    
    if market == "TW":
        now_local = now_utc.astimezone(TZ_TW)
        market_start = dtime(9, 0)
        market_end = dtime(13, 30)
        market_name = "台股"
    else:
        now_local = now_utc.astimezone(TZ_US)
        market_start = dtime(9, 30)
        market_end = dtime(16, 0)
        market_name = "美股"
    
    current_time = now_local.time()
    is_weekday = now_local.weekday() < 5
    
    if is_weekday and market_start <= current_time <= market_end:
        return {
            "market": market,
            "name": market_name,
            "is_open": True,
            "status": "開盤中",
            "local_time": now_local.strftime("%H:%M")
        }
    else:
        return {
            "market": market,
            "name": market_name,
            "is_open": False,
            "status": "休市",
            "local_time": now_local.strftime("%H:%M")
        }

# ==========================================
# API 路由
# ==========================================
@app.get("/")
async def root():
    return {"message": "股票監控 API", "version": "1.0.0"}

@app.get("/api/market-status")
async def api_market_status():
    """取得台股/美股市場狀態"""
    return {
        "TW": get_market_status("TW"),
        "US": get_market_status("US"),
        "server_time": datetime.now(TZ_TW).strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/config")
async def api_get_config():
    """取得設定"""
    return load_config()

@app.put("/api/config/thresholds")
async def api_update_thresholds(data: ConfigUpdate):
    """更新門檻設定"""
    config = load_config()
    if data.market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="Invalid market")
    config[data.market]["thresholds"] = data.thresholds
    save_config(config)
    return {"success": True, "message": "門檻已更新"}

@app.post("/api/groups")
async def api_create_group(data: GroupCreate):
    """新增投資組合"""
    config = load_config()
    if data.market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="Invalid market")
    if data.name in config[data.market]["groups"]:
        raise HTTPException(status_code=400, detail="群組名稱已存在")
    
    # 處理股票代號
    stocks = []
    for s in data.stocks:
        s = s.strip().upper()
        if data.market == "TW" and not s.endswith(".TW"):
            s += ".TW"
        stocks.append(s)
    
    config[data.market]["groups"][data.name] = stocks
    save_config(config)
    return {"success": True, "message": f"已新增 {data.name}"}

@app.delete("/api/groups/{market}/{name}")
async def api_delete_group(market: str, name: str):
    """刪除投資組合"""
    config = load_config()
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="Invalid market")
    if name not in config[market]["groups"]:
        raise HTTPException(status_code=404, detail="群組不存在")
    
    del config[market]["groups"][name]
    save_config(config)
    return {"success": True, "message": f"已刪除 {name}"}

@app.get("/api/stocks")
async def api_get_stocks():
    """取得所有監控股票的即時數據"""
    config = load_config()
    result = {"TW": [], "US": []}
    
    for market in ["TW", "US"]:
        groups = config[market].get("groups", {})
        seen = set()
        
        for group_name, symbols in groups.items():
            for symbol in symbols:
                if symbol in seen:
                    continue
                seen.add(symbol)
                
                stock_data = get_stock_data(symbol)
                stock_data["group"] = group_name
                result[market].append(stock_data)
    
    return result

@app.get("/api/stocks/{symbol}")
async def api_get_single_stock(symbol: str):
    """取得單一股票數據"""
    return get_stock_data(symbol.upper())

# ==========================================
# 啟動
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
