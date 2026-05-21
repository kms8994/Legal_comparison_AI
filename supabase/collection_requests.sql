create table if not exists collection_requests (
    id uuid primary key default gen_random_uuid(),
    query_text text not null,
    normalized_query text not null unique,
    domain text,
    case_type text,
    legal_issue text,
    fact_pattern text,
    key_facts jsonb not null default '[]'::jsonb,
    requested_count integer not null default 1,
    priority integer not null default 0,
    status text not null default 'pending',
    source text not null default 'user_search',
    last_requested_at timestamptz not null default now(),
    processed_at timestamptz,
    error_message text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_collection_requests_status check (
        status in ('pending', 'collecting', 'structured', 'done', 'failed', 'dismissed')
    ),
    constraint chk_collection_requests_source check (
        source in ('user_search', 'seed', 'admin')
    )
);

create index if not exists idx_collection_requests_status
    on collection_requests (status);

create index if not exists idx_collection_requests_priority
    on collection_requests (priority desc, requested_count desc, last_requested_at desc);
