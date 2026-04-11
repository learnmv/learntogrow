from .subjects import router as subjects_router
from .grades import router as grades_router
from .domains import router as domains_router
from .clusters import router as clusters_router
from .standards import router as standards_router
from .questions import router as questions_router
from .auth import router as auth_router
from .parent import router as parent_router
from .admin import router as admin_router

__all__ = [
    "subjects_router",
    "grades_router",
    "domains_router",
    "clusters_router",
    "standards_router",
    "questions_router",
    "auth_router",
    "parent_router",
    "admin_router",
]
