from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def upsert_collection_request(
    db: Session,
    *,
    query_text: str,
    extracted_facts: dict[str, object] | None,
    source: str = "user_search",
) -> None:
    facts = extracted_facts or {}
    normalized_query = _build_normalized_query(query_text, facts)
    key_facts = facts.get("key_facts")
    if not isinstance(key_facts, list):
        key_facts = []

    db.execute(
        text(
            """
            insert into collection_requests (
                query_text,
                normalized_query,
                domain,
                case_type,
                legal_issue,
                fact_pattern,
                key_facts,
                source,
                status,
                last_requested_at
            )
            values (
                :query_text,
                :normalized_query,
                :domain,
                :case_type,
                :legal_issue,
                :fact_pattern,
                cast(:key_facts as jsonb),
                :source,
                'pending',
                now()
            )
            on conflict (normalized_query) do update set
                requested_count = collection_requests.requested_count + 1,
                query_text = excluded.query_text,
                domain = coalesce(excluded.domain, collection_requests.domain),
                case_type = coalesce(excluded.case_type, collection_requests.case_type),
                legal_issue = coalesce(excluded.legal_issue, collection_requests.legal_issue),
                fact_pattern = coalesce(excluded.fact_pattern, collection_requests.fact_pattern),
                key_facts = case
                    when excluded.key_facts = '[]'::jsonb then collection_requests.key_facts
                    else excluded.key_facts
                end,
                status = case
                    when collection_requests.status in ('done', 'dismissed') then collection_requests.status
                    else 'pending'
                end,
                last_requested_at = now(),
                updated_at = now()
            """
        ),
        {
            "query_text": query_text,
            "normalized_query": normalized_query,
            "domain": _optional_string(facts.get("domain")),
            "case_type": _optional_string(facts.get("case_type")),
            "legal_issue": _optional_string(facts.get("legal_issue")),
            "fact_pattern": _optional_string(facts.get("fact_pattern")),
            "key_facts": json.dumps(key_facts, ensure_ascii=False),
            "source": source,
        },
    )


def _build_normalized_query(query_text: str, facts: dict[str, object]) -> str:
    parts = [
        _optional_string(facts.get("domain")),
        _optional_string(facts.get("case_type")),
        _optional_string(facts.get("legal_issue")),
        _optional_string(facts.get("fact_pattern")),
        _optional_string(query_text),
    ]
    raw = "|".join(part for part in parts if part)
    return _normalize(raw or query_text)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, list):
        joined = " ".join(str(item).strip() for item in value if str(item).strip())
        return joined or None
    return str(value)
