from sqlalchemy import Column, Integer, String, Text, ForeignKey, ARRAY, Numeric, TIMESTAMP
from sqlalchemy.orm import relationship
from app.database import Base

class Standard(Base):
    __tablename__ = "standards"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"))
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"))
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    keywords = Column(ARRAY(String))
    difficulty_base = Column(Numeric(3, 2))
    conceptual_category = Column(String(50))
    created_at = Column(TIMESTAMP)
    cluster = relationship("Cluster", backref="standards")
    grade = relationship("Grade", backref="standards")
    domain = relationship("Domain", backref="standards")
