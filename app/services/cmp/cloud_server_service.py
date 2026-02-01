# app/services/cmp/instance_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.common.util import gen_random_name
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.common.ipaddress import allocate_private_ip
from app.core.security import hash_password

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.services.cmp.subnet_service import SubnetService
from app.services.cmp.vpc_service import VPCService
from app.services.cmp.eip_service import EIPService

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

from app.services.cmp.cbs_service import CbsService

# 通知
from app.services.cmp.operation_helper import execute_with_notification

from app.repositories.cmp.server_instance_repo import ServerInstanceRepo
from app.schemas.cmp.server_instance_schema import (
InstanceActionSchema, InstanceUpdatePassword, InstanceCreateSchema, InstanceBaseOut, InstancePage
)

class InstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServerInstanceRepo(db)
        self.cbs_service = CbsService(db)
        self.resource_bind_service = ResourceGroupService(db)
        self.eip_service = EIPService(db)
        self.vpc_service = VPCService(db)
        self.subnet_service = SubnetService(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)

    # 创建服务器
    def create_instance(self, user: dict, data: InstanceCreateSchema):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            try:
                with self.db.begin():
                    # 先查子网
                    subnet_all = self.repo.get_find_by_subnet_id(data.vswitch_id)
                    private_ips = {row.private_ip for row in subnet_all}

                    # 默认开启释放保护
                    # schema['enable_protection'] = 1
                    # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
                    cidr = data.cidr_block
                    private_ip = ''
                    if cidr:
                        # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
                        private_ip = allocate_private_ip(cidr, private_ips)

                    payload = {
                        **data.model_dump(),
                        "hashed_password": hash_password(data.password),
                        "status": "RUNNING",
                        "instance_id": f"cloud_server-{generate(size=12)}",
                        "created_by": user_id,
                        "created_by_name": username,
                        "private_ip": private_ip
                    }

                    # ⭐ 3) payload 中删除 cidr_block
                    payload.pop("cidr_block", None)
                    payload.pop("password", None)

                    instance = self.repo.create_instance_task(payload)
                    if not instance:
                        raise BusinessException(code= ErrorCode.FAILED,message="实例创建失败")  # 不返回 False，直接抛异常

                    # 查看账户
                    account = self.account_service.account_exists(user_id)
                    if not account:
                        raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

                    # 创建成功，生成周期性任务
                    self.bill_service.create(
                        user=user,
                        account_id=account.id,
                        resource_type="SERVER",
                        charge_type=instance.charge_type,
                        instance_id=instance.instance_id,
                        instance=instance,
                        unit_price=data.price,  # 👈 创建时提交的价格
                    )

                    #  设置vpc
                    self.vpc_service.update_vpc(data.vpc_id)

                    # 设置子网
                    self.subnet_service.update_subnet(data.vswitch_id)

                    # 5. 是否需要公网 IP
                    public_ip = self.eip_service.allocate_eip(
                        provider_code=data.cloud_provider_code,
                        region_id=data.region_id,
                        instance_id=instance.id,
                    )

                    instance.public_ip = public_ip

                    # -----------------------------
                    # 2. 创建系统盘 CBS
                    # -----------------------------
                    system_disk_data = {
                        "cloud_provider_code": data.cloud_provider_code,
                        "region_id": data.region_id,
                        "zone_id": data.zone_id,
                        "resource_group_id": data.resource_group_id,
                        "disk_name": gen_random_name('cbs-system'),
                        "disk_type": "system",  # 磁盘类型：system 系统盘 / data 数据盘。
                        "disk_category": data.system_disk_category,  # 磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等
                        "disk_size": data.system_disk_size,  # 磁盘大小
                        "charge_type": data.charge_type,  # 计费方式：PrePaid 包年包月 / PostPaid 按量付费
                        "period": data.period or 1,  # 包年月的月份
                        "auto_renew": data.auto_renew,
                        "attached_instance_id": str(instance.id),  # 挂载的实例 ID（ecs/lh/lb）
                        "attached_device": data.instance_name,  # 挂载点名称，如 /dev/vdb
                        "attached_time": datetime.now(timezone.utc),  # 挂载时间
                        "description": f"系统盘，挂载到实例 {instance.instance_name}",
                        "tags": [],
                    }
                    self.cbs_service.cbs_create_auto(user, system_disk_data, instance.charge_type, 2.5)

                    # -----------------------------
                    # 3. 创建数据盘 CBS
                    # -----------------------------
                    if data.data_disks:
                        for disk in data.data_disks:
                            disk_data = {
                                "cloud_provider_code": data.cloud_provider_code,
                                "region_id": data.region_id,
                                "zone_id": data.zone_id,
                                "resource_group_id": data.resource_group_id,
                                "disk_name": gen_random_name('cbs-data'),
                                "disk_type": "data",  # 磁盘类型：system 系统盘 / data 数据盘。
                                "disk_category": disk.disk_category,  # 磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等
                                "disk_size": disk.disk_size,  # 磁盘大小
                                "charge_type": data.charge_type,  # 计费方式：PrePaid 包年包月 / PostPaid 按量付费
                                "period": data.period or 1,  # 包年月的月份
                                "auto_renew": data.auto_renew,
                                "attached_instance_id": str(instance.id),  # 挂载的实例 ID（ecs/lh/lb）
                                "attached_device": data.instance_name,  # 挂载点名称，如 /dev/vdb
                                "attached_time": datetime.now(timezone.utc),  # 挂载时间
                                "description": f"系统盘，挂载到实例 {instance.instance_name}",
                                "tags": [],
                            }
                            self.cbs_service.cbs_create_auto(user, disk_data, disk_data['charge_type'], 2.5)

                    #   绑定资源组
                    self.resource_bind_service.bind(
                        ResourceGroupBindingCreate(
                            cloud_provider_code=data.cloud_provider_code,
                            created_by = user_id,
                            created_by_name = username,
                            resource_group_id=data.resource_group_id,
                            resource_type="cloud_server",
                            resource_id=str(instance.id),
                        )
                    )
                return instance
            except BusinessException as exception:
                self.db.rollback()
                raise exception
        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="SERVER",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else 0,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="云服务器创建成功",
            failed_desc="云服务器创建失败",
            func=_do
        )


    # 返回服务器列表
    def server_list_page(
        self,
        user_id: int,
        provider_code: str,
        region_id: str,
        zone_id: str,
        resource_group_id: str,
        instance_id: str,
        instance_name: str,
        instance_type: str,
        ip: str,
        status: int,
        ssh_proxy_port: int,
        page: int,
        page_size: int,
    ):
        items, total = self.repo.list_page(
            user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, instance_id,
            instance_name, instance_type, ip, status, ssh_proxy_port
        )

        return InstancePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[InstanceBaseOut.model_validate(i) for i in items],
        )


    # 开机，关机，重启，
    def start_instance(self, data: InstanceActionSchema):
        # 1️⃣ 创建操作任务
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        instance.status = data.status
        # instance.last_operation = data.status
        instance.updated_at = datetime.now(timezone.utc)
        self.repo.commit()

        # 创建轮询任务
        # self.repo.create_status_check_task(
        #     main_task_id=instance.id,
        #     instance_id=instance.instance_id,
        #     check_count=0,
        #     max_check=10,
        #     status=1
        # )
        # self.repo.commit()
        return {"instance_id": instance.instance_id}


    # 修改服务器密码   hash_password
    def save_server_password(self, data: InstanceUpdatePassword):
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        hashed_password = hash_password(data.password)
        result = self.repo.save_server_password(instance.instance_id, hashed_password)
        return result

    # 开启/关闭释放保护
    def toggle_server_release(self, instance_id: int, user_id: int):
        instance = self.repo.get_instance_by_find(instance_id)
        if instance.user_id != user_id:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return self.repo.toggle_server_release(instance_id)

    # 释放
    def server_release(self, instance_id: int):
        instance = self.repo.get_instance_by_find(instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if instance.enable_protection == 1:
           raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="此服务器无法释放")

        active_status = {
            'STARTING',
            'CREATING',
            'RUNNING',
            'DEPLOYING',
            'DISK_EXPANDING',
            'PREPARE_REBOOT'
        }

        if instance.status in active_status:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前服务器正在使用，无法释放")
        return self.repo.server_release(instance_id)

    # 克隆
    def server_clone(self, instance_id: int):
        db_instance = self.repo.get_instance_by_find(instance_id)
        if not db_instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return self.repo.clone_instance(instance_id)