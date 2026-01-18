# app/services/public/cloud_vpc_service.py
from typing import List
from sqlalchemy.orm import Session
from nanoid import generate

from app.core.logger import logger
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException

from app.schemas.cmp.vpc_schema import VpcOut, VpcCreate, VpcBase, VpcList
from app.repositories.cmp.vpc_repo import VpcRepository

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

# 通知
from app.services.cmp.operation_helper import execute_with_notification

"""
VPC 服务层：提供业务逻辑处理
"""
class VPCService:
    def __init__(self, cmp_db: Session):
        self.db = cmp_db
        self.vpc_repo = VpcRepository(cmp_db)
        self.resource_bind_service = ResourceGroupService(self.db)

    """
    获取指定 Region 的 VPC 列表
    """
    def sync_vpcs(self, user_id: int, provider_code: str, region_id: str):
        vpcs = self.vpc_repo.get_by_vpcs(user_id, provider_code, region_id)
        return [VpcOut.model_validate(i) for i in vpcs]

    # 返回带分页的vpc
    def list_page(
        self,
        user_id: int, page: int, page_size: int, provider_code: str,
        region_id: str, resource_group_id: str, vpc_name: str):
        return self.vpc_repo.list_page(user_id, page, page_size, provider_code, region_id, resource_group_id, vpc_name)

    # --------------------------------
    # 创建单个 VPC
    # --------------------------------
    def create(self, user: dict, data: VpcCreate):
        user_id = user.get('user_id')
        def _do():
            payload = {
                **data.model_dump(),
                "created_by": user_id,
                "vpc_id": f"vpc-{generate(size=12)}"
            }
            vpc = self.vpc_repo.create(payload)
            if not vpc:
                raise BusinessException(code=ErrorCode.FAILED, message="vpc创建失败")  # 不返回 False，直接抛异常

            self.resource_bind_service.bind(
                ResourceGroupBindingCreate(
                    cloud_provider_code=data.cloud_provider_code,
                    user_id=user_id,
                    resource_group_id=data.resource_group_id,
                    resource_type="vpc",
                    resource_id=str(vpc),
                )
            )
            return vpc
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="VPC",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="vpc创建成功",
            failed_desc="vpc创建失败",
            func=_do
        )


    # 释放逻辑
    def release(self, vpc_id: int) -> bool:
        vpc = self.vpc_repo.get(vpc_id)
        if not vpc:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if vpc.is_released:
            raise BusinessException(code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND, message= '该 VPC 已释放，无需重复释放')

        vpc_release = self.vpc_repo.release(vpc)
        if vpc_release:
            return True
        return False


    # 修改vpc
    def update_vpc(self, vpc_id: int):
        find = self.vpc_repo.get(vpc_id)
        vpc_payload = {
            "used_count": find.used_count + 1,
        }
        if find.status != "IN_USE":
            vpc_payload["status"] = "IN_USE"

        result = self.vpc_repo.update_vpc(find, vpc_payload)
        return result