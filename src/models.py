from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Time, Enum
from datetime import datetime, timezone
from .database import Base
import enum


class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    TRAINER = "trainer"
    INSTITUTION = "institution"
    PROGRAMME_MANAGER = "programme_manager"
    MONITORING_OFFICER = "monitoring_officer"

class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

class Institution(Base):
    __tablename__ = 'institutions'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Batch(Base):
    __tablename__ = 'batches'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class BatchTrainer(Base):
    __tablename__ = 'batch_trainers'
    batch_id = Column(Integer, ForeignKey('batches.id'), primary_key=True)
    trainer_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

class BatchStudent(Base):
    __tablename__ = 'batch_students'
    batch_id = Column(Integer, ForeignKey('batches.id'), primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

class BatchInvite(Base):
    __tablename__ = 'batch_invites'
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    trainer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(AttendanceStatusEnum), nullable=False)
    marked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
