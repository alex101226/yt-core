# app/models/cmp/dictionary_item.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone

from app.core.database import CmpBase
from app.core.config import settings

class DictItem(CmpBase):
    """
    通用字典表，用于存储网络类型、存储类型、操作系统类型等
    - type_code: 字典类型标识（例如 NETWORK_TYPE, OS_TYPE）
    - item_code: 字典项标识（例如 VPC, CLASSIC）
    - item_name: 字典项名称（例如 专有网络, 经典网络）
    - description: 描述信息
    """

    __tablename__ = f"{settings.CMP_TABLE_PREFIX}dict_item"
    __table_args__ = {"comment": "通用字典表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(50), nullable=False, comment="字典类型标识")
    item_code = Column(String(50), nullable=False, comment="字典项编码")
    item_name = Column(String(100), nullable=False, comment="字典项名称")
    description = Column(Text, nullable=True, comment="描述信息，可选")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, comment="创建时间 (UTC)")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, comment="更新时间 (UTC)")
