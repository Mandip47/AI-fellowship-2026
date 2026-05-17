from pydantic import BaseModel
from typing import Optional
from datetime import date


class ProductLineSchema(BaseModel):
    id: int
    productLine: str
    textDescription: Optional[str] = None

    class Config:
        from_attributes = True


class ProductSchema(BaseModel):
    id: int
    productCode: str
    productName: str
    quantityInStock: int
    buyPrice: float
    MSRP: float

    class Config:
        from_attributes = True


class OfficeSchema(BaseModel):
    id: int
    officeCode: str
    city: str
    country: str

    class Config:
        from_attributes = True


class EmployeeSchema(BaseModel):
    id: int
    employeeNumber: int
    firstName: str
    lastName: str
    email: str
    jobTitle: str

    class Config:
        from_attributes = True


class CustomerSchema(BaseModel):
    id: int
    customerNumber: int
    customerName: str
    city: str
    country: str

    class Config:
        from_attributes = True


class PaymentSchema(BaseModel):
    id: int
    checkNumber: str
    paymentDate: date
    amount: float

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: int
    orderNumber: int
    orderDate: date
    status: str

    class Config:
        from_attributes = True


class OrderDetailSchema(BaseModel):
    id: int
    quantityOrdered: int
    priceEach: float

    class Config:
        from_attributes = True


class DashboardStatsSchema(BaseModel):
    customers: int
    orders: int
    products: int
    employees: int
    offices: int
    payments: int
    orderdetails: int
    productlines: int
