from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    department_router,
    forecast_version_router,
    matter_router,
    member_router,
    project_router,
    workload_router,
)

app = FastAPI(
    title="プロジェクト工数管理システム",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workload_router.router)
app.include_router(matter_router.router)
app.include_router(project_router.router)
app.include_router(department_router.router)
app.include_router(member_router.router)
app.include_router(forecast_version_router.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
