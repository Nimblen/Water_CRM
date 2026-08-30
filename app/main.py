from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import ConnectionPool, Redis
from app.api.v1.auth import router as auth_router
from app.api.v1.admin.drivers import router as admin_router
from app.api.v1.drivers import router as driver_router
from app.api.v1.admin.customers import router as admin_customer
from app.api.v1.admin.prices import router as admin_price
from app.api.v1.admin.routes import router as admin_routes
from app.api.v1.admin.reports import router as admin_reports
from app.api.v1.admin.notifications import router as admin_notification
from app.api.v1.notifications import router as driver_notification
from app.middlewares.logging_middleware import logging_middleware
from app.core.exceptions.handlers import register_exception_handlers
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = ConnectionPool.from_url(settings.REDIS_URL, max_connections=20)
    app.state.redis = Redis(connection_pool=pool)
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await pool.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
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
app.include_router(admin_customer)
app.include_router(admin_price)
app.include_router(admin_routes)
app.include_router(admin_reports)
app.include_router(admin_notification)
app.include_router(driver_notification)