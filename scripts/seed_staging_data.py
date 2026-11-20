"""
MSGI One — Staging Synthetic Data Seeder & Auth Provisioner
Provisions synthetic test accounts in Supabase Auth and seeds all 12 modules
into the hosted staging PostgreSQL instance.
Adheres strictly to:
  - AGENTS.md Rule 7: Zero credential logging or exposure.
  - AGENTS.md Rule 9: Synthetic data strictly on @example.msgi.edu.
  - AGENTS.md Rule 10 & 16: Evidence-based verification.
"""

import os
import sys
import time
import ssl
import json
import asyncio
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, unquote

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg is required.")
    sys.exit(1)


def load_env(env_path: Path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def get_or_create_auth_user(supabase_url: str, service_key: str, email: str, password: str, metadata: dict) -> str:
    """Create or retrieve a user in Supabase Auth via Admin API."""
    # First, list users to check if already exists
    list_url = f"{supabase_url}/auth/v1/admin/users"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(f"{list_url}?page=1&per_page=100", headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            for u in data.get("users", []):
                if u.get("email", "").lower() == email.lower():
                    return u["id"]
    except Exception as e:
        print(f"Warning: could not list users: {e}")

    # Create user
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": metadata,
        "app_metadata": {"provider": "email", "providers": ["email"], "roles": [metadata.get("requested_role", "student")]}
    }
    req = urllib.request.Request(list_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode())
            return res["id"]
    except urllib.error.HTTPError as he:
        body = he.read().decode()
        if "already exists" in body or "email_exists" in body:
            # Re-fetch user ID
            req = urllib.request.Request(f"{list_url}?page=1&per_page=100", headers=headers)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                for u in data.get("users", []):
                    if u.get("email", "").lower() == email.lower():
                        return u["id"]
        raise Exception(f"Failed to create auth user {email}: {body}")


async def seed_staging():
    repo_root = Path(__file__).resolve().parent.parent
    load_env(repo_root / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://", 1)

    parsed = urlparse(db_url)
    user = parsed.username
    password = unquote(parsed.password or "")
    host = parsed.hostname or "aws-1-ap-south-1.pooler.supabase.com"
    port = parsed.port or 6543
    dbname = parsed.path.lstrip("/") or "postgres"

    print("================================================================================")
    print("MSGI ONE — STAGING SYNTHETIC AUTH & DATA PROVISIONING PIPELINE")
    print("================================================================================")

    # 1. Provision 14 Synthetic Auth Users
    test_users = [
        {"alias": "user-student-001", "email": "alex.rivera@example.msgi.edu", "first": "Alex", "last": "Rivera", "role": "student"},
        {"alias": "user-student-002", "email": "jordan.smith@example.msgi.edu", "first": "Jordan", "last": "Smith", "role": "student"},
        {"alias": "user-student-phase4-001", "email": "priya.nair@example.msgi.edu", "first": "Priya", "last": "Nair", "role": "student"},
        {"alias": "user-student-phase4-002", "email": "lucas.vance@example.msgi.edu", "first": "Lucas", "last": "Vance", "role": "student"},
        {"alias": "student-journey-uuid-999", "email": "student.journey@example.msgi.edu", "first": "Journey", "last": "Student", "role": "student"},
        {"alias": "user-kenji-001", "email": "kenji.sato@example.msgi.edu", "first": "Kenji", "last": "Sato", "role": "alumni"},
        {"alias": "user-ananya-002", "email": "ananya.sharma@example.msgi.edu", "first": "Ananya", "last": "Sharma", "role": "alumni"},
        {"alias": "user-david-003", "email": "david.chen@example.msgi.edu", "first": "David", "last": "Chen", "role": "alumni"},
        {"alias": "user-yuki-004", "email": "yuki.tanaka@example.msgi.edu", "first": "Yuki", "last": "Tanaka", "role": "alumni"},
        {"alias": "user-candidate-001", "email": "maya.patel@example.msgi.edu", "first": "Maya", "last": "Patel", "role": "alumni", "verified": False},
        {"alias": "user-candidate-002", "email": "carlos.mendez@example.msgi.edu", "first": "Carlos", "last": "Mendez", "role": "alumni", "verified": False},
        {"alias": "user-faculty-001", "email": "robert.zhang@example.msgi.edu", "first": "Robert", "last": "Zhang", "role": "faculty"},
        {"alias": "user-recruiter-001", "email": "elena.rostova@example.msgi.edu", "first": "Elena", "last": "Rostova", "role": "recruiter"},
        {"alias": "user-admin-001", "email": "sarah.jenkins@example.msgi.edu", "first": "Sarah", "last": "Jenkins", "role": "admin"},
    ]

    default_pw = "MsgiStaging2026!"
    uuid_map = {}

    print("Provisioning 14 Synthetic Accounts in Supabase Auth ...")
    for u in test_users:
        meta = {
            "first_name": u["first"],
            "last_name": u["last"],
            "requested_role": u["role"],
        }
        uid = get_or_create_auth_user(supabase_url, service_key, u["email"], default_pw, meta)
        uuid_map[u["alias"]] = uid
        u["uuid"] = uid
        print(f"  [PROVISIONED] {u['email']:<35} -> Auth UUID: {uid[:8]}... (Role: {u['role']})")

    # Save mapping file
    uuid_map_file = repo_root / "scripts" / "staging_uuid_map.json"
    with open(uuid_map_file, "w", encoding="utf-8") as f:
        json.dump(uuid_map, f, indent=2)
    print(f"Auth UUID mapping cached to: {uuid_map_file}")

    # 2. Connect to Hosted PostgreSQL to update user roles, sub-profiles, and business entities
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    conn = await asyncpg.connect(
        user=user,
        password=password,
        database=dbname,
        host=host,
        port=port,
        ssl=ssl_ctx,
        statement_cache_size=0
    )
    print("\nConnected to hosted PostgreSQL for relational data seeding ...")

    try:
        # A. Update public.users and assign roles
        for u in test_users:
            uid = u["uuid"]
            role = u["role"]
            req_role = "faculty" if role == "admin" else role
            is_ver = u.get("verified", True)
            await conn.execute("""
                INSERT INTO public.users (id, email, first_name, last_name, requested_role, is_verified, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, true)
                ON CONFLICT (id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    requested_role = EXCLUDED.requested_role,
                    is_verified = EXCLUDED.is_verified,
                    updated_at = now();
            """, uid, u["email"], u["first"], u["last"], req_role, is_ver)

            # Assign specific role
            await conn.execute("""
                INSERT INTO public.user_roles (user_id, role_id)
                VALUES ($1, $2)
                ON CONFLICT (user_id, role_id) DO NOTHING;
            """, uid, role)

        print("Updated public.users and assigned explicit roles in public.user_roles.")

        # B. Alumni Profiles
        kenji_id = uuid_map["user-kenji-001"]
        ananya_id = uuid_map["user-ananya-002"]
        david_id = uuid_map["user-david-003"]
        yuki_id = uuid_map["user-yuki-004"]

        alumni_data = [
            (kenji_id, 2018, "B.Tech", "Computer Science", "Staff AI Engineer at Rakuten Symphony", "Rakuten Symphony", "Staff AI Engineer", "Artificial Intelligence", "Specialising in distributed deep learning infrastructure and large language model serving."),
            (ananya_id, 2019, "B.Tech", "Computer Science", "Senior Product Manager at Microsoft", "Microsoft", "Senior Product Manager", "Cloud Computing", "Guiding next-generation engineers in transitioning from code to technical product ownership."),
            (david_id, 2015, "B.Tech", "Business & IT", "Principal Product Manager at Grab", "Grab", "Principal Product Manager", "Technology", "Leading urban mobility solutions and mentoring early-career PMs across Southeast Asia."),
            (yuki_id, 2021, "B.Tech", "Data Science", "Machine Learning Specialist at Sony", "Sony", "ML Specialist", "Entertainment & AI", "Researching real-time audio neural synthesis and spatial audio models."),
        ]

        alumni_profile_ids = {}
        for uid, yr, deg, maj, head, comp, titl, ind, bio in alumni_data:
            pid = await conn.fetchval("""
                INSERT INTO public.alumni_profiles (user_id, graduation_year, degree, major, headline, current_company, current_title, industry, bio, visibility)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'institutional')
                ON CONFLICT (user_id) DO UPDATE SET
                    headline = EXCLUDED.headline,
                    current_company = EXCLUDED.current_company,
                    current_title = EXCLUDED.current_title
                RETURNING id;
            """, uid, yr, deg, maj, head, comp, titl, ind, bio)
            alumni_profile_ids[uid] = pid

        print("Seeded 4 verified alumni profiles.")

        # C. Student Profiles
        alex_id = uuid_map["user-student-001"]
        jordan_id = uuid_map["user-student-002"]
        journey_id = uuid_map["student-journey-uuid-999"]

        student_data = [
            (alex_id, "MSGI-2021-CS-042", 2021, 2025, "Computer Science", "B.Tech Computer Science", 8.9),
            (jordan_id, "MSGI-2022-EE-108", 2022, 2026, "Electrical Engineering", "B.Tech Electrical", 9.1),
            (journey_id, "MSGI-2022-CS-999", 2022, 2025, "Computer Science", "B.Tech Computer Science", 9.4),
        ]
        for sid, roll, ey, gy, dept, prog, cg in student_data:
            await conn.execute("""
                INSERT INTO public.student_profiles (user_id, roll_number, enrollment_year, expected_graduation_year, department, degree_program, cgpa)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO NOTHING;
            """, sid, roll, ey, gy, dept, prog, cg)

        print("Seeded 3 student profiles.")

        # D. Mentor Profiles (Kenji, Ananya, Yuki)
        for uid in [kenji_id, ananya_id, yuki_id]:
            apid = alumni_profile_ids[uid]
            await conn.execute("""
                INSERT INTO public.mentor_profiles (alumni_id, user_id, is_accepting_requests, max_active_mentees, current_active_mentees, advisory_topics, preferred_frequency, bio)
                VALUES ($1, $2, true, 3, 1, ARRAY['AI Career Pathways', 'Distributed Systems', 'Interview Prep'], 'bi-weekly', 'Dedicated to coaching MSGI students toward tier-1 engineering roles.')
                ON CONFLICT (user_id) DO UPDATE SET is_accepting_requests = true;
            """, apid, uid)

        print("Seeded 3 active mentor profiles.")

        # E. Career Role Skills & Learning Resources
        role_skills = [
            ("ml_engineer", "Machine Learning Engineer", "Python", "Advanced", 5),
            ("ml_engineer", "Machine Learning Engineer", "PyTorch", "Intermediate", 4),
            ("ml_engineer", "Machine Learning Engineer", "Docker", "Intermediate", 3),
            ("cloud_architect", "Cloud Solutions Architect", "Docker", "Advanced", 5),
            ("cloud_architect", "Cloud Solutions Architect", "Kubernetes", "Advanced", 5),
            ("fullstack_dev", "Full Stack Developer", "TypeScript", "Advanced", 5),
            ("fullstack_dev", "Full Stack Developer", "FastAPI", "Intermediate", 4),
        ]
        for rid, rname, sname, lvl, wt in role_skills:
            await conn.execute("""
                INSERT INTO public.career_role_skills (role_id, role_name, skill_name, required_level, importance_weight)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (role_id, skill_name) DO NOTHING;
            """, rid, rname, sname, lvl, wt)

        learning_resources = [
            ("res-fastapi-01", "Production FastAPI Microservices", "MSGI Engineering", "FastAPI", "Intermediate", 12.0, "https://academy.example.msgi.edu/fastapi", 4.9),
            ("res-pytorch-01", "Deep Learning with PyTorch", "DeepLearning.AI", "PyTorch", "Advanced", 24.0, "https://academy.example.msgi.edu/pytorch", 4.8),
            ("res-docker-01", "Containerization & Cloud Native", "Cloud Native Foundation", "Docker", "Intermediate", 16.0, "https://academy.example.msgi.edu/docker", 4.7),
        ]
        for rid, titl, prov, tsk, diff, dur, url, rat in learning_resources:
            await conn.execute("""
                INSERT INTO public.learning_resources (resource_id, title, provider, target_skill, difficulty, duration_hours, url, rating)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (resource_id) DO NOTHING;
            """, rid, titl, prov, tsk, diff, dur, url, rat)

        print("Seeded Career Role Skills & Learning Resources.")

        # F. Jobs & Events
        recruiter_id = uuid_map["user-recruiter-001"]
        admin_id = uuid_map["user-admin-001"]

        await conn.execute("""
            INSERT INTO public.jobs (creator_id, title, company, location, country, opportunity_type, workplace_type, description, required_skills, is_active, is_verified_listing)
            VALUES ($1, 'Graduate AI Research Engineer', 'Rakuten Symphony', 'Tokyo', 'Japan', 'full_time', 'hybrid',
                    'Join our foundational robotics AI research team working on multi-modal autonomy.',
                    ARRAY['Python', 'PyTorch', 'ROS 2'], true, true);
        """, kenji_id)

        await conn.execute("""
            INSERT INTO public.jobs (creator_id, title, company, location, country, opportunity_type, workplace_type, description, required_skills, is_active, is_verified_listing)
            VALUES ($1, 'Junior Cloud Infrastructure Associate', 'CloudNative Labs', 'London', 'UK', 'full_time', 'remote',
                    'Exciting opportunity for MSGI graduates in Kubernetes cluster reliability engineering.',
                    ARRAY['Docker', 'Kubernetes', 'Linux', 'Go'], true, true);
        """, recruiter_id)

        await conn.execute("""
            INSERT INTO public.events (organizer_id, title, event_type, description, location, is_virtual, start_time, end_time, max_capacity, is_published)
            VALUES ($1, 'Global MSGI Tech Summit & Alumni Reunion 2026', 'conference',
                    'Annual flagship ecosystem reunion featuring executive keynotes and technical workshops.',
                    'MSGI Tokyo Innovation Hall', false, now() + interval '14 days', now() + interval '15 days', 250, true);
        """, admin_id)

        print("Seeded Jobs and Events.")

        # G. Extended Modules (Communities, Projects, Startups, Impact)
        # Communities
        comm1_id = await conn.fetchval("""
            INSERT INTO public.communities (name, slug, description, category, is_private, creator_id, member_count, topics)
            VALUES ('MSGI AI & Robotics Guild', 'msgi-ai-robotics', 'Community for students and alumni building embodied AI and ROS systems.', 'Technology', false, $1, 48, ARRAY['AI', 'Robotics', 'Python'])
            ON CONFLICT (slug) DO UPDATE SET member_count = EXCLUDED.member_count
            RETURNING id;
        """, kenji_id)

        comm2_id = await conn.fetchval("""
            INSERT INTO public.communities (name, slug, description, category, is_private, creator_id, member_count, topics)
            VALUES ('Cloud Native & DevOps Practitioners', 'cloud-native-devops', 'Architectural discussions on Kubernetes and high-availability cloud.', 'Technology', false, $1, 32, ARRAY['Cloud', 'Kubernetes', 'DevOps'])
            ON CONFLICT (slug) DO UPDATE SET member_count = EXCLUDED.member_count
            RETURNING id;
        """, ananya_id)

        # Community Memberships
        for cid, uid, r, s in [(comm1_id, kenji_id, 'moderator', 'active'), (comm1_id, alex_id, 'member', 'active'), (comm2_id, ananya_id, 'moderator', 'active'), (comm2_id, jordan_id, 'member', 'active')]:
            await conn.execute("""
                INSERT INTO public.community_memberships (community_id, user_id, role, status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (community_id, user_id) DO NOTHING;
            """, cid, uid, r, s)

        # Projects
        await conn.execute("""
            INSERT INTO public.projects (title, description, owner_id, required_skills, status, member_count)
            VALUES ('Autonomous Agricultural Drone Perception Pipeline', 'Multi-spectral computer vision for automated crop yield estimation.', $1, ARRAY['Python', 'PyTorch', 'ROS 2'], 'active', 4);
        """, kenji_id)

        # Startups
        await conn.execute("""
            INSERT INTO public.startups (name, founder_id, industry, stage, tagline, website_url, seeking_mentors, seeking_talent, is_verified)
            VALUES ('NeuralFlow Dynamics', $1, 'Artificial Intelligence', 'seed', 'Real-time robotics inference acceleration using custom toolchains.', 'https://neuralflow.example.msgi.edu', true, true, true);
        """, kenji_id)

        # Impact Programmes
        await conn.execute("""
            INSERT INTO public.impact_programmes (title, description, coordinator_id, programme_type, target_volunteers, current_volunteers, is_active)
            VALUES ('MSGI STEM Youth Outreach & Coding Mentorship', 'Alumni-led weekend computational thinking workshops for high schoolers.', $1, 'volunteering', 25, 14, true);
        """, admin_id)

        # Notifications
        await conn.execute("""
            INSERT INTO public.notifications (user_id, event_type, entity_id, title, message, is_read)
            VALUES ($1, 'system_welcome', 'welcome-001', 'Welcome to MSGI One Staging', 'Your institutional account has been successfully provisioned.', false);
        """, alex_id)

        print("Seeded Communities, Memberships, Projects, Startups, Impact, and Notifications.")

        # Count tables with records
        tables_with_records = await conn.fetch("""
            SELECT 'users' as tbl, count(*) as cnt FROM public.users
            UNION ALL SELECT 'user_roles', count(*) FROM public.user_roles
            UNION ALL SELECT 'alumni_profiles', count(*) FROM public.alumni_profiles
            UNION ALL SELECT 'student_profiles', count(*) FROM public.student_profiles
            UNION ALL SELECT 'mentor_profiles', count(*) FROM public.mentor_profiles
            UNION ALL SELECT 'jobs', count(*) FROM public.jobs
            UNION ALL SELECT 'events', count(*) FROM public.events
            UNION ALL SELECT 'communities', count(*) FROM public.communities
            UNION ALL SELECT 'community_memberships', count(*) FROM public.community_memberships
            UNION ALL SELECT 'projects', count(*) FROM public.projects
            UNION ALL SELECT 'startups', count(*) FROM public.startups
            UNION ALL SELECT 'impact_programmes', count(*) FROM public.impact_programmes
            UNION ALL SELECT 'notifications', count(*) FROM public.notifications;
        """)

        print("\n================================================================================")
        print("SEEDING SUMMARY BY TABLE:")
        print("--------------------------------------------------------------------------------")
        for row in tables_with_records:
            print(f"  {row['tbl']:<25} : {row['cnt']} record(s)")
        print("================================================================================")

    finally:
        await conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(seed_staging())
