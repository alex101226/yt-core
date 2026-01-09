from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.core.logger import logger
from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.schemas.cmp.oss_schema import OssCreate, OssPage, OssOut
from app.repositories.cmp.oss_repo import OssRepoRepository

class OssBucketService:
    def __init__(self, db: Session):
        self.db = db
        self.oss_repo = OssRepoRepository(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)

        # 生成计费任务

    def create_initial_bill(
            self,
            user_id: int,
            charge_type: str,
            instance_id: str,
            unit_price: float,
            instance,
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
            resource_type="OSS",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )


    def oss_create(self, user_id: int, data: OssCreate):
        payload = {
            **data.model_dump(),
            "user_id": user_id,
            "charge_type": "PostPaid",
            "status": "ACTIVE",
            "bucket_id": f"oss-{generate(size=12)}",
            "endpoint": "ecs.aliyuncs.com"
        }
        payload.pop('price')
        with self.db.begin():
            result = self.oss_repo.oss_create(payload)
            self.create_initial_bill(
                user_id, payload['charge_type'], result.bucket_id, data.price, result,
            )
            return result

    def oss_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        bucket_name: str = None,
        permission: str = None
    ):
        items, total = self.oss_repo.oss_page_list(user_id, page, page_size, provider_code, region_id, resource_group_id, bucket_name, permission)
        return OssPage(
            total=total,
            page=page,
            page_size=page_size,
            items = [OssOut.model_validate(item) for item in items]
        )