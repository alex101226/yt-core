# app/common/dependencies.py
from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette import status
from app.core.auth import verify_token
from app.core.database import SessionLocal

# 假设你的 SessionLocal 是像 { "public": session_factory, ... }
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")  # tokenUrl 仅用于文档，实际端点按你实现

#   sso登录
def get_sso_db() -> Generator[Session, None, None]:
    db = SessionLocal["sso_auth"]()
    try:
        yield db
    finally:
        db.close()

#   公共资源
def get_public_db() -> Generator[Session, None, None]:
    db = SessionLocal["public"]()
    try:
        yield db
    finally:
        db.close()

#   公共审计
def get_audit_db() -> Generator[Session, None, None]:
    db = SessionLocal["audit_center"]()
    try:
        yield db
    finally:
        db.close()

#   算力调度平台
def get_cmp_db() -> Generator[Session, None, None]:
    db = SessionLocal["cmp"]()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_sso_db)):
    """
    从 OAuth2 token 中解析当前用户并返回（这里返回一个 dict，真实项目返回 User ORM）。
    如果 token 无效则抛出 HTTPException 401。
    """
    user = verify_token(token, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
