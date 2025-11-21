from typing import List
from sqlalchemy.orm import Session
from app.schemas.cmp.security_group_schema import SecurityGroupSearch, SecurityGroupPage, SecurityGroupCreate, SecurityGroup
from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.cmp.security_group_repo import SecurityGroupRepository
from app.common.pagination import paginate_query
from app.common.status_code import ErrorCode
from app.common.messages import Message

class SecurityGroupService:
    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.provider_repo = CloudProviderRepository(public_db)
        self.security_group_repo = SecurityGroupRepository(cmp_db)
    #   分页
    def list_page(self, filters: SecurityGroupSearch) -> SecurityGroupPage:

        q = self.security_group_repo.search(filters)
        total, items = paginate_query(q, filters.page, filters.page_size)

        if total > 0:
            return SecurityGroupPage(total=total, page=filters.page, page_size=filters.page_size, items=items)

        if total == 0 and filters.cloud_provider_code and filters.region_id:
            self.security_groups(provider_code=filters.cloud_provider_code, region_id=filters.region_id)
            # 重新查询 DB
            q = self.security_group_repo.search(filters)
            total, items = paginate_query(q, filters.page, filters.page_size)

        return SecurityGroupPage(total=total, page=filters.page, page_size=filters.page_size, items=items)

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
    def create(self, data: SecurityGroupCreate):
        # provider = self.provider_repo.get_by_code(data.cloud_provider_code)
        # if not provider:
        #     raise BusinessException(
        #         code=ErrorCode.DATA_NOT_FOUND,
        #         message="云厂商未配置"
        #     )

        # 本地先落库
        sg = self.security_group_repo.create_group(data)

        # ----- 云端创建安全组 -----
        # cloud_client = CloudClientFactory.create_client(
        #     data.cloud_provider_code,
        #     provider.access_key_id,
        #     provider.access_key_secret,
        #     provider.endpoint,
        # )

        # cloud_resp = cloud_client.create_security_group(
        #     security_name=data.security_name,
        #     description=data.description,
        #     region_id=data.region_id,
        #     vpc_id=sg.vpc.cloud_vpc_id,  # 本地 VPC 映射云端 VPC
        # )

        # cloud_group_id = cloud_resp.get("SecurityGroupId")
        # if not cloud_group_id:
        #     raise BusinessException(
        #         code=ErrorCode.CLOUD_API_ERROR,
        #         message="云端创建安全组失败"
        #     )

        # 回写云端 ID
        # sg.cloud_group_id = cloud_group_id
        sg.sync_status = 1
        self.db.commit()

        return sg

    # ----------------------------
    # 释放安全组
    # ----------------------------
    def release(self, group_id: str):
        sg = self.security_group_repo.mark_released(group_id)
        if not sg:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # provider = self.provider_repo.get_by_code(sg.cloud_provider_code)
        # cloud_client = CloudClientFactory.create_client(
        #     sg.cloud_provider_code,
        #     provider.access_key_id,
        #     provider.access_key_secret,
        #     provider.endpoint,
        # )

        # if sg.cloud_group_id:
        #     cloud_client.delete_security_group(security_group_id=sg.cloud_group_id)

        sg.sync_status = 3
        self.db.commit()

        return True


    def list_security_groups(self, provider_code: str, region_id: str, vpc_id: int) -> List[SecurityGroup]:
        return self.security_group_repo.get_by_security_group(provider_code, region_id, vpc_id)