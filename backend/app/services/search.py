from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models import Standard

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_standards(self, query: str) -> List[Standard]:
        search_pattern = f"%{query}%"
        return self.db.query(Standard).filter(
            or_(
                Standard.code.ilike(search_pattern),
                Standard.description.ilike(search_pattern),
                Standard.keywords.any(query)
            )
        ).all()

    def search_by_keywords(self, keywords: List[str]) -> List[Standard]:
        results = set()
        for keyword in keywords:
            standards = self.db.query(Standard).filter(
                Standard.keywords.any(keyword)
            ).all()
            results.update(standards)
        return list(results)
