from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger
from app.common.ipaddress import allocate_private_ip
from app.core.security import hash_password

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

from app.services.cmp.eip_service import EIPService

from app.repositories.cmp.cbs_repo import CbsDiskRepository
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate

from app.repositories.cmp.bare_metal_instance_repo import BareMetalInstanceRepo
from app.schemas.cmp.bare_metal_instance_schema import (
BareMetalInstanceCreate, BareMetalInstanceOut, BareMetalInstancePage
)

class BareMetalInstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BareMetalInstanceRepo(db)
        self.cbs_repo = CbsDiskRepository(db)
        self.resource_bind_service = ResourceGroupService(db)
        self.eip_service = EIPService(db)


    # 创建裸金属
    def bare_metal_instance_create(self, user_id: int, data: BareMetalInstanceCreate):
        # 先查子网
        subnet_all = self.repo.get_find_by_subnet_id(data.vswitch_id)
        if not subnet_all:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        private_ips = {row.private_ip for row in subnet_all}

        # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
        cidr = data.cidr_block
        private_ip = ''
        if cidr:
            # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
            private_ip = allocate_private_ip(cidr, private_ips)

        # 1️⃣ 构造主表数据
        payload = {
            **data.model_dump(),
            "hashed_password": hash_password(data.password),
            "status": "RUNNING",
            "delivery_status": "DELIVERED",
            "last_operation": "RUNNING",
            "instance_id": f"bare_metal-{generate(size=12)}",
            "created_by": user_id,
            "private_ip": private_ip,
            "physical_machine_id": f"bare_metal-physical-{generate(size=6)}",
        }
        payload.pop("cidr_block", None)
        payload.pop("password", None)

        instance = self.repo.bare_metal_create(payload)
        if not instance:
            return False
        # 5. 是否需要公网 IP
        public_ip = self.eip_service.allocate_eip(
            provider_code=data.cloud_provider_code,
            region_id=data.region_id,
            instance_id=instance.id,
        )

        instance.public_ip = public_ip

        #   绑定安全组
        self.resource_bind_service.bind(
            ResourceGroupBindingCreate(
                cloud_provider_code=data.cloud_provider_code,
                user_id=user_id,
                resource_group_id=data.resource_group_id,
                resource_type="bare-metal",
                resource_id=str(instance.id),
            )
        )

        # 6. 提交
        self.db.commit()

        return True


    # 分页列表
    def bare_metal_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
        instance_id: Optional[str] = None,
        instance_name: Optional[str] = None,
        instance_type_id: Optional[str] = None,
        public_ip: Optional[str] = None,
        status: Optional[str] = None,
        ssh_proxy_port: Optional[int] = None,
    ):
        items, total = self.repo.bare_metal_page_list(
            user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id,
            instance_id, instance_name, instance_type_id, public_ip, status, ssh_proxy_port
        )

        return BareMetalInstancePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[BareMetalInstanceOut.model_validate(item) for item in items]
        )

