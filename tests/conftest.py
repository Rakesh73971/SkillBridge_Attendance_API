import pytest
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import models, utils
from src.database import Base, get_db
from src.main import app
from src.config import settings


SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False,expire_on_commit=False)



TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with test database."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_data(db):
    """Create seed data for testing."""
    inst1 = models.Institution(name="Tech Institute", region="North")
    inst2 = models.Institution(name="Skill Academy", region="South")
    db.add(inst1)
    db.add(inst2)
    db.commit()
    db.refresh(inst1)
    db.refresh(inst2)

    trainer_password = utils.hash_password("trainer123")
    trainer1 = models.User(
        name="John Trainer",
        email="john.trainer@example.com",
        hashed_password=trainer_password,
        role=models.RoleEnum.TRAINER,
        institution_id=inst1.id,
    )
    trainer2 = models.User(
        name="Jane Trainer",
        email="jane.trainer@example.com",
        hashed_password=trainer_password,
        role=models.RoleEnum.TRAINER,
        institution_id=inst2.id,
    )
    db.add(trainer1)
    db.add(trainer2)
    db.commit()
    db.refresh(trainer1)
    db.refresh(trainer2)

    student_password = utils.hash_password("student123")
    students = []
    for i in range(5):
        student = models.User(
            name=f"Student {i + 1}",
            email=f"student{i + 1}@example.com",
            hashed_password=student_password,
            role=models.RoleEnum.STUDENT,
            institution_id=inst1.id,
        )
        db.add(student)
        students.append(student)
    db.commit()
    for student in students:
        db.refresh(student)

    batch = models.Batch(name="Python Batch 2024", institution_id=inst1.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    batch_trainer = models.BatchTrainer(batch_id=batch.id, trainer_id=trainer1.id)
    db.add(batch_trainer)

    for student in students:
        batch_student = models.BatchStudent(batch_id=batch.id, student_id=student.id)
        db.add(batch_student)
    db.commit()

    session_date = datetime.now(timezone.utc).date()
    session = models.Session(
        batch_id=batch.id,
        trainer_id=trainer1.id,
        title="Introduction to Python",
        date=session_date,
        start_time=datetime.now(timezone.utc).time(),
        end_time=(datetime.now(timezone.utc) + timedelta(hours=2)).time(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    for i, student in enumerate(students):
        status = (
            models.AttendanceStatusEnum.PRESENT
            if i % 3 != 0
            else models.AttendanceStatusEnum.ABSENT
        )
        attendance = models.Attendance(
            session_id=session.id,
            student_id=student.id,
            status=status,
        )
        db.add(attendance)
    db.commit()

    return {
        "institutions": [inst1, inst2],
        "trainers": [trainer1, trainer2],
        "students": students,
        "batch": batch,
        "session": session,
    }


@pytest.fixture(scope="function")
def test_student(db):
    """Create a test student user."""
    student_password = utils.hash_password("student123")
    inst = models.Institution(name="Test Institute", region="Test")
    db.add(inst)
    db.commit()
    db.refresh(inst)

    student = models.User(
        name="Test Student",
        email="test.student@example.com",
        hashed_password=student_password,
        role=models.RoleEnum.STUDENT,
        institution_id=inst.id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture(scope="function")
def test_trainer(db):
    """Create a test trainer user."""
    trainer_password = utils.hash_password("trainer123")
    inst = models.Institution(name="Test Institute", region="Test")
    db.add(inst)
    db.commit()
    db.refresh(inst)

    trainer = models.User(
        name="Test Trainer",
        email="test.trainer@example.com",
        hashed_password=trainer_password,
        role=models.RoleEnum.TRAINER,
        institution_id=inst.id,
    )
    db.add(trainer)
    db.commit()
    db.refresh(trainer)
    return trainer


@pytest.fixture(scope="function")
def test_monitoring_officer(db):
    password = utils.hash_password("monitor123")
    monitor = models.User(
        name="Test Monitor",
        email="test.monitor@example.com",
        hashed_password=password,
        role=models.RoleEnum.MONITORING_OFFICER,
        institution_id=None,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


@pytest.fixture(scope="function")
def test_institution_user(db):
    inst = models.Institution(name="Institution User Institute", region="North")
    other_inst = models.Institution(name="Other Institute", region="South")
    db.add(inst)
    db.add(other_inst)
    db.commit()
    db.refresh(inst)
    db.refresh(other_inst)

    password = utils.hash_password("institution123")
    institution_user = models.User(
        name="Test Institution User",
        email="test.institution@example.com",
        hashed_password=password,
        role=models.RoleEnum.INSTITUTION,
        institution_id=inst.id,
    )
    db.add(institution_user)
    db.commit()
    db.refresh(institution_user)
    institution_user.other_institution_id = other_inst.id
    return institution_user


@pytest.fixture(scope="function")
def test_programme_manager(db):
    inst = models.Institution(name="Programme Region Institute", region="North")
    db.add(inst)
    db.commit()
    db.refresh(inst)

    password = utils.hash_password("progmgr123")
    manager = models.User(
        name="Test Programme Manager",
        email="test.progmgr@example.com",
        hashed_password=password,
        role=models.RoleEnum.PROGRAMME_MANAGER,
        institution_id=inst.id,
    )
    db.add(manager)
    db.commit()
    db.refresh(manager)
    return manager
