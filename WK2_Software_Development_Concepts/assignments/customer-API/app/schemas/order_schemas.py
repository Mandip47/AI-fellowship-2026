from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

OrderStatus = Literal[
    "Shipped",
    "Resolved",
    "Cancelled",
    "On Hold",
    "Disputed",
    "In Process",
]


class OrderDetailBrief(BaseModel):
    productCode: str
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    orderNumber: int
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: OrderStatus
    comments: Optional[str] = None
    customerNumber: int

    @model_validator(mode="after")
    def required_after_order(self):
        if self.requiredDate < self.orderDate:
            raise ValueError("requiredDate must be on or after orderDate")
        return self


class OrderOut(BaseModel):
    orderNumber: int
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: str
    comments: Optional[str] = None
    customerNumber: int

    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    orderDate: Optional[date] = None
    requiredDate: Optional[date] = None
    shippedDate: Optional[date] = None
    status: Optional[OrderStatus] = None
    comments: Optional[str] = None
    customerNumber: Optional[int] = None

    @model_validator(mode="after")
    def dates_consistent(self):
        od, rd = self.orderDate, self.requiredDate
        if od is not None and rd is not None and rd < od:
            raise ValueError("requiredDate must be on or after orderDate")
        return self


class OrderWithDetailsOut(OrderOut):
    orderdetails: List[OrderDetailBrief] = []

    model_config = ConfigDict(from_attributes=True)
