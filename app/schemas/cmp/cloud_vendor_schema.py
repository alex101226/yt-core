from typing import Optional

from pydantic import BaseModel


class CloudVendorSchema(BaseModel):
    cloud_code: str
    cloud_name: str
    description: Optional[str] = None


class CloudVendorCreateSchema(CloudVendorSchema):
    pass

class CloudVendorUpdateSchema(BaseModel):
    cloud_vendor_id: int
    cloud_name: str
    description: Optional[str] = None