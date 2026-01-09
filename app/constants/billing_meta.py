from dataclasses import dataclass
from app.constants.enums import ResourceType, BillingMethod

@dataclass
class BillingMeta:
    product_name: str
    business_name: str

# 名称转换
BILLING_META_MAP = {
    ResourceType.SERVER: BillingMeta(
        product_name="云服务器",
        business_name="云服务器计算资源",
    ),
    ResourceType.DISK: BillingMeta(
        product_name="云硬盘",
        business_name="云硬盘存储资源",
    ),
    ResourceType.EIP: BillingMeta(
        product_name="弹性公网IP",
        business_name="公网带宽服务",
    ),
    ResourceType.BAREMETAL: BillingMeta(
        product_name="裸金属服务器",
        business_name="裸金属计算资源",
    ),
    ResourceType.CLUSTER: BillingMeta(
        product_name="集群",
        business_name="集群资源",
    ),
    ResourceType.CUSTOM_IMAGE: BillingMeta(
        product_name="自定义镜像",
        business_name="自定义镜像资源",
    ),
    ResourceType.LOAD_INSTANCE: BillingMeta(
        product_name="负载均衡",
        business_name="负载均衡",
    ),
    ResourceType.GPFS: BillingMeta(
        product_name="GPFS文件存储",
        business_name="GPFS文件存储资源",
    ),
    ResourceType.CEPHFS: BillingMeta(
        product_name="CEPHFS文件存储",
        business_name="CEPHFS文件存储资源",
    ),
    ResourceType.OSS: BillingMeta(
        product_name="OSS对象存储",
        business_name="OSS对象存储资源",
    ),
    ResourceType.CONTAINER_IMAGE: BillingMeta(
        product_name="容器镜像",
        business_name="容器镜像资源",
    ),
}


@dataclass
class BillingMethodMeta:
    consume_type: str
    unit: str
    text: str

# 计费方式和周期转换
BILLING_METHOD_META = {
    BillingMethod.PostPaid: BillingMethodMeta(
        consume_type= "VOLUME_BASED",
        unit = "HOUR",
        text = "按量付费"
    ),
    BillingMethod.PrePaid: BillingMethodMeta(
        consume_type = "PACKAGE_MONTHLY",
        unit = "MONTH",
        text="包年包月"
    )
}
