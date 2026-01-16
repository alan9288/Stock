"""
資料庫連接模組
使用 SQLAlchemy 非同步連接 PostgreSQL
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 建立非同步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 設為 True 可看到 SQL 語句
    pool_size=5,
    max_overflow=10
)

# 建立 Session 工廠
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 基礎模型類別
Base = declarative_base()


async def get_db():
    """取得資料庫 Session（用於 FastAPI 依賴注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化資料庫（建立所有資料表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
