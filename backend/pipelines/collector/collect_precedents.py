from __future__ import annotations

import argparse
import json
from time import sleep

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from pipelines.collector.law_open_api import LawOpenApiClient
from pipelines.preprocessor.precedent_normalizer import (
    NormalizedPrecedent,
    normalize_precedent_detail,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="국가법령정보 API 판례 수집 파이프라인")
    parser.add_argument("--query", default="교통사고", help="판례 목록 검색어")
    parser.add_argument("--pages", type=int, default=1, help="수집할 목록 페이지 수")
    parser.add_argument("--display", type=int, default=10, help="페이지당 목록 개수, 최대 100")
    parser.add_argument("--sleep", type=float, default=0.2, help="상세 조회 사이 대기 시간")
    args = parser.parse_args()

    if not settings.law_open_api_oc:
        raise RuntimeError("LAW_OPEN_API_OC 환경변수를 backend/.env에 설정해 주세요.")
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL 환경변수를 backend/.env에 설정해 주세요.")

    client = LawOpenApiClient(settings.law_open_api_oc)
    total_saved = 0

    with SessionLocal() as db:
        for page in range(1, args.pages + 1):
            items = client.search_precedents(
                query=args.query,
                page=page,
                display=args.display,
            )
            print(f"page={page} items={len(items)}")

            for item in items:
                if not item.precedent_id:
                    continue
                job_id = _create_job(db, "collect")
                try:
                    detail_payload = client.get_precedent_detail(item.precedent_id)
                    normalized = normalize_precedent_detail(detail_payload)
                    precedent_id = _upsert_precedent(db, normalized, item.precedent_id)
                    _upsert_structure(db, precedent_id, normalized)
                    _finish_job(db, job_id, precedent_id, "succeeded")
                    total_saved += 1
                except Exception as exc:
                    _finish_job(db, job_id, None, "failed", str(exc))
                    print(f"failed id={item.precedent_id} error={exc}")
                db.commit()
                sleep(args.sleep)

    print(f"saved={total_saved}")


def _create_job(db: Session, job_type: str) -> str:
    return str(
        db.execute(
            text(
                """
                insert into processing_jobs (job_type, status, started_at)
                values (:job_type, 'running', now())
                returning id
                """
            ),
            {"job_type": job_type},
        ).scalar_one()
    )


def _finish_job(
    db: Session,
    job_id: str,
    precedent_id: str | None,
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
            "precedent_id": precedent_id,
            "status": status,
            "error_message": error_message,
        },
    )


def _upsert_precedent(
    db: Session,
    precedent: NormalizedPrecedent,
    external_id: str,
) -> str:
    return str(
        db.execute(
            text(
                """
                insert into precedents (
                    case_number,
                    court_name,
                    decision_date,
                    case_name,
                    case_type,
                    domain,
                    raw_text,
                    source_url,
                    source_provider,
                    collected_at
                )
                values (
                    :case_number,
                    :court_name,
                    :decision_date,
                    :case_name,
                    :case_type,
                    :domain,
                    :raw_text,
                    :source_url,
                    'national_law_api',
                    now()
                )
                on conflict (case_number) do update set
                    court_name = excluded.court_name,
                    decision_date = excluded.decision_date,
                    case_name = excluded.case_name,
                    case_type = excluded.case_type,
                    domain = excluded.domain,
                    raw_text = excluded.raw_text,
                    source_url = excluded.source_url,
                    source_provider = excluded.source_provider,
                    collected_at = excluded.collected_at,
                    updated_at = now()
                returning id
                """
            ),
            {
                "case_number": precedent.case_number,
                "court_name": precedent.court_name,
                "decision_date": precedent.decision_date,
                "case_name": precedent.case_name,
                "case_type": precedent.case_type,
                "domain": precedent.domain,
                "raw_text": precedent.raw_text,
                "source_url": precedent.source_url
                or f"https://www.law.go.kr/DRF/lawService.do?target=prec&ID={external_id}&type=HTML",
            },
        ).scalar_one()
    )


def _upsert_structure(
    db: Session,
    precedent_id: str,
    precedent: NormalizedPrecedent,
) -> None:
    db.execute(
        text(
            """
            insert into precedent_structures (
                precedent_id,
                issue_summary,
                fact_summary,
                holding_label,
                referenced_statutes,
                referenced_precedents,
                llm_model,
                prompt_version,
                confidence_score,
                review_status
            )
            values (
                cast(:precedent_id as uuid),
                :issue_summary,
                :fact_summary,
                :holding_label,
                cast(:referenced_statutes as jsonb),
                cast(:referenced_precedents as jsonb),
                'rule-based',
                'preprocessor-v1',
                0.500,
                'unreviewed'
            )
            on conflict (precedent_id) do update set
                issue_summary = excluded.issue_summary,
                fact_summary = excluded.fact_summary,
                holding_label = excluded.holding_label,
                referenced_statutes = excluded.referenced_statutes,
                referenced_precedents = excluded.referenced_precedents,
                llm_model = excluded.llm_model,
                prompt_version = excluded.prompt_version,
                confidence_score = excluded.confidence_score,
                review_status = excluded.review_status,
                updated_at = now()
            """
        ),
        {
            "precedent_id": precedent_id,
            "issue_summary": precedent.issue_summary,
            "fact_summary": precedent.fact_summary,
            "holding_label": precedent.holding_label,
            "referenced_statutes": json.dumps(precedent.referenced_statutes, ensure_ascii=False),
            "referenced_precedents": json.dumps(precedent.referenced_precedents, ensure_ascii=False),
        },
    )


if __name__ == "__main__":
    main()
