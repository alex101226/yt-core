from typing import List, Optional
from pydantic import BaseModel, Field

# 单条规则（创建）
class SecurityGroupRuleItem(BaseModel):
    direction: str = Field(..., description="方向：inbound / outbound")
    policy_code: str
    protocol_code: str
    port_range: str
    source: str
    description: Optional[str] = None


# 批量规则更新（入 + 出）
class SecurityGroupRuleUpdate(BaseModel):
    security_group_id: str = Field(..., description="所属安全组ID")
    ingress_rules: List[SecurityGroupRuleItem] = Field(default_factory=list)
    egress_rules: List[SecurityGroupRuleItem] = Field(default_factory=list)


# 输出模型
class SecurityGroupRuleOut(BaseModel):
    id: str
    security_group_id: str
    direction: str
    policy_code: str
    protocol_code: str
    port_range: str
    source: str
    description: Optional[str]
    cloud_rule_id: Optional[str]
    sync_status: int

    class Config:
        from_attributes = True
