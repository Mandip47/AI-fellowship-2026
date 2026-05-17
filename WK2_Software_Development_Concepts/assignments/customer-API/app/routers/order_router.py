from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import order_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.order_schemas import (
    OrderCreate,
    OrderOut,
    OrderUpdate,
    OrderWithDetailsOut,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("/customer/{customer_number}", response_model=list[OrderOut])
def list_orders_by_customer(
    request: Request,
    customer_number: int,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return order_crud.list_orders_for_customer(db, customer_number)


@router.get("", response_model=list[OrderOut])
def list_orders(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return order_crud.list_orders(db, skip, limit)


@router.get("/{order_number}", response_model=OrderOut)
def read_order(request: Request, order_number: int, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    return order_crud.get_order(db, order_number)


@router.get("/{order_number}/orderdetails", response_model=OrderWithDetailsOut)
def read_order_orderdetails(
    request: Request,
    order_number: int,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return order_crud.get_order_with_orderdetails(db, order_number)


@router.post("", response_model=OrderOut)
def create_order(request: Request, body: OrderCreate, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    return order_crud.create_order(db, body)


@router.put("/{order_number}", response_model=OrderOut)
def update_order(
    request: Request,
    order_number: int,
    body: OrderUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return order_crud.update_order(db, order_number, body)


@router.delete("/{order_number}")
def delete_order(request: Request, order_number: int, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    order_crud.delete_order(db, order_number)
    return {"message": "Order deleted"}
