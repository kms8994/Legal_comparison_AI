from fastapi import APIRouter

from app.schemas.compare import CompareRequest, CompareResponse
from app.services.search.mock_compare import build_mock_comparison

router = APIRouter(tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
def compare_cases(payload: CompareRequest) -> CompareResponse:
    return build_mock_comparison(payload)
