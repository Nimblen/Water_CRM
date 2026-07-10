from contextvars import ContextVar




trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


request_id_var: ContextVar[str] = ContextVar("request_id", default="")

user_id_var: ContextVar[str] = ContextVar("user_id", default="")

worker_id_var: ContextVar[str] = ContextVar("worker_id", default="")


def get_trace_id() -> str:
    return trace_id_var.get() or ""


def get_request_id() -> str:
    return request_id_var.get() or ""


def get_user_id() -> str:
    return user_id_var.get() or ""

def get_worker_id() -> str:
    return worker_id_var.get() or ""


def set_trace_id(trace_id: str) -> None:
    trace_id_var.set(trace_id)


def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)


def set_worker_id(worker_id: str) -> None:
    worker_id_var.set(worker_id)


def set_user_id(user_id: str) -> None:
    user_id_var.set(user_id)