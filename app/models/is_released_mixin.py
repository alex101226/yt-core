from datetime import datetime, timezone
from sqlalchemy import (
    Column, DateTime, Boolean, Integer, String
)


class IsReleasedMixin:
    is_released = Column(Boolean, default=False, nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True, comment="创建人id")
    created_by_name=Column(String(60), nullable=True, comment="创建人信息")

    @classmethod
    def __declare_last__(cls):
        from sqlalchemy import event
        @event.listens_for(cls, "before_update")
        def _auto_released_at(mapper, connection, target):
            if target.is_released and target.released_at is None:
                target.released_at = datetime.now(timezone.utc)



class SSOReleasedMixin:
    is_released = Column(Boolean, default=False, nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)

    @classmethod
    def __declare_last__(cls):
        from sqlalchemy import event
        @event.listens_for(cls, "before_update")
        def _auto_released_at(mapper, connection, target):
            if target.is_released and target.released_at is None:
                target.released_at = datetime.now(timezone.utc)
