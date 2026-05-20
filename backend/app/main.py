from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.compare import router as compare_router
from app.api.db_health import router as db_health_router
from app.core.config import settings

app = FastAPI(
    title="판례비교 API",
    description="자연어 사건 설명을 기반으로 기준 판례와 다른 결론의 판례를 비교합니다.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(compare_router, prefix="/api")
app.include_router(db_health_router, prefix="/api")
