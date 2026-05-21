from pydantic import BaseModel, Field


class PrecedentStructureResult(BaseModel):
    issue_summary: str | None = Field(default=None, description="판례의 핵심 쟁점")
    fact_summary: str | None = Field(default=None, description="판례의 핵심 사실관계")
    legal_question: str | None = Field(default=None, description="법원이 판단한 법적 질문")
    holding_label: str | None = Field(default=None, description="결론 라벨")
    holding_summary: str | None = Field(default=None, description="법원의 결론 요약")
    reasoning_summary: str | None = Field(default=None, description="판단 이유 요약")
    key_facts: list[str] = Field(default_factory=list, description="결론에 영향을 준 핵심 사실")
    distinguishing_facts: list[str] = Field(
        default_factory=list,
        description="다른 결론과 구별될 수 있는 사실",
    )
    referenced_statutes: list[str] = Field(default_factory=list, description="참조 조문")
    referenced_precedents: list[str] = Field(default_factory=list, description="참조 판례")
    confidence_score: float = Field(default=0.5, ge=0, le=1)


class QueryStructureResult(BaseModel):
    domain: str | None = Field(default=None, description="민사, 형사, 행정 등 법영역")
    case_type: str | None = Field(default=None, description="사건 유형")
    legal_issue: str | None = Field(default=None, description="사용자 입력의 핵심 법적 쟁점")
    fact_pattern: str = Field(description="검색에 사용할 사실관계 요약")
    key_facts: list[str] = Field(default_factory=list, description="검색에 중요한 핵심 사실")
    parties: list[str] = Field(default_factory=list, description="사건의 주요 당사자")
    disputed_action: str | None = Field(default=None, description="문제가 된 행위 또는 처분")
    claimed_damage_or_result: str | None = Field(
        default=None,
        description="발생한 손해, 처분, 결과",
    )
    user_wants: str | None = Field(default=None, description="사용자가 알고 싶은 비교 방향")
    desired_comparison: str | None = Field(
        default=None,
        description="찾고 싶은 비교 방향",
    )
