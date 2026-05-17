from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud
import asyncio
import time

router = APIRouter()


@router.get("/customers/count")
async def customers_count(db: AsyncSession = Depends(get_db)):
    return {"customers": await crud.get_customers_count(db)}


@router.get("/orders/count")
async def orders_count(db: AsyncSession = Depends(get_db)):
    return {"orders": await crud.get_orders_count(db)}


@router.get("/products/count")
async def products_count(db: AsyncSession = Depends(get_db)):
    return {"products": await crud.get_products_count(db)}


@router.get("/employees/count")
async def employees_count(db: AsyncSession = Depends(get_db)):
    return {"employees": await crud.get_employees_count(db)}


@router.get("/offices/count")
async def offices_count(db: AsyncSession = Depends(get_db)):
    return {"offices": await crud.get_offices_count(db)}


@router.get("/payments/count")
async def payments_count(db: AsyncSession = Depends(get_db)):
    return {"payments": await crud.get_payments_count(db)}


@router.get("/orderdetails/count")
async def orderdetails_count(db: AsyncSession = Depends(get_db)):
    return {"orderdetails": await crud.get_orderdetails_count(db)}


@router.get("/productlines/count")
async def productlines_count(db: AsyncSession = Depends(get_db)):
    return {"productlines": await crud.get_productlines_count(db)}


@router.get("/overall_counts")
async def overall_counts(db: AsyncSession = Depends(get_db)):

    start_time = time.time()

    tasks = [
        crud.get_customers_count(db),
        crud.get_orders_count(db),
        crud.get_products_count(db),
        crud.get_employees_count(db),
        crud.get_offices_count(db),
        crud.get_payments_count(db),
        crud.get_orderdetails_count(db),
        crud.get_productlines_count(db),
    ]

    results = await asyncio.gather(*tasks)

    end_time = time.time()

    return {
        "customers": results[0],
        "orders": results[1],
        "products": results[2],
        "employees": results[3],
        "offices": results[4],
        "payments": results[5],
        "orderdetails": results[6],
        "productlines": results[7],
        "response_time": f"{end_time - start_time:.4f} seconds",
    }
