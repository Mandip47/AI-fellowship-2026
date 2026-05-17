import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.database import engine
from app.logger import get_logger
from app import models
from app.routers import (
    customer_router,
    employee_router,
    office_router,
    order_router,
    orderdetail_router,
    payment_router,
    product_router,
    productline_router,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ensuring database tables exist")
    last_error: OperationalError | None = None
    for attempt in range(1, 31):
        try:
            models.Base.metadata.create_all(bind=engine)
            last_error = None
            break
        except OperationalError as e:
            last_error = e
            logger.warning(
                "Database not ready yet (attempt %s/30): %s",
                attempt,
                e.orig if getattr(e, "orig", None) else e,
            )
            await asyncio.sleep(2)
    if last_error is not None:
        logger.exception("Giving up waiting for database")
        raise last_error
    yield


app = FastAPI(title="ClassicModels API", version="2.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logger.warning(
        "Validation error on %s %s: %s", request.method, request.url.path, exc.errors()
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "ClassicModels API is running!"}


app.include_router(customer_router.router, prefix="/customers", tags=["Customers"])
app.include_router(product_router.router, prefix="/products", tags=["Products"])
app.include_router(
    productline_router.router, prefix="/productlines", tags=["ProductLines"]
)
app.include_router(office_router.router, prefix="/offices", tags=["Offices"])
app.include_router(employee_router.router, prefix="/employees", tags=["Employees"])
app.include_router(order_router.router, prefix="/orders", tags=["Orders"])
app.include_router(
    orderdetail_router.router, prefix="/orderdetails", tags=["OrderDetails"]
)
app.include_router(payment_router.router, prefix="/payments", tags=["Payments"])
