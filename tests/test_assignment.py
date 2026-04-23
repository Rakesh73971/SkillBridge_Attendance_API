from datetime import datetime, timezone, timedelta

from src import models


def test_create_institution(client):
    response = client.post("/institutions", json={"name": "New Institute", "region": "West"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Institute"
    assert data["region"] == "West"
    assert "id" in data


def test_student_signup_and_login(client, db):
    """Test 1: Successful student signup and login, asserting a valid JWT is returned"""

    inst = models.Institution(name="Test Institute", region="Test")
    db.add(inst)
    db.commit()
    db.refresh(inst)

    signup_data = {
        "name": "John Student",
        "email": "john.student@example.com",
        "password": "password123",
        "role": "student",
        "institution_id": inst.id
    }
    response = client.post("/auth/signup", json=signup_data)
    assert response.status_code == 201  # Signup returns 201 Created
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

    login_data = {
        "email": "john.student@example.com",
        "password": "password123"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_trainer_creating_session(client, test_trainer, db):
    """Test 2: A trainer creating a session with all required fields"""

    batch = models.Batch(name="Python Batch", institution_id=test_trainer.institution_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.add(models.BatchTrainer(batch_id=batch.id, trainer_id=test_trainer.id))
    db.commit()

    login_data = {
        "email": test_trainer.email,
        "password": "trainer123"
    }
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    session_date = datetime.now(timezone.utc).date()
    session_data = {
        "batch_id": batch.id,
        "title": "Advanced Python",
        "date": session_date.isoformat(),
        "start_time": "09:00:00",
        "end_time": "11:00:00"
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/sessions", json=session_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Advanced Python"
    assert data["batch_id"] == batch.id
    assert data["trainer_id"] == test_trainer.id


def test_student_marking_attendance(client, test_student, test_trainer, db):
    """Test 3: A student successfully marking their own attendance"""

    batch = models.Batch(name="Attendance Batch", institution_id=test_trainer.institution_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.add(models.BatchTrainer(batch_id=batch.id, trainer_id=test_trainer.id))
    db.commit()

    batch_student = models.BatchStudent(batch_id=batch.id, student_id=test_student.id)
    db.add(batch_student)
    db.commit()

    now = datetime.now(timezone.utc)
    session_date = now.date()
    session = models.Session(
        batch_id=batch.id,
        trainer_id=test_trainer.id,
        title="Test Session",
        date=session_date,
        start_time=(now - timedelta(minutes=30)).time().replace(microsecond=0),
        end_time=(now + timedelta(minutes=30)).time().replace(microsecond=0)
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    login_data = {
        "email": test_student.email,
        "password": "student123"
    }
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    attendance_data = {
        "session_id": session.id,
        "status": "present"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/attendance/mark", json=attendance_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "present"
    assert data["student_id"] == test_student.id
    assert data["session_id"] == session.id


def test_monitoring_attendance_requires_scoped_token(client, test_monitoring_officer, db):
    login_data = {
        "email": test_monitoring_officer.email,
        "password": "monitor123"
    }
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    response = client.get("/monitoring/attendance", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_signup_with_invalid_institution_returns_404(client):
    signup_data = {
        "name": "Invalid Institution User",
        "email": "invalid.institution@example.com",
        "password": "password123",
        "role": "student",
        "institution_id": 9999
    }
    response = client.post("/auth/signup", json=signup_data)
    assert response.status_code == 404


def test_student_cannot_mark_attendance_for_inactive_session(client, test_student, test_trainer, db):
    batch = models.Batch(name="Inactive Attendance Batch", institution_id=test_trainer.institution_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.add(models.BatchTrainer(batch_id=batch.id, trainer_id=test_trainer.id))
    db.commit()

    db.add(models.BatchStudent(batch_id=batch.id, student_id=test_student.id))
    db.commit()

    now = datetime.now(timezone.utc)
    session = models.Session(
        batch_id=batch.id,
        trainer_id=test_trainer.id,
        title="Old Session",
        date=now.date(),
        start_time=(now - timedelta(hours=2)).time().replace(microsecond=0),
        end_time=(now - timedelta(hours=1)).time().replace(microsecond=0),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    login_response = client.post("/auth/login", json={
        "email": test_student.email,
        "password": "student123"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/attendance/mark",
        json={"session_id": session.id, "status": "present"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_monitoring_attendance_post_returns_405(client):
    """Test 4: A POST to /monitoring/attendance returning 405 Method Not Allowed"""
    response = client.post("/monitoring/attendance", json={})
    assert response.status_code == 405


def test_protected_endpoint_without_token_returns_401(client):
    """Test 5: A request to a protected endpoint with no token returning 401"""
    response = client.get("/sessions/1/attendance")
    assert response.status_code == 401


def test_institution_cannot_create_batch_for_other_institution(client, test_institution_user):
    login_response = client.post("/auth/login", json={
        "email": test_institution_user.email,
        "password": "institution123"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/batches",
        json={
            "name": "Cross Institution Batch",
            "institution_id": test_institution_user.other_institution_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_institution_can_create_batch_for_own_institution(client, test_institution_user):
    login_response = client.post("/auth/login", json={
        "email": test_institution_user.email,
        "password": "institution123"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/batches",
        json={
            "name": "Institution Owned Batch",
            "institution_id": test_institution_user.institution_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["institution_id"] == test_institution_user.institution_id
