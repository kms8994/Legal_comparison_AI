from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.schemas.compare import ClarificationQuestion
from app.schemas.llm import QueryStructureResult
from app.services.llm.gemini_client import GeminiLlmClient


@dataclass(frozen=True)
class RequiredSlot:
    key: str
    label: str
    question: str
    reason: str
    example: str


REQUIRED_SLOTS = [
    RequiredSlot(
        key="fact_pattern",
        label="사실관계",
        question="무슨 일이 있었는지 시간 순서대로 한두 문장으로 더 적어주세요.",
        reason="판례 검색은 비슷한 사실관계를 먼저 좁혀야 정확도가 올라갑니다.",
        example="예: 신호 없는 교차로에서 좌회전 차량과 직진 차량이 충돌했습니다.",
    ),
    RequiredSlot(
        key="parties",
        label="당사자",
        question="누구와 누구 사이의 분쟁인지 알려주세요.",
        reason="당사자 관계가 같아야 같은 유형의 판례를 우선 찾을 수 있습니다.",
        example="예: 임차인과 임대인, 운전자 A와 운전자 B, 근로자와 회사",
    ),
    RequiredSlot(
        key="disputed_action",
        label="문제가 된 행위",
        question="어떤 행위나 결정이 문제인지 알려주세요.",
        reason="법원이 판단한 핵심 행위를 알아야 쟁점이 비슷한 판례를 찾을 수 있습니다.",
        example="예: 계약 해지, 해고 통보, 좌회전 진입, 과속, 처분 취소",
    ),
    RequiredSlot(
        key="claimed_damage_or_result",
        label="결과 또는 손해",
        question="그 행위 때문에 어떤 결과나 손해가 발생했는지 알려주세요.",
        reason="손해나 결과는 결론이 달라지는 핵심 구별 요소가 될 수 있습니다.",
        example="예: 차량 파손과 치료비 발생, 보증금 미반환, 해고, 과징금 부과",
    ),
    RequiredSlot(
        key="legal_issue",
        label="궁금한 쟁점",
        question="무엇이 궁금한지 적어주세요. 책임 여부, 과실 비율, 계약 해제 가능성처럼 써도 됩니다.",
        reason="사용자의 관심 쟁점과 같은 법적 질문을 다룬 판례를 우선 검색합니다.",
        example="예: 좌회전 차량의 과실이 더 큰지, 회사의 해고가 정당한지",
    ),
]

MAX_CLARIFICATION_QUESTIONS = 3


def structure_query_once(description: str) -> QueryStructureResult:
    return GeminiLlmClient().structure_query(description)


def find_missing_slots(structured: QueryStructureResult) -> list[RequiredSlot]:
    return [slot for slot in REQUIRED_SLOTS if not _has_slot_value(structured, slot.key)]


def build_clarification_questions(
    missing_slots: list[RequiredSlot],
) -> list[ClarificationQuestion]:
    return [
        ClarificationQuestion(
            slot=slot.key,
            label=slot.label,
            question=slot.question,
            reason=slot.reason,
            example=slot.example,
        )
        for slot in missing_slots[:MAX_CLARIFICATION_QUESTIONS]
    ]


def should_request_clarification(
    structured: QueryStructureResult,
    description: str,
) -> bool:
    if len(description.strip()) < 15:
        return True
    missing = find_missing_slots(structured)
    return len(missing) >= 2


def to_search_text(structured: QueryStructureResult, fallback: str) -> str:
    parts = [
        structured.domain,
        structured.case_type,
        structured.legal_issue,
        structured.fact_pattern,
        " ".join(structured.key_facts),
        " ".join(structured.parties),
        structured.disputed_action,
        structured.claimed_damage_or_result,
        structured.user_wants,
        structured.desired_comparison,
    ]
    text = "\n".join(part for part in parts if part)
    return text or fallback


def safe_extracted_facts(structured: QueryStructureResult) -> dict[str, object]:
    data = structured.model_dump()
    return {
        key: value
        for key, value in data.items()
        if _value_present(value)
    }


def _has_slot_value(structured: QueryStructureResult, key: str) -> bool:
    return _value_present(getattr(structured, key))


def _value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and stripped not in {"불명확", "원문상 불명확", "알 수 없음"}
    if isinstance(value, list):
        return any(_value_present(item) for item in value)
    return True
