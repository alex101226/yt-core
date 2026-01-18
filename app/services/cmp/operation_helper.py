# app/services/operation_helper.py
from typing import Callable, Optional

from app.core.logger import logger
from app.services.cmp.stat_service import StatService

from app.common.exceptions import BusinessException

from app.schemas.cmp.state_schema import AuditLogSchema

from app.constants.enums import ActionMode, ActionOperate

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
    """
    执行业务操作，并自动记录通知
    """
    stat_service = StatService(db)
    # ✅ 从枚举里取 value（确保传入的是枚举名字符串）
    mode = ActionMode[action_mode].value
    ac = ActionOperate[action].value

    try:
        result = func()

        # 动态生成 source_id
        source_id = source_id_fn(result) if source_id_fn else None

        data = AuditLogSchema(
            operate_id=str(user.get('user_id', '')),
            operate_name=user['username'],
            system=system,
            system_name=system_name,
            action_mode=mode,
            action=ac,
            source_id=str(source_id),
            message=success_desc,
            status="success",
        )

        stat_service.create_notification(data)

        return result

    except BusinessException as e:
        # 失败时，source_id 使用传入的默认值（或者 None）
        source_id = source_id_on_fail
        data = AuditLogSchema(
            operate_id=str(user.get('user_id', '')),
            operate_name=user['username'],
            system=system,
            system_name=system_name,
            action_mode=mode,
            action=ac,
            source_id=source_id,
            message=failed_desc,
            status="failed",
        )
        stat_service.create_notification(data)
        raise
