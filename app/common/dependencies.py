# app/common/dependencies.py
from typing import Generator

from sqlalchemy.orm import Session
from app.core.database import SessionLocal

#   sso登录
def get_sso_db() -> Generator[Session, None, None]:
    db = SessionLocal["sso"]()
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
