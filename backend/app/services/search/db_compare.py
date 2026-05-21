from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.compare import (
    CandidateSummary,
    CompareAnalysis,
    CompareRequest,
    CompareResponse,
    PrecedentSummary,
)

MIN_REFERENCE_SCORE = 2
MIN_OPPOSITE_SCORE = 2
MIN_SEARCHABLE_PRECEDENTS = 2


@dataclass(frozen=True)
class SearchablePrecedent:
    id: UUID
    case_number: str
    court: str
    decision_date: str
    outcome: str
    issue_summary: str
    fact_summary: str
    statutes: list[str]
    original_url: str | None
    case_type: str | None
    domain: str | None


def build_db_comparison(db: Session, payload: CompareRequest) -> CompareResponse:
    precedents = _load_searchable_precedents(db)
    if len(precedents) < MIN_SEARCHABLE_PRECEDENTS:
        raise ValueError("검색 가능한 판례 데이터가 충분하지 않습니다.")

    reference_case = _select_reference_case(
        precedents,
        payload.description,
        payload.query_type,
    )
    opposite_case = _select_opposite_case(precedents, reference_case)
    candidates = _select_other_candidates(precedents, reference_case, opposite_case)

    return CompareResponse(
        query=payload.description,
        reference_case=_to_precedent_summary("기준 판례", reference_case),
        opposite_case=_to_precedent_summary("유사하지만 결론이 다른 판례", opposite_case),
        analysis=_build_analysis(reference_case, opposite_case),
        other_candidates=[
            CandidateSummary(
                case_number=candidate.case_number,
                outcome=candidate.outcome,
                issue_summary=candidate.issue_summary,
                reason=_candidate_reason(reference_case, candidate),
            )
            for candidate in candidates
        ],
        disclaimer=(
            "이 비교 설명은 DB에 저장된 구조화 데이터를 기반으로 만든 학습 보조 정보입니다. "
            "실제 판단 전에는 반드시 원문을 확인하세요."
        ),
    )


def _load_searchable_precedents(db: Session) -> list[SearchablePrecedent]:
    rows = db.execute(
        text(
            """
            select
                p.id,
                p.case_number,
                coalesce(p.court_name, '') as court,
                to_char(p.decision_date, 'YYYY.MM.DD') as decision_date,
                p.source_url,
                p.case_type,
                p.domain,
                coalesce(ps.issue_summary, '') as issue_summary,
                coalesce(ps.fact_summary, '') as fact_summary,
                coalesce(ps.holding_label, '미분류') as outcome,
                ps.referenced_statutes
            from precedents p
            join precedent_structures ps on ps.precedent_id = p.id
            where ps.review_status in ('reviewed', 'unreviewed')
            order by p.decision_date desc nulls last
            """
        )
    ).mappings()

    return [
        SearchablePrecedent(
            id=row["id"],
            case_number=row["case_number"],
            court=row["court"],
            decision_date=row["decision_date"] or "",
            outcome=row["outcome"],
            issue_summary=row["issue_summary"],
            fact_summary=row["fact_summary"],
            statutes=_coerce_statutes(row["referenced_statutes"]),
            original_url=row["source_url"],
            case_type=row["case_type"],
            domain=row["domain"],
        )
        for row in rows
    ]


def _select_reference_case(
    precedents: list[SearchablePrecedent],
    description: str,
    query_type: str,
) -> SearchablePrecedent:
    normalized_description = _normalize_text(description)

    exact_case = _find_case_number(precedents, normalized_description)
    if exact_case is not None:
        return exact_case

    if query_type == "case_number":
        raise ValueError("사건번호에 해당하는 판례를 찾지 못했습니다.")

    scored = [
        (_text_score(description, precedent), precedent)
        for precedent in precedents
    ]
    best_score, best_precedent = max(scored, key=lambda item: (item[0], item[1].decision_date))
    if best_score < MIN_REFERENCE_SCORE:
        raise ValueError("입력한 사건과 관련 있는 판례 데이터가 아직 충분하지 않습니다.")
    return best_precedent


def _find_case_number(
    precedents: list[SearchablePrecedent],
    normalized_query: str,
) -> SearchablePrecedent | None:
    for precedent in precedents:
        if _normalize_text(precedent.case_number) in normalized_query:
            return precedent
    return None


def _select_opposite_case(
    precedents: list[SearchablePrecedent],
    reference_case: SearchablePrecedent,
) -> SearchablePrecedent:
    opposite_candidates = [
        precedent
        for precedent in precedents
        if precedent.id != reference_case.id and precedent.outcome != reference_case.outcome
    ]
    if not opposite_candidates:
        raise ValueError("유사하지만 결론이 다른 판례를 찾지 못했습니다.")

    scored = [
        (_similarity_score(reference_case, precedent), precedent)
        for precedent in opposite_candidates
    ]
    best_score, best_precedent = max(scored, key=lambda item: item[0])
    if best_score < MIN_OPPOSITE_SCORE:
        raise ValueError("유사하지만 결론이 다른 판례 데이터가 아직 충분하지 않습니다.")
    return best_precedent


def _select_other_candidates(
    precedents: list[SearchablePrecedent],
    reference_case: SearchablePrecedent,
    opposite_case: SearchablePrecedent,
) -> list[SearchablePrecedent]:
    excluded_ids = {reference_case.id, opposite_case.id}
    candidates = [precedent for precedent in precedents if precedent.id not in excluded_ids]
    return sorted(
        candidates,
        key=lambda precedent: _similarity_score(reference_case, precedent),
        reverse=True,
    )[:3]


def _to_precedent_summary(role: str, precedent: SearchablePrecedent) -> PrecedentSummary:
    return PrecedentSummary(
        role=role,
        case_number=precedent.case_number,
        court=precedent.court,
        decision_date=precedent.decision_date,
        outcome=precedent.outcome,
        issue_summary=precedent.issue_summary,
        statutes=precedent.statutes,
        original_url=precedent.original_url,
    )


def _build_analysis(
    reference_case: SearchablePrecedent,
    opposite_case: SearchablePrecedent,
) -> CompareAnalysis:
    common_points = []
    if reference_case.domain and reference_case.domain == opposite_case.domain:
        common_points.append(f"두 판례 모두 {reference_case.domain} 영역의 사건입니다.")
    if reference_case.case_type and reference_case.case_type == opposite_case.case_type:
        common_points.append(f"두 판례 모두 {reference_case.case_type} 유형의 사건입니다.")

    shared_statutes = sorted(set(reference_case.statutes) & set(opposite_case.statutes))
    if shared_statutes:
        common_points.append(f"공통 참조조문은 {', '.join(shared_statutes)}입니다.")

    if not common_points:
        common_points.append("두 판례는 저장된 쟁점 요약과 사실관계 요약을 기준으로 함께 비교되었습니다.")

    return CompareAnalysis(
        key_differences=[
            f"{reference_case.case_number}의 결론 라벨은 '{reference_case.outcome}'입니다.",
            f"{opposite_case.case_number}의 결론 라벨은 '{opposite_case.outcome}'입니다.",
            f"기준 판례의 사실관계 요약: {reference_case.fact_summary}",
            f"비교 판례의 사실관계 요약: {opposite_case.fact_summary}",
        ],
        common_points=common_points,
        short_explanation=(
            "두 판례는 사건 유형과 참조조문이 비슷하지만, 저장된 판결 결과 라벨이 달라 "
            "유사하지만 결론이 다른 판례로 함께 제시되었습니다."
        ),
    )


def _candidate_reason(
    reference_case: SearchablePrecedent,
    candidate: SearchablePrecedent,
) -> str:
    reasons = []
    if reference_case.case_type and reference_case.case_type == candidate.case_type:
        reasons.append("같은 사건유형")
    if reference_case.domain and reference_case.domain == candidate.domain:
        reasons.append("같은 법영역")
    if set(reference_case.statutes) & set(candidate.statutes):
        reasons.append("공통 참조조문")
    return ", ".join(reasons) if reasons else "구조화 데이터 기준 관련 후보"


def _similarity_score(
    reference_case: SearchablePrecedent,
    candidate: SearchablePrecedent,
) -> int:
    score = 0
    if reference_case.case_type and reference_case.case_type == candidate.case_type:
        score += 5
    if reference_case.domain and reference_case.domain == candidate.domain:
        score += 3
    score += len(set(reference_case.statutes) & set(candidate.statutes)) * 2
    score += len(_tokenize(reference_case.issue_summary) & _tokenize(candidate.issue_summary))
    score += len(_tokenize(reference_case.fact_summary) & _tokenize(candidate.fact_summary))
    return score


def _text_score(description: str, precedent: SearchablePrecedent) -> int:
    query_tokens = _tokenize(description)
    searchable_text = " ".join(
        [
            precedent.case_number,
            precedent.case_type or "",
            precedent.domain or "",
            precedent.issue_summary,
            precedent.fact_summary,
            " ".join(precedent.statutes),
        ]
    )
    target_tokens = _tokenize(searchable_text)
    return len(query_tokens & target_tokens)


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[0-9A-Za-z가-힣]+", value.lower())
        if len(token) >= 2
    }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _coerce_statutes(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
