from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PaymentCreate(BaseModel):
    customerNumber: int
    checkNumber: str
    paymentDate: date
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v

    @field_validator("paymentDate")
    @classmethod
    def payment_not_future(cls, v: date):
        if v > date.today():
            raise ValueError("paymentDate cannot be in the future")
        return v


class PaymentOut(BaseModel):
    customerNumber: int
    checkNumber: str
    paymentDate: date
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentUpdate(BaseModel):
    paymentDate: Optional[date] = None
    amount: Optional[Decimal] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[Decimal]):
        if v is not None and v <= 0:
            raise ValueError("amount must be greater than 0")
        return v

    @field_validator("paymentDate")
    @classmethod
    def payment_not_future(cls, v: Optional[date]):
        if v is not None and v > date.today():
            raise ValueError("paymentDate cannot be in the future")
        return v
