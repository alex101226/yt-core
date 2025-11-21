from typing import List, Optional
from sqlalchemy.orm import Session
from nanoid import generate

from app.models.cmp.security_group_rule import SecurityGroupRule
from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleItem


class SecurityGroupRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    # 清空原规则
    def delete_by_group(self, security_group_id: str):
        self.db.query(SecurityGroupRule).filter(
            SecurityGroupRule.security_group_id == security_group_id,
            SecurityGroupRule.is_deleted == 0
        ).delete()
        self.db.flush()

    #   删除 cloud_rule_id != None 的云端规则，本地创建的规则不动
    def delete_cloud_rules(self, security_group_id: str):
        self.db.query(SecurityGroupRule).filter(
            SecurityGroupRule.security_group_id == security_group_id,
            SecurityGroupRule.cloud_rule_id.isnot(None)
        ).delete()
        self.db.flush()

    #   云端批量插入
    def insert_cloud_rule(self, security_group_id: str, rule: dict):
        item = SecurityGroupRule(
            id=self._gen_uuid(),
            security_group_id=security_group_id,
            direction=rule["direction"],
            policy_code=rule["policy_code"],
            protocol_code=rule["protocol_code"],
            port_range=rule["port_range"],
            source=rule["source"],
            description=rule.get("description"),
            cloud_rule_id=rule.get("cloud_rule_id"),
            sync_status=1,  # 表示：来自云端
        )
        self.db.add(item)

    # 本地批量插入
    def bulk_create(self, security_group_id: str, rules: List[SecurityGroupRuleItem]):
        for item in rules:
            rule = SecurityGroupRule(
                id=self._gen_uuid(),
                security_group_id=security_group_id,
                direction=item.direction,
                policy_code=item.policy_code,
                protocol_code=item.protocol_code,
                port_range=item.port_range,
                source=item.source,
                description=item.description,
                sync_status=0,  # 本地新增 → 未同步
            )
            self.db.add(rule)
        self.db.flush()

    # 列表
    def list_by_group(self, security_group_id: str) -> List[SecurityGroupRuleItem]:
        return (
            self.db.query(SecurityGroupRule)
            .filter(
                SecurityGroupRule.security_group_id == security_group_id,
                SecurityGroupRule.is_released == 0,
            )
            .all()
        )

    # 逻辑删除规则：标记 is_released, released_at, sync_status
    def mark_delete(self, rule_id: str):
        rule = (
            self.db.query(SecurityGroupRule)
            .filter(
                SecurityGroupRule.id == rule_id,
                SecurityGroupRule.is_released == 0
            )
            .first()
        )
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        rule.is_released = 1
        rule.released_at = now
        rule.sync_status = 3  # 删除中或已删除

        self.db.flush()
        return True


    def get_by_rule_id(self, rule_id: str) -> Optional[type[SecurityGroupRule]]:
        return self.db.query(SecurityGroupRule).filter_by(id=rule_id).first()

    @staticmethod
    def _gen_uuid():
        return generate(size=12)
