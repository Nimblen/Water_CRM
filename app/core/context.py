import structlog.contextvars

def set_trace_id(trace_id: str) -> None:
    structlog.contextvars.bind_contextvars(trace_id=trace_id)

def set_request_id(request_id: str) -> None:
    structlog.contextvars.bind_contextvars(request_id=request_id)

def get_trace_id() -> str:
    ctx = structlog.contextvars.get_contextvars()
    return ctx.get("trace_id", "")

def get_request_id() -> str:
    ctx = structlog.contextvars.get_contextvars()
    return ctx.get("request_id", "")
