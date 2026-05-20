from app.schemas.compare import (
    CandidateSummary,
    CompareAnalysis,
    CompareRequest,
    CompareResponse,
    PrecedentSummary,
)


def build_mock_comparison(payload: CompareRequest) -> CompareResponse:
    """Temporary response boundary until the collection/search pipeline is connected."""
    reference_case = PrecedentSummary(
        role="기준 판례",
        case_number="대법원 2019다12345",
        court="대법원",
        decision_date="2019.06.27",
        outcome="인용",
        issue_summary="신호 없는 교차로에서 직진 차량과 좌회전 차량이 충돌한 사고에서 직진 차량의 과실 범위가 문제된 사건",
        statutes=["도로교통법 제25조", "도로교통법 제27조", "민법 제750조"],
        original_url=None,
    )
    opposite_case = PrecedentSummary(
        role="반대 결론 판례",
        case_number="대법원 2018다23456",
        court="대법원",
        decision_date="2018.08.13",
        outcome="기각",
        issue_summary="교차로에서 좌회전 차량과 직진 차량이 충돌한 사고에서 좌회전 차량의 과실이 더 크다고 본 사건",
        statutes=["도로교통법 제25조", "도로교통법 제27조", "민법 제750조"],
        original_url=None,
    )
    analysis = CompareAnalysis(
        key_differences=[
            "기준 판례는 직진 차량의 과속과 주의의무 위반을 더 크게 보았습니다.",
            "반대 결론 판례는 좌회전 차량의 진입 방식과 확인 의무 위반을 더 크게 보았습니다.",
        ],
        common_points=[
            "두 판례 모두 신호 없는 교차로에서 발생한 충돌 사고입니다.",
            "두 판례 모두 교차로 통행 방법과 운전자의 주의의무가 문제되었습니다.",
            "도로교통법과 민법상 손해배상 책임이 함께 검토되었습니다.",
        ],
        short_explanation=(
            "두 판례는 사고 유형과 적용 조문이 유사하지만, 법원이 더 중요하게 본 "
            "주의의무 위반 주체가 달라 최종 결론이 달라졌습니다."
        ),
    )
    candidates = [
        CandidateSummary(
            case_number="대법원 2021다56789",
            outcome="인용",
            issue_summary="교차로 충돌 사고에서 직진 차량의 과속 여부가 문제된 사건",
            reason="같은 조문 · 유사한 쟁점",
        ),
        CandidateSummary(
            case_number="서울고등법원 2020나34567",
            outcome="인용",
            issue_summary="좌회전 차량과 직진 차량의 통행 우선순위가 문제된 사건",
            reason="같은 조문 · 사고 유형 유사",
        ),
    ]

    return CompareResponse(
        query=payload.description,
        reference_case=reference_case,
        opposite_case=opposite_case,
        analysis=analysis,
        other_candidates=candidates,
        disclaimer="본 비교 설명은 AI가 생성한 학습 보조 정보입니다. 실제 판단 전 원문을 반드시 확인해 주세요.",
    )
