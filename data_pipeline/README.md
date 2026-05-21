# Data Collection Pipeline

이 폴더는 판례 데이터를 Supabase DB에 적재하기 위한 수동 실행용 파이프라인입니다.

서비스 요청 시에는 국가법령정보 API를 직접 호출하지 않습니다. 운영 백엔드는 Supabase DB만 조회하고, 판례 수집은 로컬 개발 환경에서 필요할 때 따로 실행합니다.

## 흐름

```text
로컬 PC
  -> 국가법령정보 API
  -> 전처리
  -> Supabase DB 저장
  -> 서비스 백엔드는 DB만 조회
```

## 실행 전 체크

`backend/.env`에 아래 값이 있어야 합니다.

```env
DATABASE_URL=postgresql+psycopg://...
LAW_OPEN_API_OC=...
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
LLM_STRUCTURE_MODEL=gemini-2.5-flash-lite
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
```

국가법령정보 API는 호출 IP를 검증하므로, 로컬 PC의 공인 IP가 국가법령정보 API 관리 화면에 등록되어 있어야 합니다.

```powershell
curl ifconfig.me
```

## Windows 실행

프로젝트 루트에서 실행합니다.

```powershell
.\data_pipeline\run_collect.ps1 -Query "교통사고" -Pages 1 -Display 10
```

여러 페이지를 수집하려면:

```powershell
.\data_pipeline\run_collect.ps1 -Query "손해배상" -Pages 5 -Display 20
```

## macOS/Linux 실행

```bash
chmod +x ./data_pipeline/run_collect.sh
./data_pipeline/run_collect.sh "교통사고" 1 10
```

## DB 저장 확인

Windows:

```powershell
.\data_pipeline\check_counts.ps1
```

수동으로 확인하려면:

```powershell
cd backend
python -c "from app.db.session import SessionLocal; from sqlalchemy import text; db=SessionLocal(); print(db.execute(text('select count(*) from precedents')).scalar_one()); db.close()"
```

## LLM 구조화 및 임베딩

판례 수집 후 Supabase SQL Editor에서 `supabase/llm_schema.sql`을 한 번 실행해 구조화 컬럼을 추가합니다.

그 다음 로컬에서 아래 명령으로 미검수 판례를 구조화하고 임베딩을 생성합니다.

```powershell
cd backend
python -m pipelines.structure.structure_precedents --limit 5
```

LLM 구조화만 먼저 확인하려면:

```powershell
cd backend
python -m pipelines.structure.structure_precedents --limit 1 --skip-embeddings
```

## 수집 요청 큐

사용자 입력과 관련된 판례가 부족하면 서비스는 `collection_requests` 테이블에 수집 요청을 저장합니다.

처음 한 번 아래 명령으로 큐 테이블과 추천 seed 요청을 적용합니다.

```powershell
.\data_pipeline\apply_collection_queue_schema.ps1
```

대기 중인 요청 확인:

```powershell
cd backend
python -m pipelines.collector.list_collection_requests --limit 20
```

이 목록을 보고 필요한 검색어를 골라 수집합니다.

```powershell
.\data_pipeline\run_collect.ps1 -Query "중고거래 사기" -Pages 2 -Display 20
cd backend
python -m pipelines.structure.structure_precedents --limit 20
```

## 검색어 예시

검색어 목록은 `queries.example.txt`를 참고합니다. MVP 단계에서는 너무 넓은 검색어보다 사건 유형이 드러나는 검색어를 우선합니다.

예:

- 교통사고
- 손해배상
- 임대차
- 사기
- 근로자

## 주의

- 수집 스크립트는 중복 사건번호를 upsert하므로 같은 검색어를 다시 실행해도 기존 판례를 갱신합니다.
- 현재 수집 스크립트는 원문 저장과 rule-based 기본 구조화를 수행합니다.
- 다음 단계에서 LLM 구조화와 임베딩 생성을 이 파이프라인에 붙입니다.
- LLM은 저비용 MVP 기준으로 `gemini-2.5-flash-lite`, 임베딩은 `gemini-embedding-001`을 기본값으로 사용합니다.
- 운영 서버에서 법령 API를 직접 호출하지 않는 것이 현재 MVP 기준입니다.
- 사용자 자연어 입력은 LLM이 직접 답을 만들지 않고, 미리 정의된 검색 슬롯만 추출합니다.
- 부족한 입력 질문은 LLM이 생성하지 않고 코드에 고정된 템플릿에서 선택합니다.
