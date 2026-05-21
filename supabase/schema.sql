create extension if not exists vector;

create table if not exists precedents (
    id uuid primary key default gen_random_uuid(),
    case_number text not null unique,
    court_name text,
    decision_date date,
    case_name text,
    case_type text,
    domain text,
    raw_text text,
    source_url text,
    source_provider text not null default 'national_law_api',
    collected_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_precedents_case_number on precedents (case_number);
create index if not exists idx_precedents_decision_date on precedents (decision_date);
create index if not exists idx_precedents_domain on precedents (domain);
create index if not exists idx_precedents_case_type on precedents (case_type);

create table if not exists precedent_structures (
    id uuid primary key default gen_random_uuid(),
    precedent_id uuid not null references precedents(id) on delete cascade,
    issue_summary text,
    fact_summary text,
    legal_question text,
    holding_label text,
    holding_summary text,
    reasoning_summary text,
    key_facts jsonb not null default '[]'::jsonb,
    distinguishing_facts jsonb not null default '[]'::jsonb,
    referenced_statutes jsonb not null default '[]'::jsonb,
    referenced_precedents jsonb not null default '[]'::jsonb,
    llm_model text,
    prompt_version text,
    confidence_score numeric(4, 3),
    review_status text not null default 'unreviewed',
    llm_raw_output jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_precedent_structures_precedent unique (precedent_id),
    constraint chk_precedent_structures_review_status check (
        review_status in ('unreviewed', 'reviewed', 'needs_reprocess')
    )
);

create index if not exists idx_precedent_structures_holding
    on precedent_structures (holding_label);

create table if not exists precedent_embeddings (
    id uuid primary key default gen_random_uuid(),
    precedent_id uuid not null references precedents(id) on delete cascade,
    embedding_type text not null,
    embedding_model text not null,
    embedding_dimension integer not null default 1536,
    embedding vector(1536) not null,
    created_at timestamptz not null default now(),
    constraint uq_precedent_embeddings_target unique (
        precedent_id,
        embedding_type,
        embedding_model
    ),
    constraint chk_precedent_embeddings_type check (
        embedding_type in ('issue', 'facts', 'combined')
    )
);

create index if not exists idx_precedent_embeddings_type
    on precedent_embeddings (embedding_type);

create index if not exists idx_precedent_embeddings_vector
    on precedent_embeddings
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

create table if not exists processing_jobs (
    id uuid primary key default gen_random_uuid(),
    job_type text not null,
    target_precedent_id uuid references precedents(id) on delete set null,
    status text not null default 'pending',
    attempt_count integer not null default 0,
    error_message text,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_processing_jobs_type check (
        job_type in ('collect', 'structure', 'embed', 'reprocess')
    ),
    constraint chk_processing_jobs_status check (
        status in ('pending', 'running', 'succeeded', 'failed')
    )
);

create index if not exists idx_processing_jobs_status on processing_jobs (status);
create index if not exists idx_processing_jobs_type on processing_jobs (job_type);

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

create table if not exists comparison_feedback (
    id uuid primary key default gen_random_uuid(),
    query_text text,
    reference_precedent_id uuid references precedents(id) on delete set null,
    opposite_precedent_id uuid references precedents(id) on delete set null,
    is_factually_similar text,
    is_holding_correct text,
    is_helpful text,
    comment text,
    created_at timestamptz not null default now(),
    constraint chk_comparison_feedback_answer_similar check (
        is_factually_similar is null or is_factually_similar in ('yes', 'partial', 'no')
    ),
    constraint chk_comparison_feedback_answer_holding check (
        is_holding_correct is null or is_holding_correct in ('yes', 'partial', 'no')
    ),
    constraint chk_comparison_feedback_answer_helpful check (
        is_helpful is null or is_helpful in ('yes', 'partial', 'no')
    )
);

create table if not exists error_reports (
    id uuid primary key default gen_random_uuid(),
    precedent_id uuid references precedents(id) on delete set null,
    report_type text not null,
    description text,
    reporter_email text,
    status text not null default 'open',
    created_at timestamptz not null default now(),
    resolved_at timestamptz,
    constraint chk_error_reports_type check (
        report_type in ('holding_label', 'fact_summary', 'statute', 'other')
    ),
    constraint chk_error_reports_status check (
        status in ('open', 'reviewing', 'resolved', 'dismissed')
    )
);

create index if not exists idx_error_reports_status on error_reports (status);
create index if not exists idx_error_reports_precedent on error_reports (precedent_id);
