alter table precedent_structures
add column if not exists legal_question text,
add column if not exists holding_summary text,
add column if not exists reasoning_summary text,
add column if not exists key_facts jsonb not null default '[]'::jsonb,
add column if not exists distinguishing_facts jsonb not null default '[]'::jsonb,
add column if not exists llm_raw_output jsonb;
