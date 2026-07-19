
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions.base import AppException
from app.core.exceptions.cache import _CachedResponse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions.base import AppException
from app.core.exceptions.cache import _CachedResponse


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(_CachedResponse)
    async def cached_response_handler(
        request: Request,
        exc: _CachedResponse,
    ):
        return JSONResponse(status_code=exc.status_code, content=exc.body)