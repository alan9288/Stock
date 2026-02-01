from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import re

from services.database import get_db
from services.models import User, Holding, HoldingTransaction
from services.stock_api import stock_api
from services.buy_signal import get_buy_signal
from routers.auth import get_current_user

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


# ==========================================
# Pydantic 模型（含驗證）
# ==========================================

class HoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="股票代號")
    market: Literal["TW", "US"] = Field(..., description="市場：TW 或 US")
    quantity: float = Field(..., gt=0, description="股數必須大於 0")
    price: float = Field(..., gt=0, description="價格必須大於 0")
    transaction_date: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=200)
    
    @model_validator(mode='after')
    def validate_symbol_by_market(self):
        """根據市場類型驗證股票代號格式"""
        symbol = self.symbol.upper().strip()
        market = self.market
        
        if market == 'US':
            # 美股：1-5 個大寫字母
            if not re.match(r'^[A-Z]{1,5}$', symbol):
                raise ValueError('美股代號必須是 1-5 個大寫英文字母（如 AAPL, TSLA）')
        else:
            # 台股：4-6 位數字（可選 .TW 後綴）
            clean = symbol.replace('.TW', '')
            if not re.match(r'^\d{4,6}$', clean):
                raise ValueError('台股代號必須是 4-6 位數字（如 2330, 0050）')
        
        # 更新 symbol 為大寫
        self.symbol = symbol
        return self


class TransactionCreate(BaseModel):
    quantity: float = Field(..., gt=0, description="股數必須大於 0")
    price: float = Field(..., gt=0, description="價格必須大於 0")
    transaction_date: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=200)



class TransactionResponse(BaseModel):
    id: int
    quantity: float  # 支援小數股數
    price: str
    transaction_date: Optional[datetime]
    note: Optional[str]
    created_at: datetime


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    market: str
    name: Optional[str] = None
    total_quantity: float  # 支援小數股數
    avg_cost: float
    total_cost: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    return_pct: Optional[float] = None
    transactions: List[TransactionResponse]


# ==========================================
# API 端點
# ==========================================

@router.get("")
async def get_holdings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取得所有持股"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    # 使用 selectinload 預先載入 transactions（解決 async lazy loading 問題）
    result = await db.execute(
        select(Holding)
        .options(selectinload(Holding.transactions))
        .where(Holding.user_id == current_user.id)
    )
    holdings = result.scalars().all()
    
    holdings_data = []
    for holding in holdings:
        # 取得交易記錄（已預先載入）
        txns = holding.transactions
        
        # 計算總股數和總成本
        total_quantity = sum(float(t.quantity) for t in txns)
        total_cost = sum(float(t.quantity) * float(t.price) for t in txns)
        avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
        
        # 取得現價
        quote = stock_api.get_quote(holding.symbol, holding.market)
        current_price = quote.get("price") if quote.get("status") == "success" else None
        stock_name = quote.get("name", "")
        
        # 計算未實現損益
        unrealized_pnl = None
        return_pct = None
        if current_price and total_quantity > 0:
            unrealized_pnl = round((current_price - avg_cost) * total_quantity, 2)
            return_pct = round((current_price - avg_cost) / avg_cost * 100, 2) if avg_cost > 0 else 0
        
        # 取得買入信號
        buy_signal = None
        if current_price and avg_cost > 0:
            try:
                buy_signal = get_buy_signal(
                    symbol=holding.symbol,
                    market=holding.market,
                    current_price=current_price,
                    avg_cost=avg_cost,
                    total_cost=total_cost,
                    total_quantity=total_quantity
                )
            except Exception as e:
                print(f"[Holdings] 取得 {holding.symbol} 買入信號失敗: {e}")
        
        holdings_data.append({
            "id": holding.id,
            "symbol": holding.symbol,
            "market": holding.market,
            "name": stock_name,
            "total_quantity": total_quantity,
            "avg_cost": round(avg_cost, 2),
            "total_cost": round(total_cost, 2),
            "current_price": current_price,
            "unrealized_pnl": unrealized_pnl,
            "return_pct": return_pct,
            "buy_signal": buy_signal,
            "transactions": [
                {
                    "id": t.id,
                    "quantity": t.quantity,
                    "price": t.price,
                    "transaction_date": t.transaction_date,
                    "note": t.note,
                    "created_at": t.created_at
                }
                for t in txns
            ]
        })
    
    # 計算總損益
    total_unrealized_pnl = sum(h["unrealized_pnl"] or 0 for h in holdings_data)
    total_cost = sum(h["total_cost"] for h in holdings_data)
    total_return_pct = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
    
    return {
        "holdings": holdings_data,
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
            "total_return_pct": round(total_return_pct, 2)
        }
    }


@router.post("")
async def create_holding(
    data: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """新增持股"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    # 格式化 symbol
    symbol = data.symbol.upper()
    if data.market == "TW" and not symbol.endswith(".TW"):
        symbol = f"{symbol}.TW"
    
    # 檢查是否已存在
    result = await db.execute(
        select(Holding).where(
            and_(
                Holding.user_id == current_user.id,
                Holding.symbol == symbol
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # 已存在，新增交易記錄
        txn = HoldingTransaction(
            holding_id=existing.id,
            quantity=data.quantity,
            price=str(data.price),
            transaction_date=data.transaction_date or datetime.now(),
            note=data.note
        )
        db.add(txn)
        await db.commit()
        return {"message": "已新增補倉記錄", "holding_id": existing.id}
    
    # 新增持股
    holding = Holding(
        user_id=current_user.id,
        symbol=symbol,
        market=data.market
    )
    db.add(holding)
    await db.flush()
    
    # 新增第一筆交易
    txn = HoldingTransaction(
        holding_id=holding.id,
        quantity=data.quantity,
        price=str(data.price),
        transaction_date=data.transaction_date or datetime.now(),
        note=data.note or "首次買入"
    )
    db.add(txn)
    await db.commit()
    
    return {"message": "已新增持股", "holding_id": holding.id}


@router.post("/{holding_id}/transactions")
async def add_transaction(
    holding_id: int,
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """新增補倉記錄"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    # 檢查持股是否存在且屬於該用戶
    result = await db.execute(
        select(Holding).where(
            and_(
                Holding.id == holding_id,
                Holding.user_id == current_user.id
            )
        )
    )
    holding = result.scalar_one_or_none()
    
    if not holding:
        raise HTTPException(status_code=404, detail="持股不存在")
    
    txn = HoldingTransaction(
        holding_id=holding_id,
        quantity=data.quantity,
        price=str(data.price),
        transaction_date=data.transaction_date or datetime.now(),
        note=data.note or "補倉"
    )
    db.add(txn)
    await db.commit()
    
    return {"message": "已新增補倉記錄", "transaction_id": txn.id}


@router.get("/{holding_id}/transactions")
async def get_transactions(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取得交易記錄"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    result = await db.execute(
        select(Holding)
        .options(selectinload(Holding.transactions))
        .where(
            and_(
                Holding.id == holding_id,
                Holding.user_id == current_user.id
            )
        )
    )
    holding = result.scalar_one_or_none()
    
    if not holding:
        raise HTTPException(status_code=404, detail="持股不存在")
    
    return {
        "symbol": holding.symbol,
        "transactions": [
            {
                "id": t.id,
                "quantity": float(t.quantity),
                "price": t.price,
                "transaction_date": t.transaction_date,
                "note": t.note,
                "created_at": t.created_at
            }
            for t in holding.transactions
        ]
    }


@router.delete("/{holding_id}")
async def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """刪除持股（包含所有交易記錄）"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    result = await db.execute(
        select(Holding).where(
            and_(
                Holding.id == holding_id,
                Holding.user_id == current_user.id
            )
        )
    )
    holding = result.scalar_one_or_none()
    
    if not holding:
        raise HTTPException(status_code=404, detail="持股不存在")
    
    await db.delete(holding)
    await db.commit()
    
    return {"message": "已刪除持股"}


@router.delete("/{holding_id}/transactions/{transaction_id}")
async def delete_transaction(
    holding_id: int,
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """刪除單筆交易記錄"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登入")
    
    # 驗證持股所有權
    result = await db.execute(
        select(Holding).where(
            and_(
                Holding.id == holding_id,
                Holding.user_id == current_user.id
            )
        )
    )
    holding = result.scalar_one_or_none()
    
    if not holding:
        raise HTTPException(status_code=404, detail="持股不存在")
    
    # 找到交易記錄
    txn_result = await db.execute(
        select(HoldingTransaction).where(
            and_(
                HoldingTransaction.id == transaction_id,
                HoldingTransaction.holding_id == holding_id
            )
        )
    )
    txn = txn_result.scalar_one_or_none()
    
    if not txn:
        raise HTTPException(status_code=404, detail="交易記錄不存在")
    
    await db.delete(txn)
    await db.commit()
    
    return {"message": "已刪除交易記錄"}
