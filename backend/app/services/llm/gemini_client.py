from __future__ import annotations

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.llm import PrecedentStructureResult, QueryStructureResult


class GeminiLlmClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY 환경변수를 설정해 주세요.")
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def structure_precedent(
        self,
        *,
        case_number: str,
        case_name: str | None,
        court_name: str | None,
        raw_text: str,
    ) -> PrecedentStructureResult:
        prompt = _build_precedent_prompt(
            case_number=case_number,
            case_name=case_name,
            court_name=court_name,
            raw_text=raw_text,
        )
        response = self.client.models.generate_content(
            model=settings.llm_structure_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PrecedentStructureResult,
            ),
        )
        return PrecedentStructureResult.model_validate_json(response.text)

    def structure_query(self, description: str) -> QueryStructureResult:
        prompt = _build_query_prompt(description)
        response = self.client.models.generate_content(
            model=settings.llm_query_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QueryStructureResult,
            ),
        )
        return QueryStructureResult.model_validate_json(response.text)


def _build_precedent_prompt(
    *,
    case_number: str,
    case_name: str | None,
    court_name: str | None,
    raw_text: str,
) -> str:
    clipped_text = raw_text[:20000]
    return f"""
너는 한국 판례 데이터를 검색 가능한 구조로 정리하는 보조 시스템이다.
아래 원문에 근거가 있는 내용만 JSON으로 추출하라.

규칙:
- 원문에 없는 사실을 추가하지 않는다.
- 불명확한 내용은 추측하지 말고 null 또는 빈 배열로 둔다.
- 법률 조언을 하지 않는다.
- holding_label은 가능하면 인용, 기각, 파기, 유죄, 무죄, 일부인용, 각하, 기타 중 하나로 쓴다.
- key_facts와 distinguishing_facts는 짧은 문장 배열로 작성한다.
- referenced_statutes와 referenced_precedents는 원문에 명시된 것만 넣는다.

사건번호: {case_number}
사건명: {case_name or ""}
법원명: {court_name or ""}

판례 원문:
{clipped_text}
""".strip()


def _build_query_prompt(description: str) -> str:
    return f"""
너는 사용자의 자연어 사건 설명을 판례 검색용 슬롯 JSON으로 정리하는 보조 시스템이다.

역할 제한:
- 최종 법률 답변을 생성하지 않는다.
- 판례를 추측하거나 사건명을 만들어내지 않는다.
- 사용자 설명에 없는 사실, 손해, 당사자, 쟁점을 보충하지 않는다.
- 애매한 내용은 null 또는 빈 배열로 둔다.
- key_facts는 사용자 설명에 직접 드러난 사실만 짧게 나열한다.
- parties는 명시된 당사자만 쓴다. 추정하지 않는다.
- legal_issue는 사용자가 명시했거나 문장상 거의 직접 드러난 질문만 쓴다.
- desired_comparison/user_wants는 사용자가 원하는 비교 방향이 드러날 때만 쓴다.

추출해야 하는 슬롯:
- domain: 민사/형사/행정 등. 불명확하면 null.
- case_type: 교통사고, 손해배상, 임대차, 해고 등. 불명확하면 null.
- legal_issue: 사용자가 궁금해하는 핵심 법적 쟁점.
- fact_pattern: 사용자가 말한 사실관계만 요약.
- key_facts: 검색에 중요한 사실 배열.
- parties: 당사자 배열.
- disputed_action: 문제가 된 행위나 처분.
- claimed_damage_or_result: 손해, 처분, 사고 결과.
- user_wants: 사용자가 알고 싶은 것.
- desired_comparison: 찾고 싶은 판례 비교 방향.

사용자 설명:
{description}
""".strip()
