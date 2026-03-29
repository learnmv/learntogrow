from .subjects import router as subjects_router
from .grades import router as grades_router
from .domains import router as domains_router
from .clusters import router as clusters_router
from .standards import router as standards_router
from .questions import router as questions_router

__all__ = [
    "subjects_router",
    "grades_router",
    "domains_router",
    "clusters_router",
    "standards_router",
    "questions_router",
]
