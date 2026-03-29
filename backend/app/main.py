import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    subjects_router,
    grades_router,
    domains_router,
    clusters_router,
    standards_router,
    questions_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LearnToGrow API",
    version="1.0.0",
    description="API for accessing California Common Core curriculum standards"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subjects_router, prefix="/api/v1")
app.include_router(grades_router, prefix="/api/v1")
app.include_router(domains_router, prefix="/api/v1")
app.include_router(clusters_router, prefix="/api/v1")
app.include_router(standards_router, prefix="/api/v1")
app.include_router(questions_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "name": "LearnToGrow API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting LearnToGrow API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
