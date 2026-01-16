"""
排程服務
自動發送每日報告
- 台股: 每日 14:00 (台灣時間，收盤後)
- 美股: 每日 05:00 (台灣時間，收盤後)
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
import pytz

from services.database import AsyncSessionLocal
from services.models import User, Portfolio, WatchlistItem, NotificationSettings
from services.daily_report import (
    generate_market_report_data,
    generate_market_report_html
)

TZ_TW = pytz.timezone("Asia/Taipei")

# Logger
logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

# Scheduler instance
scheduler = AsyncIOScheduler(timezone=TZ_TW)


async def get_all_users_with_watchlist(market: str):
    """取得所有有觀察清單的用戶"""
    async with AsyncSessionLocal() as db:
        # 找出有該市場觀察清單的用戶
        result = await db.execute(
            select(User)
            .join(Portfolio, User.id == Portfolio.user_id)
            .join(WatchlistItem, Portfolio.id == WatchlistItem.portfolio_id)
            .where(Portfolio.market == market)
            .distinct()
        )
        users = result.scalars().all()
        return users


async def get_user_watchlist(user_id: int, market: str, db):
    """取得用戶指定市場的觀察清單"""
    portfolio_result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == user_id,
            Portfolio.market == market
        )
    )
    portfolio = portfolio_result.scalar_one_or_none()
    
    if not portfolio:
        return []
    
    items_result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
    )
    return [item.symbol for item in items_result.scalars().all()]


async def send_market_report(user: User, market: str, report_html: str, db):
    """發送市場報告給單一用戶"""
    
    # 取得用戶通知設定
    settings_result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    settings = settings_result.scalar_one_or_none()
    
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
    
    market_name = "台股" if market == "TW" else "美股"
    
    # 建立郵件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'📊 {market_name}收盤報告 - {user.name or user.email}'
    msg['From'] = SENDER_EMAIL
    msg['To'] = settings.notification_email
    
    msg.attach(MIMEText(report_html, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, settings.notification_email, msg.as_string())
        server.quit()
        logger.info(f"已發送 {market_name} 報告給 {user.email}")
        return True
    except Exception as e:
        logger.error(f"發送失敗給 {user.email}: {e}")
        return False


async def send_tw_reports():
    """發送台股收盤報告給所有用戶"""
    logger.info("開始發送台股收盤報告...")
    
    async with AsyncSessionLocal() as db:
        # 取得所有用戶
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        
        sent_count = 0
        for user in users:
            # 取得用戶的台股觀察清單
            watchlist = await get_user_watchlist(user.id, "TW", db)
            
            if not watchlist:
                continue
            
            # 生成報告
            report_data = generate_market_report_data("TW", watchlist)
            report_html = generate_market_report_html(report_data, user.name or user.email)
            
            # 發送
            if await send_market_report(user, "TW", report_html, db):
                sent_count += 1
        
        logger.info(f"台股報告發送完成，共 {sent_count} 封")


async def send_us_reports():
    """發送美股收盤報告給所有用戶"""
    logger.info("開始發送美股收盤報告...")
    
    async with AsyncSessionLocal() as db:
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        
        sent_count = 0
        for user in users:
            watchlist = await get_user_watchlist(user.id, "US", db)
            
            if not watchlist:
                continue
            
            report_data = generate_market_report_data("US", watchlist)
            report_html = generate_market_report_html(report_data, user.name or user.email)
            
            if await send_market_report(user, "US", report_html, db):
                sent_count += 1
        
        logger.info(f"美股報告發送完成，共 {sent_count} 封")


def setup_scheduler():
    """設定排程任務"""
    
    # 台股收盤報告: 每日 14:00 (台灣時間)
    scheduler.add_job(
        send_tw_reports,
        CronTrigger(hour=14, minute=0, timezone=TZ_TW),
        id="tw_daily_report",
        name="台股每日收盤報告",
        replace_existing=True
    )
    
    # 美股收盤報告: 每日 05:00 (台灣時間，對應美東 16:00)
    scheduler.add_job(
        send_us_reports,
        CronTrigger(hour=5, minute=0, timezone=TZ_TW),
        id="us_daily_report",
        name="美股每日收盤報告",
        replace_existing=True
    )
    
    logger.info("排程任務已設定:")
    logger.info("  - 台股報告: 每日 14:00 (台灣時間)")
    logger.info("  - 美股報告: 每日 05:00 (台灣時間)")


def start_scheduler():
    """啟動排程器"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        logger.info("排程器已啟動")


def stop_scheduler():
    """停止排程器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("排程器已停止")


def get_scheduled_jobs():
    """取得所有排程任務"""
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
        }
        for job in jobs
    ]
