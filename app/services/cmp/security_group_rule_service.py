from sqlalchemy.orm import Session

from app.clients.cloud_client_factory import CloudClientFactory
from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.cmp.security_group_rule_repo import SecurityGroupRuleRepository
from app.repositories.cmp.security_group_repo import SecurityGroupRepository
from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleUpdate, SecurityGroupRuleOut
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message


class SecurityGroupRuleService:
    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.rule_repo = SecurityGroupRuleRepository(cmp_db)
        self.sg_repo = SecurityGroupRepository(cmp_db)
        self.public_repo = CloudProviderRepository(public_db)

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

    #   删除规则
    def delete_rules(self, rule_id: str):
        # 验证安全组存在
        rule = self.rule_repo.get_by_rule_id(rule_id)
        if not rule:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        deleted = self.rule_repo.mark_delete(rule_id)
        self.db.commit()
        # return [r.id for r in deleted]
        return deleted


    #   返回列表
    def list_rules(self, security_group_id: str):
        # 验证安全组存在
        # sg = self.sg_repo.get_by_id(security_group_id)
        # if not sg:
        #     raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        # ---- 自动同步云规则（不影响本地创建的规则）----
        # if sg.cloud_group_id:
        #     self.sync_from_cloud(sg)

        # ---- 返回本地规则（本地 + 云同步的）----
        return self.rule_repo.list_by_group(security_group_id)


    # 云同步安全组规则 1. 云端安全组必须存在 cloud_group_id
    def sync_from_cloud(self, sg):
        if not sg.cloud_group_id:
            return

        # 2. 云厂商凭证
        cred = self.sg_repo.get_credential_by_sg(sg.id)
        if not cred:
            return

        # 3. 创建阿里云客户端
        provider = self.provider_repo.get_by_code(sg.cloud_provider_code)
        client = CloudClientFactory.create_client(
            provider.provider_code,
            cred.access_key_id,
            cred.access_key_secret,
            provider.endpoint,
        )

        # 4. 调用云 API
        rules = client.list_security_group_rules(
            region_id=sg.region_id,
            security_group_id=sg.cloud_group_id
        )

        # 5. 清空旧的阿里云规则（本地创建的不删）
        self.rule_repo.delete_cloud_rules(sg.id)

        # 6. 写入新的云规则
        for r in rules:
            self.rule_repo.insert_cloud_rule(sg.id, r)

        self.db.commit()