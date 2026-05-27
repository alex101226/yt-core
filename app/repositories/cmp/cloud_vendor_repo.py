from sqlalchemy.orm import Session

from app.models.cmp import CloudVendor


class CloudVendorRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, cloud_code: str):
        return (
            self.db.query(CloudVendor)
            .filter(
                CloudVendor.cloud_code == cloud_code,
                CloudVendor.is_released == 0,
            )
            .first()
        )

    # 云厂商列表
    def cloud_vendor_list(self):
        rows = (
            self.db.query(
                CloudVendor.cloud_code,
                CloudVendor.cloud_name,
            )
            .filter(CloudVendor.is_released == 0)
            .order_by(CloudVendor.id.desc())
            .all()
        )
        return [
            {
                "cloud_code": row.cloud_code,
                "cloud_name": row.cloud_name,
            }
            for row in rows
        ]

    # 云厂商page_list
    def cloud_vendor_page_list(self, user_id: int, page: int, page_size: int):
        query = self.db.query(CloudVendor).filter(CloudVendor.created_by == user_id).order_by(CloudVendor.id.desc())

        count = query.count()

        offset_value = (page - 1) * page_size

        items = query.offset(offset_value).limit(page_size).all()
        return items, count

    # 创建云厂商
    def cloud_vendor_create(self, data: dict):
        cloud_vendor = CloudVendor(**data)
        self.db.add(cloud_vendor)
        self.db.commit()
        self.db.refresh(cloud_vendor)
        return cloud_vendor


    # 修改云厂商
    def cloud_vendor_update(self, old_data: CloudVendor, data: dict):
        for key, value in data.items():
            if hasattr(old_data, key):
                setattr(old_data, key, value)

        self.db.commit()
        self.db.refresh(old_data)
        return old_data


    # 单条查询
    def cloud_vendor_by_id(self, cloud_vendor_id: int):
        record = self.db.query(CloudVendor).filter_by(id=cloud_vendor_id).first()
        return record
