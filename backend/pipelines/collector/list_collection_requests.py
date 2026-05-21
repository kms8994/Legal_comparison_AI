from __future__ import annotations

import argparse

from sqlalchemy import text

from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="대기 중인 판례 수집 요청 확인")
    parser.add_argument("--limit", type=int, default=20, help="조회할 요청 수")
    parser.add_argument("--status", default="pending", help="조회할 상태")
    args = parser.parse_args()

    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL 환경변수를 backend/.env에 설정해 주세요.")

    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                select
                    query_text,
                    domain,
                    case_type,
                    legal_issue,
                    requested_count,
                    priority,
                    source,
                    status,
                    last_requested_at
                from collection_requests
                where status = :status
                order by priority desc, requested_count desc, last_requested_at desc
                limit :limit
                """
            ),
            {"status": args.status, "limit": args.limit},
        ).mappings()

        for index, row in enumerate(rows, start=1):
            print(
                f"{index}. [{row['status']}] priority={row['priority']} "
                f"count={row['requested_count']} source={row['source']}"
            )
            print(f"   query: {row['query_text']}")
            print(
                "   meta: "
                f"domain={row['domain'] or '-'} "
                f"case_type={row['case_type'] or '-'} "
                f"issue={row['legal_issue'] or '-'}"
            )


if __name__ == "__main__":
    main()
