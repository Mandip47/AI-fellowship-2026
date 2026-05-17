from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate

logger = get_logger(__name__)


def list_employees(db: Session, skip: int = 0, limit: int = 10):
    logger.info("List employees skip=%s limit=%s", skip, limit)
    return db.query(models.Employee).offset(skip).limit(limit).all()


def get_employee(db: Session, employee_number: int):
    row = (
        db.query(models.Employee)
        .filter(models.Employee.employeeNumber == employee_number)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return row


def get_employee_with_customers(db: Session, employee_number: int):
    row = (
        db.query(models.Employee)
        .options(selectinload(models.Employee.customers))
        .filter(models.Employee.employeeNumber == employee_number)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return row


def list_employee_reports(db: Session, employee_number: int):
    get_employee(db, employee_number)
    return (
        db.query(models.Employee)
        .filter(models.Employee.reportsTo == employee_number)
        .all()
    )


def create_employee(db: Session, data: EmployeeCreate):
    logger.info("Create employee employeeNumber=%s", data.employeeNumber)
    obj = models.Employee(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating employee: %s", integrity_message(e))
        raise HTTPException(
            status_code=422,
            detail="Could not create employee: invalid officeCode or reportsTo reference.",
        ) from e
    db.refresh(obj)
    return obj


def update_employee(db: Session, employee_number: int, data: EmployeeUpdate):
    obj = (
        db.query(models.Employee)
        .filter(models.Employee.employeeNumber == employee_number)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="Could not update employee: invalid officeCode or reportsTo reference.",
        ) from e
    db.refresh(obj)
    return obj


def delete_employee(db: Session, employee_number: int):
    obj = (
        db.query(models.Employee)
        .filter(models.Employee.employeeNumber == employee_number)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    has_reports = (
        db.query(models.Employee)
        .filter(models.Employee.reportsTo == employee_number)
        .first()
    )
    if has_reports:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete employee who still has direct reports.",
        )
    has_customers = (
        db.query(models.Customer)
        .filter(models.Customer.salesRepEmployeeNumber == employee_number)
        .first()
    )
    if has_customers:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete employee assigned as sales rep to customers.",
        )
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete employee: related records still exist.",
        ) from e
    return True
