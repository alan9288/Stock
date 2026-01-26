"""
即時股票警示監控服務
當股票漲跌幅超過用戶設定的閾值時發送 Email 通知
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import os
import logging
import pytz
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from services.database import AsyncSessionLocal
from services.models import User, Portfolio, WatchlistItem, NotificationSettings, AlertHistory
from services.stock_api import stock_api
from services.power_manager import is_market_open

TZ_TW = pytz.timezone("Asia/Taipei")
logger = logging.getLogger("alert_monitor")
logger.setLevel(logging.INFO)


def parse_thresholds(threshold_str: str) -> list:
    """
    解析閾值字串
    例如: "+3 +5 -5 -10" -> [3.0, 5.0, -5.0, -10.0]
    """
    try:
        return [float(t) for t in threshold_str.split()]
    except:
        return [3.0, 5.0, -5.0, -10.0]


def check_threshold_hit(change_pct: float, thresholds: list) -> str:
    """
    檢查漲跌幅是否超過任一閾值
    回傳觸發的閾值字串，如 "+5" 或 "-10"
    如果沒有觸發返回 None
    """
    for threshold in thresholds:
        if threshold > 0 and change_pct >= threshold:
            return f"+{int(threshold)}"
        elif threshold < 0 and change_pct <= threshold:
            return str(int(threshold))
    return None


async def is_already_notified_today(db: AsyncSession, user_id: int, symbol: str, threshold: str) -> bool:
    """檢查今天是否已經通知過相同的閾值"""
    today_start = datetime.now(TZ_TW).replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await db.execute(
        select(AlertHistory).where(
            and_(
                AlertHistory.user_id == user_id,
                AlertHistory.symbol == symbol,
                AlertHistory.threshold_hit == threshold,
                AlertHistory.notified_at >= today_start
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def send_alert_email(user: User, stock_data: dict, threshold: str, settings: NotificationSettings) -> bool:
    """發送警示 Email"""
    
    if not settings or not settings.notification_email:
        logger.warning(f"用戶 {user.email} 未設定通知信箱")
        return False
    
    if not settings.enabled:
        logger.info(f"用戶 {user.email} 已停用通知")
        return False
    
    # SMTP 設定
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.error("SMTP 設定不完整")
        return False
    
    symbol = stock_data.get('symbol', 'N/A')
    name = stock_data.get('name', symbol)
    change_pct = stock_data.get('change_pct', 0)
    price = stock_data.get('price', 'N/A')
    
    # 判斷漲跌
    if change_pct >= 0:
        direction = "📈 上漲"
        color = "#10B981"
    else:
        direction = "📉 下跌"
        color = "#EF4444"
    
    # 建立 HTML 郵件
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #ffffff; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #16213e; border-radius: 10px; padding: 20px;">
            <h2 style="color: #ffffff; margin-top: 0;">📊 股票警示通知</h2>
            
            <div style="background-color: #0f3460; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h3 style="margin: 0; color: #ffffff;">{symbol}</h3>
                <p style="margin: 5px 0; color: #a0a0a0;">{name}</p>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin: 15px 0;">
                <div>
                    <p style="color: #a0a0a0; margin: 0;">當前漲跌幅</p>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: {color};">
                        {'+' if change_pct >= 0 else ''}{change_pct:.2f}%
                    </p>
                </div>
                <div>
                    <p style="color: #a0a0a0; margin: 0;">觸發閾值</p>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #fbbf24;">
                        {threshold}%
                    </p>
                </div>
            </div>
            
            <div style="background-color: #0f3460; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <p style="margin: 0; color: #a0a0a0;">當前價格</p>
                <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: #ffffff;">
                    ${price}
                </p>
            </div>
            
            <p style="color: #a0a0a0; font-size: 12px; margin-top: 20px;">
                ⏰ {datetime.now(TZ_TW).strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)
            </p>
            
            <hr style="border-color: #333; margin: 20px 0;">
            <p style="color: #666; font-size: 11px; margin: 0;">
                此郵件由股票監控系統自動發送
            </p>
        </div>
    </body>
    </html>
    """
    
    # 建立郵件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'⚠️ {symbol} {direction} {change_pct:+.2f}% (觸發 {threshold}%)'
    msg['From'] = SENDER_EMAIL
    msg['To'] = settings.notification_email
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, settings.notification_email, msg.as_string())
        server.quit()
        logger.info(f"已發送警示給 {user.email}: {symbol} {threshold}%")
        return True
    except Exception as e:
        logger.error(f"發送警示失敗給 {user.email}: {e}")
        return False


async def check_user_alerts(user: User, db: AsyncSession):
    """檢查單一用戶的所有股票警示"""
    
    # 取得通知設定
    settings_result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    settings = settings_result.scalar_one_or_none()
    
    if not settings or not settings.enabled:
        return
    
    # 取得用戶的所有觀察清單
    portfolios_result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user.id)
    )
    portfolios = portfolios_result.scalars().all()
    
    for portfolio in portfolios:
        # 取得該組合的股票
        items_result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
        )
        items = items_result.scalars().all()
        
        # 根據市場選擇閾值
        if portfolio.market == "TW":
            thresholds = parse_thresholds(settings.thresholds_tw)
            if not is_market_open("TW"):
                continue
        else:
            thresholds = parse_thresholds(settings.thresholds_us)
            if not is_market_open("US"):
                continue
        
        # 檢查每支股票
        for item in items:
            try:
                # 取得即時股價
                stock_data = stock_api.get_quote(item.symbol, portfolio.market)
                
                if stock_data.get('error'):
                    continue
                
                change_pct = stock_data.get('change_pct', 0)
                
                # 檢查是否觸發閾值
                threshold_hit = check_threshold_hit(change_pct, thresholds)
                
                if threshold_hit:
                    # 檢查今天是否已通知
                    if await is_already_notified_today(db, user.id, item.symbol, threshold_hit):
                        continue
                    
                    # 發送警示
                    if await send_alert_email(user, stock_data, threshold_hit, settings):
                        # 記錄警示歷史
                        alert_record = AlertHistory(
                            user_id=user.id,
                            symbol=item.symbol,
                            stock_name=stock_data.get('name', item.symbol),
                            threshold_hit=threshold_hit,
                            change_pct=f"{change_pct:+.2f}%",
                            price=str(stock_data.get('price', 'N/A'))
                        )
                        db.add(alert_record)
                        await db.commit()
                        
            except Exception as e:
                logger.error(f"檢查 {item.symbol} 時發生錯誤: {e}")


async def check_all_users_alerts():
    """檢查所有用戶的警示"""
    logger.info("開始檢查股票警示...")
    
    async with AsyncSessionLocal() as db:
        # 取得所有用戶
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        
        alert_count = 0
        for user in users:
            await check_user_alerts(user, db)
        
        logger.info(f"股票警示檢查完成")


async def send_test_alert(user_id: int):
    """發送測試警示"""
    async with AsyncSessionLocal() as db:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {"success": False, "message": "用戶不存在"}
        
        settings_result = await db.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        settings = settings_result.scalar_one_or_none()
        
        test_stock = {
            "symbol": "TEST",
            "name": "測試股票",
            "change_pct": 5.23,
            "price": "100.00"
        }
        
        success = await send_alert_email(user, test_stock, "+5", settings)
        
        return {
            "success": success,
            "message": "測試警示已發送" if success else "發送失敗，請檢查設定"
        }
