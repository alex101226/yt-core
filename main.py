# app/main.py
import uvicorn

from app.core.init_app import create_app
from app.core.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=(settings.ENV=="development"))
