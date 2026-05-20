from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class NormalizedPrecedent:
    case_number: str
    court_name: str | None
    decision_date: date | None
    case_name: str | None
    case_type: str | None
    domain: str | None
    raw_text: str
    source_url: str | None
    issue_summary: str | None
    fact_summary: str | None
    holding_label: str | None
    referenced_statutes: list[str]
    referenced_precedents: list[str]


def normalize_precedent_detail(payload: dict[str, Any]) -> NormalizedPrecedent:
    detail = _find_detail(payload)

    case_number = _text(_pick(detail, "사건번호", "caseNumber"))
    case_name = _optional_text(_pick(detail, "사건명", "caseName"))
    court_name = _optional_text(_pick(detail, "법원명", "courtName"))
    decision_date = _parse_date(_pick(detail, "선고일자", "decisionDate"))
    case_type = _optional_text(_pick(detail, "사건종류명", "caseType"))
    raw_text = _clean_text(_pick(detail, "판례내용", "내용", "precContent") or "")
    issue_summary = _clean_text(_pick(detail, "판시사항", "issue") or "") or None
    judgment_summary = _clean_text(_pick(detail, "판결요지", "summary") or "")

    fact_summary = _summarize_fact(raw_text, judgment_summary)
    referenced_statutes = _split_references(_pick(detail, "참조조문", "statutes"))
    referenced_precedents = _split_references(_pick(detail, "참조판례", "referencedPrecedents"))

    return NormalizedPrecedent(
        case_number=case_number,
        court_name=court_name,
        decision_date=decision_date,
        case_name=case_name,
        case_type=case_type,
        domain=_infer_domain(case_type, raw_text),
        raw_text=raw_text,
        source_url=_optional_text(_pick(detail, "판례상세링크", "상세링크", "sourceUrl")),
        issue_summary=issue_summary or judgment_summary[:300] or None,
        fact_summary=fact_summary,
        holding_label=_infer_holding_label(_pick(detail, "판결유형", "judgmentType"), raw_text),
        referenced_statutes=referenced_statutes,
        referenced_precedents=referenced_precedents,
    )


def _find_detail(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        payload.get("PrecService"),
        payload.get("precService"),
        payload.get("Prec"),
        payload.get("prec"),
        payload,
    ]
    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate
    return payload


def _pick(value: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in value:
            return value[key]
    return None


def _text(value: Any) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError("필수 판례 필드가 누락되었습니다.")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = _clean_text(value)
    return text or None


def _clean_text(value: Any) -> str:
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) != 8:
        return None
    return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))


def _split_references(value: Any) -> list[str]:
    text = _clean_text(value or "")
    if not text:
        return []
    parts = re.split(r"[,;·ㆍ/]|(?:\s{2,})", text)
    return [part.strip() for part in parts if part.strip()]


def _summarize_fact(raw_text: str, judgment_summary: str) -> str | None:
    source = judgment_summary or raw_text
    if not source:
        return None
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s+", source)
    return " ".join(sentences[:2]).strip()[:500] or None


def _infer_holding_label(judgment_type: Any, raw_text: str) -> str | None:
    text = f"{judgment_type or ''} {raw_text[:1000]}"
    if "상고기각" in text or "기각" in text:
        return "기각"
    if "파기" in text:
        return "파기"
    if "인용" in text:
        return "인용"
    if "무죄" in text:
        return "무죄"
    if "유죄" in text:
        return "유죄"
    return _optional_text(judgment_type)


def _infer_domain(case_type: str | None, raw_text: str) -> str | None:
    source = f"{case_type or ''} {raw_text[:1000]}"
    if any(keyword in source for keyword in ["손해배상", "민사", "임대차", "계약"]):
        return "민사"
    if any(keyword in source for keyword in ["살인", "절도", "사기", "형사", "유죄", "무죄"]):
        return "형사"
    if any(keyword in source for keyword in ["행정", "취소", "처분"]):
        return "행정"
    return None
