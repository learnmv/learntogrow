from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services import CurriculumService

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_curriculum_service(db: Session = Depends(get_db)):
    return CurriculumService(db)
