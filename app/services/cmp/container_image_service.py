from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.core.logger import logger
from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.repositories.cmp.container_image_repo import ContainerImageRepository
from app.schemas.cmp.container_image_schema import ContainerImageCreate, ContainerImagePage, ContainerImageOut

class ContainerImageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContainerImageRepository(db)
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
            resource_type="CUSTOM_IMAGE",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 创建镜像服务
    def image_create(self, user_id: int, data: dict):
        payload = {
            "created_by": user_id,
            "enable_https": 0,
            "repository_id": f"cr-{generate(size=12)}",
            "repository_name": data['repository_name'],
            "capacity_gb": data['capacity_gb'],
            "cephfs_id": data['cephfs_id'],
            "charge_type": data['charge_type'],
            "cloud_provider_code": data['cloud_provider_code'],
            "region_id": data['region_id'],
            "instance_spec": data['instance_spec'],
            "resource_group_id": data['resource_group_id'],
            "price": data['price'],
            "status": "AVAILABLE"
        }
        with self.db.begin():  # begin() 会自动管理 commit/rollback  resource_id， resource_group_id
            result = self.repo.image_create(payload)
            self.create_initial_bill(
                user_id, payload['charge_type'], result.repository_id, payload['price'], result,
            )
            return result


    # 分页列表
    def con_image_page_list(
            self,
            user_id: int,
            page: int,
            page_size: int,
            provider_code: Optional[str] = None,
            region_id: Optional[int] = None,
            resource_group_id: Optional[str] = None,
            repository_name: str = None
    ):
        items, total = self.repo.con_image_page_list(
            user_id, page, page_size, provider_code, region_id, resource_group_id,
            repository_name
        )

        return ContainerImagePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[ContainerImageOut.model_validate(item) for item in items]
        )