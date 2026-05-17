from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud import office_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.office_schemas import (
    OfficeCreate,
    OfficeOut,
    OfficeUpdate,
    OfficeWithEmployeesOut,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[OfficeOut])
def list_offices(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return office_crud.list_offices(db, skip, limit)


@router.get("/{office_code}", response_model=OfficeOut)
def read_office(request: Request, office_code: str, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    return office_crud.get_office(db, office_code)


@router.get("/{office_code}/employees", response_model=OfficeWithEmployeesOut)
def read_office_employees(
    request: Request,
    office_code: str,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return office_crud.get_office_with_employees(db, office_code)


@router.post("", response_model=OfficeOut)
def create_office(request: Request, body: OfficeCreate, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    return office_crud.create_office(db, body)


@router.put("/{office_code}", response_model=OfficeOut)
def update_office(
    request: Request,
    office_code: str,
    body: OfficeUpdate,
    db: Session = Depends(get_db),
):
    logger.info("%s %s", request.method, request.url.path)
    return office_crud.update_office(db, office_code, body)


@router.delete("/{office_code}")
def delete_office(request: Request, office_code: str, db: Session = Depends(get_db)):
    logger.info("%s %s", request.method, request.url.path)
    office_crud.delete_office(db, office_code)
    return {"message": "Office deleted"}
