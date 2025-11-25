from fastapi import APIRouter, Depends, Request

from app.core.dependencies import require_user

from app.common.response import Response

from app.schemas.sso.auth_schema import UserOut

from app.services.sso.dependencies import get_user_service
from app.services.sso.user_service import UserService

router = APIRouter(
    prefix="/user",
    tags=["用户信息"],
    dependencies=[Depends(require_user)],
)


# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3LCJleHAiOjE3NjM4ODQwNzEsInR5cGUiOiJhY2Nlc3MifQ.QlDIHBA-toJQa9uxP6AcuSv9DHMaFWtvAWpKUHBNdVM
@router.get("/user_info", response_model=UserOut)
def me(request: Request, service: UserService = Depends(get_user_service)):
    auth = request.state.user
    user = service.user_info(auth['user_id'])
    return Response.success(user)