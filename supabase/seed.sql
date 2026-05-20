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
) values
(
    '대법원 2019다2345',
    '대법원',
    '2019-06-27',
    '손해배상',
    '교통사고',
    '민사',
    '신호등 없는 교차로에서 직진 차량과 좌회전 차량이 충돌한 사고에서 직진 차량의 과실 범위가 문제된 사건이다.',
    'https://example.com/precedents/2019da2345',
    'seed',
    now()
),
(
    '대법원 2018다3456',
    '대법원',
    '2018-08-13',
    '손해배상',
    '교통사고',
    '민사',
    '교차로에서 좌회전 차량과 직진 차량이 충돌했지만 좌회전 차량의 진입 방식과 확인 의무가 더 크게 문제된 사건이다.',
    'https://example.com/precedents/2018da3456',
    'seed',
    now()
),
(
    '대법원 2021다6789',
    '대법원',
    '2021-11-04',
    '손해배상',
    '교통사고',
    '민사',
    '교차로 충돌 사고에서 직진 차량의 과속 여부와 전방주시의무 위반이 문제된 사건이다.',
    'https://example.com/precedents/2021da6789',
    'seed',
    now()
),
(
    '서울고등법원 2020나4567',
    '서울고등법원',
    '2020-03-19',
    '손해배상',
    '교통사고',
    '민사',
    '좌회전 차량과 직진 차량의 통행 우선순위 및 교차로 진입 시 주의의무가 문제된 사건이다.',
    'https://example.com/precedents/2020na4567',
    'seed',
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
    updated_at = now();

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
select
    p.id,
    s.issue_summary,
    s.fact_summary,
    s.holding_label,
    s.referenced_statutes::jsonb,
    '[]'::jsonb,
    'seed',
    'seed-v1',
    0.900,
    'reviewed'
from (
    values
    (
        '대법원 2019다2345',
        '신호등 없는 교차로에서 직진 차량의 과실 범위',
        '직진 차량과 좌회전 차량이 충돌했고, 직진 차량의 과속 및 전방주시의무 위반이 쟁점이 되었다.',
        '인용',
        '["도로교통법 제5조", "도로교통법 제7조", "민법 제750조"]'
    ),
    (
        '대법원 2018다3456',
        '신호등 없는 교차로에서 좌회전 차량의 확인 의무',
        '좌회전 차량과 직진 차량이 충돌했으며, 좌회전 차량의 진입 방식과 안전 확인 의무가 쟁점이 되었다.',
        '기각',
        '["도로교통법 제5조", "도로교통법 제7조", "민법 제750조"]'
    ),
    (
        '대법원 2021다6789',
        '교차로 충돌 사고에서 직진 차량의 과속 여부',
        '직진 차량의 과속 여부와 교차로 진입 당시 전방주시의무 위반 여부가 문제되었다.',
        '인용',
        '["도로교통법 제5조", "민법 제750조"]'
    ),
    (
        '서울고등법원 2020나4567',
        '좌회전 차량과 직진 차량의 통행 우선순위',
        '교차로에서 좌회전 차량과 직진 차량의 통행 우선순위 및 각 운전자의 주의의무가 문제되었다.',
        '인용',
        '["도로교통법 제7조", "민법 제750조"]'
    )
) as s(case_number, issue_summary, fact_summary, holding_label, referenced_statutes)
join precedents p on p.case_number = s.case_number
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
    updated_at = now();

insert into processing_jobs (
    job_type,
    target_precedent_id,
    status,
    attempt_count,
    started_at,
    finished_at
)
select
    'structure',
    p.id,
    'succeeded',
    1,
    now(),
    now()
from precedents p
where p.source_provider = 'seed'
on conflict do nothing;
