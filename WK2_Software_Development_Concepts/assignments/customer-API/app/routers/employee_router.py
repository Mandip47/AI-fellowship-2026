from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import employee_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.employee_schemas import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    EmployeeWithCustomersOut,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return employee_crud.list_employees(db, skip, limit)


@router.get("/{employee_number}", response_model=EmployeeOut)
def read_employee(
    request: Request, employee_number: int, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    return employee_crud.get_employee(db, employee_number)


@router.get("/{employee_number}/customers", response_model=EmployeeWithCustomersOut)
def read_employee_customers(
    request: Request,
    employee_number: int,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return employee_crud.get_employee_with_customers(db, employee_number)


@router.get("/{employee_number}/reports", response_model=list[EmployeeOut])
def read_employee_reports(
    request: Request,
    employee_number: int,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return employee_crud.list_employee_reports(db, employee_number)


@router.post("", response_model=EmployeeOut)
def create_employee(
    request: Request, body: EmployeeCreate, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    return employee_crud.create_employee(db, body)


@router.put("/{employee_number}", response_model=EmployeeOut)
def update_employee(
    request: Request,
    employee_number: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return employee_crud.update_employee(db, employee_number, body)


@router.delete("/{employee_number}")
def delete_employee(
    request: Request, employee_number: int, db: Session = Depends(get_db)
):
    logger.info("%s %s", request.method, request.url.path)
    employee_crud.delete_employee(db, employee_number)
    return {"message": "Employee deleted"}
