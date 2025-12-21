# app/main.py
import uvicorn

from app.core.init_app import create_app
from app.core.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        # reload=settings.ENV == "development",
    )
    # uvicorn.run("main:app", host="0.0.0.0", port=8084, reload=(settings.ENV=="development"))
