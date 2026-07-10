from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import FRONTEND_DIST
from app.database import init_db
from app.routers import ai, auth, dashboard, demo_target, endpoints, imports, projects, runs, testcases


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TestPilot API",
    description="AI 辅助接口自动化测试平台",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, projects.router, endpoints.router, testcases.router, ai.router, runs.router, dashboard.router, imports.router):
    app.include_router(router, prefix="/api")
app.include_router(demo_target.router)


@app.get("/api/health", tags=["system"])
def api_health():
    return {"status": "ok"}


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


def _frontend_response(path: str = "index.html"):
    candidate = (FRONTEND_DIST / path).resolve()
    dist_root = FRONTEND_DIST.resolve()
    if candidate.is_file() and (candidate == dist_root or dist_root in candidate.parents):
        return FileResponse(candidate)
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        {
            "name": "TestPilot",
            "message": "Vue 前端尚未构建。开发模式请运行 npm run dev，生产模式请运行 npm run build。",
            "api_docs": "/docs",
        }
    )


@app.get("/", include_in_schema=False)
def index():
    return _frontend_response()


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "demo-target/")):
        raise HTTPException(status_code=404, detail="not found")
    return _frontend_response(full_path)
