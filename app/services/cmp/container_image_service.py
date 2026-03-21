from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.core.logger import logger
from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.services.cmp.operation_helper import execute_with_notification

from app.repositories.cmp.cephfs_file_repo import CephfsFileRepository

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
        self.cephfs_repo = CephfsFileRepository(db)

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
            resource_type="CUSTOM_IMAGE",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 创建镜像服务
    def image_create(self, user: dict, data: dict):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            payload = {
                "created_by": user_id,
                "created_by_name": username,
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
                if not result:
                    raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)

                self.save_file_data(result.cephfs_id, True)
                self.create_initial_bill(
                    user, payload['charge_type'], result.repository_id, payload['price'], result,
                )
                return result
        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="CONTAINER_IMAGE",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="容器镜像创建成功",
            failed_desc="容器镜像创建失败",
            func=_do
        )


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

    # 释放
    def release(self, image_id: int):
        find = self.repo.release(image_id)
        if not find:
            raise BusinessException(code=ErrorCode.FAILED,message=Message.FAILED)
        self.save_file_data(find.cephfs_id, False)
        self.db.commit()
        self.db.refresh(find)
        return True

    # 修改存储
    # 更新文件系统数据
    def save_file_data(self, fs_id: int, is_mounted: bool):
        status = 'MOUNTED' if is_mounted else 'ACTIVE'
        self.cephfs_repo.save_status(fs_id, status)
