insert into collection_requests (
    query_text,
    normalized_query,
    domain,
    case_type,
    legal_issue,
    fact_pattern,
    key_facts,
    priority,
    source,
    status
)
values
(
    '중고거래 사기 물건 미발송 환불 거부',
    '형사|사기|중고거래 물건 미발송 환불 거부',
    '형사',
    '사기',
    '중고거래에서 대금을 받고 물건을 보내지 않은 경우 사기죄 성립 여부',
    '판매자가 대금을 받은 뒤 물건을 보내지 않고 환불도 거부한 사안',
    '["중고거래", "대금 수령", "물건 미발송", "환불 거부"]'::jsonb,
    100,
    'seed',
    'pending'
),
(
    '전세 보증금 미반환 임대차 종료',
    '민사|임대차|전세 보증금 미반환',
    '민사',
    '임대차',
    '임대차 종료 후 보증금 반환 책임과 지연손해금',
    '임대차가 종료되었는데 임대인이 보증금을 반환하지 않은 사안',
    '["임대차 종료", "보증금 미반환", "임대인", "임차인"]'::jsonb,
    95,
    'seed',
    'pending'
),
(
    '부당해고 해고 통보 절차 근로자',
    '민사|노동|부당해고 해고 통보 절차',
    '민사',
    '노동',
    '해고 사유와 절차가 부족한 경우 해고의 정당성',
    '회사가 근로자에게 해고를 통보했고 근로자는 해고 사유와 절차를 다투는 사안',
    '["근로자", "회사", "해고 통보", "해고 사유", "절차"]'::jsonb,
    90,
    'seed',
    'pending'
),
(
    '계약금 반환 계약 해제 매매계약',
    '민사|계약|계약 해제 계약금 반환',
    '민사',
    '계약',
    '계약 해제 시 계약금 반환 또는 몰취 가능성',
    '매매계약 체결 후 일방이 계약 해제를 주장하며 계약금 반환을 다투는 사안',
    '["매매계약", "계약금", "계약 해제", "반환"]'::jsonb,
    85,
    'seed',
    'pending'
),
(
    '음주운전 사고 형사처벌 손해배상',
    '형사|교통사고|음주운전 사고 처벌 손해배상',
    '형사',
    '교통사고',
    '음주운전 사고에서 형사책임과 손해배상 책임',
    '음주 상태에서 운전하다 사고가 발생해 피해가 생긴 사안',
    '["음주운전", "교통사고", "피해 발생", "형사책임"]'::jsonb,
    80,
    'seed',
    'pending'
),
(
    '행정처분 취소 영업정지 과징금',
    '행정|처분취소|영업정지 과징금',
    '행정',
    '처분취소',
    '영업정지나 과징금 처분의 위법성 판단',
    '행정청이 영업정지 또는 과징금을 부과했고 당사자가 처분 취소를 구하는 사안',
    '["행정처분", "영업정지", "과징금", "처분 취소"]'::jsonb,
    75,
    'seed',
    'pending'
),
(
    '학교폭력 징계 처분 취소',
    '행정|학교폭력|징계 처분 취소',
    '행정',
    '학교폭력',
    '학교폭력 징계처분의 절차와 비례성',
    '학교폭력 사안에서 징계처분을 받은 학생이 처분의 취소를 다투는 사안',
    '["학교폭력", "징계처분", "절차", "비례성"]'::jsonb,
    70,
    'seed',
    'pending'
),
(
    '층간소음 손해배상 정신적 손해',
    '민사|손해배상|층간소음 정신적 손해',
    '민사',
    '손해배상',
    '층간소음으로 인한 손해배상 책임과 위자료 인정 여부',
    '이웃 간 층간소음 문제로 정신적 손해와 배상책임이 다투어진 사안',
    '["층간소음", "이웃", "정신적 손해", "손해배상"]'::jsonb,
    65,
    'seed',
    'pending'
)
on conflict (normalized_query) do update set
    query_text = excluded.query_text,
    domain = excluded.domain,
    case_type = excluded.case_type,
    legal_issue = excluded.legal_issue,
    fact_pattern = excluded.fact_pattern,
    key_facts = excluded.key_facts,
    priority = greatest(collection_requests.priority, excluded.priority),
    source = excluded.source,
    updated_at = now();
