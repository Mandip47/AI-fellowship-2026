from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.order_schemas import OrderOut
from app.schemas.payment_schemas import PaymentOut


class CustomerCreate(BaseModel):
    customerNumber: int
    customerName: str = Field(max_length=50)
    contactLastName: str = Field(max_length=50)
    contactFirstName: str = Field(max_length=50)
    phone: str = Field(max_length=50)
    addressLine1: str = Field(max_length=50)
    addressLine2: Optional[str] = Field(None, max_length=50)
    city: str = Field(max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    postalCode: str = Field(max_length=15)
    country: str = Field(max_length=50)
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[Decimal] = None


class CustomerUpdate(BaseModel):
    customerName: Optional[str] = Field(None, max_length=50)
    contactLastName: Optional[str] = Field(None, max_length=50)
    contactFirstName: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    addressLine1: Optional[str] = Field(None, max_length=50)
    addressLine2: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    postalCode: Optional[str] = Field(None, max_length=15)
    country: Optional[str] = Field(None, max_length=50)
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[Decimal] = None


class CustomerOut(BaseModel):
    customerNumber: int
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postalCode: str
    country: str
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[Decimal] = None
    orders: List[OrderOut] = []
    payments: List[PaymentOut] = []

    model_config = ConfigDict(from_attributes=True)


class CustomerBrief(BaseModel):
    customerNumber: int
    customerName: str

    model_config = ConfigDict(from_attributes=True)
