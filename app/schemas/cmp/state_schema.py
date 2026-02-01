from pydantic import BaseModel


class AuditLogSchema(BaseModel):
    created_by: int= 0
    created_by_name: str
    system: int = 0
    system_name: str
    action_mode: str
    action: str
    source_id: str
    message: str = None
    status: str = None