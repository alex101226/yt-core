# app/main.py
import uvicorn

from app.core.init_app import create_app
from app.core.config import settings

from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer

# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title="My API",
#         version="1.0.0",
#         description="API Docs",
#         routes=app.routes,
#     )
#
#     # ⭐ 在 Swagger UI 中添加 Bearer Token 的输入框
#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#         }
#     }
#
#     # ⭐ 默认所有路由可选择使用 BearerAuth
#     for route in openapi_schema["paths"].values():
#         for method in route.values():
#             method.setdefault("security", [{"BearerAuth": []}])
#
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema


app = create_app()

# app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=(settings.ENV=="development"))
