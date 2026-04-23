from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db
from datetime import datetime, timezone

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/mark", response_model=schemas.AttendanceResponse)
def mark_attendance(
    attendance: schemas.AttendanceMark, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.STUDENT]))
):
    session = db.query(models.Session).filter(models.Session.id == attendance.session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    enrollment = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == session.batch_id,
        models.BatchStudent.student_id == current_user.id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this batch") 

    now = datetime.now(timezone.utc)
    session_start = datetime.combine(session.date, session.start_time, tzinfo=timezone.utc)
    session_end = datetime.combine(session.date, session.end_time, tzinfo=timezone.utc)
    if not (session_start <= now <= session_end):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attendance can only be marked for an active session")

    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.session_id == attendance.session_id,
        models.Attendance.student_id == current_user.id
    ).first()
    if existing_attendance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attendance already marked for this session")

    new_attendance = models.Attendance(
        session_id=attendance.session_id,
        student_id=current_user.id,
        status=attendance.status
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return new_attendance
