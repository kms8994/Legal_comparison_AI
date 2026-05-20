# DB 스키마 설계서
## Supabase Postgres + pgvector

| 항목 | 내용 |
| :--- | :--- |
| 기준 문서 | `prd.md`, `development_plan.md` |
| 작성일 | 2026-05-20 |
| 목적 | 판례 원문, 구조화 데이터, 임베딩, 처리 상태를 분리 저장하여 검색과 유지보수를 쉽게 한다 |

---

## 1. 설계 원칙

- 프론트엔드는 Supabase에 직접 연결하지 않는다.
- 모든 DB 접근은 FastAPI 백엔드를 통해 수행한다.
- 원문 데이터와 LLM 가공 데이터는 분리한다.
- 임베딩은 별도 테이블에 저장한다.
- LLM 모델명, 프롬프트 버전, 처리 상태를 저장해 재처리와 품질 관리를 가능하게 한다.

---

## 2. 필수 확장

Supabase SQL Editor에서 먼저 실행한다.

```sql
create extension if not exists vector;
```

---

## 3. 테이블 개요

| 테이블 | 역할 |
| :--- | :--- |
| `precedents` | 판례 원문과 기본 메타데이터 |
| `precedent_structures` | LLM 또는 파서가 만든 검색용 구조화 데이터 |
| `precedent_embeddings` | 쟁점/사실관계 임베딩 |
| `processing_jobs` | 수집, 전처리, 임베딩 생성, 재처리 상태 |
| `comparison_feedback` | 사용자의 비교 결과 피드백 |
| `error_reports` | 판례/라벨/요약 오류 신고 |

---

## 4. 주요 테이블

### 4.1 `precedents`

판례 원문과 기본 정보를 저장한다.

주요 필드:

- `id`
- `case_number`
- `court_name`
- `decision_date`
- `case_name`
- `case_type`
- `domain`
- `raw_text`
- `source_url`
- `source_provider`
- `collected_at`
- `created_at`
- `updated_at`

### 4.2 `precedent_structures`

검색과 비교에 사용할 정제 데이터를 저장한다.

주요 필드:

- `precedent_id`
- `issue_summary`
- `fact_summary`
- `holding_label`
- `referenced_statutes`
- `referenced_precedents`
- `llm_model`
- `prompt_version`
- `confidence_score`
- `review_status`

### 4.3 `precedent_embeddings`

벡터 검색용 임베딩을 저장한다.

초기 임베딩 차원은 `text-embedding-3-small` 기준 `1536`으로 둔다.

주요 필드:

- `precedent_id`
- `embedding_type`
- `embedding_model`
- `embedding_dimension`
- `embedding`

### 4.4 `processing_jobs`

배치 처리 상태와 실패 사유를 저장한다.

주요 필드:

- `job_type`
- `target_precedent_id`
- `status`
- `attempt_count`
- `error_message`
- `started_at`
- `finished_at`

---

## 5. 사용자 피드백 테이블

### 5.1 `comparison_feedback`

비교 결과에 대한 간단한 사용자 피드백을 저장한다.

초기 항목:

- 유사하다고 느꼈는가
- 결론 분류가 맞는가
- 도움이 되었는가

### 5.2 `error_reports`

오류 신고를 저장한다.

신고 유형:

- `holding_label`
- `fact_summary`
- `statute`
- `other`

---

## 6. 보안 원칙

- DB 연결 문자열은 백엔드 `.env`에만 둔다.
- `NEXT_PUBLIC_` 환경변수에는 DB 관련 값을 넣지 않는다.
- 가능하면 Supabase 네트워크 제한에서 GCE VM 고정 IP만 허용한다.
- MVP에서는 프론트 직접 DB 접근을 사용하지 않는다.

---

## 7. SQL 파일

실제 생성 SQL은 아래 파일에 둔다.

```text
supabase/schema.sql
```
