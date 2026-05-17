from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.order_schemas import OrderCreate, OrderUpdate

logger = get_logger(__name__)


def list_orders(db: Session, skip: int = 0, limit: int = 10):
    logger.info("List orders skip=%s limit=%s", skip, limit)
    return db.query(models.Order).offset(skip).limit(limit).all()


def get_order(db: Session, order_number: int):
    row = (
        db.query(models.Order).filter(models.Order.orderNumber == order_number).first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return row


def get_order_with_orderdetails(db: Session, order_number: int):
    row = (
        db.query(models.Order)
        .options(selectinload(models.Order.orderdetails))
        .filter(models.Order.orderNumber == order_number)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return row


def list_orders_for_customer(db: Session, customer_number: int):
    logger.info("List orders for customerNumber=%s", customer_number)
    return (
        db.query(models.Order)
        .filter(models.Order.customerNumber == customer_number)
        .order_by(models.Order.orderNumber)
        .all()
    )


def create_order(db: Session, data: OrderCreate):
    logger.info("Create order orderNumber=%s", data.orderNumber)
    obj = models.Order(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating order: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not create order: invalid customerNumber or duplicate orderNumber.",
        ) from e
    db.refresh(obj)
    return obj


def update_order(db: Session, order_number: int, data: OrderUpdate):
    obj = (
        db.query(models.Order).filter(models.Order.orderNumber == order_number).first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Order not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(obj, key, value)
    if obj.requiredDate < obj.orderDate:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="requiredDate must be on or after orderDate.",
        )
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="Could not update order: invalid customerNumber.",
        ) from e
    db.refresh(obj)
    return obj


def delete_order(db: Session, order_number: int):
    obj = (
        db.query(models.Order).filter(models.Order.orderNumber == order_number).first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete order while order line items still exist.",
        ) from e
    return True
