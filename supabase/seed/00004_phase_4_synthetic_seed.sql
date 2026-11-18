-- ====================================================================
-- MSGI One — Phase 4 Synthetic Seed Fixtures: 00004_phase_4_synthetic_seed.sql
-- NOTICE: All records below are strictly synthetic development fixtures.
-- Uses standard example domain @example.msgi.edu.
-- Strictly NO live payment receipts, credit cards, or real institutional data.
-- ====================================================================

-- 1. Seed Communities (6 communities: 4 public, 2 private)
INSERT INTO public.communities (id, name, slug, description, category, is_private, creator_id, member_count, topics, created_at) VALUES
    ('comm-ai-001', 'MSGI AI & Robotics Guild', 'msgi-ai-robotics', 'Cross-disciplinary community for students and alumni building embodied AI, LLMs, and ROS systems.', 'Technology', false, 'user-kenji-001', 48, ARRAY['AI', 'Robotics', 'Python', 'ROS 2'], '2026-09-01T00:00:00Z'),
    ('comm-cloud-002', 'Cloud Native & DevOps Practitioners', 'cloud-native-devops', 'Architectural discussions on Kubernetes, Terraform, and high-availability cloud platforms.', 'Technology', false, 'user-ananya-002', 32, ARRAY['Cloud', 'Kubernetes', 'DevOps', 'GCP'], '2026-09-15T00:00:00Z'),
    ('comm-exec-003', 'Alumni Founders & Executive Circle', 'alumni-founders-circle', 'Private advisory council for vetted alumni startup founders and senior executives.', 'Entrepreneurship', true, 'user-admin-001', 12, ARRAY['Ventures', 'Leadership', 'Funding', 'Scale'], '2026-10-01T00:00:00Z'),
    ('comm-women-004', 'Women in STEM & Engineering Guild', 'women-in-stem-guild', 'Empowering women researchers, engineers, and student leaders through peer mentoring and executive sponsorships.', 'Leadership', false, 'user-ananya-002', 64, ARRAY['Mentorship', 'Leadership', 'Career', 'Engineering'], '2026-10-10T00:00:00Z'),
    ('comm-bio-005', 'Computational Biology & HealthTech Hub', 'comp-bio-healthtech', 'Interdisciplinary cluster investigating genomics, structural proteomics, and machine learning in medicine.', 'Life Sciences', false, 'user-david-003', 27, ARRAY['Bioinformatics', 'Genomics', 'Python', 'Machine Learning'], '2026-10-20T00:00:00Z'),
    ('comm-research-006', 'Postgraduate & Faculty Research Council', 'faculty-research-council', 'Restricted academic forum coordinating cross-institutional research grants and doctoral fellowships.', 'Academic', true, 'user-faculty-001', 15, ARRAY['Research', 'Grants', 'Publications', 'Peer Review'], '2026-11-01T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 2. Seed Community Memberships (12 memberships)
INSERT INTO public.community_memberships (id, community_id, user_id, role, status, joined_at) VALUES
    ('cm-001', 'comm-ai-001', 'user-kenji-001', 'moderator', 'active', '2026-09-01T00:00:00Z'),
    ('cm-002', 'comm-cloud-002', 'user-ananya-002', 'moderator', 'active', '2026-09-15T00:00:00Z'),
    ('cm-003', 'comm-exec-003', 'user-admin-001', 'moderator', 'active', '2026-10-01T00:00:00Z'),
    ('cm-004', 'comm-women-004', 'user-ananya-002', 'moderator', 'active', '2026-10-10T00:00:00Z'),
    ('cm-005', 'comm-bio-005', 'user-david-003', 'moderator', 'active', '2026-10-20T00:00:00Z'),
    ('cm-006', 'comm-research-006', 'user-faculty-001', 'moderator', 'active', '2026-11-01T00:00:00Z'),
    ('cm-007', 'comm-ai-001', 'user-student-001', 'member', 'active', '2026-10-05T00:00:00Z'),
    ('cm-008', 'comm-cloud-002', 'user-student-002', 'member', 'active', '2026-10-12T00:00:00Z'),
    ('cm-009', 'comm-women-004', 'user-student-002', 'member', 'active', '2026-10-15T00:00:00Z'),
    ('cm-010', 'comm-bio-005', 'user-kenji-001', 'member', 'active', '2026-10-22T00:00:00Z'),
    ('cm-011', 'comm-exec-003', 'user-yuki-004', 'member', 'pending', '2026-11-05T00:00:00Z'),
    ('cm-012', 'comm-research-006', 'user-student-001', 'member', 'pending', '2026-11-10T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 3. Seed Institutional Verification Requests (5 pending requests — do NOT auto-approve)
INSERT INTO public.verification_requests (id, user_id, user_email, requested_role, evidence_payload, status, created_at) VALUES
    ('vreq-001', 'user-candidate-001', 'candidate.alumni@example.msgi.edu', 'alumni', '{"graduation_year": 2023, "degree": "B.Tech Computer Science", "student_id": "MSGI-2019-CS-104", "diploma_url": "https://credentials.example.msgi.edu/verify/daiki-2023"}'::jsonb, 'pending', '2026-11-15T08:30:00Z'),
    ('vreq-002', 'user-candidate-002', 'candidate.faculty@example.msgi.edu', 'faculty', '{"department": "School of Electrical Engineering", "employee_id": "FAC-2026-908", "appointment_letter": "https://credentials.example.msgi.edu/verify/patel-appointment"}'::jsonb, 'pending', '2026-11-16T09:15:00Z'),
    ('vreq-003', 'user-student-001', 'student@example.msgi.edu', 'alumni', '{"graduation_year": 2026, "degree": "B.Tech Information Technology", "student_id": "MSGI-2022-IT-045", "provisional_certificate": "https://credentials.example.msgi.edu/verify/haruto-provisional"}'::jsonb, 'pending', '2026-11-17T11:00:00Z'),
    ('vreq-004', 'user-david-003', 'david.chen@example.msgi.edu', 'faculty', '{"position": "Adjunct Industry Lecturer", "course": "Embedded ROS 2 Robotics", "faculty_sponsor": "user-faculty-001"}'::jsonb, 'pending', '2026-11-18T14:20:00Z'),
    ('vreq-005', 'user-recruiter-001', 'talent@example.msgi.edu', 'recruiter', '{"company": "Rakuten Group", "corporate_domain": "rakuten.example.msgi.edu", "business_registration": "CORP-REG-JP-2026-88"}'::jsonb, 'pending', '2026-11-19T10:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 4. Seed Collaboration Projects (6 projects)
INSERT INTO public.projects (id, title, description, owner_id, required_skills, status, member_count, created_at) VALUES
    ('proj-agentic-001', 'Autonomous Agricultural Drone Perception Pipeline', 'Multi-spectral computer vision models for automated crop yield estimation and pest detection.', 'user-kenji-001', ARRAY['Python', 'PyTorch', 'ROS 2', 'Edge AI'], 'active', 4, '2026-09-10T00:00:00Z'),
    ('proj-health-002', 'Decentralized Clinical Trial Data Exchange', 'Privacy-preserving zero-knowledge verification for multi-institutional health analytics.', 'user-ananya-002', ARRAY['TypeScript', 'FastAPI', 'Cryptography', 'Zero Knowledge'], 'active', 3, '2026-10-01T00:00:00Z'),
    ('proj-slam-003', 'Autonomous Mobile Robot SLAM for Campus Logistics', 'Autonomous campus shuttle telemetry and indoor-outdoor LiDAR mapping using Nav2 and Cartographer.', 'user-david-003', ARRAY['C++', 'ROS 2', 'LiDAR', 'Sensor Fusion'], 'active', 5, '2026-10-15T00:00:00Z'),
    ('proj-mesh-004', 'Open-Source Microservices Mesh with eBPF', 'Zero-overhead distributed tracing and sidecar-less traffic security across Kubernetes pods.', 'user-yuki-004', ARRAY['Go', 'Kubernetes', 'eBPF', 'Linux'], 'active', 3, '2026-10-25T00:00:00Z'),
    ('proj-genomic-005', 'High-Throughput Genomic Variant Annotation Pipeline', 'Automated variant effect prediction workflow orchestrating Ensembl VEP, ClinVar, and AlphaGenome.', 'user-faculty-001', ARRAY['Python', 'Nextflow', 'Bioinformatics', 'FastAPI'], 'active', 4, '2026-11-05T00:00:00Z'),
    ('proj-career-006', 'Multi-Agent Campus Career Advisory System', 'Graph-orchestrated conversational career assistant pairing graduating seniors with alumni mentors.', 'user-kenji-001', ARRAY['Python', 'LangGraph', 'FastAPI', 'Vector Databases'], 'active', 2, '2026-11-12T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 5. Seed Startups (5 startups)
INSERT INTO public.startups (id, name, founder_id, industry, stage, tagline, website_url, seeking_mentors, seeking_talent, is_verified, created_at) VALUES
    ('start-neural-001', 'NeuralFlow Dynamics', 'user-kenji-001', 'Artificial Intelligence', 'seed', 'Real-time robotics inference acceleration using customized compiler toolchains.', 'https://neuralflow.example.msgi.edu', true, true, true, '2026-08-01T00:00:00Z'),
    ('start-agri-002', 'VerdantSense Systems', 'user-ananya-002', 'CleanTech / AgTech', 'early', 'Precision satellite soil telemetry for regenerative farming collectives.', 'https://verdantsense.example.msgi.edu', true, false, true, '2026-09-01T00:00:00Z'),
    ('start-robotics-003', 'BionicMotion Labs', 'user-david-003', 'Robotics', 'seed', 'Low-cost compliant robotic actuators for prosthetic mobility assistance.', 'https://bionicmotion.example.msgi.edu', false, true, true, '2026-09-20T00:00:00Z'),
    ('start-cloud-004', 'KubeSphere Cloud', 'user-yuki-004', 'DevOps & Infrastructure', 'growth', 'Automated multi-cloud failover orchestration for latency-critical workloads.', 'https://kubesphere.example.msgi.edu', false, true, true, '2026-10-05T00:00:00Z'),
    ('start-bio-005', 'HelixGen Therapeutics', 'user-faculty-001', 'BioTech', 'early', 'Targeted RNA therapeutics candidate discovery via structural deep learning.', 'https://helixgen.example.msgi.edu', true, true, true, '2026-10-25T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 6. Seed Impact Programmes (4 volunteering programmes — strictly NO live payments)
INSERT INTO public.impact_programmes (id, title, description, coordinator_name, programme_type, target_volunteers, current_volunteers, is_active, created_at) VALUES
    ('impact-stem-001', 'MSGI STEM Youth Outreach & Coding Mentorship', 'Alumni-led weekend computational thinking and Python workshops for underprivileged high school students.', 'MSGI Community Foundation', 'volunteering', 25, 14, true, '2026-08-15T00:00:00Z'),
    ('impact-sustain-002', 'Green Campus Solar & Urban Reforestation Drive', 'Collaborative biodiversity and clean energy auditing drive across institutional campus sites.', 'MSGI Sustainability Office', 'volunteering', 50, 38, true, '2026-09-01T00:00:00Z'),
    ('impact-mock-003', 'Alumni Mock Technical Interview Marathon', 'Senior alumni volunteer two hours to conduct live technical mock interviews for graduating students.', 'MSGI Career Placement Cell', 'mentorship_drive', 30, 22, true, '2026-09-20T00:00:00Z'),
    ('impact-civic-004', 'Disaster Preparedness Open Data Initiative', 'Open-source geospatial mapping and sensor calibration drive for municipal flood resilience.', 'MSGI Civic Technology Lab', 'community_outreach', 40, 19, true, '2026-10-10T00:00:00Z')
ON CONFLICT (id) DO NOTHING;
