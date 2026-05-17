from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.productline_schemas import ProductLineCreate, ProductLineUpdate

logger = get_logger(__name__)


def list_productlines(db: Session, skip: int = 0, limit: int = 10):
    logger.info("List productlines skip=%s limit=%s", skip, limit)
    rows = db.query(models.ProductLine).offset(skip).limit(limit).all()
    logger.info("Returned %s product lines", len(rows))
    return rows


def get_productline(db: Session, product_line: str):
    logger.info("Get productline=%s", product_line)
    row = (
        db.query(models.ProductLine)
        .filter(models.ProductLine.productLine == product_line)
        .first()
    )
    if row is None:
        logger.warning("Product line %s not found", product_line)
        raise HTTPException(status_code=404, detail="Product line not found")
    return row


def get_productline_with_products(db: Session, product_line: str):
    logger.info("Get productline with products productLine=%s", product_line)
    row = (
        db.query(models.ProductLine)
        .options(selectinload(models.ProductLine.products))
        .filter(models.ProductLine.productLine == product_line)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Product line not found")
    return row


def create_productline(db: Session, data: ProductLineCreate):
    logger.info("Create productline=%s", data.productLine)
    obj = models.ProductLine(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating productline: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not create product line: duplicate key or invalid data.",
        ) from e
    db.refresh(obj)
    return obj


def update_productline(db: Session, product_line: str, data: ProductLineUpdate):
    obj = (
        db.query(models.ProductLine)
        .filter(models.ProductLine.productLine == product_line)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Product line not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError updating productline: %s", integrity_message(e))
        raise HTTPException(
            status_code=422, detail="Could not update product line."
        ) from e
    db.refresh(obj)
    return obj


def delete_productline(db: Session, product_line: str):
    obj = (
        db.query(models.ProductLine)
        .filter(models.ProductLine.productLine == product_line)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Product line not found")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError deleting productline: %s", integrity_message(e))
        raise HTTPException(
            status_code=409,
            detail="Cannot delete product line while products still reference it.",
        ) from e
    logger.info("Product line %s deleted", product_line)
    return True
