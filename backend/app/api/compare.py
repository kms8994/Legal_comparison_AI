from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.search.db_compare import build_db_comparison

router = APIRouter(tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
def compare_cases(
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> CompareResponse:
    try:
        return build_db_comparison(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
