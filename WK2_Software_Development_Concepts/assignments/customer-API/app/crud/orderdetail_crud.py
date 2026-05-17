from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.orderdetail_schemas import OrderDetailCreate, OrderDetailUpdate

logger = get_logger(__name__)


def list_orderdetails(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.OrderDetail).offset(skip).limit(limit).all()


def get_orderdetail(db: Session, order_number: int, product_code: str):
    row = (
        db.query(models.OrderDetail)
        .filter(
            models.OrderDetail.orderNumber == order_number,
            models.OrderDetail.productCode == product_code,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Order detail not found")
    return row


def list_orderdetails_for_order(db: Session, order_number: int):
    logger.info("List orderdetails for orderNumber=%s", order_number)
    return (
        db.query(models.OrderDetail)
        .filter(models.OrderDetail.orderNumber == order_number)
        .order_by(models.OrderDetail.orderLineNumber)
        .all()
    )


def list_orderdetails_for_product(db: Session, product_code: str):
    logger.info("List orderdetails for productCode=%s", product_code)
    return (
        db.query(models.OrderDetail)
        .filter(models.OrderDetail.productCode == product_code)
        .all()
    )


def create_orderdetail(db: Session, data: OrderDetailCreate):
    logger.info(
        "Create orderdetail order=%s product=%s",
        data.orderNumber,
        data.productCode,
    )
    obj = models.OrderDetail(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating orderdetail: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not create order detail: invalid orderNumber or productCode.",
        ) from e
    db.refresh(obj)
    return obj


def update_orderdetail(
    db: Session,
    order_number: int,
    product_code: str,
    data: OrderDetailUpdate,
):
    obj = get_orderdetail(db, order_number, product_code)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    if obj.quantityOrdered <= 0:
        db.rollback()
        raise HTTPException(
            status_code=422, detail="quantityOrdered must be greater than 0."
        )
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=422, detail="Could not update order detail."
        ) from e
    db.refresh(obj)
    return obj


def delete_orderdetail(db: Session, order_number: int, product_code: str):
    obj = (
        db.query(models.OrderDetail)
        .filter(
            models.OrderDetail.orderNumber == order_number,
            models.OrderDetail.productCode == product_code,
        )
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Order detail not found")
    db.delete(obj)
    db.commit()
    return True
