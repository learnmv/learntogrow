from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(Text, nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"))
    domain = relationship("Domain", backref="clusters")
    grade = relationship("Grade", backref="clusters")
