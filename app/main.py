from fastapi import FastAPI

from app.api.api_v1.api import api_router
from app.core.config import settings


#TODO: доделать все

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_STR)