from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.logger import logger
from app import models


async def get_table_count(session: AsyncSession, model) -> int:

    logger.info(f"Counting rows in {model.__tablename__}")

    try:
        stmt = select(func.count()).select_from(model)
        result = await session.execute(stmt)
        count = result.scalar_one()

        logger.info(f"{model.__tablename__} count = {count}")

        return count

    except Exception as e:

        logger.error(f"Database error while querying " f"{model.__tablename__}: {e}")

        return 0


async def get_customers_count(session):
    return await get_table_count(session, models.Customer)


async def get_orders_count(session):
    return await get_table_count(session, models.Order)


async def get_products_count(session):
    return await get_table_count(session, models.Product)


async def get_employees_count(session):
    return await get_table_count(session, models.Employee)


async def get_offices_count(session):
    return await get_table_count(session, models.Office)


async def get_payments_count(session):
    return await get_table_count(session, models.Payment)


async def get_orderdetails_count(session):
    return await get_table_count(session, models.OrderDetail)


async def get_productlines_count(session):
    return await get_table_count(session, models.ProductLine)
