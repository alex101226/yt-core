from pydantic import BaseModel, Field


class CreateUserAccessKeySchema(BaseModel):
    cloud_provider_code: str = Field(..., description="云厂商code")