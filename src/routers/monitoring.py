from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..database import get_db


router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/attendance")
def get_monitoring_attendance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_monitoring_user)
):
   
    attendance_data = db.query(models.Attendance).all()
    return attendance_data
