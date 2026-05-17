from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product_schemas import ProductOut


class ProductLineCreate(BaseModel):
    productLine: str = Field(max_length=50)
    textDescription: Optional[str] = Field(None, max_length=4000)
    htmlDescription: Optional[str] = None
    image: Optional[bytes] = None


class ProductLineOut(BaseModel):
    productLine: str
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductLineUpdate(BaseModel):
    textDescription: Optional[str] = Field(None, max_length=4000)
    htmlDescription: Optional[str] = None
    image: Optional[bytes] = None


class ProductLineWithProductsOut(ProductLineOut):
    products: List[ProductOut] = []

    model_config = ConfigDict(from_attributes=True)
