from typing import List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone

from nanoid import generate

from app.core.logger import logger
from app.models.cmp import SecurityGroupRule
from app.models.cmp.security_group import SecurityGroup

from app.models.cmp.vpc import Vpc
from app.models.cmp.resource_group import ResourceGroup

from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleItem

# from app.schemas.cmp.security_group_schema import SecurityGroupCreate

class SecurityGroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_page(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: str,
        region_id: str,
        resource_group_id: str,
        sg_name: str):

        query = self.db.query(
            SecurityGroup.id,
            SecurityGroup.cloud_group_id,
            SecurityGroup.sg_id,
            SecurityGroup.sg_name,
            SecurityGroup.description,
            SecurityGroup.cloud_provider_code,
            SecurityGroup.region_id,
            SecurityGroup.vpc_id,
            SecurityGroup.resource_group_id,
            SecurityGroup.sync_status,
            SecurityGroup.is_released,
            SecurityGroup.created_at,
            SecurityGroup.updated_at,
            Vpc.vpc_name.label("vpc_name"),
            ResourceGroup.rg_name.label("resource_group_name"),
        ).outerjoin(
            Vpc,
            Vpc.id == SecurityGroup.vpc_id
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == SecurityGroup.resource_group_id
        )

        filters = [SecurityGroup.created_by == user_id, SecurityGroup.is_released == 0]
        if provider_code:
            filters.append(SecurityGroup.cloud_provider_code == provider_code)
        if region_id:
            filters.append(SecurityGroup.region_id == region_id)
        if resource_group_id:
            filters.append(SecurityGroup.resource_group_id == resource_group_id)

        if sg_name:
            filters.append(SecurityGroup.sg_name.like(f"%{sg_name}%"))

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    #   根据安全组id获取数据
    def get_by_id(self, group_id: int) -> Optional[type[SecurityGroup]]:
        return self.db.query(SecurityGroup).filter(
            SecurityGroup.id == group_id,
            SecurityGroup.is_released==0
        ).first()

    # --------------------------
    # 创建安全组（仅主表）
    # --------------------------
    def create_group(self, data: dict):
        sg = SecurityGroup(**data)
        self.db.add(sg)
        self.db.commit()
        self.db.refresh(sg)
        if not sg.id:
            return None
        return sg.id

    # --------------------------
    # 安全组标记释放
    # --------------------------
    def group_mark_released(self, group_id: int):
        sg = self.get_by_id(group_id)
        if not sg:
            return None
        sg.is_released = 1
        sg.sync_status = 3
        self.db.commit()
        return sg

    #   返回安全组的列表数据
    def get_by_security_group(self, provider_code: str, region_id: str, vpc_id: int) -> List[SecurityGroup]:
        return self.db.query(SecurityGroup).filter(
            SecurityGroup.is_released == 0,
            SecurityGroup.cloud_provider_code == provider_code,
            SecurityGroup.region_id == region_id,
            SecurityGroup.vpc_id==vpc_id
        ).all()

        # 清空原规则

    # 清空原规则
    def delete_by_group(self, security_group_id: int):
        self.db.query(SecurityGroupRule).filter(
            SecurityGroupRule.security_group_id == security_group_id,
            SecurityGroupRule.is_released == 0
        ).delete()
        self.db.flush()


    # 本地批量插入
    def bulk_create(self, security_group_id: int, rules: List[SecurityGroupRuleItem]):
        for item in rules:
            rule = SecurityGroupRule(
                security_group_id=security_group_id,
                direction=item.direction,
                policy_code=item.policy_code,
                protocol_code=item.protocol_code,
                port_range=item.port_range,
                source=item.source,
                description=item.description,
                sort=item.sort,
            )
            self.db.add(rule)
        self.db.flush()

    def create_rule(self, data: SecurityGroupRuleItem):
        rule = SecurityGroupRule(**data.model_dump())
        self.db.add(rule)
        self.db.flush()
        self.db.commit()
        return rule.id

    # 配置规则列表
    def list_by_rule(self, security_group_id: str) -> List[SecurityGroupRuleItem]:
        result = ((self.db.query(SecurityGroupRule)
        .filter(
                SecurityGroupRule.security_group_id == security_group_id,
                SecurityGroupRule.is_released == 0,
            )).all())
        return result

    # 删除规格
    def rule_mark_delete(self, rule_id: str):
        rule = self.get_by_rule_id(rule_id)
        if not rule:
            return None

        rule.is_released = 1
        rule.sync_status = 3  # 删除中或已删除

        self.db.flush()
        return True

    # 查找规则
    def get_by_rule_id(self, rule_id: str) -> Optional[type[SecurityGroupRule]]:
        return self.db.query(SecurityGroupRule).filter(
            SecurityGroupRule.id == rule_id,
            SecurityGroupRule.is_released == 0
        ).first()

    @staticmethod
    def _gen_uuid():
        return generate(size=12)


