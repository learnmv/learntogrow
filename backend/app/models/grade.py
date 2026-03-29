from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"))
    display_name = Column(String(50))
    subject = relationship("Subject", backref="grades")
