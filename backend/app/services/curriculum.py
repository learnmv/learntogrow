from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Subject, Grade, Domain, Cluster, Standard
from app.schemas import StandardFilter

class CurriculumService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_subjects(self) -> List[Subject]:
        return self.db.query(Subject).all()

    def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        return self.db.query(Subject).filter(Subject.id == subject_id).first()

    def get_grades_by_subject(self, subject_id: int) -> List[Grade]:
        return self.db.query(Grade).filter(Grade.subject_id == subject_id).all()

    def get_grade_by_id(self, grade_id: int) -> Optional[Grade]:
        return self.db.query(Grade).filter(Grade.id == grade_id).first()

    def get_domains_by_grade(self, grade_id: int) -> List[Domain]:
        return self.db.query(Domain).join(Cluster).filter(Cluster.grade_id == grade_id).distinct().all()

    def get_domain_by_id(self, domain_id: int) -> Optional[Domain]:
        return self.db.query(Domain).filter(Domain.id == domain_id).first()

    def get_clusters_by_domain(self, domain_id: int) -> List[Cluster]:
        return self.db.query(Cluster).filter(Cluster.domain_id == domain_id).all()

    def get_clusters_by_grade_and_domain(self, grade_id: int, domain_id: int) -> List[Cluster]:
        return self.db.query(Cluster).filter(
            Cluster.grade_id == grade_id,
            Cluster.domain_id == domain_id
        ).all()

    def get_cluster_by_id(self, cluster_id: int) -> Optional[Cluster]:
        return self.db.query(Cluster).filter(Cluster.id == cluster_id).first()

    def get_standards_by_cluster(self, cluster_id: int) -> List[Standard]:
        return self.db.query(Standard).filter(Standard.cluster_id == cluster_id).all()

    def get_standards_by_grade(self, grade_id: int) -> List[Standard]:
        return self.db.query(Standard).filter(Standard.grade_id == grade_id).all()

    def get_standards_by_domain(self, domain_id: int) -> List[Standard]:
        return self.db.query(Standard).filter(Standard.domain_id == domain_id).all()

    def get_standards(self, filters: StandardFilter, skip: int = 0, limit: int = 100) -> List[Standard]:
        query = self.db.query(Standard)

        if filters.grade_id:
            query = query.filter(Standard.grade_id == filters.grade_id)
        if filters.domain_id:
            query = query.filter(Standard.domain_id == filters.domain_id)
        if filters.cluster_id:
            query = query.filter(Standard.cluster_id == filters.cluster_id)
        if filters.min_difficulty is not None:
            query = query.filter(Standard.difficulty_base >= filters.min_difficulty)
        if filters.max_difficulty is not None:
            query = query.filter(Standard.difficulty_base <= filters.max_difficulty)

        return query.offset(skip).limit(limit).all()

    def get_standard_by_id(self, standard_id: int) -> Optional[Standard]:
        return self.db.query(Standard).filter(Standard.id == standard_id).first()

    def get_by_difficulty_range(self, min_diff: float, max_diff: float) -> List[Standard]:
        return self.db.query(Standard).filter(
            and_(
                Standard.difficulty_base >= min_diff,
                Standard.difficulty_base <= max_diff
            )
        ).all()

    def get_full_curriculum_path(self, standard_id: int) -> Optional[dict]:
        standard = self.get_standard_by_id(standard_id)
        if not standard:
            return None

        return {
            "standard": standard,
            "cluster": standard.cluster,
            "domain": standard.domain,
            "grade": standard.grade,
            "subject": standard.grade.subject if standard.grade else None
        }
