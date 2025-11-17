# app/controllers/__init__.py
from .public import cloud_certificate_controller
# 统一导入所有子控制器
from .public.cloud_provider_controller import router as cloud_provider_router
from .public.cloud_region_controller import router as cloud_region_router
from .public.cloud_zone_controller import router as cloud_zone_router
from .public.cloud_certificate_controller import router as cloud_certificate_router
from .public.resource_group_controller import router as resource_group_router
from .public.resource_group_binding_controller import router as resource_group_binding_router

from .cmp.vpc_controller import router as vpc_router