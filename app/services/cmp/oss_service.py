import random

from sqlalchemy import func
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
from app.services.cmp.operation_helper import execute_with_notification


class OssBucketService:
    def __init__(self, db: Session):
        self.db = db
        self.oss_repo = OssRepoRepository(db)
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
        account = self.account_service.owner_account_exists(user)
        if not account:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        self.bill_service.create(
            user=user,
            account_id=account.id,
            resource_type="OSS",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )


    def oss_create(self, user: dict, data: OssCreate):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            payload = {
                **data.model_dump(),
                "created_by": user_id,
                "created_by_name": username,
                "charge_type": "PostPaid",
                "status": "ACTIVE",
                "bucket_id": f"oss-{generate(size=12)}",
                "endpoint": "ecs.aliyuncs.com",
                "object_count": random.randint(0, 100_000),
            }
            payload.pop('price')
            with self.db.begin():
                result = self.oss_repo.oss_create(payload)
                self.create_initial_bill(
                    user, payload['charge_type'], result.bucket_id, data.price, result,
                )
                return result

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="OSS",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="OSS对象存储创建成功",
            failed_desc="OSS对象存储创建失败",
            func=_do
        )

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

    # 释放
    def release(self, oss_id: int):
        result = self.oss_repo.release(oss_id)
        if not result:
            raise BusinessException(
                code=ErrorCode.FAILED,
                message=Message.FAILED
            )
        return result
