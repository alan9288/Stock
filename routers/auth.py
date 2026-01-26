"""
認證路由
處理使用者註冊、登入、取得當前使用者
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from services.database import get_db
from services.models import User, NotificationSettings, Portfolio
from services.auth import (
    UserCreate, UserLogin, UserResponse, Token, TokenData,
    hash_password, verify_password, create_access_token, decode_access_token
)

router = APIRouter(prefix="/api/auth", tags=["認證"])

# OAuth2 設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ==========================================
# 依賴注入：取得當前使用者
# ==========================================
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """取得當前登入的使用者"""
    if not token:
        return None
    
    token_data = decode_access_token(token)
    if not token_data or not token_data.user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """取得當前使用者（必須登入）"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登入或 Token 已過期",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


# ==========================================
# 路由
# ==========================================
@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    註冊新使用者
    """
    # 檢查 Email 是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此 Email 已被註冊"
        )
    
    # 建立新使用者
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name or user_data.email.split("@")[0]
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # 建立預設通知設定
    notification = NotificationSettings(
        user_id=new_user.id,
        notification_email=new_user.email
    )
    db.add(notification)
    
    # 建立預設投資組合
    tw_portfolio = Portfolio(user_id=new_user.id, name="台股觀測", market="TW")
    us_portfolio = Portfolio(user_id=new_user.id, name="美股觀測", market="US")
    db.add(tw_portfolio)
    db.add(us_portfolio)
    
    await db.commit()
    
    # 產生 Token
    access_token = create_access_token(
        data={"sub": new_user.id, "email": new_user.email}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(id=new_user.id, email=new_user.email, name=new_user.name)
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    使用者登入（支援 OAuth2 規範）
    """
    # 查詢使用者
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email 或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 產生 Token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(id=user.id, email=user.email, name=user.name)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user_required)):
    """
    取得當前登入使用者資料
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name
    )


@router.post("/logout")
async def logout():
    """
    登出（前端清除 Token 即可）
    """
    return {"message": "已登出"}


# ==========================================
# 密碼修改
# ==========================================
from pydantic import BaseModel as PydanticBaseModel

class PasswordChange(PydanticBaseModel):
    """密碼修改 Schema"""
    current_password: str
    new_password: str


@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密碼
    """
    # 驗證現有密碼
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現有密碼錯誤"
        )
    
    # 驗證新密碼長度
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密碼至少需要 6 個字元"
        )
    
    # 更新密碼
    current_user.password_hash = hash_password(data.new_password)
    await db.commit()
    
    return {"message": "密碼已更新成功"}
