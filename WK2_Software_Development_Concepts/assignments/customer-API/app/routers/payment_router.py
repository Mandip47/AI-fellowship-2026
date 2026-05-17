from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import payment_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.payment_schemas import PaymentCreate, PaymentOut, PaymentUpdate

router = APIRouter()
logger = get_logger(__name__)


@router.get("/customer/{customer_number}", response_model=list[PaymentOut])
def list_payments_by_customer(
    request: Request,
    customer_number: int,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return payment_crud.list_payments_for_customer(db, customer_number)


@router.get("", response_model=list[PaymentOut])
def list_payments(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return payment_crud.list_payments(db, skip, limit)


@router.get("/{customer_number}/{check_number}", response_model=PaymentOut)
def read_payment(
    request: Request,
    customer_number: int,
    check_number: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return payment_crud.get_payment(db, customer_number, check_number)


@router.post("", response_model=PaymentOut)
def create_payment(
    request: Request, body: PaymentCreate, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    return payment_crud.create_payment(db, body)


@router.put("/{customer_number}/{check_number}", response_model=PaymentOut)
def update_payment(
    request: Request,
    customer_number: int,
    check_number: str,
    body: PaymentUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return payment_crud.update_payment(db, customer_number, check_number, body)


@router.delete("/{customer_number}/{check_number}")
def delete_payment(
    request: Request,
    customer_number: int,
    check_number: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    payment_crud.delete_payment(db, customer_number, check_number)
    return {"message": "Payment deleted"}
