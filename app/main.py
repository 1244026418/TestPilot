from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.database import init_db
from app.routers import ai, auth, dashboard, demo_target, endpoints, projects, runs, testcases


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TestPilot",
    description="AI assisted API test automation platform MVP",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(endpoints.router)
app.include_router(testcases.router)
app.include_router(ai.router)
app.include_router(runs.router)
app.include_router(dashboard.router)
app.include_router(demo_target.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", tags=["system"], response_class=FileResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
