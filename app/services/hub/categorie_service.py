from sqlalchemy.orm import Session

from app.repositories.hub.hub_repo import HubRepo

class HubCategoryService:
    def __init__(self, session: Session):
        self.session = session
        self.hub_repo = HubRepo(session)

    def categories_list(self):
        return self.hub_repo.categories_list()

    def model_list(self):
        return self.hub_repo.model_list()

    def model_detail(self, slug: str):
        return self.hub_repo.model_detail(slug)