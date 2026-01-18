from pydantic import BaseModel


class AuditLogSchema(BaseModel):
    operate_id: str
    operate_name: str
    system: int = 0
    system_name: str
    action_mode: str
    action: str
    source_id: str
    message: str = None
    status: str = None