import time
from uuid import uuid4

import structlog
from fastapi import Request

from app.core.context import set_request_id, set_trace_id, set_worker_id, set_user_id



logger = structlog.get_logger("http")


async def logging_middleware(request: Request, call_next):

    trace_id = (request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID") or str(uuid4()))

    request_id = str(uuid4())

    set_trace_id(trace_id)
    set_request_id(request_id)
    set_worker_id(str(time.time()))
    set_user_id(request.headers.get("X-User-ID", ""))
    start = time.perf_counter()

    logger.info("request started", method=request.method)
    try:
        response = await call_next(request)
        duration = round(time.perf_counter() - start, 4)
        logger.info("request_finished", status_code=response.status_code, duration=duration)
        response.headers["X-Trace-ID"] = trace_id
        return response
    except Exception as e:
        duration = round(time.perf_counter() - start, 4)
        logger.error("request_finished", status_code=500, duration=duration, exc_info=e)
        raise
    finally:
        structlog.contextvars.clear_contextvars()