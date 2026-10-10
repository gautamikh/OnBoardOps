CREATE TABLE IF NOT EXISTS onboarding_requests (
    id UUID PRIMARY KEY,
    employee_name VARCHAR(120) NOT NULL,
    job_title VARCHAR(120) NOT NULL,
    department VARCHAR(80) NOT NULL,
    location VARCHAR(80) NOT NULL,
    start_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);