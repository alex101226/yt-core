# cmp
from .cmp.dict_controller import router as dict_router

from .cmp.user_access_key_controller import router as user_access_key_router
from .cmp.user_certificate_controller import router as user_certificate_router
from .cmp.resource_group_controller import router as resource_group_router
from .cmp.cloud_vendor_controller import router as cloud_vendor_router
from .cmp.vpc_controller import router as vpc_router
from .cmp.subnet_controller import router as subnet_router
from .cmp.security_group_controller import router as security_group_router
from .cmp.cloud_server_instance_controller import router as server_instance_router
from .cmp.bare_metal_instance_controller import router as bare_metal_instance_router
from .cmp.cloud_image_controller import router as cloud_image_router

from .cmp.cloud_controller import router as cloud_router
from .cmp.eip_controller import router as eip_router
from .cmp.cbs_controller import router as cbs_router
from .cmp.oss_controller import router as oss_router
from .cmp.gpfs_controller import router as gpfs_router
from .cmp.cephfs_file_controller import router as cephfs_file_router
from .cmp.fs_mount_controller import router as fs_mount_router

from .cmp.container_image_controller import router as container_image_router
from .cmp.cluster_controller import router as cluster_router
from .cmp.account_controller import router as account_router
from .cmp.bill_controller import router as bill_router
from .cmp.invoice_email_controller import router as invoice_email_router
from .cmp.invoice_controller import router as invoice_router
from .cmp.invoice_item_controller import router as invoice_item_router

from .cmp.stat_controller import router as stat_router

from .cmp.load_controller import router as load_router

# sso
from .sso.auth_controller import router as auth_router
from .sso.user_controller import router as user_router
from .sso.role_controller import router as role_router

# hub
from .hub.categoire_controller import router as categoire_router


__routes__ = [
'dict_router', 'user_access_key_router', 'user_certificate_router', 'resource_group_router',
'cloud_vendor_router', 'vpc_router', 'subnet_router', 'security_group_router', 'server_instance_router',
'bare_metal_instance_router', 'cloud_image_router', 'cloud_router', 'eip_router', 'cbs_router',
'oss_router', 'gpfs_router', 'cephfs_file_router', 'fs_mount_router', 'container_image_router',
'cluster_router', 'account_router', 'bill_router', 'invoice_email_router', 'invoice_router',
'invoice_item_router', 'stat_router', 'load_router', 'auth_router', 'user_router', 'role_router',
'categoire_router'
]