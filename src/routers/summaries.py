from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(tags=["Summaries"])

def calculate_summary(query_result):
    
    summary = {"total_students_marked": 0, "present_count": 0, "absent_count": 0, "late_count": 0}
    for status, count in query_result:
        summary["total_students_marked"] += count
        if status == models.AttendanceStatusEnum.PRESENT:
            summary["present_count"] = count
        elif status == models.AttendanceStatusEnum.ABSENT:
            summary["absent_count"] = count
        elif status == models.AttendanceStatusEnum.LATE:
            summary["late_count"] = count
    return summary


def get_user_region(db: Session, current_user: models.User) -> str:
    if current_user.institution_id is None:
        raise HTTPException(status_code=403, detail="User is not linked to a region")

    institution = db.query(models.Institution).filter(models.Institution.id == current_user.institution_id).first()
    if not institution or not institution.region:
        raise HTTPException(status_code=403, detail="User region is not configured")
    return institution.region

@router.get("/batches/{id}/summary", response_model=schemas.AttendanceSummaryResponse)
def get_batch_summary(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.INSTITUTION])) 
):
    
    batch = db.query(models.Batch).filter(models.Batch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if current_user.institution_id != batch.institution_id:
        raise HTTPException(status_code=403, detail="Not enough permissions for this batch")

    
    results = db.query(models.Attendance.status, func.count(models.Attendance.id)).join(
        models.Session, models.Attendance.session_id == models.Session.id
    ).filter(models.Session.batch_id == id).group_by(models.Attendance.status).all()
    
    return calculate_summary(results)

@router.get("/institutions/{id}/summary", response_model=schemas.AttendanceSummaryResponse)
def get_institution_summary(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.PROGRAMME_MANAGER])) 
):
    institution = db.query(models.Institution).filter(models.Institution.id == id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    manager_region = get_user_region(db, current_user)
    if institution.region != manager_region:
        raise HTTPException(status_code=403, detail="Not enough permissions for this institution")

    results = db.query(models.Attendance.status, func.count(models.Attendance.id)).join(
        models.Session, models.Attendance.session_id == models.Session.id
    ).join(
        models.Batch, models.Session.batch_id == models.Batch.id
    ).filter(models.Batch.institution_id == id).group_by(models.Attendance.status).all()
    
    return calculate_summary(results)

@router.get("/programme/summary", response_model=schemas.AttendanceSummaryResponse)
def get_programme_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.PROGRAMME_MANAGER]))
):
    manager_region = get_user_region(db, current_user)
    results = db.query(models.Attendance.status, func.count(models.Attendance.id)).join(
        models.Session, models.Attendance.session_id == models.Session.id
    ).join(
        models.Batch, models.Session.batch_id == models.Batch.id
    ).join(
        models.Institution, models.Batch.institution_id == models.Institution.id
    ).filter(
        models.Institution.region == manager_region
    ).group_by(models.Attendance.status).all()
    return calculate_summary(results)
