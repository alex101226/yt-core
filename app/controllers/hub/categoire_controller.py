from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_hub_db

from app.services.hub.categorie_service import HubCategoryService

def get_auth_service(
    hub_db: Session = Depends(get_hub_db),
):
  return HubCategoryService(hub_db)

router = APIRouter(prefix="/hub", tags=["大模型广场"])

@router.get("/categories_list")
def categories_list(service: HubCategoryService = Depends(get_auth_service)):
    result = service.categories_list()
    return Response.success(result)

@router.get("/model_list")
def model_list(service: HubCategoryService = Depends(get_auth_service)):
    result = service.model_list()
    return Response.success(result)

@router.get('/model_detail')
def model_detail(
    slug: str,
    service: HubCategoryService = Depends(get_auth_service)
):
    result = service.model_detail(slug)
    return Response.success(result)
