from typing import Literal

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    description: str = Field(..., min_length=2, description="사용자가 입력한 사건번호 또는 자연어 사건 설명")
    query_type: Literal["case_number", "natural_language"] = Field(
        default="natural_language",
        description="사용자 입력 방식",
    )


class PrecedentSummary(BaseModel):
    role: str
    case_number: str
    court: str
    decision_date: str
    outcome: str
    issue_summary: str
    statutes: list[str]
    original_url: str | None = None


class CompareAnalysis(BaseModel):
    key_differences: list[str]
    common_points: list[str]
    short_explanation: str


class CandidateSummary(BaseModel):
    case_number: str
    outcome: str
    issue_summary: str
    reason: str


class ClarificationQuestion(BaseModel):
    slot: str
    label: str
    question: str
    reason: str
    example: str


class ClarificationResponse(BaseModel):
    status: Literal["needs_clarification"] = "needs_clarification"
    query: str
    extracted_facts: dict[str, object]
    questions: list[ClarificationQuestion]
    guidance: str


class InsufficientDataResponse(BaseModel):
    status: Literal["insufficient_data"] = "insufficient_data"
    query: str
    reason: str
    extracted_facts: dict[str, object] | None = None
    suggestions: list[str]


class CompareResponse(BaseModel):
    status: Literal["ready"] = "ready"
    query: str
    reference_case: PrecedentSummary
    opposite_case: PrecedentSummary
    analysis: CompareAnalysis
    other_candidates: list[CandidateSummary]
    disclaimer: str


CompareApiResponse = CompareResponse | ClarificationResponse | InsufficientDataResponse
