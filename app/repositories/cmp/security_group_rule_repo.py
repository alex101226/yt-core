from typing import List
from sqlalchemy.orm import Session
from app.models.cmp.security_group_rule import SecurityGroupRule
from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleItem


class SecurityGroupRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    # 清空原规则
    def delete_by_group(self, security_group_id: str):
        self.db.query(SecurityGroupRule).filter(
            SecurityGroupRule.security_group_id == security_group_id,
            SecurityGroupRule.is_released == False,
        ).delete()
        self.db.flush()

    # 批量插入
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

    @staticmethod
    def _gen_uuid():
        from nanoid import generate
        return generate(size=12)
