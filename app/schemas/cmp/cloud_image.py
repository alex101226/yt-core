from typing import Optional

from pydantic import BaseModel


class CloudImageCreate(BaseModel):
    image_name: str
    os_type: str
    os_name: str
    cloud_provider_code: str
    region_id: str
    architecture: str
    boot_mode: str
    size: int
    description: Optional[str] = None
    charge_type: Optional[str] = "PostPaid"
    resource_group_id: int = 0
    price: Optional[float] = None