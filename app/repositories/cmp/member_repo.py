from sqlalchemy.orm import Session

from app.models.cmp.member import Member


class MemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, member_id: int):
        return self.db.query(Member).filter(Member.id == member_id, Member.is_released == 0).first()

    def get_by_user_id(self, user_id: int):
        return self.db.query(Member).filter(Member.user_id == user_id, Member.is_released == 0).first()

    def get_active_by_user_id(self, user_id: int):
        return self.db.query(Member).filter(
            Member.user_id == user_id,
            Member.is_released == 0,
            Member.is_frozen == 0,
        ).first()

    def get_active_by_id(self, member_id: int):
        return self.db.query(Member).filter(
            Member.id == member_id,
            Member.is_released == 0,
            Member.is_frozen == 0,
        ).first()

    def create(self, payload: dict):
        member = Member(**payload)
        self.db.add(member)
        self.db.flush()
        return member

    def page_list(self, page: int, page_size: int, member_name: str = None, member_account: str = None, member_type: str = None):
        query = self.db.query(Member).filter(Member.is_released == 0).order_by(Member.id.desc())
        if member_name:
            query = query.filter(Member.member_name.like(f"%{member_name}%"))
        if member_account:
            query = query.filter(Member.member_account.like(f"%{member_account}%"))
        if member_type:
            query = query.filter(Member.member_type == member_type)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_all(self, only_active: bool = True):
        query = self.db.query(Member).filter(Member.is_released == 0)
        if only_active:
            query = query.filter(Member.is_frozen == 0)
        return query.order_by(Member.id.desc()).all()

    def delete(self, member: Member):
        member.is_released = True
        member.user_id = None
        member.member_account = None
        self.db.flush()
        return True

    def toggle_freeze(self, member: Member):
        member.is_frozen = not bool(member.is_frozen)
        self.db.flush()
        return member.is_frozen

    def active_member_user_ids(self):
        rows = self.db.query(Member.user_id).filter(Member.is_released == 0, Member.user_id.isnot(None)).all()
        return {r[0] for r in rows}
