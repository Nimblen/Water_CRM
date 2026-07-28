import time
from uuid import uuid4

import structlog
from fastapi import Request

from app.core.context import set_request_id, set_trace_id

logger = structlog.get_logger("http")
#TODO: добавить ip address

async def logging_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID") or str(uuid4())
    request_id = str(uuid4())

    set_trace_id(trace_id)
    set_request_id(request_id)

    start = time.perf_counter()
    logger.info("request_started", method=request.method, path=request.url.path)

    try:
        response = await call_next(request)
        duration = round(time.perf_counter() - start, 4)
        logger.info(
            "request_finished",
            status_code=response.status_code,
            duration=duration,
            method=request.method,
            path=request.url.path,
        )
        response.headers["X-Trace-ID"] = trace_id
        return response
    except Exception as e:
        duration = round(time.perf_counter() - start, 4)
        logger.exception(
            "request_failed",
            duration=duration,
        )
        raise
    finally:
        structlog.contextvars.clear_contextvars()
        