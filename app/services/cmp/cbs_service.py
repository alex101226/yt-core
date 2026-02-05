from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from nanoid import generate

from app.core.logger import logger
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.util import gen_random_name

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.repositories.cmp.cbs_repo import CbsDiskRepository
from app.schemas.cmp.cbs_disk_schema import CbsInstallSchema, CbsDiskOut, CbsDiskPage

from app.services.cmp.operation_helper import execute_with_notification

class CbsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CbsDiskRepository(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)

    # 生成计费任务
    def create_initial_bill(
        self,
        user: dict,
        charge_type: str,
        instance_id: str,
        unit_price: float,
        instance,
    ):
        account = self.account_service.account_exists(user.get('user_id'))
        if not account:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        self.bill_service.create(
            user=user,
            account_id=account.id,
            resource_type="DISK",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 硬盘模块创建
    def cbs_create(self, user: dict, data: dict):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            payload = {
                **data,
                "disk_id": f"CBS-{generate(size=12)}",
                "encrypted": False,
                "status": "InUse" if data['attached_instance_id'] else "Available",
                "attached_time": data.get('attached_time', None),
                "is_attached": bool(data.get('attached_instance_id')),
                "created_by": user_id,
                "created_by_name": username,
            }
            payload.pop('price')
            result = self.repo.cbs_create(payload)
            self.create_initial_bill(
                user, payload['charge_type'], result.disk_id, data['price'], result,
            )
            self.db.commit()
            self.db.refresh(result)
            return result
        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="DISK",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="云硬盘（CBS）创建成功",
            failed_desc="云硬盘（CBS）创建失败",
            func=_do
        )


    #   自动创建cbs
    def cbs_create_auto(self, user: dict, price: float, data: dict, instance):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            payload = {
                **data,
                "created_by": user_id,
                "created_by_name": username,
                "disk_id": f"CBS-{generate(size=12)}",
                "encrypted": False,
                "tags": [],
                "status": "InUse" if data.get('attached_instance_id') else "Available",
                "cloud_provider_code": instance.cloud_provider_code,
                "region_id": instance.region_id,
                "zone_id": instance.zone_id,
                "resource_group_id": instance.resource_group_id,
                "charge_type": instance.charge_type,
            }
            result = self.repo.cbs_create(payload)
            self.create_initial_bill(
                user, payload['charge_type'], result.disk_id, price, result,
            )
            return result
        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="DISK",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="云硬盘（CBS）创建成功",
            failed_desc="云硬盘（CBS）创建失败",
            func=_do
        )

    # 返回分页列表
    def cbs_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[int] = None,
        zone_id: Optional[int] = None,
        resource_group_id: Optional[str] = None,
        cbs_id: Optional[str] = None
    ) -> CbsDiskPage:
        items, total = self.repo.get_page_list(user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, cbs_id)
        item_out = [CbsDiskOut.model_validate(s) for s in items]
        return CbsDiskPage(
            total=total,
            page=page,
            page_size=page_size,
            items=item_out,
        )


    # 释放
    def cbs_release(self, cbs_id: int) -> bool:
        db_cbs = self.repo.get_find(cbs_id)
        if db_cbs is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        invalid = {'Creating', 'Attaching', 'Detaching'}
        if db_cbs.status in invalid:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="请先卸载实例后再执行释放操作")

        return self.repo.cbs_release(cbs_id)

    # 卸载，系统盘不允许卸载，只允许根据实例一起释放
    def cbs_uninstall(self, cbs_id: int) -> bool:
        db_cbs = self.repo.get_find(cbs_id)
        if db_cbs is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if db_cbs.disk_type == 'system':
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="系统盘不允许卸载实例")

        return self.repo.cbs_uninstall(cbs_id)

    # 挂载
    def cbs_install(self, data: CbsInstallSchema):
        cbs = self.repo.cbs_install(data.model_dump())
        if not cbs:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return cbs