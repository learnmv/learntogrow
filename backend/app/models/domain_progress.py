from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DomainProgress(Base):
    """Tracks student performance per domain for adaptive learning."""
    __tablename__ = "domain_progress"
    __table_args__ = (UniqueConstraint('student_id', 'domain_id', name='uq_student_domain'),)

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    total_answered = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    accuracy = Column(Numeric(5, 4), nullable=False, default=0.0)
    current_difficulty = Column(Numeric(3, 2), nullable=False, default=0.5)
    last_answered_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", backref="domain_progress")
    domain = relationship("Domain", backref="student_progress")

    def __repr__(self):
        return (
            f"<DomainProgress(student_id={self.student_id}, domain_id={self.domain_id}, "
            f"accuracy={self.accuracy}, difficulty={self.current_difficulty})>"
        )
