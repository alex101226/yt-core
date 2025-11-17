# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, declared_attr
from app.core.config import settings
from typing import Dict

def create_db_engine(database_url: str):
    return create_engine(database_url, echo=(settings.ENV == "development"), pool_pre_ping=True)

def create_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_base():
    return declarative_base()

# === Engines & Sessions for each DB ===
engines: Dict[str, any] = {
    "sso_auth": create_db_engine(settings.DB_SSO_AUTH),
    "public": create_db_engine(settings.DB_PUBLIC),
    "audit_center": create_db_engine(settings.DB_AUDIT_CENTER),
    "cmp": create_db_engine(settings.DB_CMP),
}

SessionLocal = {
    name: create_session_factory(engine)
    for name, engine in engines.items()
}

# Distinct Base metadata objects (one per DB) - used by Alembic target_metadata
SsoBase = create_base()
PublicBase = create_base()
AuditBase = create_base()
CmpBase = create_base()
