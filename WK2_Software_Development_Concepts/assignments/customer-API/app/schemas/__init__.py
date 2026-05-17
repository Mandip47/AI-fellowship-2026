"""Re-export schema modules for convenient imports."""

from app.schemas.customer_schemas import (
    CustomerBrief,
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
)
from app.schemas.employee_schemas import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    EmployeeWithCustomersOut,
)
from app.schemas.office_schemas import (
    OfficeCreate,
    OfficeOut,
    OfficeUpdate,
    OfficeWithEmployeesOut,
)
from app.schemas.order_schemas import (
    OrderCreate,
    OrderDetailBrief,
    OrderOut,
    OrderUpdate,
    OrderWithDetailsOut,
)
from app.schemas.orderdetail_schemas import (
    OrderDetailCreate,
    OrderDetailOut,
    OrderDetailUpdate,
)
from app.schemas.payment_schemas import PaymentCreate, PaymentOut, PaymentUpdate
from app.schemas.product_schemas import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductWithOrderDetailsOut,
)
from app.schemas.productline_schemas import (
    ProductLineCreate,
    ProductLineOut,
    ProductLineUpdate,
    ProductLineWithProductsOut,
)

__all__ = [
    "CustomerBrief",
    "CustomerCreate",
    "CustomerOut",
    "CustomerUpdate",
    "EmployeeCreate",
    "EmployeeOut",
    "EmployeeUpdate",
    "EmployeeWithCustomersOut",
    "OfficeCreate",
    "OfficeOut",
    "OfficeUpdate",
    "OfficeWithEmployeesOut",
    "OrderCreate",
    "OrderDetailBrief",
    "OrderDetailCreate",
    "OrderDetailOut",
    "OrderDetailUpdate",
    "OrderOut",
    "OrderUpdate",
    "OrderWithDetailsOut",
    "PaymentCreate",
    "PaymentOut",
    "PaymentUpdate",
    "ProductCreate",
    "ProductLineCreate",
    "ProductLineOut",
    "ProductLineUpdate",
    "ProductLineWithProductsOut",
    "ProductOut",
    "ProductUpdate",
    "ProductWithOrderDetailsOut",
]
