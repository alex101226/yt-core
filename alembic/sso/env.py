# alembic/public/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 导入项目配置
from app.core.config import settings
from app.core.database import SsoBase
from app import models  # 导入所有模型模块，确保 Alembic 能扫描到

config = context.config

# ✅ 关键：从 settings 注入数据库 URL（这个是 .env.development 里的 DB_SSO_AUTH）
config.set_main_option("sqlalchemy.url", settings.DB_SSO_AUTH)

# ✅ 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SsoBase.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
