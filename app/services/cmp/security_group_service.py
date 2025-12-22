from typing import List

from pydantic import model_validator
from sqlalchemy.orm import Session
from nanoid import generate

from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException

from app.schemas.cmp.security_group_schema import SecurityGroupPage, SecurityGroup, SecurityGroupOut, SecurityGroupCreate
from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleUpdate, SecurityGroupRuleItem
from app.repositories.cmp.security_group_repo import SecurityGroupRepository

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

class SecurityGroupService:
    def __init__(self, cmp_db: Session):
        self.db = cmp_db
        self.security_group_repo = SecurityGroupRepository(cmp_db)
        self.resource_bind_service = ResourceGroupService(self.db)

    #   分页
    def list_page(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: str,
        region_id: str,
        resource_group_id: str,
        sg_name: str
    ) -> SecurityGroupPage:

        items, total = self.security_group_repo.list_page(
            user_id, page, page_size, provider_code, region_id, resource_group_id, sg_name
        )

        out_item = [SecurityGroupOut.model_validate(row)
            for row in items
        ]
        return SecurityGroupPage(
            total=total,
            page=page,
            page_size=page_size,
            items=out_item
        )

    def security_groups(self, provider_code: str, region_id: str, page: int = 1, page_size: int = 50):
        # provider = self.provider_repo.get_by_code(provider_code)
        # if not provider:
        #     raise BusinessException(...)
        # cloud_client = CloudClientFactory.create_client(
        #     provider_code,
        #     provider.access_key_id,
        #     provider.access_key_secret,
        #     provider.endpoint,
        # )
        current_page = page

        while True:
            resp = cloud_client.list_security_groups(
                region_id=region_id,
                vpc_id=None,
                page=current_page,
                page_size=page_size
            )

            items = resp.get("items", [])
            if not items:
                break

            # 批量保存
            self.security_group_repo.bulk_upsert_from_cloud(
                provider_code, region_id, items
            )

            # 如果少于 page_size 说明没有下一页
            if len(items) < page_size:
                break

            current_page += 1

        return True

    # ----------------------------
    # 创建安全组（本地 + 云端）
    # ----------------------------
    def create(self, user_id: int, data: SecurityGroupCreate):
        payload = {
            **data.model_dump(),
            "created_by": user_id,
            "sg_id": f'sg-{generate(size=12)}',
            "status": "AVAILABLE"
        }
        result = self.security_group_repo.create_group(payload)
        if not result:
            return False
        # self.update_rules(result)
        self.resource_bind_service.bind(
            ResourceGroupBindingCreate(
                cloud_provider_code=data.cloud_provider_code,
                user_id=user_id,
                resource_group_id=data.resource_group_id,
                resource_type="security",
                resource_id=str(result),
            )
        )
        return result

    # ----------------------------
    # 释放安全组
    # ----------------------------
    def release(self, group_id: int):
        sg = self.security_group_repo.group_mark_released(group_id)
        if not sg:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )
        return True

    #   返回安全组的列表数据
    def list_security_groups(self, provider_code: str, region_id: str, vpc_id: int) -> List[SecurityGroup]:
        return self.security_group_repo.get_by_security_group(provider_code, region_id, vpc_id)

    # 更新规则（入 + 出）
    def batch_update_rules(self, data: SecurityGroupRuleUpdate):
        sg = self.security_group_repo.get_by_id(data.security_group_id)
        if not sg:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND,
            )

        # 1. 清空原规则
        self.security_group_repo.delete_by_group(data.security_group_id)

        # 2. 设置 direction 字段
        for item in data.ingress_rules:
            item.direction = "inbound"

        for item in data.egress_rules:
            item.direction = "outbound"

        # 3. 入方向写入
        self.security_group_repo.bulk_create(data.security_group_id, data.ingress_rules)

        # 4. 出方向写入
        self.security_group_repo.bulk_create(data.security_group_id, data.egress_rules)

        self.db.commit()
        return True

        #   删除规则

    # 单挑规则插入（入 + 出）
    def create_rule(self, data: SecurityGroupRuleItem):
        sg = self.security_group_repo.get_by_id(data.security_group_id)
        if not sg:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND,
            )
        result = self.security_group_repo.create_rule(data)
        if not result:
            return False
        return True

    # 删除某个规则
    def delete_rules(self, rule_id: str):
        # 验证安全组存在
        rule = self.security_group_repo.get_by_rule_id(rule_id)
        if not rule:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        deleted = self.security_group_repo.rule_mark_delete(rule_id)
        self.db.commit()
        return deleted

        #   返回列表

    # 配置规则列表
    def list_rules(self, security_group_id: str):
        return self.security_group_repo.list_by_rule(security_group_id)
