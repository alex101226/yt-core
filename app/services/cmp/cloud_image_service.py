from sqlalchemy.orm import Session

from app.repositories.cmp.cloud_image_repo import CloudImageRepo
from app.schemas.cmp.cloud_image import CloudImageCreate


class CloudImageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CloudImageRepo(db)

    def create_image(self, user_id: int, image_data: CloudImageCreate):

        payload = {
            **image_data.model_dump(),
            "user_id": user_id,
            "image_id": image_data.image_name,
        }
        return self.repo.create(payload)
