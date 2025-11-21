from typing import Optional

from app.clients.cloud_client_factory import CloudClientFactory
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/cloud/image", tags=["系统镜像"])

