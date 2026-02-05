from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.core.logger import logger
from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.services.cmp.operation_helper import execute_with_notification

from app.models.cmp import CephfsFile

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.repositories.cmp.cephfs_file_repo import CephfsFileRepository
from app.schemas.cmp.cephfs_file_schema import (
CephfsCreate, CephfsPage, CephfsOut, CEPHFSCapacitySchema
)


class CephfsFileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CephfsFileRepository(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)

     # 生成计费任务
    def create_initial_bill(
        self,
        user: dict,
        charge_type: str,
        instance_id: str,
        unit_price: float,
        instance: CephfsFile,
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
            resource_type="CEPHFS",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    def cephfs_file_create(self, user: dict, data: CephfsCreate):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            payload = {
                **data.model_dump(),
                "created_by": user_id,
                "created_by_name": username,
                "charge_type": "PostPaid",
                "status": "ACTIVE",
                "fs_id": f"cephfs-{generate(size=12)}",
            }
            payload.pop('price')
            with self.db.begin():  # begin() 会自动管理 commit/rollback
                result = self.repo.cephfs_file_create(payload)
                if not result:
                    raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)



                self.create_initial_bill(
                    user, payload['charge_type'], result.fs_id, data.price, result,
                )
                return result

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="CEPHFS",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="CEPHFS文件存储创建成功",
            failed_desc="CEPHFS文件存储创建失败",
            func=_do
        )


    def cephfs_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[int] = None,
        resource_group_id: Optional[str] = None,
        storage_type: str = None,
        fs_name: str = None
    ):
        items, total = self.repo.cephfs_page_list(
            user_id, page, page_size, provider_code, region_id, resource_group_id,
            storage_type, fs_name
        )

        return CephfsPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[CephfsOut.model_validate(item) for item in items]
        )


    # 返回gpfs的列表
    def cephfs_list(self, user_id: int, region_id: str, status: Optional[str] = None):
        result = self.repo.cephfs_list(user_id, region_id, status)
        # logger.info(f'查看列表呗 {result}')
        if not result:
            return []
        return result


    # 容量配置
    def save_capacity_gb(self, data: CEPHFSCapacitySchema):
        result = self.repo.save_capacity_gb(data.model_dump())
        if not result:
            raise BusinessException(
                code=ErrorCode.FAILED,
                message=Message.FAILED
            )
        return result

    # 释放
    def release(self, cephfs_id: int):
        result = self.repo.release(cephfs_id)
        if not result:
            raise BusinessException(
                code=ErrorCode.FAILED,
                message=Message.FAILED
            )
        return result