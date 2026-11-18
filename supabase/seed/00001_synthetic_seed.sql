-- ====================================================================
-- MSGI One — Synthetic Test Seed Data: 00001_synthetic_seed.sql
-- NOTICE: All records below are strictly synthetic test accounts.
-- Uses standard example domain @example.msgi.edu.
-- ====================================================================

-- 1. Ensure Roles Exist
INSERT INTO public.roles (id, description) VALUES
    ('student', 'Active matriculated student (default base access)'),
    ('alumni', 'Verified graduate holding an institutional degree'),
    ('faculty', 'Academic faculty, professor, or researcher'),
    ('recruiter', 'Verified corporate hiring manager or placement partner'),
    ('admin', 'Institutional ecosystem compliance and system administrator')
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;

-- 2. Seed Skills Taxonomy
INSERT INTO public.skills (id, name, category) VALUES
    ('a1111111-1111-1111-1111-111111111111', 'Python', 'technical'),
    ('a2222222-2222-2222-2222-222222222222', 'PyTorch', 'technical'),
    ('a3333333-3333-3333-3333-333333333333', 'Transformers', 'technical'),
    ('a4444444-4444-4444-4444-444444444444', 'Docker', 'technical'),
    ('a5555555-5555-5555-5555-555555555555', 'FastAPI', 'technical'),
    ('a6666666-6666-6666-6666-666666666666', 'SQL', 'technical'),
    ('a7777777-7777-7777-7777-777777777777', 'Linux', 'technical'),
    ('a8888888-8888-8888-8888-888888888888', 'Japanese Business Etiquette', 'soft_skill')
ON CONFLICT (name) DO NOTHING;
