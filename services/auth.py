"""
認證服務模組
處理 JWT Token 生成、密碼加密、使用者驗證
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

# JWT 設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# 密碼加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================================
# Pydantic 模型
# ==========================================
class UserCreate(BaseModel):
    """註冊用 Schema"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    """登入用 Schema"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """使用者回應 Schema"""
    id: int
    email: str
    name: Optional[str]
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 回應 Schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token 資料 Schema"""
    user_id: Optional[int] = None
    email: Optional[str] = None


# ==========================================
# 密碼處理
# ==========================================
import re

class PasswordValidationError(Exception):
    """密碼驗證錯誤"""
    pass


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    驗證密碼強度
    規則：
    - 至少 8 個字元
    - 至少包含一個數字
    - 至少包含一個字母
    
    Returns:
        (is_valid, message)
    """
    if len(password) < 8:
        return False, "密碼至少需要 8 個字元"
    
    if not re.search(r"\d", password):
        return False, "密碼至少需要包含一個數字"
    
    if not re.search(r"[a-zA-Z]", password):
        return False, "密碼至少需要包含一個英文字母"
    
    return True, "密碼強度符合要求"


def hash_password(password: str) -> str:
    """加密密碼"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# JWT Token 處理
# ==========================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """建立 JWT Token"""
    to_encode = data.copy()
    
    # JWT 標準規定 sub 必須是字串
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """解碼 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        email: str = payload.get("email")
        
        if sub is None:
            return None
        
        # 將 sub 從字串轉回整數
        user_id = int(sub)
        
        return TokenData(user_id=user_id, email=email)
    except (JWTError, ValueError):
        return None
