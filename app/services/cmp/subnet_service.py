# app/services/cmp/subnet_service.py
from sqlalchemy.orm import Session
from typing import List

from app.models.cmp import Subnet
# from nanoid import generate

from app.repositories.cmp.subnet_repo import SubnetRepository
from app.schemas.cmp.subnet_schema import SubnetCreate, SubnetOut, SubnetPage, SubnetBase
from app.common.status_code import ErrorCode
from app.common.messages import Message

class SubnetService:
    def __init__(self, cmp_db: Session):
        self.db = cmp_db
        self.subnet_repo = SubnetRepository(cmp_db)

    # 一个list
    def list_subnets(self, vpc_id: int) -> list[type[Subnet]]:
        subnets = self.subnet_repo.list_by_subnet(vpc_id)
        return subnets

    # 分页查列表
    def page_subnets(
            self,
            cloud_provider_code: str = None,
            region_id: str = None,
            subnet_id: str = None,
            resource_group_id: int = None,
            page: int = 1,
            page_size: int = 20
    ) -> SubnetPage:
        items, total = self.subnet_repo.list_page(
            cloud_provider_code=cloud_provider_code,
            region_id=region_id,
            subnet_id=subnet_id,
            resource_group_id=resource_group_id,
            page=page,
            page_size=page_size
        )
        return SubnetPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[SubnetOut.model_validate(s) for s in items]
        )

    # 某个vpc下的子网查询
    def vpc_id_by_subnet(self, vpc_id: int, page: int, page_size: int) -> SubnetPage:
        total, items = self.subnet_repo.vpc_by_subnet_page_list(vpc_id, page, page_size)
        return SubnetPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[SubnetOut.model_validate(s) for s in items]
        )

    # 创建
    def create(self, data: dict) -> SubnetOut:
        obj = self.subnet_repo.create(data)
        return SubnetOut.model_validate(obj)

    # 删除
    def subnet_release(self, subnet_id: str, cloud_provider_code: str) -> SubnetOut:
        obj = self.subnet_repo.get(subnet_id, cloud_provider_code)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        obj = self.subnet_repo.release(obj)
        return SubnetOut.model_validate(obj)

