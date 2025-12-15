from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger
from app.common.ipaddress import allocate_private_ip
from app.core.security import hash_password

from app.repositories.cmp.cbs_repo import CbsDiskRepository
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate

from app.repositories.cmp.bare_metal_instance_repo import BareMetalInstanceRepo
from app.schemas.cmp.bare_metal_instance_schema import BareMetalInstanceCreate

class BareMetalInstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BareMetalInstanceRepo(db)
        self.cbs_repo = CbsDiskRepository(db)


    # 创建裸金属
    def bare_metal_instance_create(self, user_id: int, data: BareMetalInstanceCreate):
        # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
        cidr = data.cidr_block
        private_ip = ''
        if cidr:
            # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
            used_ips = []
            private_ip = allocate_private_ip(cidr, used_ips)
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
        }
        payload.pop("cidr_block", None)
        payload.pop("password", None)

        instance = self.repo.bare_metal_create(payload)
        if not instance:
            return False
        return True
