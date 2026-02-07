# 使用 Python 3.9 官方 slim 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 创建非 root 用户
#RUN useradd -m -s /bin/bash yt_back

# 升级 pip，防止依赖安装报错
RUN python -m pip install --upgrade pip

# 先 COPY requirements.txt 并安装依赖（利用缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 显式安装 uvicorn 和 fastapi，避免 requirements.txt 不完整
RUN pip install --no-cache-dir uvicorn fastapi gunicorn python-dotenv

# 切换到非 root 用户
#USER yt_back

# COPY 项目源码到容器，并修改归属
#COPY --chown=yt_back:yt_back . .
COPY . .

# 创建日志目录
#RUN mkdir -p /app/logs \
#    && chown -R yt_back:yt_back /app/logs
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8000

# 使用 python -m uvicorn 启动，避免找不到 uvicorn
#CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD 改为 Gunicorn + UvicornWorker
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "-w", "4", "-b", "0.0.0.0:8000", "--log-level", "info"]