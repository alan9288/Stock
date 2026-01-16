"""
資料庫模型定義
使用 SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
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
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"))
    symbol = Column(String(20), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    portfolio = relationship("Portfolio", back_populates="stocks")
