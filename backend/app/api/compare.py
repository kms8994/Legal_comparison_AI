from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.compare import (
    ClarificationResponse,
    CompareApiResponse,
    CompareRequest,
    InsufficientDataResponse,
)
from app.services.collection_requests import upsert_collection_request
from app.services.search.db_compare import build_db_comparison
from app.services.search.query_slots import (
    build_clarification_questions,
    find_missing_slots,
    safe_extracted_facts,
    should_request_clarification,
    structure_query_once,
    to_search_text,
)

router = APIRouter(tags=["compare"])


@router.post("/compare", response_model=CompareApiResponse)
def compare_cases(
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> CompareApiResponse:
    try:
        extracted_facts = None
        if payload.query_type == "natural_language":
            structured_query = structure_query_once(payload.description)
            extracted_facts = safe_extracted_facts(structured_query)
            missing_slots = find_missing_slots(structured_query)
            if should_request_clarification(structured_query, payload.description):
                return ClarificationResponse(
                    query=payload.description,
                    extracted_facts=extracted_facts,
                    questions=build_clarification_questions(missing_slots),
                    guidance=(
                        "정확한 판례 검색을 위해 부족한 정보만 추가로 확인합니다. "
                        "모르는 내용은 비워두고 아는 사실만 적어도 됩니다."
                    ),
                )
            payload = payload.model_copy(
                update={"description": to_search_text(structured_query, payload.description)}
            )
        return build_db_comparison(db, payload)
    except ValueError as exc:
        upsert_collection_request(
            db,
            query_text=payload.description,
            extracted_facts=extracted_facts,
        )
        db.commit()
        return InsufficientDataResponse(
            query=payload.description,
            reason=str(exc),
            extracted_facts=extracted_facts,
            suggestions=[
                "현재 DB에 저장된 판례가 적어 관련 판례를 안정적으로 찾지 못했습니다.",
                "사건 유형이 드러나는 검색어로 판례를 추가 수집한 뒤 다시 시도해 주세요.",
                "입력한 사실관계와 다른 판례를 억지로 비교하지 않도록 결과 표시를 중단했습니다.",
            ],
        )
