from typing import Optional, Tuple, List, Any
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.load_instance import LoadBalancer
from app.models.cmp.load_listener import LoadBalancerListener
from app.models.cmp.load_backend_pool import BackendPool
from app.models.cmp.load_backend_member import BackendMember
from app.models.cmp.load_acl import LoadBalancerACL
from app.models.cmp.load_acl_rule import LoadBalancerACLRule
from app.models.cmp.load_certificate import LoadBalancerCertificate

from app.schemas.cmp.load_schema import (
LoadBalancerCreate,BackendMemberCreate,BackendPoolCreate,ListenerCreate
)

class LoadBalancerRepo:
    def __init__(self, db: Session):
        self.db = db
    # ===========   负载均衡实例  ================
    # 创建负载均衡实例
    def create_instance(self, lb: dict):
        lb_db = LoadBalancer(**lb)
        self.db.add(lb_db)
        # self.db.commit()
        # self.db.refresh(lb_db)
        self.db.flush()
        return lb_db

    # 根据 ID 查询
    def get_by_instance_id(self, lb_id: int) -> Optional[LoadBalancer]:
        return self.db.query(LoadBalancer).filter(
            LoadBalancer.id == lb_id
        ).first()

    # 根据子网查询
    def get_subnet_id_by_find(self, subnet_id: int):
        return self.db.query(
            LoadBalancer.subnet_id,
            LoadBalancer.private_ip,
        ).filter(LoadBalancer.subnet_id==subnet_id, LoadBalancer.is_released == 0).all()


    # 列表分页
    def instance_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        lb_name: Optional[str] = None,
    ):
        query = self.db.query(LoadBalancer).order_by(LoadBalancer.id.desc())
        filters = [LoadBalancer.user_id == user_id, LoadBalancer.is_released == 0]
        if provider_code:
            filters.append(LoadBalancer.cloud_provider_code == provider_code)
        if region_id:
            filters.append(LoadBalancer.region_id == region_id)
        if resource_group_id:
            filters.append(LoadBalancer.resource_group_id == resource_group_id)
        if lb_name:
            filters.append(LoadBalancer.lb_name.like(f'%{lb_name}%'))

        query = query.filter(*filters)
        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(LoadBalancer.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total

    # ==============访问控制=============
    # 创建 ACL
    def create_acl(self, acl_data: dict):
        acl = LoadBalancerACL(**acl_data)
        self.db.add(acl)
        self.db.flush()  # 拿到 acl.id
        return acl

    # 批量创建 ACL 规则
    def bulk_create_rules(self, acl_id: int, rules: List[dict]):
        rule_objs = []
        for rule in rules:
            rule["acl_id"] = acl_id
            rule_objs.append(LoadBalancerACLRule(**rule))

        self.db.bulk_save_objects(rule_objs)

    # 禁用 ACL 下的所有规则
    def disable_rules_by_acl_id(self, acl_id: int):
        self.db.query(LoadBalancerACLRule).filter(
            LoadBalancerACLRule.acl_id == acl_id
        ).update(
            {
                "status": "DISABLED"
            },
            synchronize_session=False
        )

    # 查找单个acl
    def acl_get_by_id(self, acl_id: int) -> Optional[LoadBalancerACL]:
        return self.db.query(LoadBalancerACL).filter(
            LoadBalancerACL.id == acl_id,
            LoadBalancerACL.is_released == 0
        ).first()

    # acl列表
    def acl_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        cloud_provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
        name: Optional[str] = None,
    ):

        query = self.db.query(LoadBalancerACL).filter(
            LoadBalancerACL.user_id == user_id,
            LoadBalancerACL.is_released == 0
        )

        if cloud_provider_code:
            query = query.filter(LoadBalancerACL.cloud_provider_code == cloud_provider_code)
        if region_id:
            query = query.filter(LoadBalancerACL.region_id == region_id)
        if resource_group_id:
            query = query.filter(LoadBalancerACL.resource_group_id == resource_group_id)
        if name:
            query = query.filter(LoadBalancerACL.name.like(f"%{name}%"))

        total = query.count()
        items = query.order_by(
            LoadBalancerACL.id.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    # acl删除
    def soft_delete(self, acl_id: int):
        find = self.acl_get_by_id(acl_id)
        if not find:
            return None
        find.is_released = 1
        self.db.commit()
        self.db.refresh(find)
        return find

    # ==============证书管理=============
    def create_certificate(self, cert_data: dict) -> LoadBalancerCertificate:
        """
        创建负载均衡证书
        :param cert_data: dict 包含证书必要字段，例如：
            cert_name, resource_group_id, cloud_provider_code, region_id,
            cert_content, cert_key, tags, description, user_id
        """
        cert_db = LoadBalancerCertificate(**cert_data)
        self.db.add(cert_db)
        self.db.flush()  # flush 保证立即生成主键
        return cert_db

    # ================== 根据 ID 查询证书 ==================
    def cert_get_by_id(self, cert_id: int) -> Optional[LoadBalancerCertificate]:
        return self.db.query(LoadBalancerCertificate).filter(
            LoadBalancerCertificate.id == cert_id
        ).first()

    # ================== 根据证书名称查询 ==================
    def cert_get_by_name(self, cert_name: str, user_id: Optional[int] = None):
        query = self.db.query(LoadBalancerCertificate).filter(
            LoadBalancerCertificate.cert_name == cert_name
        )
        if user_id:
            query = query.filter(LoadBalancerCertificate.user_id == user_id)
        return query.all()

    # ================== 分页列表 ========================
    def certificate_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
    ):
        """
        分页获取证书列表
        """
        query = self.db.query(LoadBalancerCertificate).order_by(LoadBalancerCertificate.id.desc())
        filters = [LoadBalancerCertificate.user_id == user_id]
        if provider_code:
            filters.append(LoadBalancerCertificate.cloud_provider_code == provider_code)
        if region_id:
            filters.append(LoadBalancerCertificate.region_id == region_id)
        if resource_group_id:
            filters.append(LoadBalancerCertificate.resource_group_id == resource_group_id)

        query = query.filter(*filters)
        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.offset(offset_value).limit(page_size).all()
        return items, total

    # ==============监听器=============
    # 创建监听器
    def listen_create(self, listener: ListenerCreate):
        self.db.add(listener)
        self.db.flush()
        return listener

    # 根据负载均衡实例查询
    def listen_list_by_lb(self, lb_id: int):
        return self.db.query(LoadBalancerListener).filter(
            LoadBalancerListener.lb_id == lb_id
        ).all()

    # 查询单个监听器
    def get_by_listen_id(self, listener_id: int) -> Optional[LoadBalancerListener]:
        return self.db.query(LoadBalancerListener).filter(
            LoadBalancerListener.id == listener_id
        ).first()

    # ==============后端池=============
    # 创建后端池
    def backend_pool_create(self, pool: BackendPoolCreate) -> BackendPool:
        self.db.add(pool)
        self.db.flush()
        return pool

    # 根据监听器查询
    def backend_pool_list_by_listener(self, listener_id: int):
        return self.db.query(BackendPool).filter(
            BackendPool.listener_id == listener_id
        ).all()

    # 查询单个后端池
    def backend_pool_get_by_id(self, pool_id: int) -> Optional[BackendPool]:
        return self.db.query(BackendPool).filter(
            BackendPool.id == pool_id
        ).first()

    # ==============后端成员=============
    # 批量添加后端成员（服务器 / 集群节点）
    def batch_create(
        self,
        backends: List[BackendMemberCreate]
    ):
        self.db.add_all(backends)
        self.db.flush()
        return backends

    # 查询某个后端池的成员
    def list_by_pool(self, pool_id: int):
        return self.db.query(BackendMember).filter(
            BackendMember.backend_pool_id == pool_id
        ).all()