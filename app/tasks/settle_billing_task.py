from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from nanoid import generate

from app.core.database import SessionLocal

from app.constants.enums import BillingMethod, ResourceType
from app.common.exceptions import BusinessException
from app.core.logger import logger

from app.models.cmp import BillingInstance, Account

from app.repositories.cmp.bill_repo import BillRepository
from app.services.cmp.order_service import OrderService
from app.services.cmp.account_service import AccountService

def billing_cron_job():
    with SessionLocal["cmp"]() as db:
        service = BillingCronService(db)
        service.run()


class BillingCronService:

    def __init__(self, db):
        self.db = db
        self.repo = BillRepository(db)
        self.order_service = OrderService(db)
        self.account_service = AccountService(db)

    def run(self):
        now = datetime.now(timezone.utc)

        billings = self.repo.find_due_billings(now)

        for billing in billings:
            account = self.account_service.account_exists(billing.created_by)
            try:
                if billing.billing_method == BillingMethod.PostPaid:
                    self._handle_postpaid(billing, now, account)
                else:
                    self._handle_prepaid(billing, now, account)

            except BusinessException as e:
                logger.exception(f"billing failed: {billing.id}")
                self.db.rollback()

    def _resolve_order_instance_id(self, billing: BillingInstance) -> str:
        resource = self.repo.fetch_resource(billing.resource_type, billing.resource_id)
        if not resource:
            return str(billing.resource_id)

        attr_map = {
            ResourceType.SERVER: "instance_id",
            ResourceType.BAREMETAL: "instance_id",
            ResourceType.DISK: "disk_id",
            ResourceType.EIP: "eip_id",
            ResourceType.CLUSTER: "cluster_id",
            ResourceType.GPFS: "fs_id",
            ResourceType.CEPHFS: "fs_id",
            ResourceType.LOAD_INSTANCE: "lb_id",
            ResourceType.OSS: "bucket_name",
        }
        attr_name = attr_map.get(billing.resource_type)
        resolved = getattr(resource, attr_name, None) if attr_name else None
        return str(resolved or billing.resource_id)

    # 扣费
    def _handle_postpaid(self, billing: BillingInstance, now: datetime, account: Optional[Account]):
        # 每周扣费一次
        last_billing = billing.last_billing_time or billing.billing_start_time
        # 统一成 UTC aware
        if last_billing.tzinfo is None:
            last_billing = last_billing.replace(tzinfo=timezone.utc)

        next_billing_due = last_billing + timedelta(weeks=1)
        if now < next_billing_due:
            return  # 本周期还没到

        if billing.billing_end_time and now >= billing.billing_end_time:
            billing.status = "RELEASED"
            billing.next_bill_time = None
            self.db.commit()
            logger.info(f"按量计费任务到期结束, billing_id={billing.id}")
            return

        amount = billing.unit_price * 7 * 24  # 假设按小时计费，7天*24小时

        # 创建订单 + 扣费
        self.order_service.create_and_pay_order(
            user={
                'user_id': billing.created_by,
                "username": billing.created_by_name,
            },
            account_id=account.id,
            instance_id=self._resolve_order_instance_id(billing),
            billing=billing,
            amount=amount,
            order_type="RENEW",
            cloud_provider_code=billing.cloud_provider_code,
            region_id=billing.region_id,
        )

        # 更新计费时间
        billing.last_billing_time = now
        billing.next_bill_time = now + timedelta(weeks=1)

        logger.info(f"按量付费扣费成功, billing_id={billing.id}")
        # self.db.flush()
        self.db.commit()

    # PrePaid 到期检查
    def _handle_prepaid(self, billing: BillingInstance, now: datetime,  account: Optional[Account]):
        # end_time = billing.billing_start_time + relativedelta(
        #     months=billing.billing_period_count
        # )
        # 计算本周期结束时间
        last_billing = billing.last_billing_time or billing.billing_start_time

        if last_billing.tzinfo is None:
            last_billing = last_billing.replace(tzinfo=timezone.utc)

        period_months = billing.billing_period_count or 1
        end_time = last_billing + relativedelta(months=+period_months)
        if now < end_time:
            return  # 本周期还没到

        # 如果自动续费，扣费生成新订单
        if billing.auto_renew:
            amount = billing.unit_price * period_months
            self.order_service.create_and_pay_order(
                user={
                    'user_id': billing.created_by,
                    "username": billing.created_by_name,
                },
                account_id=account.id,
                instance_id=self._resolve_order_instance_id(billing),
                billing=billing,
                amount=amount,
                order_type="RENEW",
                cloud_provider_code=billing.cloud_provider_code,
                region_id=billing.region_id,
            )

            # 更新计费时间
            billing.last_billing_time = now
            billing.next_bill_time = now + relativedelta(months=+period_months)
            billing.billing_end_time = billing.next_bill_time

            self.db.flush()

            logger.info(f"包年月任务成功, billing_id={billing.id}")
        else:
            # 未勾选自动续费，标记释放
            billing.status = "RELEASED"
            self.db.flush()
            logger.info(f"包年月任务结束, billing_id={billing.id}")
        self.db.flush()

scheduler = None

def bill_start_scheduler():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        billing_cron_job,
        trigger="interval",
        minutes=1,  # 每小时执行一次
        id="billing_cron",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("计费任务轮训已启动")


def bill_stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("计费任务轮训已停止")


if __name__ == "__main__":
    bill_start_scheduler()
    import time
    while True:
        time.sleep(60)
