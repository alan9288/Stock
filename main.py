"""
股票監控系統 - FastAPI 後端
提供 RESTful API 供 Vue 3 前端使用
支援多用戶認證
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, time as dtime
import pytz
import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.stock_api import stock_api
from services.database import init_db, get_db
from services.models import User, Portfolio, WatchlistItem
from services.power_manager import get_power_status, get_polling_interval
from services.logger import app_logger, log_request, log_error
from routers.auth import router as auth_router, get_current_user
from routers.notifications import router as notifications_router
from routers.watchlist import router as watchlist_router
from routers.reports import router as reports_router
from routers.alerts import router as alerts_router
from routers.holdings import router as holdings_router

# ==========================================
# 初始化
# ==========================================
app = FastAPI(
    title="股票監控 API",
    description="美股/台股監控系統後端（支援多用戶）",
    version="2.0.0"
)


# ==========================================
# 全域錯誤處理
# ==========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全域異常處理器 - 統一錯誤格式"""
    log_error(exc, {"path": request.url.path, "method": request.method})
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "伺服器內部錯誤",
            "detail": str(exc) if app.debug else None
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


# ==========================================
# 請求計時中間件
# ==========================================
@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    """記錄請求時間"""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    # 只記錄 API 請求
    if request.url.path.startswith("/api"):
        log_request(request.method, request.url.path, response.status_code, duration_ms)
    
    return response

# 載入路由
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(watchlist_router)
app.include_router(reports_router)
app.include_router(alerts_router)
app.include_router(holdings_router)

# CORS 設定（僅允許指定的前端域名）
CORS_ORIGINS = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://frontend-alan9288s-projects.vercel.app",
    "https://stock-jade-gamma.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# 啟動事件：初始化資料庫和排程器
@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        print("✅ 資料庫連接成功")
    except Exception as e:
        print(f"⚠️ 資料庫連接失敗（可能尚未啟動 Docker）: {e}")
    
    # 啟動排程器
    try:
        from services.scheduler import start_scheduler
        start_scheduler()
        print("✅ 排程器已啟動")
        print("   - 台股報告: 每日 14:00 (台灣時間)")
        print("   - 美股報告: 每日 05:00 (台灣時間)")
    except Exception as e:
        print(f"⚠️ 排程器啟動失敗: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from services.scheduler import stop_scheduler
        stop_scheduler()
        print("✅ 排程器已停止")
    except Exception as e:
        print(f"⚠️ 排程器停止失敗: {e}")

# 時區設定
TZ_TW = pytz.timezone("Asia/Taipei")
TZ_US = pytz.timezone("America/New_York")


# ==========================================
# 工具函式
# ==========================================
def get_stock_data(symbol: str, market: str = "US") -> dict:
    """取得單一股票數據"""
    data = stock_api.get_quote(symbol, market)
    if "group" not in data:
        data["group"] = None
    return data


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
    return {"message": "股票監控 API", "version": "2.0.0"}


@app.get("/api/market-status")
async def api_market_status():
    """取得台股/美股市場狀態"""
    power_status = get_power_status()
    return {
        "TW": get_market_status("TW"),
        "US": get_market_status("US"),
        "server_time": datetime.now(TZ_TW).strftime("%Y-%m-%d %H:%M:%S"),
        "power_mode": power_status["mode"],
        "polling_interval": power_status["polling_interval"]
    }


@app.get("/api/power-mode")
async def api_power_mode():
    """取得電源模式狀態"""
    return get_power_status()


@app.get("/api/stocks")
async def api_get_stocks(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取得所有監控股票的即時數據
    從資料庫讀取登入用戶的觀察清單
    """
    from sqlalchemy.orm import selectinload
    from services.models import Holding
    
    result = {"TW": [], "US": []}
    
    if not current_user:
        return result
    
    # 先取得用戶的所有持股平均成本
    holdings_result = await db.execute(
        select(Holding)
        .options(selectinload(Holding.transactions))
        .where(Holding.user_id == current_user.id)
    )
    holdings = holdings_result.scalars().all()
    
    # 建立 symbol -> avg_cost 的對照表
    avg_cost_map = {}
    for holding in holdings:
        txns = holding.transactions
        if txns:
            total_quantity = sum(float(t.quantity) for t in txns)
            total_cost = sum(float(t.quantity) * float(t.price) for t in txns)
            avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
            avg_cost_map[holding.symbol] = round(avg_cost, 2)
    
    # 從資料庫讀取用戶的股票
    for market in ["TW", "US"]:
        portfolio_result = await db.execute(
            select(Portfolio).where(
                Portfolio.user_id == current_user.id,
                Portfolio.market == market
            )
        )
        portfolio = portfolio_result.scalar_one_or_none()
        
        if portfolio:
            stocks_result = await db.execute(
                select(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
            )
            items = stocks_result.scalars().all()
            symbols = [item.symbol for item in items]
            
            if symbols:
                stock_data_list = stock_api.get_quotes_batch(symbols, market)
                for stock_data in stock_data_list:
                    stock_data["group"] = portfolio.name
                    # 加入平均成本
                    stock_data["avg_cost"] = avg_cost_map.get(stock_data["symbol"])
                    result[market].append(stock_data)
    
    return result


@app.get("/api/stocks/{symbol}")
async def api_get_single_stock(symbol: str, market: str = "US"):
    """取得單一股票數據"""
    return get_stock_data(symbol.upper(), market)


@app.get("/api/validate-stock/{symbol}")
async def api_validate_stock(symbol: str, market: str = "US"):
    """
    驗證股票代號是否有效
    回傳 { valid: true/false, symbol: string, message: string }
    """
    symbol = symbol.upper()
    
    # 加入台股後綴
    if market == "TW" and not symbol.endswith(".TW"):
        symbol += ".TW"
    
    # 嘗試取得股票資料
    data = get_stock_data(symbol, market)
    
    if data.get("status") == "success" and data.get("price") is not None:
        return {
            "valid": True,
            "symbol": symbol,
            "price": data.get("price"),
            "message": f"{symbol} 驗證成功"
        }
    else:
        return {
            "valid": False,
            "symbol": symbol,
            "price": None,
            "message": f"找不到股票「{symbol}」，請確認代號是否正確"
        }


@app.get("/api/stocks/{symbol}/history")
async def api_get_stock_history(symbol: str, market: str = "US", period: str = "1d"):
    """
    取得股票歷史資料（用於走勢圖）
    period: 1d (日內), 5d, 1mo, 3mo
    """
    import yfinance as yf
    
    symbol = symbol.upper()
    if market == "TW" and not symbol.endswith(".TW"):
        symbol += ".TW"
    
    try:
        ticker = yf.Ticker(symbol)
        
        # 根據時間區間設定 interval
        if period == "1d":
            hist = ticker.history(period="1d", interval="5m")
        elif period == "5d":
            hist = ticker.history(period="5d", interval="15m")
        else:
            hist = ticker.history(period=period, interval="1d")
        
        if hist is None or len(hist) == 0:
            return {"symbol": symbol, "data": [], "error": "無歷史資料"}
        
        # 轉換成圖表格式
        # lightweight-charts 需要 UTC 時間戳，但要轉換為當地時區顯示
        data = []
        for idx, row in hist.iterrows():
            # 取得 UTC 時間戳
            timestamp = int(idx.timestamp())
            
            # 時區偏移量，讓圖表顯示交易所當地時間
            if market == "TW":
                timestamp += 8 * 3600  # 台股: UTC+8
            else:
                timestamp -= 5 * 3600  # 美股: UTC-5 (紐約時間)
            
            data.append({
                "time": timestamp,
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
            })
        
        return {"symbol": symbol, "data": data}
        
    except Exception as e:
        return {"symbol": symbol, "data": [], "error": str(e)}


# ==========================================
# 啟動
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
