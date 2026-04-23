from fastapi import FastAPI
from .database import engine
from . import models
from .routers import oauth, batches, attendance, monitoring, sessions, summaries, institutions


app = FastAPI(title="SkillBridge Attendance API")

models.Base.metadata.create_all(bind=engine)


app.include_router(institutions.router)
app.include_router(oauth.router)
app.include_router(batches.router)
app.include_router(attendance.router)
app.include_router(monitoring.router)
app.include_router(sessions.router)
app.include_router(summaries.router)
