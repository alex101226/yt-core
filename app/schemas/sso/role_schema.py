from pydantic import BaseModel, Field

class RoleAddSchema(BaseModel):
    role_code: str = Field(..., description="权限编号")
    role_name: str = Field(..., description="权限名称")
    description: str = Field(None, description="权限描述")