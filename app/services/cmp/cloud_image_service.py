from typing import Optional

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService


from app.repositories.cmp.cloud_image_repo import CloudImageRepo
from app.schemas.cmp.cloud_image import CloudImageCreate
from app.services.cmp.operation_helper import execute_with_notification


class CloudImageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CloudImageRepo(db)
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
                message=Message.DATA_NOT_FOUND,
            )

        self.bill_service.create(
            user=user,
            account_id=account.id,
            resource_type="CUSTOM_IMAGE",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 创建云镜像
    def create_image(self, user: dict, image_data: CloudImageCreate):
        user_id = user.get('user_id')
        username = user.get('username')

        def _do():
            payload = {
                **image_data.model_dump(),
                "created_by": user_id,
                "created_by_name": username,
                "image_id": image_data.image_name,
            }
            payload.pop('price')

            result = self.repo.create(payload)
            self.create_initial_bill(
                user, payload['charge_type'], payload['image_id'], image_data.price, result,
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
            action_mode="CUSTOM_IMAGE",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="自定义镜像创建成功",
            failed_desc="自定义镜像创建失败",
            func=_do
        )

    def list_page_images(
        self,
        user_id: int,
        page: int,
        page_size: int,
        cloud_provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
        image_name: Optional[str] = None,
    ):

        items, total = self.repo.get_page_list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            cloud_provider_code=cloud_provider_code,
            region_id=region_id,
            resource_group_id=resource_group_id,
            image_name=image_name,
        )

        items_dict = []
        for img, rg_name in items:
            items_dict.append({
                "id": img.id,
                "image_id": img.image_id,
                "image_name": img.image_name,
                "os_type": img.os_type,
                "os_name": img.os_name,
                "cloud_provider_code": img.cloud_provider_code,
                "region_id": img.region_id,
                "resource_group_id": img.resource_group_id,
                "resource_group_name": rg_name,
                "architecture": img.architecture,
                "boot_mode": img.boot_mode,
                "size": img.size,
                "description": img.description,
                "status": img.status,
                "charge_type": img.charge_type,
                "period": img.period,
                "auto_renew": img.auto_renew,
                "created_at": img.created_at,
                "updated_at": img.updated_at,
            })

        return {
            "items": items_dict,
            "total": total,
            "page": page,
            "page_size": page_size,
        }