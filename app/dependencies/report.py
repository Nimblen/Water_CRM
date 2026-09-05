from typing import Annotated
from datetime import date
from uuid import UUID

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.session import SessionDep
from app.services.report import ReportService
from app.schemas.report import ReportDateFilter


def get_report_service(
    session: SessionDep,
) -> ReportService:
    return ReportService(session)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


def get_report_date_filter(
    date_from: date = Query(...),
    date_to: date = Query(...),
    driver_id: UUID | None = Query(None),
) -> ReportDateFilter:
    if date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="date_from не может быть позже date_to",
        )
    return ReportDateFilter(
        date_from=date_from,
        date_to=date_to,
        driver_id=driver_id,
    )


ReportDateFilterDep = Annotated[ReportDateFilter, Depends(get_report_date_filter)]