# 판례비교

자연어로 사건을 입력하면 기준 판례와 반대 결론 판례를 좌우로 비교해 보여주는 MVP입니다.

## 구조

```text
frontend/  Next.js UI
backend/   FastAPI API
docs/      추후 상세 문서 위치
```

현재 구현은 실제 국가법령정보 API와 Supabase 연결 전 단계입니다. 프론트엔드는 `/api/compare` 호출을 시도하고, 백엔드가 없으면 예시 데이터를 표시합니다.

## 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

기본 주소는 `http://localhost:3000`입니다.

## 백엔드 실행

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

헬스 체크:

```bash
curl http://127.0.0.1:8000/api/health
```

## Supabase 연결

1. Supabase SQL Editor에서 스키마를 실행합니다.

   ```text
   supabase/schema.sql
   ```

2. `backend/.env.example`을 참고해 `backend/.env`를 만듭니다.

   ```env
   DATABASE_URL=postgresql+psycopg://...
   ```

3. DB 연결 확인:

   ```bash
   curl http://127.0.0.1:8000/api/db/health
   ```

프론트엔드에는 Supabase DB 접속 정보를 넣지 않습니다. DB 연결은 FastAPI 백엔드에서만 수행합니다.

## 다음 개발 단계

1. Supabase DB 스키마 작성
2. 국가법령정보 API 수집기 구현
3. LLM 전처리 파이프라인 연결
4. 임베딩 기반 후보 검색 구현
5. 현재 목업 `/api/compare`를 실제 검색 결과로 교체
