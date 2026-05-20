from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.session import engine

router = APIRouter(tags=["database"])


@router.get("/db/health")
def database_health_check() -> dict[str, str]:
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is not configured.",
        )

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {exc}",
        ) from exc

    return {"status": "ok"}
