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
