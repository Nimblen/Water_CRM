from typing import Annotated
from fastapi import Depends, Header, HTTPException, Request
from starlette.responses import JSONResponse

from app.repositories.idempotency import IdempotencyRepository
from app.dependencies.session import SessionDep
from app.core.exceptions.cache import _CachedResponse

async def get_idempotency_key(
    request: Request,
    session: SessionDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    if idempotency_key is None:
        return None

    repo = IdempotencyRepository(session)
    existing = await repo.get(idempotency_key, endpoint=request.url.path)
    if existing:
        raise _CachedResponse(existing.status_code, existing.response_body)

    return idempotency_key



IdempotencyKeyDep = Annotated[str | None, Depends(get_idempotency_key)]