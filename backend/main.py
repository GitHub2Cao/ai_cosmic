"""Backend entrypoint — FastAPI app."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth, documents, iterations, projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="COSMIC 智能文档转换平台",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(projects.router, prefix="/api/projects")
app.include_router(iterations.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cosmic-backend", "version": "1.1.0"}


# ------------------------------------------------------------------
# Placeholder routes (to be implemented in Phase 2)
# ------------------------------------------------------------------
@app.get("/api")
def root():
    return {"message": "COSMIC API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
