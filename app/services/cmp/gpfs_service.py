from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService


from app.repositories.cmp.gpfs_repo import GPFSRepository
from app.schemas.cmp.gpfs_schema import GPFSCreate, GPFSOut, GPFSPage, GPFSCapacitySchema
from app.services.cmp.operation_helper import execute_with_notification


class GPFSService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GPFSRepository(db)
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
            resource_type="GPFS",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 创建gpfs
    def gpfs_create(self, user: dict, data: GPFSCreate):
        user_id = user.get('user_id')
        def _do():
            payload = {
                **data.model_dump(),
                "created_by": user_id,
                "status": "ACTIVE",
                "fs_id": f"{data.storage_type}-{generate(size=12)}",
                "fs_name": f"{data.storage_type}-{generate(size=16)}",
            }
            with self.db.begin():
                result = self.repo.gpfs_create(payload)
                # 计费方式：PrePaid / PostPaid
                self.create_initial_bill(
                    user, data.charge_type, result.fs_id, data.price, result,
                )

                return result

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="GPFS",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="GPFS文件存储创建成功",
            failed_desc="GPFS文件存储创建失败",
            func=_do
        )


    # 分页列表
    def gpfs_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        storage_type: str = None,
        fs_name: str = None
    ) -> Optional[GPFSPage]:
        items, total = self.repo.gpfs_page_list(
            user_id, page, page_size, provider_code, region_id, zone_id,
            storage_type, fs_name
        )
        return GPFSPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[GPFSOut.model_validate(i) for i in items]
        )


    # 返回gpfs的列表
    def gpfs_list(self, user_id: int, subnet_id: str):
        result = self.repo.gpfs_list(user_id, subnet_id)
        return result

    # 容量配置
    def save_capacity_gb(self, data: GPFSCapacitySchema):
        result = self.repo.save_capacity_gb(data.model_dump())
        if not result:
            raise BusinessException(
                code=ErrorCode.FAILED,
                message=Message.FAILED
            )
        return result

    # 释放
    def release(self, gpfs_id: int):
        result = self.repo.release(gpfs_id)
        if not result:
            raise BusinessException(
                code=ErrorCode.FAILED,
                message=Message.FAILED
            )
        return result