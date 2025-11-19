from sqlalchemy.orm import Session
from app.repositories.cmp.security_group_rule_repo import SecurityGroupRuleRepository
from app.repositories.cmp.security_group_repo import SecurityGroupRepository
from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleUpdate
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message


class SecurityGroupRuleService:
    def __init__(self, db: Session):
        self.db = db
        self.rule_repo = SecurityGroupRuleRepository(db)
        self.sg_repo = SecurityGroupRepository(db)

    # 批量更新规则（入 + 出）
    def update_rules(self, data: SecurityGroupRuleUpdate):
        sg = self.sg_repo.get_by_id(data.security_group_id)
        if not sg:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND,
            )

        # 1. 清空原规则
        self.rule_repo.delete_by_group(data.security_group_id)

        # 2. 设置 direction 字段
        for item in data.ingress_rules:
            item.direction = "inbound"

        for item in data.egress_rules:
            item.direction = "outbound"

        # 3. 入方向写入
        self.rule_repo.bulk_create(data.security_group_id, data.ingress_rules)

        # 4. 出方向写入
        self.rule_repo.bulk_create(data.security_group_id, data.egress_rules)

        self.db.commit()
        return True
