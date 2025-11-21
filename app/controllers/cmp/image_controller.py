from typing import Optional

from app.clients.cloud_client_factory import CloudClientFactory
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/cloud/image", tags=["系统镜像"])

@router.get("/list")
def list_images():
    """
    测试接口：获取阿里云镜像列表
    """
    client = CloudClientFactory.create_client(
        'aliyun',
        'LTAI5tHPqqYXb7GMUXCFZCS2',
        'b4bARGw719ETqsxJODySfskRWVzAEA',
        'ecs.aliyuncs.com'
    )
    result = client.list_images('cn-qingdao')
    return {"items": result}
