"""
報告路由
每日報告生成和發送 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from services.database import get_db
from services.models import User, Portfolio, WatchlistItem, NotificationSettings
from services.daily_report import (
    generate_daily_report_data,
    generate_report_html,
    generate_market_report_data,
    generate_market_report_html,
    get_trending_recommendations
)
from services.scheduler import get_scheduled_jobs, start_scheduler, stop_scheduler
from routers.auth import get_current_user_required

router = APIRouter(prefix="/api/reports", tags=["報告"])


# ==========================================
# 輔助函式
# ==========================================
async def get_user_watchlist(user_id: int, db: AsyncSession) -> dict:
    """取得用戶的觀察清單"""
    result = {"TW": [], "US": []}
    
    portfolios = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id)
    )
    
    for portfolio in portfolios.scalars().all():
        items = await db.execute(
            select(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
        )
        result[portfolio.market] = [item.symbol for item in items.scalars().all()]
    
    return result


async def send_report_email(user: User, report_html: str, subject: str, db: AsyncSession):
    """發送報告郵件"""
    
    settings_result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    settings = settings_result.scalar_one_or_none()
    
    if not settings or not settings.notification_email:
        raise ValueError("尚未設定通知信箱")
    
    if not settings.enabled:
        raise ValueError("通知已停用")
    
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise ValueError("SMTP 設定不完整")
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = settings.notification_email
    
    msg.attach(MIMEText(report_html, 'html'))
    
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, settings.notification_email, msg.as_string())
    server.quit()
    
    return settings.notification_email


# ==========================================
# 綜合報告 API
# ==========================================
@router.get("/daily")
async def get_daily_report(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """取得今日綜合報告（JSON 格式）"""
    watchlist = await get_user_watchlist(current_user.id, db)
    
    report_data = generate_daily_report_data(
        watchlist_tw=watchlist["TW"],
        watchlist_us=watchlist["US"]
    )
    
    return report_data


@router.get("/daily/html")
async def get_daily_report_html(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """取得今日綜合報告（HTML 格式）"""
    watchlist = await get_user_watchlist(current_user.id, db)
    
    report_data = generate_daily_report_data(
        watchlist_tw=watchlist["TW"],
        watchlist_us=watchlist["US"]
    )
    
    html = generate_report_html(report_data, current_user.name or current_user.email)
    return HTMLResponse(content=html)


@router.post("/daily/send")
async def send_daily_report(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """手動發送綜合報告"""
    watchlist = await get_user_watchlist(current_user.id, db)
    
    report_data = generate_daily_report_data(
        watchlist_tw=watchlist["TW"],
        watchlist_us=watchlist["US"]
    )
    report_html = generate_report_html(report_data, current_user.name or current_user.email)
    
    try:
        email = await send_report_email(
            current_user, 
            report_html, 
            f'📊 每日股票報告 - {current_user.name or current_user.email}',
            db
        )
        return {"success": True, "message": f"報告已發送至 {email}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發送失敗: {str(e)}"
        )


# ==========================================
# 分開的市場報告 API
# ==========================================
@router.get("/{market}/report")
async def get_market_report(
    market: str,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """取得單一市場報告（JSON 格式）"""
    market = market.upper()
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    watchlist = await get_user_watchlist(current_user.id, db)
    report_data = generate_market_report_data(market, watchlist.get(market, []))
    
    return report_data


@router.get("/{market}/report/html")
async def get_market_report_html(
    market: str,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """取得單一市場報告（HTML 格式）"""
    market = market.upper()
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    watchlist = await get_user_watchlist(current_user.id, db)
    report_data = generate_market_report_data(market, watchlist.get(market, []))
    report_html = generate_market_report_html(report_data, current_user.name or current_user.email)
    
    return HTMLResponse(content=report_html)


@router.post("/{market}/send")
async def send_market_report(
    market: str,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """手動發送單一市場報告"""
    market = market.upper()
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    market_name = "台股" if market == "TW" else "美股"
    
    watchlist = await get_user_watchlist(current_user.id, db)
    report_data = generate_market_report_data(market, watchlist.get(market, []))
    report_html = generate_market_report_html(report_data, current_user.name or current_user.email)
    
    try:
        email = await send_report_email(
            current_user, 
            report_html, 
            f'📊 {market_name}收盤報告 - {current_user.name or current_user.email}',
            db
        )
        return {"success": True, "message": f"{market_name}報告已發送至 {email}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發送失敗: {str(e)}"
        )


# ==========================================
# 潛力股推薦 API
# ==========================================
@router.get("/trending/{market}")
async def get_trending_stocks(
    market: str,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """取得潛力股推薦"""
    market = market.upper()
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    watchlist = await get_user_watchlist(current_user.id, db)
    exclude_symbols = watchlist.get(market, [])
    
    recommendations = get_trending_recommendations(
        market=market,
        top_n=10,
        exclude_symbols=exclude_symbols
    )
    
    return {
        "market": market,
        "recommendations": recommendations
    }


# ==========================================
# 排程管理 API
# ==========================================
@router.get("/scheduler/jobs")
async def get_jobs(
    current_user: User = Depends(get_current_user_required)
):
    """取得所有排程任務"""
    return {"jobs": get_scheduled_jobs()}


@router.post("/scheduler/start")
async def start_scheduler_api(
    current_user: User = Depends(get_current_user_required)
):
    """啟動排程器"""
    start_scheduler()
    return {"success": True, "message": "排程器已啟動", "jobs": get_scheduled_jobs()}


@router.post("/scheduler/stop")
async def stop_scheduler_api(
    current_user: User = Depends(get_current_user_required)
):
    """停止排程器"""
    stop_scheduler()
    return {"success": True, "message": "排程器已停止"}


# ==========================================
# 股票詳細資訊 API
# ==========================================
@router.get("/stock/{symbol}/detail")
async def get_stock_detail_api(
    symbol: str,
    market: str = "US",
    current_user: User = Depends(get_current_user_required)
):
    """
    取得股票完整詳細資訊
    包含：價格數據、公司資訊、推薦理由、新聞
    """
    from services.stock_detail import get_stock_detail
    
    # 處理台股代號
    if market.upper() == "TW" and not symbol.endswith(".TW"):
        symbol = symbol.upper() + ".TW"
    else:
        symbol = symbol.upper()
    
    detail = get_stock_detail(symbol)
    return detail


@router.get("/stock/{symbol}/news")
async def get_stock_news_api(
    symbol: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user_required)
):
    """取得股票相關新聞"""
    from services.stock_detail import get_stock_news
    
    news = get_stock_news(symbol.upper(), limit)
    return {"symbol": symbol.upper(), "news": news}


@router.get("/stock/{symbol}/reasons")
async def get_stock_reasons_api(
    symbol: str,
    market: str = "US",
    current_user: User = Depends(get_current_user_required)
):
    """取得股票推薦理由"""
    from services.stock_detail import generate_recommendation_reasons
    from services.daily_report import get_stock_analysis, calculate_potential_score
    
    # 處理台股代號
    if market.upper() == "TW" and not symbol.endswith(".TW"):
        symbol = symbol.upper() + ".TW"
    else:
        symbol = symbol.upper()
    
    stock_data = get_stock_analysis(symbol)
    if stock_data.get("status") == "success":
        stock_data["score"] = calculate_potential_score(stock_data)
    
    reasons = generate_recommendation_reasons(stock_data)
    
    return {
        "symbol": symbol,
        "stock_data": stock_data,
        "reasons": reasons
    }
