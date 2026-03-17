from datetime import datetime
from datetime import timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.cmp.credit_flow import CreditFlow
from app.models.cmp.credit_grant import CreditGrant
from app.models.cmp.member import Member


class CreditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_grant(self, payload: dict) -> CreditGrant:
        obj = CreditGrant(**payload)
        self.db.add(obj)
        self.db.flush()
        return obj

    def create_flow(self, payload: dict) -> CreditFlow:
        obj = CreditFlow(**payload)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_grant(self, grant_id: int) -> Optional[CreditGrant]:
        return self.db.query(CreditGrant).filter(
            CreditGrant.id == grant_id,
            CreditGrant.is_released == 0,
        ).first()

    def expire_grants(self, member_id: int, now: datetime) -> int:
        result = self.db.query(CreditGrant).filter(
            CreditGrant.member_id == member_id,
            CreditGrant.status == "ACTIVE",
            CreditGrant.approve_status == "APPROVED",
            CreditGrant.valid_end < now,
            CreditGrant.is_released == 0,
        ).update({CreditGrant.status: "EXPIRED"}, synchronize_session=False)
        return result or 0

    def active_grants_for_member(
        self,
        member_id: int,
        cloud_provider_code: Optional[str],
        now: datetime,
    ) -> List[CreditGrant]:
        filters = [
            CreditGrant.member_id == member_id,
            CreditGrant.status == "ACTIVE",
            CreditGrant.approve_status == "APPROVED",
            CreditGrant.remaining_amount > 0,
            CreditGrant.valid_start <= now,
            CreditGrant.valid_end >= now,
            CreditGrant.is_released == 0,
        ]
        if cloud_provider_code:
            filters.append(CreditGrant.cloud_provider_code == cloud_provider_code)
        return self.db.query(CreditGrant).filter(*filters).order_by(CreditGrant.valid_end.asc()).all()

    def balance_by_cloud_provider(self, member_id: int, now: datetime):
        return (
            self.db.query(
                CreditGrant.cloud_provider_code,
                func.sum(CreditGrant.amount).label("total_amount"),
                func.sum(
                    func.if_(CreditGrant.approve_status == "APPROVED", CreditGrant.amount, 0)
                ).label("distributed_amount"),
                func.sum(
                    func.if_(
                        (CreditGrant.approve_status == "APPROVED") & (CreditGrant.status == "EXPIRED"),
                        CreditGrant.remaining_amount,
                        0,
                    )
                ).label("expired_amount"),
                func.sum(
                    func.if_(
                        (CreditGrant.approve_status == "APPROVED")
                        & (CreditGrant.status == "ACTIVE")
                        & (CreditGrant.valid_start <= now)
                        & (CreditGrant.valid_end >= now),
                        CreditGrant.remaining_amount,
                        0,
                    )
                ).label("remaining_amount"),
            )
            .filter(
                CreditGrant.member_id == member_id,
                CreditGrant.is_released == 0,
            )
            .group_by(CreditGrant.cloud_provider_code)
            .all()
        )

    def grant_page_list(
        self,
        page: int,
        page_size: int,
        member_id: Optional[int] = None,
        cloud_provider_code: Optional[str] = None,
        status: Optional[str] = None,
        approve_status: Optional[str] = None,
    ) -> Tuple[list, int]:
        query = (
            self.db.query(
                CreditGrant.id,
                CreditGrant.member_id,
                Member.member_name,
                Member.member_account,
                CreditGrant.amount,
                CreditGrant.remaining_amount,
                CreditGrant.cloud_provider_code,
                CreditGrant.valid_start,
                CreditGrant.valid_end,
                CreditGrant.status,
                CreditGrant.source_type,
                CreditGrant.approve_status,
                CreditGrant.approved_by,
                CreditGrant.approved_by_name,
                CreditGrant.approved_at,
                CreditGrant.reject_reason,
                CreditGrant.description,
                CreditGrant.created_at,
                CreditGrant.updated_at,
            )
            .join(Member, Member.id == CreditGrant.member_id)
            .filter(CreditGrant.is_released == 0)
            .order_by(CreditGrant.id.desc())
        )
        if member_id:
            query = query.filter(CreditGrant.member_id == member_id)
        if cloud_provider_code:
            query = query.filter(CreditGrant.cloud_provider_code == cloud_provider_code)
        if status:
            query = query.filter(CreditGrant.status == status)
        if approve_status:
            query = query.filter(CreditGrant.approve_status == approve_status)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def flow_page_list(
        self,
        page: int,
        page_size: int,
        member_id: Optional[int] = None,
    ) -> Tuple[list, int]:
        query = (
            self.db.query(
                CreditFlow.id,
                CreditFlow.grant_id,
                CreditFlow.member_id,
                Member.member_name,
                Member.member_account,
                CreditFlow.amount,
                CreditFlow.direction,
                CreditFlow.flow_type,
                CreditFlow.cloud_provider_code,
                CreditFlow.ref_type,
                CreditFlow.ref_id,
                CreditFlow.description,
                CreditFlow.created_by,
                CreditFlow.created_by_name,
                CreditFlow.created_at,
            )
            .join(Member, Member.id == CreditFlow.member_id)
            .filter(CreditFlow.is_released == 0)
            .order_by(CreditFlow.id.desc())
        )
        if member_id:
            query = query.filter(CreditFlow.member_id == member_id)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def overview_summary(self, now: datetime, member_id: int = None):
        today_start = datetime(now.year, now.month, now.day)
        query = self.db.query(
            func.sum(case(
                (
                    (CreditGrant.approve_status == "APPROVED")
                    & (CreditGrant.status == "ACTIVE")
                    & (CreditGrant.valid_start <= now)
                    & (CreditGrant.valid_end >= now)
                    & (CreditGrant.is_released == 0),
                    CreditGrant.remaining_amount,
                ),
                else_=0,
            )).label("remaining_distributable_amount"),
            func.sum(case(
                (CreditGrant.is_released == 0, CreditGrant.amount),
                else_=0,
            )).label("total_amount"),
            func.sum(case(
                (
                    (CreditGrant.approve_status == "APPROVED")
                    & (CreditGrant.status == "EXPIRED")
                    & (CreditGrant.is_released == 0),
                    CreditGrant.remaining_amount,
                ),
                else_=0,
            )).label("expired_amount"),
            func.sum(case(
                (
                    (CreditGrant.approve_status == "APPROVED")
                    & (CreditGrant.is_released == 0),
                    CreditGrant.amount,
                ),
                else_=0,
            )).label("distributed_amount"),
            func.sum(case(
                (
                    (CreditGrant.approve_status == "APPROVED")
                    & (CreditGrant.approved_at >= today_start)
                    & (CreditGrant.approved_at <= now)
                    & (CreditGrant.is_released == 0),
                    CreditGrant.amount,
                ),
                else_=0,
            )).label("today_distributed_amount"),
        )
        if member_id:
            query = query.filter(CreditGrant.member_id == member_id)
        return query.one()

    def overview_cards(self, now: datetime, member_id: int = None):
        today_start = datetime(now.year, now.month, now.day)
        today_flow_query = self.db.query(CreditFlow).filter(
            CreditFlow.is_released == 0,
            CreditFlow.flow_type == "CONSUME",
            CreditFlow.direction == "OUT",
            CreditFlow.created_at >= today_start,
            CreditFlow.created_at <= now,
        )
        total_flow_query = self.db.query(CreditFlow).filter(
            CreditFlow.is_released == 0,
            CreditFlow.flow_type == "CONSUME",
            CreditFlow.direction == "OUT",
        )
        if member_id:
            today_flow_query = today_flow_query.filter(CreditFlow.member_id == member_id)
            total_flow_query = total_flow_query.filter(CreditFlow.member_id == member_id)

        distributed_today_query = self.db.query(
            func.count(func.distinct(CreditGrant.member_id))
        ).filter(
            CreditGrant.is_released == 0,
            CreditGrant.approve_status == "APPROVED",
            CreditGrant.approved_at >= today_start,
            CreditGrant.approved_at <= now,
        )
        distributed_total_query = self.db.query(
            func.count(func.distinct(CreditGrant.member_id))
        ).filter(
            CreditGrant.is_released == 0,
            CreditGrant.approve_status == "APPROVED",
        )
        if member_id:
            distributed_today_query = distributed_today_query.filter(CreditGrant.member_id == member_id)
            distributed_total_query = distributed_total_query.filter(CreditGrant.member_id == member_id)

        return {
            "today_new_order_count": today_flow_query.with_entities(
                func.count(func.distinct(CreditFlow.ref_id))
            ).scalar() or 0,
            "today_consume_amount": today_flow_query.with_entities(
                func.sum(CreditFlow.amount)
            ).scalar() or 0,
            "today_distributed_member_count": distributed_today_query.scalar() or 0,
            "today_consume_member_count": today_flow_query.with_entities(
                func.count(func.distinct(CreditFlow.member_id))
            ).scalar() or 0,
            "total_order_count": total_flow_query.with_entities(
                func.count(func.distinct(CreditFlow.ref_id))
            ).scalar() or 0,
            "total_consume_amount": total_flow_query.with_entities(
                func.sum(CreditFlow.amount)
            ).scalar() or 0,
            "total_distributed_member_count": distributed_total_query.scalar() or 0,
            "total_consume_member_count": total_flow_query.with_entities(
                func.count(func.distinct(CreditFlow.member_id))
            ).scalar() or 0,
        }

    def recent_order_trend(self, now: datetime, days: int = 7, member_id: int = None):
        start = datetime(now.year, now.month, now.day) - timedelta(days=days - 1)
        query = self.db.query(
            func.date_format(CreditFlow.created_at, "%m-%d").label("day"),
            func.count(func.distinct(CreditFlow.ref_id)).label("value"),
        ).filter(
            CreditFlow.is_released == 0,
            CreditFlow.flow_type == "CONSUME",
            CreditFlow.direction == "OUT",
            CreditFlow.created_at >= start,
            CreditFlow.created_at <= now,
        )
        if member_id:
            query = query.filter(CreditFlow.member_id == member_id)
        rows = query.group_by("day").all()
        return {row.day: int(row.value or 0) for row in rows}, start

    def recent_consume_amount_trend(self, now: datetime, days: int = 7, member_id: int = None):
        start = datetime(now.year, now.month, now.day) - timedelta(days=days - 1)
        query = self.db.query(
            func.date_format(CreditFlow.created_at, "%m-%d").label("day"),
            func.sum(CreditFlow.amount).label("value"),
        ).filter(
            CreditFlow.is_released == 0,
            CreditFlow.flow_type == "CONSUME",
            CreditFlow.direction == "OUT",
            CreditFlow.created_at >= start,
            CreditFlow.created_at <= now,
        )
        if member_id:
            query = query.filter(CreditFlow.member_id == member_id)
        rows = query.group_by("day").all()
        return {row.day: float(row.value or 0) for row in rows}, start

    def today_order_top10_members(self, now: datetime, member_id: int = None):
        today_start = datetime(now.year, now.month, now.day)
        query = self.db.query(
            CreditFlow.member_id,
            Member.member_name,
            func.count(func.distinct(CreditFlow.ref_id)).label("value"),
        ).join(
            Member, Member.id == CreditFlow.member_id
        ).filter(
            CreditFlow.is_released == 0,
            CreditFlow.flow_type == "CONSUME",
            CreditFlow.direction == "OUT",
            CreditFlow.created_at >= today_start,
            CreditFlow.created_at <= now,
        )
        if member_id:
            query = query.filter(CreditFlow.member_id == member_id)
        return query.group_by(
            CreditFlow.member_id,
            Member.member_name,
        ).order_by(
            func.count(func.distinct(CreditFlow.ref_id)).desc()
        ).limit(10).all()

    def today_amount_top10_members(self, now: datetime, member_id: int = None):
        today_start = datetime(now.year, now.month, now.day)
        query = self.db.query(
            CreditFlow.member_id,
            Member.member_name,
            func.sum(CreditFlow.amount).label("value"),
        ).join(
            Member, Member.id == CreditFlow.member_id
        ).filter(
            CreditFlow.is_released == 0,
            CreditFlow.flow_type == "CONSUME",
            CreditFlow.direction == "OUT",
            CreditFlow.created_at >= today_start,
            CreditFlow.created_at <= now,
        )
        if member_id:
            query = query.filter(CreditFlow.member_id == member_id)
        return query.group_by(
            CreditFlow.member_id,
            Member.member_name,
        ).order_by(
            func.sum(CreditFlow.amount).desc()
        ).limit(10).all()
