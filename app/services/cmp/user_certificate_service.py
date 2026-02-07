from sqlalchemy.orm import Session

from app.repositories.cmp.user_certificate_repo import UserCertificateRepository

from app.schemas.cmp.user_certificate_schema import UserCertificateList, UserCertificatePage, UserCertificateOut
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.core.logger import logger
from app.services.cmp.operation_helper import execute_with_notification


class UserCertificateService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserCertificateRepository(db)

    def create_certificate(self, user: dict, data: dict):
        def _do():
            user_id = user["user_id"]
            count = self.repo.count_by_user(user_id)

            # 如果是第一条，自动设为默认
            if count == 0:
                data["is_default"] = 1
            else:
                data["is_default"] = 0

            # cloud_code 唯一校验
            if self.repo.get_by_code(user_id, data['cloud_code']):
                raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message=Message.DATA_DUPLICATE)
            certificate = self.repo.create(data)
            return certificate

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="SYSTEM_CONFIG",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="云证书创建成功",
            failed_desc="云证书创建失败",
            func=_do
        )


    def get_certificate(self, record_id: int):
        obj = self.repo.get_by_id(record_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj

    # 下拉选择的list
    def certificate_list(self, user_id: int):
        result = self.repo.certificate_list(user_id)
        out_result = [UserCertificateList.model_validate(i) for i in result]
        return out_result

    # 分页查找
    def certificates_page_list(self, user_id: int, page: int, page_size: int):
        total, items = self.repo.list_page(user_id, page, page_size)
        return UserCertificatePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[UserCertificateOut.model_validate(i) for i in items],
        )

    def update_certificate(self, record_id: int, **kwargs):
        obj = self.repo.update(record_id, **kwargs)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj

    def delete_certificate(self, user:dict, record_id: int) -> bool:
        def _do():
            ok = self.repo.delete(record_id)
            if not ok:
                raise BusinessException(code=ErrorCode.DATABASE_ERROR, message=Message.DATABASE_ERROR)
            return ok
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="SYSTEM_CONFIG",
            action="RELEASE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="云证书删除成功",
            failed_desc="云证书删除失败",
            func=_do
        )

    # 设置默认云凭证
    def set_default_certificate(self, user_id: int, record_id: int):
        # 清除旧默认
        self.repo.clear_default(user_id)

        # 设置新默认
        obj = self.repo.set_default(record_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="凭证不存在")

        return {
            "id": obj.id,
            "is_default": obj.is_default,
            "updated_at": obj.updated_at,
            "cloud_code": obj.cloud_code,
        }

    # 返回用户的默认凭证
    def get_default_certificate(self, user_id: int):
        obj = self.repo.get_certificate_find(user_id)
        return obj

    def get_user_ak(self, user_id: int):
        obj = self.repo.get_user_ak(user_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj