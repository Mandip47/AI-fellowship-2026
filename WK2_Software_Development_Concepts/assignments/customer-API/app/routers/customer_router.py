from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import customer_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.customer_schemas import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[CustomerOut])
def read_customers(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info(
        "%s %s params=%s", request.method, request.url.path, dict(request.query_params)
    )
    return customer_crud.get_customers(db, skip, limit)


@router.get("/{customer_number}", response_model=CustomerOut)
def read_customer(
    request: Request, customer_number: int, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    return customer_crud.get_customer(db, customer_number)


@router.post("", response_model=CustomerOut)
def create_customer(
    request: Request,
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return customer_crud.create_customer(db, customer)


@router.put("/{customer_number}", response_model=CustomerOut)
def update_customer(
    request: Request,
    customer_number: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return customer_crud.update_customer(db, customer_number, customer)


@router.delete("/{customer_number}")
def delete_customer(
    request: Request, customer_number: int, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    customer_crud.delete_customer(db, customer_number)
    return {"message": "Customer deleted"}
