"""
通知設定路由
管理使用者的通知 Email 和門檻設定
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.database import get_db
from services.models import User, NotificationSettings
from routers.auth import get_current_user_required

router = APIRouter(prefix="/api/notifications", tags=["通知設定"])


# ==========================================
# Pydantic 模型
# ==========================================
class NotificationSettingsResponse(BaseModel):
    """通知設定回應"""
    id: int
    notification_email: Optional[str]
    thresholds_tw: str
    thresholds_us: str
    enabled: bool

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    """更新通知設定"""
    notification_email: Optional[EmailStr] = None
    thresholds_tw: Optional[str] = None
    thresholds_us: Optional[str] = None
    enabled: Optional[bool] = None


# ==========================================
# 路由
# ==========================================
@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    取得當前使用者的通知設定
    """
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # 如果沒有設定，建立預設設定
        settings = NotificationSettings(
            user_id=current_user.id,
            notification_email=current_user.email,
            thresholds_tw="+3 +5 -5 -10",
            thresholds_us="+5 +10 -5 -10",
            enabled=True
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    update_data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    更新通知設定
    """
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # 建立新設定
        settings = NotificationSettings(
            user_id=current_user.id,
            notification_email=update_data.notification_email or current_user.email
        )
        db.add(settings)
    
    # 更新欄位
    if update_data.notification_email is not None:
        settings.notification_email = update_data.notification_email
    if update_data.thresholds_tw is not None:
        settings.thresholds_tw = update_data.thresholds_tw
    if update_data.thresholds_us is not None:
        settings.thresholds_us = update_data.thresholds_us
    if update_data.enabled is not None:
        settings.enabled = update_data.enabled
    
    await db.commit()
    await db.refresh(settings)
    
    return settings


@router.post("/test-email")
async def send_test_email(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    發送測試郵件到使用者設定的通知信箱
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    
    # 取得使用者通知設定
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.notification_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="尚未設定通知信箱"
        )
    
    # SMTP 設定
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP 設定不完整"
        )
    
    # 建立郵件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '📈 股票監控系統 - 測試郵件'
    msg['From'] = SENDER_EMAIL
    msg['To'] = settings.notification_email
    
    html = f'''
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background: #1a1a2e; color: #eee;">
        <div style="max-width: 600px; margin: 0 auto; background: #16213e; padding: 30px; border-radius: 10px;">
            <h2 style="color: #00d9ff;">🎉 郵件測試成功！</h2>
            <p>嗨 {current_user.name or current_user.email}，</p>
            <p>這是來自股票監控系統的測試郵件。</p>
            <p>如果您收到這封郵件，表示您的通知信箱設定正確！</p>
            <hr style="border-color: #333;">
            <p style="color: #888; font-size: 12px;">
                通知信箱: {settings.notification_email}<br>
                台股門檻: {settings.thresholds_tw}<br>
                美股門檻: {settings.thresholds_us}
            </p>
        </div>
    </body>
    </html>
    '''
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, settings.notification_email, msg.as_string())
        server.quit()
        return {"message": f"測試郵件已發送至 {settings.notification_email}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"郵件發送失敗: {str(e)}"
        )
