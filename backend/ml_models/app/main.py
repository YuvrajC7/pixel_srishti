"""
Entrypoint. Run with:  uvicorn app.main:app --reload
(or press F5 in VS Code using the pre-configured launch.json)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

app = FastAPI(
    title="SRISHTI-SENTINEL Backend",
    description="Agentic remote-sensing query API — single/cross-modal/bi-temporal imagery.",
    version="0.1.0",
)

# Wide-open CORS for hackathon-stage frontend development.
# TODO: restrict allow_origins to your actual frontend domain before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "SRISHTI-SENTINEL backend is running.", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

