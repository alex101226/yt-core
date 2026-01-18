# app/controllers/cmp/server_instance_controller.py
from fastapi import APIRouter, Depends, Request, Query
from typing import Optional, List
from enum import Enum
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.schemas.cmp.server_instance_schema import InstanceCreateSchema, InstanceActionSchema, InstanceUpdatePassword
from app.services.cmp.cloud_server_service import InstanceService
from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

def get_server_instance_service(
   db: Session = Depends(get_cmp_db),
):
    return InstanceService(db)

router = APIRouter(prefix="/cloud_server", tags=["云服务器"], dependencies=[Depends(require_user)])

# 创建服务器
@router.post("/server_create")
def create_instance(
    data: InstanceCreateSchema,
    request: Request,
    service: InstanceService = Depends(get_server_instance_service)):
    user = request.state.user

    instance = service.create_instance(user, data)
    return Response.success(instance)

# 分页列表
@router.get("/server_page_list")
def get_server_page_list(
    request: Request,
    provider_code: Optional[str] = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    zone_id: Optional[str] = Query(None, description="可用区id"),
    resource_group_id: Optional[str] = Query(None, description="资源组id"),
    instance_id: Optional[str] =  Query(None, description="服务器实例id"),
    instance_name: Optional[str] =  Query(None, description="服务器实例名称"),
    instance_type: Optional[str] =  Query(None, description="实例规格"),
    ip: Optional[str] =  Query(None, description="ip"),
    status: Optional[int] = Query(None, description="服务器状态"),
    ssh_proxy_port: Optional[int] = Query(None, description="ssh 代理端口"),
    page: int = Query(..., description="分页"),
    page_size:int = Query(..., description="页码"),
    service: InstanceService = Depends(get_server_instance_service),
):
    user_id = request.state.user.get('user_id')
    result = service.server_list_page(
        user_id, provider_code, region_id, zone_id, resource_group_id, instance_id, instance_name,
        instance_type, ip, status, ssh_proxy_port, page, page_size
    )
    return Response.success(result)
# 实例状态：1初始化 2运行中 3创建准备 4创建中 5创建失败 6准备关机 7关机中 8已关机 9关机失败 10准备开机
# 11 开机中 12开机失败 13准备重启 14重启中 15重启失败 16准备释放 17释放中 18已释放 19释放失败 20云端不存在
# 21网络配置失败 22代理配置失败 23部署中 24部署失败 25创建镜像中 26更换镜像中 27更换镜像失败
#  28云盘扩容中 29欠费限制 30异常

class ServerInstanceStatus(str, Enum):
    PREPARE_START = "PREPARE_START" # 开机
    PREPARE_STOP = "PREPARE_STOP"   # 关机
    PREPARE_REBOOT = "PREPARE_REBOOT"   # 重启
    IMAGE_CREATING="IMAGE_CREATING" # 创建镜像
    IMAGE_REPLACING="IMAGE_REPLACING"   # 更换镜像
    PREPARE_RELEASE="PREPARE_RELEASE"   # 释放
# 开机，关机，重启
@router.post("/action")
def start_instance(
    data: InstanceActionSchema,
    service: InstanceService = Depends(get_server_instance_service)
):
    result = service.start_instance(data)
    return Response.success(result)

@router.post('/save_server_password')
def save_server_password(
    data: InstanceUpdatePassword,
    service: InstanceService = Depends(get_server_instance_service)
):
    result = service.save_server_password(data)
    return Response.success(result)

@router.post('/toggle_release')
def toggle_release(
    request: Request,
    instance_id: int,
    service: InstanceService = Depends(get_server_instance_service)
):
    user_id = request.state.user.get("user_id")
    result = service.toggle_server_release(instance_id, user_id)
    return Response.success(result)

# 服务器释放
@router.put('/server_release')
def server_release(
    instance_id: int,
    service: InstanceService = Depends(get_server_instance_service)
):
    result = service.server_release(instance_id)
    return Response.success(result)

# 克隆
@router.put('/server_clone')
def server_release(
    instance_id: int,
    service: InstanceService = Depends(get_server_instance_service)
):
    result = service.server_clone(instance_id)
    return Response.success(result)


