from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.repositories.cmp.cloud_vendor_repo import CloudVendorRepo

class CloudVendorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CloudVendorRepo(db)

    def get_vendor_by_code(self, cloud_code: str):
        vendor = self.repo.get_by_code(cloud_code)
        if not vendor:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="云厂商不存在")
        return vendor

    def ensure_third_party_vendor(self, cloud_code: str):
        vendor = self.get_vendor_by_code(cloud_code)
        if not vendor.is_third_party:
            raise BusinessException(code=ErrorCode.FAILED, message="当前厂商为自有厂商，不支持三方云接口调用")
        return vendor

    # 云厂商列表
    def cloud_vendor_list(self):
        return self.repo.cloud_vendor_list()

    # 创建云厂商
    def cloud_vendor_create(self, user_id: int, data: dict):
        payload = {
            **data,
            "created_by": user_id,
        }
        result = self.repo.cloud_vendor_create(payload)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return True

    # 修改云厂商
    def cloud_vendor_update(self, data: dict):
        record = self.repo.cloud_vendor_by_id(data['cloud_vendor_id'])
        if not record:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        result = self.repo.cloud_vendor_update(record, data)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return True

    # 云厂商分页
    def cloud_vendor_page_list(self, user_id: int, page: int, page_size: int):
        items, total = self.repo.cloud_vendor_page_list(user_id, page, page_size)
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
