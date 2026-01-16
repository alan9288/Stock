"""
股票管理路由
管理使用者的投資組合和觀察清單
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List

from services.database import get_db
from services.models import User, Portfolio, WatchlistItem
from routers.auth import get_current_user_required

router = APIRouter(prefix="/api/watchlist", tags=["股票管理"])


# ==========================================
# Pydantic 模型
# ==========================================
class StockAdd(BaseModel):
    """新增股票"""
    symbol: str
    market: str = "US"  # "TW" or "US"


class StockRemove(BaseModel):
    """移除股票"""
    symbol: str
    market: str = "US"


class WatchlistResponse(BaseModel):
    """觀察清單回應"""
    TW: List[str]
    US: List[str]


class PortfolioStocksResponse(BaseModel):
    """投資組合股票回應"""
    id: int
    name: str
    market: str
    stocks: List[str]

    class Config:
        from_attributes = True


# ==========================================
# 輔助函式
# ==========================================
async def get_or_create_portfolio(
    db: AsyncSession, 
    user_id: int, 
    market: str
) -> Portfolio:
    """取得或建立投資組合"""
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == user_id,
            Portfolio.market == market
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        name = "台股觀測" if market == "TW" else "美股觀測"
        portfolio = Portfolio(user_id=user_id, name=name, market=market)
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
    
    return portfolio


# ==========================================
# 路由
# ==========================================
@router.get("/", response_model=WatchlistResponse)
async def get_watchlist(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    取得當前使用者的所有觀察股票
    """
    result = {"TW": [], "US": []}
    
    # 取得使用者的投資組合
    portfolios_result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == current_user.id)
    )
    portfolios = portfolios_result.scalars().all()
    
    for portfolio in portfolios:
        # 取得每個投資組合的股票
        stocks_result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
        )
        stocks = stocks_result.scalars().all()
        result[portfolio.market] = [s.symbol for s in stocks]
    
    return result


@router.get("/portfolios", response_model=List[PortfolioStocksResponse])
async def get_portfolios(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    取得使用者的所有投資組合及其股票
    """
    portfolios_result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == current_user.id)
    )
    portfolios = portfolios_result.scalars().all()
    
    result = []
    for portfolio in portfolios:
        stocks_result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
        )
        stocks = stocks_result.scalars().all()
        result.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "market": portfolio.market,
            "stocks": [s.symbol for s in stocks]
        })
    
    return result


@router.post("/add")
async def add_stock(
    data: StockAdd,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    新增股票到觀察清單
    """
    symbol = data.symbol.upper().strip()
    market = data.market.upper()
    
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    # 台股加後綴
    if market == "TW" and not symbol.endswith(".TW"):
        symbol += ".TW"
    
    # 取得或建立投資組合
    portfolio = await get_or_create_portfolio(db, current_user.id, market)
    
    # 檢查是否已存在
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.portfolio_id == portfolio.id,
            WatchlistItem.symbol == symbol
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"{symbol} 已在觀察清單中")
    
    # 新增股票
    item = WatchlistItem(portfolio_id=portfolio.id, symbol=symbol)
    db.add(item)
    await db.commit()
    
    return {"success": True, "message": f"已新增 {symbol}"}


@router.post("/remove")
async def remove_stock(
    data: StockRemove,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    從觀察清單移除股票
    """
    symbol = data.symbol.upper().strip()
    market = data.market.upper()
    
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    # 找到投資組合
    portfolio_result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == current_user.id,
            Portfolio.market == market
        )
    )
    portfolio = portfolio_result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="找不到投資組合")
    
    # 刪除股票
    result = await db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.portfolio_id == portfolio.id,
            WatchlistItem.symbol == symbol
        )
    )
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"{symbol} 不在觀察清單中")
    
    return {"success": True, "message": f"已移除 {symbol}"}


@router.delete("/clear/{market}")
async def clear_watchlist(
    market: str,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    清空指定市場的觀察清單
    """
    market = market.upper()
    if market not in ["TW", "US"]:
        raise HTTPException(status_code=400, detail="市場必須是 TW 或 US")
    
    # 找到投資組合
    portfolio_result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == current_user.id,
            Portfolio.market == market
        )
    )
    portfolio = portfolio_result.scalar_one_or_none()
    
    if portfolio:
        await db.execute(
            delete(WatchlistItem).where(WatchlistItem.portfolio_id == portfolio.id)
        )
        await db.commit()
    
    return {"success": True, "message": f"已清空 {market} 觀察清單"}
