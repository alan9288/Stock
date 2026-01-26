"""
警示 API 路由
提供警示歷史查詢和測試功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from services.database import get_db
from services.models import User, AlertHistory
from services.alert_monitor import send_test_alert
from routers.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取得警示歷史記錄"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    result = await db.execute(
        select(AlertHistory)
        .where(AlertHistory.user_id == current_user.id)
        .order_by(desc(AlertHistory.notified_at))
        .limit(limit)
    )
    alerts = result.scalars().all()
    
    return {
        "alerts": [
            {
                "id": alert.id,
                "symbol": alert.symbol,
                "stock_name": alert.stock_name,
                "threshold_hit": alert.threshold_hit,
                "change_pct": alert.change_pct,
                "price": alert.price,
                "notified_at": alert.notified_at.strftime("%Y-%m-%d %H:%M:%S") if alert.notified_at else None
            }
            for alert in alerts
        ]
    }


@router.post("/test")
async def test_alert(
    current_user: User = Depends(get_current_user)
):
    """發送測試警示 Email"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    result = await send_test_alert(current_user.id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.delete("/history/{alert_id}")
async def delete_alert_history(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """刪除特定警示記錄"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    result = await db.execute(
        select(AlertHistory).where(
            AlertHistory.id == alert_id,
            AlertHistory.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="警示記錄不存在")
    
    await db.delete(alert)
    await db.commit()
    
    return {"message": "已刪除"}
