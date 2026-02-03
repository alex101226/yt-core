from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from cryptography.fernet import Fernet
from jose import jwt
from typing import Dict
from app.core.config import settings
from app.core.logger import logger

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_EXPIRE_DAYS=settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 加密密码
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 创建 access token
def create_access_token(subject: Dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = subject.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

# 创建 refresh token
def create_refresh_token(subject: Dict, expires_days: int = REFRESH_EXPIRE_DAYS) -> str:
    to_encode = subject.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

# token解码
def decode_token(token: str) -> Dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

# =========================
# 可逆加密（用于服务器密码等）
# =========================
# print(Fernet.generate_key().decode())
fernet = Fernet('dLI8-YFTJIinEaaN6jXoyfbva1cEKagojkgT5FVIP1c=')
def encrypt_text(plain_text: str) -> str:
    if not plain_text:
        return plain_text
    return fernet.encrypt(plain_text.encode()).decode()

#  解密
def decrypt_text(cipher_text: str) -> str:
    if not cipher_text:
        return cipher_text
    try:
        return fernet.decrypt(cipher_text.encode()).decode()
    except Exception as e:
        logger.error(f"decrypt_text failed: {e}")
        return ""