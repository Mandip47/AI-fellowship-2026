from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderDetailCreate(BaseModel):
    orderNumber: int
    productCode: str = Field(max_length=15)
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int = Field(ge=1, le=32767)

    @field_validator("quantityOrdered")
    @classmethod
    def quantity_positive(cls, v: int):
        if v <= 0:
            raise ValueError("quantityOrdered must be greater than 0")
        return v


class OrderDetailOut(BaseModel):
    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int

    model_config = ConfigDict(from_attributes=True)


class OrderDetailUpdate(BaseModel):
    quantityOrdered: Optional[int] = None
    priceEach: Optional[Decimal] = None
    orderLineNumber: Optional[int] = Field(None, ge=1, le=32767)

    @field_validator("quantityOrdered")
    @classmethod
    def quantity_positive(cls, v: Optional[int]):
        if v is not None and v <= 0:
            raise ValueError("quantityOrdered must be greater than 0")
        return v
