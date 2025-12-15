# app/main.py
import uvicorn

from app.core.init_app import create_app
from app.core.config import settings

app = create_app()

# app.openapi = custom_openapi

# 云厂商, 云凭证, 区域, 可用区, VPC, IP子网, 安全组, 计费方式, 购买数量, 规格列表, 系统镜像,管理员密码,SSH代理,名称,主机名,描述,操作系统,规格,
# 资源组, IP, 带宽,创建人

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8084, reload=(settings.ENV=="development"))
