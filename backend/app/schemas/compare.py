from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    description: str = Field(..., min_length=5, description="사용자가 입력한 자연어 사건 설명")


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


class CompareResponse(BaseModel):
    query: str
    reference_case: PrecedentSummary
    opposite_case: PrecedentSummary
    analysis: CompareAnalysis
    other_candidates: list[CandidateSummary]
    disclaimer: str
