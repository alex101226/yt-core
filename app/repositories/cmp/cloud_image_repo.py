from sqlalchemy.orm import Session

from app.models.cmp.cloud_image import CloudImage

class CloudImageRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: dict) -> CloudImage:
        """
        创建云镜像记录
        """
        cloud_image = CloudImage(**data)
        self.session.add(cloud_image)
        self.session.commit()
        self.session.refresh(cloud_image)
        return cloud_image
