from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db
import secrets
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/batches", tags=["Batches"])


def get_batch_or_404(batch_id: int, db: Session):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch


def trainer_assigned_to_batch(batch_id: int, trainer_id: int, db: Session) -> bool:
    assignment = db.query(models.BatchTrainer).filter(
        models.BatchTrainer.batch_id == batch_id,
        models.BatchTrainer.trainer_id == trainer_id
    ).first()
    return assignment is not None

@router.post("/", response_model=schemas.BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    batch: schemas.BatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.TRAINER, models.RoleEnum.INSTITUTION]))
):
    institution = db.query(models.Institution).filter(models.Institution.id == batch.institution_id).first()
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    if (
        current_user.role == models.RoleEnum.INSTITUTION
        and current_user.institution_id != batch.institution_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institution users can only create batches for their own institution",
        )

    new_batch = models.Batch(**batch.model_dump())
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)

    if current_user.role == models.RoleEnum.TRAINER:
        db.add(models.BatchTrainer(batch_id=new_batch.id, trainer_id=current_user.id))
        db.commit()

    return new_batch

@router.post("/{id}/invite", response_model=schemas.BatchInviteResponse)
def generate_invite(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.TRAINER]))
):
    get_batch_or_404(id, db)
    if not trainer_assigned_to_batch(id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer is not assigned to this batch")

    token = secrets.token_urlsafe(16)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    
    new_invite = models.BatchInvite(
        batch_id=id, token=token, created_by=current_user.id, expires_at=expires
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return new_invite

@router.post("/join")
def join_batch(
    invite_req: schemas.BatchJoinRequest, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.STUDENT]))
):
    invite = db.query(models.BatchInvite).filter(models.BatchInvite.token == invite_req.token).first()
    if not invite or invite.used or invite.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    existing_join = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == invite.batch_id,
        models.BatchStudent.student_id == current_user.id
    ).first()
    if existing_join:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student already joined this batch")

    db.add(models.BatchStudent(batch_id=invite.batch_id, student_id=current_user.id))
    invite.used = True
    db.commit()
    return {"message": "Successfully joined batch"}
