from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class EIPSchema(BaseModel):
    resource_group_id: Optional[int]
    cloud_provider_code: str
    region_id: str
    zone_id: str
    description: Optional[str]
    eip_id: str
    internet_charge_type: str
    bandwidth: int
    price: float


class EIPCreate(EIPSchema):
    # public_ip: Optional[str]
    pass

class EIPOut(BaseModel):
    pass