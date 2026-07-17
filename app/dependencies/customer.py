from typing import Annotated
from fastapi import Depends
from app.services.customer import CustomerService
from app.dependencies.session import SessionDep
from app.schemas.customer import CustomerFilters


def get_customer_service(session: SessionDep) -> CustomerService:
    return CustomerService(session)


CustomerServiceDep = Annotated[
    CustomerService,
    Depends(get_customer_service),
]

CustomerFiltersDep = Annotated[
    CustomerFilters,
    Depends(),
]