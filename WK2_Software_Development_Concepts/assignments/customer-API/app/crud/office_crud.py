from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db_utils import integrity_message
from app.logger import get_logger
from app.schemas.office_schemas import OfficeCreate, OfficeUpdate

logger = get_logger(__name__)


def list_offices(db: Session, skip: int = 0, limit: int = 10):
    logger.info("List offices skip=%s limit=%s", skip, limit)
    rows = db.query(models.Office).offset(skip).limit(limit).all()
    logger.info("Returned %s offices", len(rows))
    return rows


def get_office(db: Session, office_code: str):
    logger.info("Get office officeCode=%s", office_code)
    row = (
        db.query(models.Office).filter(models.Office.officeCode == office_code).first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Office not found")
    return row


def get_office_with_employees(db: Session, office_code: str):
    logger.info("Get office with employees officeCode=%s", office_code)
    row = (
        db.query(models.Office)
        .options(selectinload(models.Office.employees))
        .filter(models.Office.officeCode == office_code)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Office not found")
    return row


def create_office(db: Session, data: OfficeCreate):
    logger.info("Create office officeCode=%s", data.officeCode)
    obj = models.Office(**data.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating office: %s", integrity_message(e))
        raise HTTPException(status_code=422, detail="Could not create office.") from e
    db.refresh(obj)
    return obj


def update_office(db: Session, office_code: str, data: OfficeUpdate):
    obj = (
        db.query(models.Office).filter(models.Office.officeCode == office_code).first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Office not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail="Could not update office.") from e
    db.refresh(obj)
    return obj


def delete_office(db: Session, office_code: str):
    obj = (
        db.query(models.Office).filter(models.Office.officeCode == office_code).first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Office not found")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete office while employees are still assigned to it.",
        ) from e
    return True
