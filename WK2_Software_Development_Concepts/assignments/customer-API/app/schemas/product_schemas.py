from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.order_schemas import OrderDetailBrief


class ProductCreate(BaseModel):
    productCode: str = Field(max_length=15)
    productName: str = Field(max_length=70)
    productLine: str = Field(max_length=50)
    productScale: str = Field(max_length=10)
    productVendor: str = Field(max_length=50)
    productDescription: str
    quantityInStock: int = Field(ge=0)
    buyPrice: Decimal
    MSRP: Decimal

    @model_validator(mode="after")
    def msrp_ge_buy(self):
        if self.MSRP < self.buyPrice:
            raise ValueError("MSRP must be greater than or equal to buyPrice")
        return self


class ProductOut(BaseModel):
    productCode: str
    productName: str
    productLine: str
    productScale: str
    productVendor: str
    productDescription: str
    quantityInStock: int
    buyPrice: Decimal
    MSRP: Decimal

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    productName: Optional[str] = Field(None, max_length=70)
    productLine: Optional[str] = Field(None, max_length=50)
    productScale: Optional[str] = Field(None, max_length=10)
    productVendor: Optional[str] = Field(None, max_length=50)
    productDescription: Optional[str] = None
    quantityInStock: Optional[int] = Field(None, ge=0)
    buyPrice: Optional[Decimal] = None
    MSRP: Optional[Decimal] = None


class ProductWithOrderDetailsOut(ProductOut):
    orderdetails: List[OrderDetailBrief] = []

    model_config = ConfigDict(from_attributes=True)
