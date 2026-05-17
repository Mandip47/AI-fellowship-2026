from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.product_schemas import ProductCreate, ProductUpdate

logger = get_logger(__name__)


def list_products(db: Session, skip: int = 0, limit: int = 10):
    logger.info("List products skip=%s limit=%s", skip, limit)
    rows = db.query(models.Product).offset(skip).limit(limit).all()
    logger.info("Returned %s products", len(rows))
    return rows


def get_product(db: Session, product_code: str):
    logger.info("Get product productCode=%s", product_code)
    row = (
        db.query(models.Product)
        .filter(models.Product.productCode == product_code)
        .first()
    )
    if row is None:
        logger.warning("Product %s not found", product_code)
        raise HTTPException(status_code=404, detail="Product not found")
    return row


def get_product_with_orderdetails(db: Session, product_code: str):
    logger.info("Get product with orderdetails productCode=%s", product_code)
    row = (
        db.query(models.Product)
        .options(selectinload(models.Product.orderdetails))
        .filter(models.Product.productCode == product_code)
        .first()
    )
    if row is None:
        logger.warning("Product %s not found", product_code)
        raise HTTPException(status_code=404, detail="Product not found")
    return row


def create_product(db: Session, data: ProductCreate):
    logger.info("Create product productCode=%s", data.productCode)
    obj = models.Product(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating product: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not create product: check productLine exists and productCode is unique.",
        ) from e
    db.refresh(obj)
    return obj


def update_product(db: Session, product_code: str, data: ProductUpdate):
    obj = (
        db.query(models.Product)
        .filter(models.Product.productCode == product_code)
        .first()
    )
    if obj is None:
        logger.warning("Product %s not found for update", product_code)
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    if data.buyPrice is not None or data.MSRP is not None:
        bp = obj.buyPrice
        msrp = obj.MSRP
        if msrp < bp:
            db.rollback()
            raise HTTPException(
                status_code=422,
                detail="MSRP must be greater than or equal to buyPrice after update.",
            )
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError updating product: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not update product: invalid productLine or constraint violation.",
        ) from e
    db.refresh(obj)
    logger.info("Product %s updated", product_code)
    return obj


def delete_product(db: Session, product_code: str):
    obj = (
        db.query(models.Product)
        .filter(models.Product.productCode == product_code)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError deleting product: %s", integrity_message(e))
        raise HTTPException(
            status_code=409,
            detail="Cannot delete product: it is still referenced by order line items.",
        ) from e
    logger.info("Product %s deleted", product_code)
    return True
