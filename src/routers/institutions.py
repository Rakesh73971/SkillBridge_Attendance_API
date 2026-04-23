from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db


router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.post("/", response_model=schemas.InstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_institution(institution: schemas.InstitutionCreate, db: Session = Depends(get_db)):
    new_institution = models.Institution(**institution.model_dump())
    db.add(new_institution)
    db.commit()
    db.refresh(new_institution)
    return new_institution
