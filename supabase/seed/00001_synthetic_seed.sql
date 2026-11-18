-- ====================================================================
-- MSGI One — Synthetic Seed Dataset (00001_synthetic_seed.sql)
-- NOTICE: All records are strictly synthetic test fixtures.
-- No real institutional PII is contained herein.
-- ====================================================================

-- 1. Seed Skills Taxonomy
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

-- 2. Seed Curated Courses
INSERT INTO public.courses (id, title, description, provider, difficulty, associated_skills) VALUES
    ('c1111111-1111-1111-1111-111111111111', 
     'Deep Learning & Transformers Masterclass', 
     'Comprehensive foundation in attention mechanisms, Hugging Face, and PyTorch.', 
     'MSGI Academy', 
     'intermediate', 
     ARRAY['PyTorch', 'Transformers']),
    ('c2222222-2222-2222-2222-222222222222', 
     'Containerized MLOps with Docker & Kubernetes', 
     'Production deployment of deep learning models in enterprise container environments.', 
     'MSGI Academy', 
     'advanced', 
     ARRAY['Docker', 'FastAPI', 'Linux'])
ON CONFLICT (id) DO NOTHING;

-- 3. Seed Institutional Impact Programme
INSERT INTO public.impact_programmes (id, title, description, target_amount, raised_amount, currency, is_active) VALUES
    ('p1111111-1111-1111-1111-111111111111', 
     'Global Alumni Tech Innovation Endowment 2026', 
     'Institutional fund supporting student overseas research internships and AI lab hardware.', 
     100000.00, 
     42500.00, 
     'USD', 
     TRUE)
ON CONFLICT (id) DO NOTHING;
