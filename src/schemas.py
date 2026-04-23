from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, date, time
from .models import RoleEnum, AttendanceStatusEnum


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[RoleEnum] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class MonitoringTokenRequest(BaseModel):
    key: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum
    institution_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleEnum
    institution_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstitutionCreate(BaseModel):
    name: str
    region: Optional[str] = None


class InstitutionResponse(BaseModel):
    id: int
    name: str
    region: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BatchCreate(BaseModel):
    name: str
    institution_id: int

class BatchResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BatchJoinRequest(BaseModel):
    token: str

class BatchInviteResponse(BaseModel):
    token: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    batch_id: int
    title: str
    date: date
    start_time: time
    end_time: time

class SessionResponse(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AttendanceMark(BaseModel):
    session_id: int
    status: AttendanceStatusEnum

class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatusEnum
    marked_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AttendanceSummaryResponse(BaseModel):
    total_students_marked: int
    present_count: int
    absent_count: int
    late_count: int
