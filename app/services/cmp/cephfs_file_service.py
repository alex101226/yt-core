from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.core.logger import logger
from app.models.cmp import CephfsFile

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.repositories.cmp.cephfs_file_repo import CephfsFileRepository
from app.schemas.cmp.cephfs_file_schema import CephfsCreate, CephfsPage, CephfsOut

class CephfsFileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CephfsFileRepository(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)

     # 生成计费任务
    def create_initial_bill(
        self,
        user_id: int,
        charge_type: str,
        instance_id: str,
        unit_price: float,
        instance: CephfsFile,
    ):
        account = self.account_service.account_exists(user_id)
        if not account:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        self.bill_service.create(
            user_id=user_id,
            account_id=account.id,
            resource_type="CEPHFS",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    def cephfs_file_create(self, user_id: int, data: CephfsCreate):
        payload = {
            **data.model_dump(),
            "user_id": user_id,
            "charge_type": "PostPaid",
            "status": "ACTIVE",
            "fs_id": f"cephfs-{generate(size=12)}",
        }
        with self.db.begin():  # begin() 会自动管理 commit/rollback
            result = self.repo.cephfs_file_create(payload)

            self.create_initial_bill(
                user_id, payload['charge_type'], result.fs_id, payload['price'], result,
            )
            return True

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
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )
        return result