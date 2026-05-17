from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db_utils import customer_integrity_detail, integrity_message
from app.logger import get_logger
from app.schemas.customer_schemas import CustomerCreate, CustomerUpdate

logger = get_logger(__name__)


def get_customers(db: Session, skip: int = 0, limit: int = 10):
    logger.info("Query customers skip=%s limit=%s", skip, limit)
    rows = (
        db.query(models.Customer)
        .options(
            selectinload(models.Customer.orders),
            selectinload(models.Customer.payments),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    logger.info("Found %s customers", len(rows))
    return rows


def get_customer(db: Session, customer_id: int):
    logger.info("Query customer customerNumber=%s", customer_id)
    row = (
        db.query(models.Customer)
        .options(
            selectinload(models.Customer.orders),
            selectinload(models.Customer.payments),
        )
        .filter(models.Customer.customerNumber == customer_id)
        .first()
    )
    if row is None:
        logger.warning("Customer %s not found", customer_id)
        raise HTTPException(status_code=404, detail="Customer not found")
    return row


def create_customer(db: Session, customer: CustomerCreate):
    logger.info("Create customer customerNumber=%s", customer.customerNumber)
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raw = integrity_message(e)
        logger.error("IntegrityError creating customer: %s", raw)
        raise HTTPException(
            status_code=422,
            detail=customer_integrity_detail(raw),
        ) from e
    db.refresh(db_customer)
    logger.info("Customer %s created", db_customer.customerNumber)
    return db_customer


def update_customer(db: Session, customer_id: int, customer: CustomerUpdate):
    db_customer = (
        db.query(models.Customer)
        .filter(models.Customer.customerNumber == customer_id)
        .first()
    )
    if not db_customer:
        logger.warning("Customer %s not found for update", customer_id)
        raise HTTPException(status_code=404, detail="Customer not found")
    updates = customer.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(db_customer, key, value)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raw = integrity_message(e)
        logger.error("IntegrityError updating customer: %s", raw)
        raise HTTPException(
            status_code=422,
            detail=customer_integrity_detail(raw),
        ) from e
    db.refresh(db_customer)
    logger.info("Customer %s updated", customer_id)
    return db_customer


def delete_customer(db: Session, customer_id: int):
    db_customer = (
        db.query(models.Customer)
        .filter(models.Customer.customerNumber == customer_id)
        .first()
    )
    if not db_customer:
        logger.warning("Customer %s not found for delete", customer_id)
        raise HTTPException(status_code=404, detail="Customer not found")
    try:
        db.delete(db_customer)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError deleting customer: %s", integrity_message(e))
        raise HTTPException(
            status_code=409,
            detail="Cannot delete customer: related orders, payments, or other records still exist.",
        ) from e
    logger.info("Customer %s deleted", customer_id)
    return True
