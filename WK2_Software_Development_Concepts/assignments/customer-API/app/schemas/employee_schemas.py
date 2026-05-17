from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.customer_schemas import CustomerBrief


class EmployeeCreate(BaseModel):
    employeeNumber: int
    lastName: str = Field(max_length=50)
    firstName: str = Field(max_length=50)
    extension: str = Field(max_length=10)
    email: EmailStr
    officeCode: str = Field(max_length=10)
    reportsTo: Optional[int] = None
    jobTitle: str = Field(max_length=50)


class EmployeeOut(BaseModel):
    employeeNumber: int
    lastName: str
    firstName: str
    extension: str
    email: str
    officeCode: str
    reportsTo: Optional[int] = None
    jobTitle: str

    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    lastName: Optional[str] = Field(None, max_length=50)
    firstName: Optional[str] = Field(None, max_length=50)
    extension: Optional[str] = Field(None, max_length=10)
    email: Optional[EmailStr] = None
    officeCode: Optional[str] = Field(None, max_length=10)
    reportsTo: Optional[int] = None
    jobTitle: Optional[str] = Field(None, max_length=50)


class EmployeeWithCustomersOut(EmployeeOut):
    customers: List[CustomerBrief] = []

    model_config = ConfigDict(from_attributes=True)
