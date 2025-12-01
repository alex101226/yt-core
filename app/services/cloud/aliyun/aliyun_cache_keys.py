# 阿里云区域
ALIYUN_REGION_KEY = "cloud:aliyun:regions"
ALIYUN_ZONES_KEY = "cloud:aliyun:{region_id}:zones"
ALIYUN_IMAGES_KEY = "cloud:aliyun:{region_id}:images"
ALIYUN_INSTANCE_TYPES_KEY = "cloud:aliyun:{region_id}:instance_types"
ALIYUN_PRICE_KEY = "cloud:aliyun:{region_id}:price"

# 阿里云可用区
def aliyun_zones_key(region_id: str):
    return f"cloud:aliyun:{region_id}:zones"

# 镜像
def aliyun_images_key(region_id: str):
    return f"cloud:aliyun:{region_id}:images"

# 实例规格
def aliyun_instance_types_key(region_id: str):
    return f"cloud:aliyun:{region_id}:instance_types"

# 可用实例规格
def aliyun_available_types_key(region_id: str):
    return f"cloud:aliyun:{region_id}:available_types"

# 系统盘种类
def aliyun_system_disks_key(region_id: str):
    return f"cloud:aliyun:{region_id}:system_disks"

# 服务器价格
def aliyun_cloud_price_key(region_id: str):
    return f"cloud:aliyun:{region_id}:prices"
