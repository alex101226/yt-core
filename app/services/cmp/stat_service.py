# app/services/stat_service.py
import random
from datetime import datetime, timezone, timedelta, date
from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.logger import logger
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

    #   纳管机器统计
    def cps_state_server_count(self, user_id: int):
        bare = self.repo.stat_baremetal_status(user_id)
        server = self.repo.state_server_status(user_id)
        return {
            'bare_run': bare.running or 0,
            'bare_stop': bare.stopped or 0,
            'bare_error': bare.error or 0,
            "running": (bare.running or 0) + (server.running or 0),
            "stopped": (bare.stopped or 0) + (server.stopped or 0),
            "error": (bare.error or 0) + (server.error or 0),
            "total_compute": self.repo.total_compute(user_id),
            "current_compute": self.repo.total_compute(user_id, True),
            "current_gpu": self.repo.total_gpu_amount(user_id, True),
            "total_gpu": self.repo.total_gpu_amount(user_id, False),
            "current_cpu": self.repo.total_cpu(user_id, True),
            "total_cpu": self.repo.total_cpu(user_id),
            "current_memory": self.repo.total_memory(user_id, True),
            "total_memory": self.repo.total_memory(user_id),
            "current_storage": self.repo.total_storage(user_id, True),
            "total_storage": self.repo.total_storage(user_id, False),
        }

    def fake_gpu_rate_series(
        self,
        base_rate,
        points: int,
        step_minutes: int,
        max_fluctuation: int,
        time_format: str
    ):
        base_rate = float(base_rate)  # ⭐ 关键一行

        now = datetime.now()
        result = []

        for i in range(points):
            time_point = now - timedelta(minutes=step_minutes * (points - i - 1))

            # fluctuation 随机波动
            fluctuation = random.uniform(-max_fluctuation, max_fluctuation)
            rate = max(0.0, min(100.0, base_rate + fluctuation))

            result.append({
                "x": time_point.strftime(time_format),
                "rate": round(rate, 2)
            })

        return result

    def gpu_rate_trend(self, user_id: int, range_type: str):
        """
        range_type: '1h' | '24h'
        """
        base_rates = self.repo.current_gpu_rate_by_provider(user_id)

        data = {}
        now = datetime.now()
        step_minutes = 5  # 统一 5 分钟间隔

        # 计算总点数
        if range_type == '1h':
            points = 60 // step_minutes  # 1 小时 = 12 点
            time_format = "%H:%M"
        else:  # 24 小时
            points = 24 * 60 // step_minutes  # 24 小时 = 288 点
            time_format = "%m-%d %H:%M"

        # 遍历所有云厂商
        for provider, base_rate in base_rates.items():
            series = []
            for i in range(points):
                time_point = now - timedelta(minutes=step_minutes * (points - i - 1))
                fluctuation = random.uniform(-5, 5) * (i + 1) / points
                rate = max(0.0, min(100.0, float(base_rate) + fluctuation))
                series.append({
                    "x": time_point,  # 返回 datetime
                    "rate": round(rate, 2)
                })
            data[provider] = series

        # 保证没有云厂商时，也生成 0 数据
        if not data:
            series = []
            for i in range(points):
                time_point = now - timedelta(minutes=step_minutes * (points - i - 1))
                series.append({
                    "x": time_point,
                    "rate": 0
                })
            data["aliyun"] = series

        return data

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