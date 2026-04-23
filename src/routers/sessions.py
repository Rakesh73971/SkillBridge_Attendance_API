from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def trainer_assigned_to_batch(batch_id: int, trainer_id: int, db: Session) -> bool:
    assignment = db.query(models.BatchTrainer).filter(
        models.BatchTrainer.batch_id == batch_id,
        models.BatchTrainer.trainer_id == trainer_id
    ).first()
    return assignment is not None

@router.post("/", response_model=schemas.SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session: schemas.SessionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.TRAINER]))
):
    batch = db.query(models.Batch).filter(models.Batch.id == session.batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    if not trainer_assigned_to_batch(batch.id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer is not assigned to this batch")
    if session.end_time <= session.start_time:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_time must be after start_time")

    new_session = models.Session(**session.model_dump(), trainer_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/{id}/attendance", response_model=list[schemas.AttendanceResponse])
def get_session_attendance(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.TRAINER]))
):
    session = db.query(models.Session).filter(models.Session.id == id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if not trainer_assigned_to_batch(session.batch_id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer is not assigned to this batch")

    attendance_records = db.query(models.Attendance).filter(models.Attendance.session_id == id).all()
    return attendance_records
