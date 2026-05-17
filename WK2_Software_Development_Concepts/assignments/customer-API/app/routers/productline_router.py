from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import productline_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.productline_schemas import (
    ProductLineCreate,
    ProductLineOut,
    ProductLineUpdate,
    ProductLineWithProductsOut,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[ProductLineOut])
def list_productlines(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return productline_crud.list_productlines(db, skip, limit)


@router.get("/{product_line}", response_model=ProductLineOut)
def read_productline(
    request: Request, product_line: str, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    return productline_crud.get_productline(db, product_line)


@router.get("/{product_line}/products", response_model=ProductLineWithProductsOut)
def read_productline_products(
    request: Request,
    product_line: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return productline_crud.get_productline_with_products(db, product_line)


@router.post("", response_model=ProductLineOut)
def create_productline(
    request: Request,
    body: ProductLineCreate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return productline_crud.create_productline(db, body)


@router.put("/{product_line}", response_model=ProductLineOut)
def update_productline(
    request: Request,
    product_line: str,
    body: ProductLineUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return productline_crud.update_productline(db, product_line, body)


@router.delete("/{product_line}")
def delete_productline(
    request: Request, product_line: str, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    productline_crud.delete_productline(db, product_line)
    return {"message": "Product line deleted"}
