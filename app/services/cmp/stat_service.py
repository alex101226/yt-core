# app/services/stat_service.py
from datetime import datetime, timezone, timedelta, date
from typing import Dict, List

from sqlalchemy.orm import Session

from app.repositories.cmp.stat_repo import StatRepository

from app.schemas.cmp.state_schema import AuditLogSchema


def trans_date(date_str: str) -> datetime:
    try:
        # 先尝试完整日期
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # 再尝试只年月
        date_obj = datetime.strptime(date_str, "%Y-%m")

    return date_obj

class StatService:

    def __init__(self, db: Session):
        self.repo = StatRepository(db)

    # 首页，资源信息统计
    def get_user_statistics(self, user_id: int) -> dict:
        return {
            "servers": self.repo.count_servers(user_id),
            "vpcs": self.repo.count_vpcs(user_id),
            "subnets": self.repo.count_subnets(user_id),
            "security_groups": self.repo.count_security_groups(user_id),
            "disks": self.repo.count_disks(user_id),
            "cephfs": self.repo.count_cephfs(user_id),
            "gpfs": self.repo.count_gpfs(user_id),
            "clusters": self.repo.count_clusters(user_id),
            "container_images": self.repo.count_container_images(user_id),
        }

    # 用户资金支出
    def get_monthly_stats(self, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        billing_period = f"{year}-{month:02d}"

        return {
            "spent_amount": self.repo.sum_monthly_spent(user_id, year, month),
            "invoice_amount": self.repo.sum_monthly_invoice_amount(user_id, billing_period),
            "credit_amount": self.repo.sum_monthly_credit(user_id, year, month),
            "voucher_amount": self.repo.sum_monthly_voucher(user_id, year, month)
        }

    #   当月总览
    def get_monthly_total(self, user_id: int):
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        return {
            "spent_amount": self.repo.sum_monthly_spent(user_id, year, month),
            "income_amount": self.repo.sum_monthly_income(user_id, year, month),
            "credit_amount": 0.00,
            "voucher_amount": 0.00
        }

    # 费用总览，按月查可用额度，月新增订单数，消费金额，退款金额，已开票金额，可开票金额
    def get_month_picker_total(self, user_id: int, date_str: str):
        time = trans_date(date_str)

        billing_period = f"{time.year}-{time.month:02d}"
        return {
            "balance": self.repo.get_available_quota(user_id),
            "order_count": self.repo.count_monthly_orders(user_id, time.year, time.month),
            "consumed_amount": self.repo.sum_monthly_spent(user_id, time.year, time.month),
            "refund_amount": 0.00,
            "invoice_amount": self.repo.sum_monthly_invoice_amount(user_id, billing_period),
            "invoiced_amount": self.repo.sum_monthly_invoiced_amount(user_id, billing_period),
        }

    # 账户概览，总揽
    def get_total_funds(self, user_id: int):
        return {
            "balance": self.repo.get_available_quota(user_id),
            "invoice_amount": self.repo.sum_monthly_invoice_amount(user_id),
            "invoiced_amount": self.repo.sum_monthly_invoiced_amount(user_id),
        }

    """
      获取过去12个月的财务统计（收入、支出、已开票、可开票）
      返回格式：
      [
          {
              "year": 2025,
              "month": 2,
              "income": 1000.0,
              "spent": 800.0,
              "invoiced": 300.0,
              "invoice_available": 200.0
          },
      ]
    """
    def get_yearly_financial_chart(self, user_id: int) -> List[Dict]:

        today = date.today()
        chart_data = []

        for i in range(12):
            # 计算每个月的年份和月份
            first_day_of_month = (today.replace(day=1) - timedelta(days=i * 30))
            year = first_day_of_month.year
            month = first_day_of_month.month
            billing_period = f"{year}-{month:02d}"

            # 调用 repo 方法
            income = self.repo.sum_monthly_income(user_id, year, month)
            spent = self.repo.sum_monthly_spent(user_id, year, month)
            invoiced = self.repo.sum_monthly_invoiced_amount(user_id, billing_period)
            invoice_available = self.repo.sum_monthly_invoice_amount(user_id, billing_period)

            chart_data.append({
                "year": year,
                "month": month,
                "income": income,
                "spent": spent,
                "invoiced": invoiced,
                "invoice_available": invoice_available
            })

        # 按时间从远到近排序（可选）
        chart_data.sort(key=lambda x: (x["year"], x["month"]))
        return chart_data

    # 查询成本，云厂商，产品，商品
    def get_monthly_top5_stats(self, user_id: int, date_str: str):
        time = trans_date(date_str)
        year, month = time.year, time.month
        return {
            "cloud_provider": self.repo.top5_by_field(user_id, year, month, "cloud_provider_code"),
            "product": self.repo.top5_by_field(user_id, year, month, "product_name"),
            "business": self.repo.top5_by_field(user_id, year, month, "business_name"),
        }

    # 创建一条系统通知（操作日志）
    def create_notification(self, data: AuditLogSchema):
        return self.repo.create_notification(**data.model_dump())

    # 获取通知列表
    def get_notifications_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        return self.repo.list_notifications(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )

    # 获取未读通知数量
    def get_unread_notification_count(self, user_id: int) -> int:
        return self.repo.count_unread_notifications(user_id)

    # 标记单条通知已读
    def mark_notification_read(self, user_id: int, log_id: int) -> bool:
        return self.repo.mark_notification_read(
            user_id=user_id,
            log_id=log_id
        )

    # 全部标记已读
    def mark_all_notifications_read(self, user_id: int) -> int:
        return self.repo.mark_all_notifications_read(user_id=user_id)