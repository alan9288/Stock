"""
資料庫模型定義
使用 SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """使用者模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 關聯
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False)
    portfolios = relationship("Portfolio", back_populates="user")


class NotificationSettings(Base):
    """通知設定模型"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    notification_email = Column(String(255))
    thresholds_tw = Column(String(100), default="+3 +5 -5 -10")
    thresholds_us = Column(String(100), default="+5 +10 -5 -10")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    user = relationship("User", back_populates="notification_settings")


class Portfolio(Base):
    """投資組合模型"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    market = Column(String(10), default="TW")  # 'TW' or 'US'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    user = relationship("User", back_populates="portfolios")
    stocks = relationship("WatchlistItem", back_populates="portfolio")


class WatchlistItem(Base):
    """觀測股票模型"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(20), nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    portfolio = relationship("Portfolio", back_populates="stocks")


class AlertHistory(Base):
    """警示歷史記錄"""
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    threshold_hit = Column(String(10))  # 如 "+5" 或 "-10"
    change_pct = Column(String(20))     # 實際漲跌幅
    price = Column(String(20))          # 當時價格
    notified_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    user = relationship("User")


class Holding(Base):
    """持股記錄"""
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(20), nullable=False, index=True)
    market = Column(String(10), nullable=False, index=True)  # TW 或 US
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    user = relationship("User")
    transactions = relationship("HoldingTransaction", back_populates="holding", cascade="all, delete-orphan")
    
    # 複合唯一約束
    __table_args__ = (
        {'extend_existing': True},
    )


class HoldingTransaction(Base):
    """持股交易記錄（買入/補倉）"""
    __tablename__ = "holding_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    holding_id = Column(Integer, ForeignKey("holdings.id", ondelete="CASCADE"))
    quantity = Column(Numeric(12, 5), nullable=False)  # 股數（支援5位小數）
    price = Column(String(20), nullable=False)        # 買入價格
    transaction_date = Column(DateTime(timezone=True))  # 交易日期
    note = Column(Text)                               # 備註
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    holding = relationship("Holding", back_populates="transactions")
