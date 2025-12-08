# cmp
from .cmp.dict_controller import router as dict_router

from .cmp.user_certificate_controller import router as user_certificate_router
from .cmp.resource_group_controller import router as resource_group_router
from .cmp.vpc_controller import router as vpc_router
from .cmp.subnet_controller import router as subnet_router
from .cmp.security_group_controller import router as security_group_router
from .cmp.server_instance_controller import router as server_instance_router
# from .cmp.image_controller import router as image_router

from .cmp.cloud_controller import router as cloud_router
from .cmp.eip_controller import router as eip_router
from .cmp.cbs_controller import router as cbs_router
from .cmp.oss_controller import router as oss_router
from .cmp.cephfs_file_controller import router as cephfs_file_router
from .cmp.fs_mount_controller import router as fs_mount_router

# sso
from .sso.auth_controller import router as auth_router
from .sso.user_controller import router as user_router