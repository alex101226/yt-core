# app/services/operation_helper.py
from typing import Callable, Optional


from app.core.logger import logger
from app.core.database import SessionLocal
from app.services.cmp.stat_service import StatService

from app.common.exceptions import BusinessException

from app.schemas.cmp.state_schema import AuditLogSchema

from app.constants.enums import ActionMode, ActionOperate

#   执行业务操作，并自动记录通知
def _write_audit_log(data: AuditLogSchema):
    # 使用独立 session，避免被业务事务影响
    db = SessionLocal["cmp"]()
    try:
        StatService(db).create_notification(data)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"audit log write failed: {e}")
    finally:
        db.close()


def execute_with_notification(
    *,
    db,
    user: dict,
    system: int,
    system_name: str,
    action_mode: str,
    action: str,
    source_id_fn: Optional[Callable] = None,
    source_id_on_fail: Optional[str] = None,
    success_desc: str,
    failed_desc: str,
    func: Callable,
):
    stat_service = StatService(db)
    # ✅ 从枚举里取 value（确保传入的是枚举名字符串）
    mode = ActionMode[action_mode].value
    ac = ActionOperate[action].value

    try:
        result = func()

        # 动态生成 source_id
        source_id = source_id_fn(result) if source_id_fn else None
        logger.info(f'看下 {source_id}')
        data = AuditLogSchema(
            created_by=user.get('user_id', 0),
            created_by_name=user.get('username'),
            system=system,
            system_name=system_name,
            action_mode=mode,
            action=ac,
            source_id=str(source_id),
            message=success_desc,
            status="success",
        )

        _write_audit_log(data)

        return result

    except BusinessException as e:
        # 失败时，source_id 使用传入的默认值（或者 None）
        data = AuditLogSchema(
            created_by=user.get('user_id', 0),
            created_by_name=user.get('username'),
            system=system,
            system_name=system_name,
            action_mode=mode,
            action=ac,
            source_id='',
            message=failed_desc,
            status="failed",
        )
        _write_audit_log(data)
        raise
