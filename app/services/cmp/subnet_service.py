# app/services/cmp/subnet_service.py
from sqlalchemy.orm import Session
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.repositories.cmp.subnet_repo import SubnetRepository
from app.schemas.cmp.subnet_schema import SubnetCreate, SubnetOut, SubnetPage, SubnetBase
from app.services.cmp.operation_helper import execute_with_notification

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

class SubnetService:
    def __init__(self, cmp_db: Session):
        self.db = cmp_db
        self.subnet_repo = SubnetRepository(cmp_db)
        self.resource_bind_service = ResourceGroupService(self.db)

    # 一个list
    def list_subnets(self, vpc_id: int):
        subnets = self.subnet_repo.list_by_subnet(vpc_id)
        return subnets

    def used_subnet(self, vpc_id: int):
        return self.subnet_repo.used_subnet(vpc_id)

    # 分页查列表
    def page_subnets(
        self,
        user_id: int,
        cloud_provider_code: str = None,
        region_id: str = None,
        zone_id: str = None,
        vpc_id: str = None,
        resource_group_id: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> SubnetPage:
        items, total = self.subnet_repo.list_page(
            user_id=user_id,
            cloud_provider_code=cloud_provider_code,
            region_id=region_id,
            zone_id=zone_id,
            vpc_id=vpc_id,
            resource_group_id=resource_group_id,
            page=page,
            page_size=page_size
        )
        return SubnetPage(
            total=total,
            page=page,
            page_size=page_size,
            items=items
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
    def create(self, user: dict, data: SubnetCreate) -> bool:
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            payload = {
                **data.model_dump(),
                "created_by": user_id,
                "created_by_name": username,
                "subnet_id": f"subnet-{generate(size=12)}",
            }
            result = self.subnet_repo.create(payload)
            if not result:
                raise BusinessException(code=ErrorCode.FAILED, message="子网创建失败")

            self.resource_bind_service.bind(
                ResourceGroupBindingCreate(
                    cloud_provider_code=data.cloud_provider_code,
                    created_by = user_id,
                    created_by_name = username,
                    resource_group_id=data.resource_group_id,
                    resource_type="subnet",
                    resource_id=str(result.id),
                )
            )
            self.db.commit()
            self.db.refresh(result)
            return result

        # -------- 交给统一封装处理通知 --------
        info = execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="SUBNET",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="子网创建成功",
            failed_desc="子网创建失败",
            func=_do
        )
        return info

    # 删除
    def subnet_release(self, subnet_id: int) -> bool:
        obj = self.subnet_repo.get(subnet_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if obj.used_count > 0 and obj.status != 'AVAILABLE':
            raise BusinessException(code=ErrorCode.FAILED, message="无法释放正在使用的子网")
        obj = self.subnet_repo.release(obj)
        return obj

    # 子网修改
    def update_subnet(self, subnet_id: int, action: str):
        find = self.subnet_repo.get(subnet_id)

        delta = 1 if action == "bind" else -1

        # 防止 used_count 变成负数
        new_used_count = max(find.used_count + delta, 0)

        subnet_payload = {
            "used_count": new_used_count,
        }
        # 使用中 / 空闲 状态自动切换
        if new_used_count > 0:
            subnet_payload["status"] = "IN_USE"
        else:
            subnet_payload["status"] = "AVAILABLE"

        result = self.subnet_repo.update_subnet(find, subnet_payload)
        return result

    # 根据子网的id查询
    def subnet_by_id(self, subnet_id: int):
        return self.subnet_repo.get(subnet_id)
