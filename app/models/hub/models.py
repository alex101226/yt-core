# models/cm_hub_models_tmp.py
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, BigInteger, DateTime, JSON
from app.core.database import HubBase
from app.core.config import settings


class HubModels(HubBase):
    __tablename__ = f"{settings.HUB_TABLE_PREFIX}models"
    __table_args__ = {"comment": "模型临时表（无约束，用于数据清洗）"}

    id = Column(BigInteger, primary_key=True, comment="模型ID")
    name = Column(String(255), nullable=True, comment="模型名称")
    slug = Column(String(255), nullable=True, comment="模型唯一标识")
    description = Column(Text, nullable=True, comment="模型描述")
    author=Column(String(255), nullable=True, comment="作者")
    downloads=Column(String(255), nullable=True, comment="下载次数")
    likes=Column(String(255), nullable=True, comment="收藏次数")
    tags = Column(JSON,  nullable=True, comment="标签")
    framework=Column(String(255), nullable=True, comment="标签")
    license=Column(String(255), nullable=True, comment="标签")
    model_size = Column(String(255), nullable=True, comment="模型大小")
    language = Column(String(255), nullable=True, comment="语言")

    category_slug = Column(String(255), nullable=True, comment="分类标识")

    icon = Column(String(255), nullable=True, comment="图标地址")
    created_at = Column(
        String(255),
        nullable=True,
        comment="创建时间（UTC）"
    )
    update_at = Column(
        String(255),
        nullable=True,
        comment="创建时间（UTC）"
    )
    last_modified = Column(
        String(255),
        nullable=True,
        comment="最后修改时间"
    )
    published_date = Column(
        String(255),
        nullable=True,
        comment="最后修改时间"
    )
    readme = Column(Text, nullable=True, comment="描述")
    usage_example = Column(Text, nullable=True, comment="描述")
    paper_url = Column(String(255), nullable=True, comment="paper_url")
    github_url = Column(String(255), nullable=True, comment="github_url")
    model_files = Column(JSON, nullable=True, comment="标签")
    task_type=Column(
        String(255),
        nullable=True,
        comment="标签"
    )
    domain=Column(
        String(255),
        nullable=True,
        comment="一些描述"
    )
    model_scope=Column(
        String(255),
        nullable=True,
        comment="一些描述"
     )
    limitations = Column(
        Text,
        nullable=True,
        comment="一些描述"
    )
    evaluation_metrics = Column(
        JSON,
        nullable=True,
        comment="一些描述"
    )
    hardware_requirements = Column(
        Text,
        nullable=True,
        comment="一些描述"
    )
    inference_speed = Column(
        Text,
        nullable=True,
        comment="一些描述"
    )
    docker_deployment = Column(
        Text,
        nullable=True,
        comment="一些描述"
    )
    model_evaluation = Column(
        Text,
        nullable=True,
        comment="一些描述"
    )