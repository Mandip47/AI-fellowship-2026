from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import orderdetail_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.orderdetail_schemas import (
    OrderDetailCreate,
    OrderDetailOut,
    OrderDetailUpdate,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[OrderDetailOut])
def list_orderdetails(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return orderdetail_crud.list_orderdetails(db, skip, limit)


@router.get("/order/{order_number}", response_model=list[OrderDetailOut])
def list_orderdetails_for_order(
    request: Request,
    order_number: int,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return orderdetail_crud.list_orderdetails_for_order(db, order_number)


@router.get("/product/{product_code}", response_model=list[OrderDetailOut])
def list_orderdetails_for_product(
    request: Request,
    product_code: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return orderdetail_crud.list_orderdetails_for_product(db, product_code)


@router.get("/{order_number}/{product_code}", response_model=OrderDetailOut)
def read_orderdetail(
    request: Request,
    order_number: int,
    product_code: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return orderdetail_crud.get_orderdetail(db, order_number, product_code)


@router.post("", response_model=OrderDetailOut)
def create_orderdetail(
    request: Request,
    body: OrderDetailCreate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return orderdetail_crud.create_orderdetail(db, body)


@router.put("/{order_number}/{product_code}", response_model=OrderDetailOut)
def update_orderdetail(
    request: Request,
    order_number: int,
    product_code: str,
    body: OrderDetailUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return orderdetail_crud.update_orderdetail(db, order_number, product_code, body)


@router.delete("/{order_number}/{product_code}")
def delete_orderdetail(
    request: Request,
    order_number: int,
    product_code: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    orderdetail_crud.delete_orderdetail(db, order_number, product_code)
    return {"message": "Order detail deleted"}
