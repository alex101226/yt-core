from datetime import datetime
from pydantic import BaseModel

class CloudRegionBase(BaseModel):
    provider_code: str
    region_id: str
    region_name: str


class CloudRegionOut(CloudRegionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
