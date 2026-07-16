from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.driver import router as driver_router

from app.middlewares.logging_middleware import logging_middleware
from app.core.exceptions.handlers import register_exception_handlers
from app.core.config import get_settings

settings = get_settings()




app = FastAPI(
    title=settings.APP_NAME,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

app.middleware("http")(logging_middleware)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(driver_router)