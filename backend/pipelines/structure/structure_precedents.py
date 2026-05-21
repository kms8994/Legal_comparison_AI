from __future__ import annotations

import argparse
import json
from time import sleep
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.llm import PrecedentStructureResult
from app.services.embedding.gemini_embeddings import (
    DEFAULT_EMBEDDING_DIMENSION,
    GeminiEmbeddingClient,
)
from app.services.llm.gemini_client import GeminiLlmClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini 판례 구조화 및 임베딩 파이프라인")
    parser.add_argument("--limit", type=int, default=5, help="처리할 판례 수")
    parser.add_argument("--sleep", type=float, default=0.2, help="판례 처리 사이 대기 시간")
    parser.add_argument(
        "--include-reviewed",
        action="store_true",
        help="이미 reviewed 상태인 판례도 다시 처리",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="LLM 구조화만 수행하고 임베딩은 건너뜀",
    )
    args = parser.parse_args()

    if settings.llm_provider != "gemini":
        raise RuntimeError("현재 구조화 파이프라인은 LLM_PROVIDER=gemini 기준입니다.")
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL 환경변수를 backend/.env에 설정해 주세요.")

    llm_client = GeminiLlmClient()
    embedding_client = None if args.skip_embeddings else GeminiEmbeddingClient()

    with SessionLocal() as db:
        rows = _load_targets(db, args.limit, args.include_reviewed)
        print(f"targets={len(rows)}")

        for row in rows:
            job_id = _create_job(db, "structure", row["id"])
            try:
                structured = llm_client.structure_precedent(
                    case_number=row["case_number"],
                    case_name=row["case_name"],
                    court_name=row["court_name"],
                    raw_text=row["raw_text"] or "",
                )
                _update_structure(db, row["id"], structured)
                if embedding_client is not None:
                    _upsert_embeddings(db, row["id"], structured, embedding_client)
                _finish_job(db, job_id, row["id"], "succeeded")
                db.commit()
                print(f"structured={row['case_number']}")
            except Exception as exc:
                db.rollback()
                with SessionLocal() as error_db:
                    _finish_job(error_db, job_id, row["id"], "failed", str(exc))
                    error_db.commit()
                print(f"failed={row['case_number']} error={exc}")
            sleep(args.sleep)


def _load_targets(db: Any, limit: int, include_reviewed: bool) -> list[dict[str, Any]]:
    review_filter = "" if include_reviewed else "and ps.review_status in ('unreviewed', 'needs_reprocess')"
    rows = db.execute(
        text(
            f"""
            select
                p.id,
                p.case_number,
                p.case_name,
                p.court_name,
                p.raw_text
            from precedents p
            join precedent_structures ps on ps.precedent_id = p.id
            where coalesce(p.raw_text, '') <> ''
            {review_filter}
            order by p.collected_at desc nulls last, p.created_at desc
            limit :limit
            """
        ),
        {"limit": limit},
    ).mappings()
    return [dict(row) for row in rows]


def _create_job(db: Any, job_type: str, precedent_id: str) -> str:
    return str(
        db.execute(
            text(
                """
                insert into processing_jobs (job_type, target_precedent_id, status, started_at)
                values (:job_type, cast(:precedent_id as uuid), 'running', now())
                returning id
                """
            ),
            {"job_type": job_type, "precedent_id": str(precedent_id)},
        ).scalar_one()
    )


def _finish_job(
    db: Any,
    job_id: str,
    precedent_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    db.execute(
        text(
            """
            update processing_jobs
            set
                target_precedent_id = cast(:precedent_id as uuid),
                status = :status,
                error_message = :error_message,
                finished_at = now(),
                updated_at = now()
            where id = cast(:job_id as uuid)
            """
        ),
        {
            "job_id": job_id,
            "precedent_id": str(precedent_id),
            "status": status,
            "error_message": error_message,
        },
    )


def _update_structure(
    db: Any,
    precedent_id: str,
    structured: PrecedentStructureResult,
) -> None:
    db.execute(
        text(
            """
            update precedent_structures
            set
                issue_summary = :issue_summary,
                fact_summary = :fact_summary,
                legal_question = :legal_question,
                holding_label = :holding_label,
                holding_summary = :holding_summary,
                reasoning_summary = :reasoning_summary,
                key_facts = cast(:key_facts as jsonb),
                distinguishing_facts = cast(:distinguishing_facts as jsonb),
                referenced_statutes = cast(:referenced_statutes as jsonb),
                referenced_precedents = cast(:referenced_precedents as jsonb),
                llm_model = :llm_model,
                prompt_version = 'gemini-structure-v1',
                confidence_score = :confidence_score,
                review_status = 'reviewed',
                llm_raw_output = cast(:llm_raw_output as jsonb),
                updated_at = now()
            where precedent_id = cast(:precedent_id as uuid)
            """
        ),
        {
            "precedent_id": str(precedent_id),
            "issue_summary": structured.issue_summary,
            "fact_summary": structured.fact_summary,
            "legal_question": structured.legal_question,
            "holding_label": structured.holding_label,
            "holding_summary": structured.holding_summary,
            "reasoning_summary": structured.reasoning_summary,
            "key_facts": json.dumps(structured.key_facts, ensure_ascii=False),
            "distinguishing_facts": json.dumps(
                structured.distinguishing_facts,
                ensure_ascii=False,
            ),
            "referenced_statutes": json.dumps(structured.referenced_statutes, ensure_ascii=False),
            "referenced_precedents": json.dumps(
                structured.referenced_precedents,
                ensure_ascii=False,
            ),
            "llm_model": settings.llm_structure_model,
            "confidence_score": structured.confidence_score,
            "llm_raw_output": structured.model_dump_json(),
        },
    )


def _upsert_embeddings(
    db: Any,
    precedent_id: str,
    structured: PrecedentStructureResult,
    embedding_client: GeminiEmbeddingClient,
) -> None:
    payloads = {
        "issue": structured.issue_summary or structured.legal_question or "",
        "facts": structured.fact_summary or "",
        "combined": _combined_embedding_text(structured),
    }
    for embedding_type, content in payloads.items():
        content = content.strip()
        if not content:
            continue
        embedding = embedding_client.embed_document(content, DEFAULT_EMBEDDING_DIMENSION)
        _upsert_embedding(db, precedent_id, embedding_type, embedding)


def _combined_embedding_text(structured: PrecedentStructureResult) -> str:
    parts = [
        structured.issue_summary,
        structured.legal_question,
        structured.fact_summary,
        structured.holding_summary,
        structured.reasoning_summary,
        " ".join(structured.key_facts),
        " ".join(structured.distinguishing_facts),
    ]
    return "\n".join(part for part in parts if part)


def _upsert_embedding(
    db: Any,
    precedent_id: str,
    embedding_type: str,
    embedding: list[float],
) -> None:
    db.execute(
        text(
            """
            insert into precedent_embeddings (
                precedent_id,
                embedding_type,
                embedding_model,
                embedding_dimension,
                embedding
            )
            values (
                cast(:precedent_id as uuid),
                :embedding_type,
                :embedding_model,
                :embedding_dimension,
                cast(:embedding as vector)
            )
            on conflict (precedent_id, embedding_type, embedding_model) do update set
                embedding_dimension = excluded.embedding_dimension,
                embedding = excluded.embedding,
                created_at = now()
            """
        ),
        {
            "precedent_id": str(precedent_id),
            "embedding_type": embedding_type,
            "embedding_model": settings.embedding_model,
            "embedding_dimension": len(embedding),
            "embedding": _vector_literal(embedding),
        },
    )


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


if __name__ == "__main__":
    main()
