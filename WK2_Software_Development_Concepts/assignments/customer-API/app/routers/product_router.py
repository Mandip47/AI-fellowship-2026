from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import product_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.product_schemas import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductWithOrderDetailsOut,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[ProductOut])
def list_products(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return product_crud.list_products(db, skip, limit)


@router.get("/{product_code}", response_model=ProductOut)
def read_product(request: Request, product_code: str, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    return product_crud.get_product(db, product_code)


@router.get("/{product_code}/orderdetails", response_model=ProductWithOrderDetailsOut)
def read_product_orderdetails(
    request: Request,
    product_code: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return product_crud.get_product_with_orderdetails(db, product_code)


@router.post("", response_model=ProductOut)
def create_product(
    request: Request, body: ProductCreate, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    return product_crud.create_product(db, body)


@router.put("/{product_code}", response_model=ProductOut)
def update_product(
    request: Request,
    product_code: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return product_crud.update_product(db, product_code, body)


@router.delete("/{product_code}")
def delete_product(request: Request, product_code: str, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    product_crud.delete_product(db, product_code)
    return {"message": "Product deleted"}
