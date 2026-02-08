# models/cm_hub_models_tmp.py
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON, Date, Integer
from app.core.database import HubBase
from app.core.config import settings


class HubModels(HubBase):
    __tablename__ = f"{settings.HUB_TABLE_PREFIX}models"
    __table_args__ = {"comment": "模型表（无约束，用于数据清洗）"}

    id = Column(Integer, primary_key=True, comment="模型ID")

    name = Column(String(255), nullable=False, comment="模型名称")
    slug = Column(String(255), nullable=True, comment="唯一标识")
    description = Column(Text, nullable=True, comment="模型描述")

    category_id = Column(Integer, nullable=True, comment="分类ID")

    author = Column(String(255), nullable=True, comment="作者")

    downloads = Column(Integer, nullable=False, default=0, comment="下载次数")
    likes = Column(Integer, nullable=False, default=0, comment="点赞数")

    tags = Column(JSON, nullable=True, comment="标签")

    framework = Column(String(100), nullable=True, comment="框架")
    license = Column(String(100), nullable=True, comment="许可证")

    model_size = Column(String(50), nullable=True, comment="模型大小")
    language = Column(String(100), nullable=True, comment="语言")

    created_at = Column(DateTime, nullable=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=True, comment="更新时间")

    readme = Column(Text, nullable=True, comment="说明文档")
    usage_example = Column(Text, nullable=True, comment="使用示例")

    paper_url = Column(String(512), nullable=True, comment="论文地址")
    github_url = Column(String(512), nullable=True, comment="GitHub 地址")

    model_files = Column(JSON, nullable=True, comment="模型文件")

    last_modified = Column(DateTime, nullable=True, comment="最后修改时间")

    task_type = Column(String(100), nullable=True, comment="任务类型")
    domain = Column(String(100), nullable=True, comment="领域")

    published_date = Column(Date, nullable=True, comment="发布日期")

    model_scope = Column(Text, nullable=True, comment="适用范围")
    limitations = Column(Text, nullable=True, comment="限制说明")

    evaluation_metrics = Column(JSON, nullable=True, comment="评估指标")

    hardware_requirements = Column(Text, nullable=True, comment="硬件要求")
    inference_speed = Column(Text, nullable=True, comment="推理速度")

    docker_deployment = Column(Text, nullable=True, comment="Docker 部署")
    deployment_guide = Column(Text, nullable=True, comment="部署指南")

    model_evaluation = Column(Text, nullable=True, comment="模型评估")