from typing import Optional

from sqlalchemy.orm import Session
from nanoid import generate

from app.core.logger import logger
from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.common.util import parse_acl_rules

from app.common.ipaddress import allocate_private_ip, create_public_ip
from app.services.cmp.operation_helper import execute_with_notification

from app.constants.enums import (
    LoadBalancerStatus,
    ACLStatus,
    LoadCertificateStatus,
    NetworkType
)

from app.repositories.cmp.load_repo import LoadBalancerRepo

from app.services.cmp.account_service import AccountService
from app.services.cmp.bill_service import BillService
from app.services.cmp.resource_group_service import ResourceGroupService

from app.repositories.cmp.subnet_repo import SubnetRepository

from app.schemas.cmp.load_schema import (
LoadBalancerCreate,BackendMemberCreate,BackendPoolCreate,ListenerCreate,
LoadCertificateCreate
)

from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

class LoadBalancerService:
    def __init__(self, db: Session):
        self.db = db
        self.lb_repo = LoadBalancerRepo(db)
        self.resource_bind_service = ResourceGroupService(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)
        self.subnet_repo = SubnetRepository(db)

    # ========== 负载均衡实例 ==========
    #  创建负载均衡完整流程
    def create_load_balancer(self, user: dict, data: LoadBalancerCreate):
        def _do():
            user_id = user.get('user_id')
            try:
                with self.db.begin():

                    # 私网的ip
                    private_ip = ''
                    if data.network_type == NetworkType.PRIVATE and data.subnet_id:
                        subnet_all = self.lb_repo.get_subnet_id_by_find(data.subnet_id)
                        private_ips = {row.private_ip for row in subnet_all}

                        cidr = self.subnet_repo.get(str(data.subnet_id))

                        private_ip = allocate_private_ip(cidr.cidr_block, private_ips)

                    # 公网的ip
                    public_ip = ''
                    if data.network_type == NetworkType.PUBLIC:
                        public_ip = create_public_ip(data.region_id)

                    instance_payload = {
                        **data.model_dump(),
                        "user_id": user_id,
                        "status": LoadBalancerStatus.CREATING,
                        "lb_id": f"load-{generate(size=12)}",
                        "private_ip": private_ip,
                        "public_ip": public_ip,
                        "instance_type": "SPEC"
                    }

                    instance_payload.pop('price')
                    instance = self.lb_repo.create_instance(instance_payload)

                    if not instance:
                        raise BusinessException(code=ErrorCode.FAILED, message="创建失败")

                    # 查看账户
                    account = self.account_service.account_exists(user_id)
                    if not account:
                        raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

                    # 创建成功，生成周期性任务
                    self.bill_service.create(
                        user_id=user_id,
                        account_id=account.id,
                        resource_type="LOAD_INSTANCE",
                        charge_type=instance.charge_type,
                        instance_id=instance.lb_id,
                        instance=instance,
                        unit_price=data.price,  # 👈 创建时提交的价格
                    )

                    #   绑定资源组
                    self.resource_bind_service.bind(
                        ResourceGroupBindingCreate(
                            cloud_provider_code=data.cloud_provider_code,
                            user_id=user_id,
                            resource_group_id=data.resource_group_id,
                            resource_type="load",
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
            action_mode="LOAD_INSTANCE",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="负载均衡实例创建成功",
            failed_desc="负载均衡实例创建失败",
            func=_do
        )

    # 列表
    def instance_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code:  Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        lb_name: Optional[str] = None,
    ):
        items, total = self.lb_repo.instance_page_list(
            user_id, page, page_size, provider_code, region_id, resource_group_id, lb_name
        )
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }

    # ========== 创建访问控制（ACL） ==========
    def create_acl(self, user: dict, data):
        def _do():
            user_id = user.get("user_id")
            try:
                with self.db.begin():

                    # 1️⃣ 创建 ACL 主表
                    acl = self.lb_repo.create_acl({
                        **data.model_dump(),
                        "status": ACLStatus.DISABLED,
                        "user_id": user_id,
                    })

                    # 2️⃣ 解析规则文本
                    rules = parse_acl_rules(data.source_cidr)

                    # 3️⃣ 批量创建规则
                    self.lb_repo.bulk_create_rules(
                        acl_id=acl.id,
                        rules=rules
                    )

                return acl

            except BusinessException as e:
                self.db.rollback()
                raise e

        # -------- 审计 / 通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="LOAD_INSTANCE",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,
            success_desc="访问控制策略创建成功",
            failed_desc="访问控制策略创建失败",
            func=_do
        )

    # 访问控制列表
    def acl_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: str,
        region_id: str,
        resource_group_id: int,
        name: str,
    ):
        items, total = self.lb_repo.acl_page_list(
            user_id, page, page_size, provider_code, region_id, resource_group_id, name
        )
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }


    # ========== 负载均衡---证书 ==========
    def create_certificate(self, user: dict, data: LoadCertificateCreate):
        def _do():
            user_id = user.get("user_id")
            try:
                with self.db.begin():
                    cert = self.lb_repo.create_certificate({
                        **data.model_dump(),
                        "user_id": user_id,
                        "cert_id": f"load-cert-{generate(size=12)}",
                        "status": LoadCertificateStatus.AVAILABLE,
                    })
                return cert

            except BusinessException as e:
                self.db.rollback()
                raise e

        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="LOAD_INSTANCE",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,
            success_desc="负载均衡证书创建成功",
            failed_desc="负载均衡证书创建失败",
            func=_do
        )

    # ========== 分页列表 ==========
    def certificate_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
    ):
        items, total = self.lb_repo.certificate_page_list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            provider_code=provider_code,
            region_id=region_id,
            resource_group_id=resource_group_id,
        )

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        }



