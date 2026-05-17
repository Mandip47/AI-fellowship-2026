from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.payment_schemas import PaymentCreate, PaymentUpdate

logger = get_logger(__name__)


def list_payments(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Payment).offset(skip).limit(limit).all()


def get_payment(db: Session, customer_number: int, check_number: str):
    row = (
        db.query(models.Payment)
        .filter(
            models.Payment.customerNumber == customer_number,
            models.Payment.checkNumber == check_number,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return row


def list_payments_for_customer(db: Session, customer_number: int):
    logger.info("List payments for customerNumber=%s", customer_number)
    return (
        db.query(models.Payment)
        .filter(models.Payment.customerNumber == customer_number)
        .order_by(models.Payment.paymentDate)
        .all()
    )


def create_payment(db: Session, data: PaymentCreate):
    logger.info(
        "Create payment customer=%s check=%s",
        data.customerNumber,
        data.checkNumber,
    )
    obj = models.Payment(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating payment: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not create payment: invalid customerNumber or duplicate composite key.",
        ) from e
    db.refresh(obj)
    return obj


def update_payment(
    db: Session,
    customer_number: int,
    check_number: str,
    data: PaymentUpdate,
):
    obj = get_payment(db, customer_number, check_number)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    if obj.amount <= 0:
        db.rollback()
        raise HTTPException(status_code=422, detail="amount must be greater than 0.")
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail="Could not update payment.") from e
    db.refresh(obj)
    return obj


def delete_payment(db: Session, customer_number: int, check_number: str):
    obj = (
        db.query(models.Payment)
        .filter(
            models.Payment.customerNumber == customer_number,
            models.Payment.checkNumber == check_number,
        )
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(obj)
    db.commit()
    return True
