CREATE TABLE IF NOT EXISTS onboarding_plans (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL UNIQUE
        REFERENCES onboarding_requests(id),
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'approved', 'rejected')),
    tasks JSONB NOT NULL
        CHECK (jsonb_typeof(tasks) = 'array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);