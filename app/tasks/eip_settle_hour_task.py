from decimal import Decimal

from fastapi import Depends
from nanoid import generate
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.core.logger import logger

from app.services.cmp.account_service import AccountService
from app.services.cmp.eip_service import EIPService


def eip_settle_hour_task():
    logger.info("eip订单扣费业务启动")

    # 1. 创建一个 db session
    db = next(get_cmp_db())  # 或者你自己的 Session 管理方式
    # 2. 初始化 service
    eip_service = EIPService(db)

    # 查询所有按量计费的EIP
    eip_list = eip_service.list_all_volume_based_eip()

    now = datetime.now(timezone.utc)
    start_at = now - timedelta(hours=1)
    end_at = now

    for eip in eip_list:
        try:
            eip_service.settle_eip_hourly(
                eip_id=eip.id,
                start_at=start_at,
                end_at=end_at
            )

            logger.info("扣款成功")
        except Exception as e:
            # 记录日志
            print(f"EIP扣费失败 {eip.id}: {e}")

    db.close()  # 别忘了关闭 session
