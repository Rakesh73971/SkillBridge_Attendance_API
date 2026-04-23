from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from src.database import SessionLocal, engine
from src import models, utils
from src.models import Base

def seed_database():
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        
        if db.query(models.Institution).first():
            print("Database already seeded. Skipping...")
            return

        print("Starting database seed...")

        
        print("Creating institutions...")
        inst1 = models.Institution(name="Northern Tech Institute", region="North")
        inst2 = models.Institution(name="Southern Skills Academy", region="South")
        db.add_all([inst1, inst2])
        db.commit()
        db.refresh(inst1)
        db.refresh(inst2)
        print(f"Created 2 institutions: {inst1.name}, {inst2.name}")

        
        print("\nCreating users...")
        
        
        trainer_pwd = utils.hash_password("trainer123")
        student_pwd = utils.hash_password("student123")
        institution_pwd = utils.hash_password("institution123")
        prog_mgr_pwd = utils.hash_password("progmgr123")
        monitor_pwd = utils.hash_password("monitor123")

        
        inst_user1 = models.User(
            name="Alice Institution",
            email="alice.institution@example.com",
            hashed_password=institution_pwd,
            role=models.RoleEnum.INSTITUTION,
            institution_id=inst1.id
        )
        inst_user2 = models.User(
            name="Bob Institution",
            email="bob.institution@example.com",
            hashed_password=institution_pwd,
            role=models.RoleEnum.INSTITUTION,
            institution_id=inst2.id
        )

        
        trainer1 = models.User(
            name="John Trainer",
            email="john.trainer@example.com",
            hashed_password=trainer_pwd,
            role=models.RoleEnum.TRAINER,
            institution_id=inst1.id
        )
        trainer2 = models.User(
            name="Jane Trainer",
            email="jane.trainer@example.com",
            hashed_password=trainer_pwd,
            role=models.RoleEnum.TRAINER,
            institution_id=inst1.id
        )
        trainer3 = models.User(
            name="Mike Trainer",
            email="mike.trainer@example.com",
            hashed_password=trainer_pwd,
            role=models.RoleEnum.TRAINER,
            institution_id=inst2.id
        )
        trainer4 = models.User(
            name="Sarah Trainer",
            email="sarah.trainer@example.com",
            hashed_password=trainer_pwd,
            role=models.RoleEnum.TRAINER,
            institution_id=inst2.id
        )

        
        students = []
        for i in range(15):
            student = models.User(
                name=f"Student {i+1}",
                email=f"student{i+1}@example.com",
                hashed_password=student_pwd,
                role=models.RoleEnum.STUDENT,
                institution_id=inst1.id if i < 8 else inst2.id
            )
            students.append(student)
        
        prog_mgr = models.User(
            name="Carol Programme Manager",
            email="carol.progmgr@example.com",
            hashed_password=prog_mgr_pwd,
            role=models.RoleEnum.PROGRAMME_MANAGER,
            institution_id=inst1.id
        )

        
        monitor = models.User(
            name="David Monitor",
            email="david.monitor@example.com",
            hashed_password=monitor_pwd,
            role=models.RoleEnum.MONITORING_OFFICER,
            institution_id=None
        )

        db.add_all([inst_user1, inst_user2, trainer1, trainer2, trainer3, trainer4, prog_mgr, monitor] + students)
        db.commit()
        
        for student in students:
            db.refresh(student)
        db.refresh(trainer1)
        db.refresh(trainer2)
        db.refresh(trainer3)
        db.refresh(trainer4)

        print(f" Created 2 institution users")
        print(f" Created 4 trainers")
        print(f" Created 15 students")
        print(f" Created 1 programme manager")
        print(f" Created 1 monitoring officer")

        
        print("\nCreating batches...")
        batch1 = models.Batch(name="Python for Beginners", institution_id=inst1.id)
        batch2 = models.Batch(name="Advanced Web Development", institution_id=inst1.id)
        batch3 = models.Batch(name="Data Science 101", institution_id=inst2.id)
        
        db.add_all([batch1, batch2, batch3])
        db.commit()
        db.refresh(batch1)
        db.refresh(batch2)
        db.refresh(batch3)
        print(f" Created 3 batches")

        
        print("\nAssigning trainers to batches...")
        bt1 = models.BatchTrainer(batch_id=batch1.id, trainer_id=trainer1.id)
        bt2 = models.BatchTrainer(batch_id=batch1.id, trainer_id=trainer2.id)
        bt3 = models.BatchTrainer(batch_id=batch2.id, trainer_id=trainer2.id)
        bt4 = models.BatchTrainer(batch_id=batch3.id, trainer_id=trainer3.id)
        bt5 = models.BatchTrainer(batch_id=batch3.id, trainer_id=trainer4.id)
        
        db.add_all([bt1, bt2, bt3, bt4, bt5])
        db.commit()
        print(f"Assigned trainers to batches")

        
        print("\nEnrolling students in batches...")
        for i, student in enumerate(students[:8]):
            bs = models.BatchStudent(batch_id=batch1.id, student_id=student.id)
            db.add(bs)
        for i, student in enumerate(students[3:10]):
            bs = models.BatchStudent(batch_id=batch2.id, student_id=student.id)
            db.add(bs)
        for i, student in enumerate(students[7:]):
            bs = models.BatchStudent(batch_id=batch3.id, student_id=student.id)
            db.add(bs)
        db.commit()
        print(f" Enrolled students in batches")

        
        print("\nCreating sessions with attendance records...")
        now = datetime.now(timezone.utc)
        
        sessions_data = [
            {
                "batch_id": batch1.id,
                "trainer_id": trainer1.id,
                "title": "Introduction to Python",
                "date": (now - timedelta(days=2)).date(),
                "start_time": "09:00:00",
                "end_time": "11:00:00"
            },
            {
                "batch_id": batch1.id,
                "trainer_id": trainer2.id,
                "title": "Python Variables and Data Types",
                "date": (now - timedelta(days=1)).date(),
                "start_time": "10:00:00",
                "end_time": "12:00:00"
            },
            {
                "batch_id": batch2.id,
                "trainer_id": trainer2.id,
                "title": "Django Basics",
                "date": (now - timedelta(days=3)).date(),
                "start_time": "14:00:00",
                "end_time": "16:00:00"
            },
            {
                "batch_id": batch2.id,
                "trainer_id": trainer2.id,
                "title": "Django Models",
                "date": (now - timedelta(days=1)).date(),
                "start_time": "14:00:00",
                "end_time": "16:00:00"
            },
            {
                "batch_id": batch3.id,
                "trainer_id": trainer3.id,
                "title": "Introduction to Data Science",
                "date": (now - timedelta(days=5)).date(),
                "start_time": "09:00:00",
                "end_time": "11:00:00"
            },
            {
                "batch_id": batch3.id,
                "trainer_id": trainer4.id,
                "title": "Pandas and NumPy",
                "date": (now - timedelta(days=4)).date(),
                "start_time": "10:00:00",
                "end_time": "12:00:00"
            },
            {
                "batch_id": batch1.id,
                "trainer_id": trainer1.id,
                "title": "Python Functions",
                "date": now.date(),
                "start_time": "09:00:00",
                "end_time": "11:00:00"
            },
            {
                "batch_id": batch3.id,
                "trainer_id": trainer3.id,
                "title": "Data Visualization",
                "date": now.date(),
                "start_time": "14:00:00",
                "end_time": "16:00:00"
            },
        ]

        sessions = []
        for session_data in sessions_data:
            session = models.Session(
                batch_id=session_data["batch_id"],
                trainer_id=session_data["trainer_id"],
                title=session_data["title"],
                date=session_data["date"],
                start_time=session_data["start_time"],
                end_time=session_data["end_time"]
            )
            db.add(session)
            sessions.append(session)
        db.commit()
        
        for session in sessions:
            db.refresh(session)
        print(f"Created 8 sessions")

        
        print("\nMarking attendance...")
        import random
        
    
        batch1_students = db.query(models.BatchStudent.student_id).filter(models.BatchStudent.batch_id == batch1.id).all()
        batch2_students = db.query(models.BatchStudent.student_id).filter(models.BatchStudent.batch_id == batch2.id).all()
        batch3_students = db.query(models.BatchStudent.student_id).filter(models.BatchStudent.batch_id == batch3.id).all()

        attendance_count = 0
        for i, session in enumerate(sessions):
            if session.batch_id == batch1.id:
                student_ids = [s[0] for s in batch1_students]
            elif session.batch_id == batch2.id:
                student_ids = [s[0] for s in batch2_students]
            else:
                student_ids = [s[0] for s in batch3_students]

            for student_id in student_ids:
                status = random.choice([
                    models.AttendanceStatusEnum.PRESENT,
                    models.AttendanceStatusEnum.PRESENT,
                    models.AttendanceStatusEnum.ABSENT,
                    models.AttendanceStatusEnum.LATE
                ])
                attendance = models.Attendance(
                    session_id=session.id,
                    student_id=student_id,
                    status=status
                )
                db.add(attendance)
                attendance_count += 1
        
        db.commit()
        print(f" Created {attendance_count} attendance records")

        print("\n" + "="*50)
        print(" Database seeding completed successfully!")
        print("="*50)
        print("\nTest Accounts:")
        print("=" * 50)
        print("STUDENT: student1@example.com / student123")
        print("TRAINER: john.trainer@example.com / trainer123")
        print("INSTITUTION: alice.institution@example.com / institution123")
        print("PROGRAMME_MANAGER: carol.progmgr@example.com / progmgr123")
        print("MONITORING_OFFICER: david.monitor@example.com / monitor123")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f" Error during seeding: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
