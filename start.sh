#!/bin/bash
BASE_DIR=$(cd "$(dirname "$0")"; pwd)
VENV_PATH="$BASE_DIR/.venv"
APP_MAIN="$BASE_DIR/app/main.py"

source "$VENV_PATH/bin/activate"

case "$1" in
  dev)
    export $(grep -v '^#' "$BASE_DIR/.env.development" | xargs)
    echo "✅ 开发环境启动中..."
    uvicorn main:app --host 127.0.0.1 --port 8080 --reload
    ;;
  prod)
    export $(grep -v '^#' "$BASE_DIR/.env.production" | xargs)
    echo "✅ 生产环境启动中..."
    uvicorn main:app --host 0.0.0.0 --port 8080
    ;;
  migrate)
    echo "📦 执行数据库迁移..."
    alembic upgrade head
    ;;
  *)
    echo "用法: ./start.sh [dev|prod|migrate]"
    exit 1
    ;;
esac
