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


#   算力调度平台
def get_cmp_db() -> Generator[Session, None, None]:
    db = SessionLocal["cmp"]()
    try:
        yield db
    finally:
        db.close()


#   大模型广场
def get_hub_db() -> Generator[Session, None, None]:
    db = SessionLocal["hub"]()
    try:
        yield db
    finally:
        db.close()

