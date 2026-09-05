from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from app.core.exceptions.base import AppException
from app.core.exceptions.cache import _CachedResponse

# Коды, у которых тела быть не может (RFC 9110). Отдать им JSON нельзя:
# uvicorn роняет ASGI-приложение с "Response content longer than Content-Length".
BODILESS_STATUSES = frozenset({204, 205, 304})


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
        # Повтор обязан выглядеть ровно как первый ответ, а у 204 он был пустым.
        if exc.status_code in BODILESS_STATUSES:
            return Response(status_code=exc.status_code)
        return JSONResponse(status_code=exc.status_code, content=exc.body)