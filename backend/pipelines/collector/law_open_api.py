from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LIST_URL = "http://www.law.go.kr/DRF/lawSearch.do"
DETAIL_URL = "http://www.law.go.kr/DRF/lawService.do"


@dataclass(frozen=True)
class PrecedentListItem:
    precedent_id: str
    case_number: str
    case_name: str | None
    court_name: str | None
    decision_date: str | None


class LawOpenApiClient:
    def __init__(self, oc: str, timeout_seconds: int = 20) -> None:
        self.oc = oc
        self.timeout_seconds = timeout_seconds

    def search_precedents(
        self,
        query: str,
        page: int = 1,
        display: int = 20,
        search: int = 2,
        org: str = "400201",
    ) -> list[PrecedentListItem]:
        payload = self._get_json(
            LIST_URL,
            {
                "OC": self.oc,
                "target": "prec",
                "type": "JSON",
                "query": query,
                "search": search,
                "display": display,
                "page": page,
                "org": org,
            },
        )
        raw_items = _ensure_list(_dig(payload, "PrecSearch", "prec") or _dig(payload, "prec"))

        return [
            PrecedentListItem(
                precedent_id=str(_pick(item, "판례일련번호", "판례정보일련번호", "ID", "id") or ""),
                case_number=str(_pick(item, "사건번호", "caseNumber") or ""),
                case_name=_string_or_none(_pick(item, "사건명", "판례명", "caseName")),
                court_name=_string_or_none(_pick(item, "법원명", "courtName")),
                decision_date=_string_or_none(_pick(item, "선고일자", "decisionDate")),
            )
            for item in raw_items
            if _pick(item, "판례일련번호", "판례정보일련번호", "ID", "id")
        ]

    def get_precedent_detail(self, precedent_id: str) -> dict[str, Any]:
        return self._get_json(
            DETAIL_URL,
            {
                "OC": self.oc,
                "target": "prec",
                "type": "JSON",
                "ID": precedent_id,
            },
        )

    def _get_json(self, url: str, params: dict[str, object]) -> dict[str, Any]:
        request_url = f"{url}?{urlencode(params)}"
        request = Request(
            request_url,
            headers={
                "Accept": "application/json,text/plain,*/*",
                "User-Agent": "LegalComparisonAI/0.1 (+https://github.com/kms8994/Legal_comparison_AI)",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("국가법령정보 API 응답 형식이 올바르지 않습니다.")
        if parsed.get("result") and not (
            _dig(parsed, "PrecSearch", "prec") or _dig(parsed, "prec")
        ):
            message = parsed.get("msg") or parsed.get("message") or parsed.get("result")
            raise RuntimeError(f"국가법령정보 API 오류: {message}")
        return parsed


def _dig(value: dict[str, Any], *path: str) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _ensure_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _pick(value: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in value:
            return value[key]
    return None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
