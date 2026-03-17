import os

os.environ["ENV"] = "production"

import uvicorn
from main import app
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.PORT,
    )
