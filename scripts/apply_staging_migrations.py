"""
MSGI One — Staging Database Migration & Verification Runner
Applies the 4 canonical migrations to the hosted Supabase PostgreSQL instance.
Strictly adheres to:
  - AGENTS.md Rule 7: Zero credential logging or exposure.
  - AGENTS.md Rule 10 & 16: Evidence-based verification.
  - AGENTS.md Rule 13 & 15: Authorized execution on staging.
"""

import os
import sys
import time
import ssl
import json
import asyncio
from pathlib import Path
from urllib.parse import urlparse, unquote

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg is required. Install via pip install asyncpg")
    sys.exit(1)


def load_env(env_path: Path):
    if not env_path.exists():
        print(f"ERROR: {env_path} does not exist.")
        sys.exit(1)
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


async def run_migrations():
    repo_root = Path(__file__).resolve().parent.parent
    load_env(repo_root / ".env")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set in environment.")
        sys.exit(1)

    normalized_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(normalized_url)
    user = parsed.username
    password = unquote(parsed.password or "")
    host = parsed.hostname or "aws-1-ap-south-1.pooler.supabase.com"
    port = parsed.port or 6543
    dbname = parsed.path.lstrip("/") or "postgres"

    print(f"Connecting to hosted staging PostgreSQL at: {host}:{port}/{dbname} ...")

    # SSL Context
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    start_time = time.time()
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=dbname,
            host=host,
            port=port,
            ssl=ssl_ctx,
            statement_cache_size=0
        )
        print("Connected successfully to hosted PostgreSQL database.")
    except Exception as e:
        print(f"ERROR: Failed to connect to PostgreSQL: {type(e).__name__}: {e}")
        sys.exit(1)

    try:
        # Pre-check database version and existing tables
        version = await conn.fetchval("SELECT version();")
        print(f"Database engine: {version.split()[0]} {version.split()[1]}")

        existing_tables_before = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        )
        before_names = [r["table_name"] for r in existing_tables_before]
        print(f"Existing public tables before migration: {len(before_names)}")

        # Migration files in order
        migrations_dir = repo_root / "supabase" / "migrations"
        migration_files = sorted([f for f in migrations_dir.glob("*.sql") if f.name.endswith(".sql")])
        print(f"Discovered {len(migration_files)} canonical migration(s) in {migrations_dir.name}:")
        for mf in migration_files:
            print(f"  - {mf.name}")

        migration_results = []
        for mf in migration_files:
            print(f"\nApplying migration: {mf.name} ...")
            m_sql = mf.read_text(encoding="utf-8")
            m_start = time.time()
            try:
                # Execute migration script
                await conn.execute(m_sql)
                m_duration = round(time.time() - m_start, 3)
                print(f"  [SUCCESS] Applied {mf.name} in {m_duration}s")
                migration_results.append({
                    "migration": mf.name,
                    "status": "SUCCESS",
                    "duration_seconds": m_duration,
                })
            except Exception as ex:
                m_duration = round(time.time() - m_start, 3)
                print(f"  [FAILED] Error applying {mf.name}: {ex}")
                migration_results.append({
                    "migration": mf.name,
                    "status": "FAILED",
                    "error": str(ex),
                    "duration_seconds": m_duration,
                })
                raise ex

        # Post-migration schema verification
        print("\nVerifying post-migration schema integrity ...")
        tables_records = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
        )
        tables = [r["table_name"] for r in tables_records]
        print(f"Total public tables created: {len(tables)}")

        # Verify RLS policies
        policies = await conn.fetch(
            "SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;"
        )
        print(f"Total RLS policies created: {len(policies)}")

        # Verify Indexes
        indexes = await conn.fetch(
            "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;"
        )
        print(f"Total indexes in public schema: {len(indexes)}")

        # Verify trigger on auth.users
        triggers = await conn.fetch("""
            SELECT trigger_name, event_manipulation, event_object_table, action_statement
            FROM information_schema.triggers
            WHERE event_object_table = 'users'
            ORDER BY trigger_name;
        """)
        auth_triggers = [dict(t) for t in triggers]
        print(f"Triggers on users table detected: {len(auth_triggers)}")
        has_auth_trigger = any(t.get("trigger_name") == "on_auth_user_created" for t in auth_triggers)
        print(f"  'on_auth_user_created' trigger attached: {has_auth_trigger}")

        # Verification report
        verification_data = {
            "status": "SUCCESS",
            "host": host,
            "port": port,
            "database": dbname,
            "total_tables_count": len(tables),
            "tables": tables,
            "total_rls_policies_count": len(policies),
            "total_indexes_count": len(indexes),
            "on_auth_user_created_trigger": has_auth_trigger,
            "migrations_applied": migration_results,
            "total_duration_seconds": round(time.time() - start_time, 3),
        }

        output_path = repo_root / "scripts" / "staging_db_verification.json"
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(verification_data, out, indent=2)
        print(f"\nVerification evidence written to: {output_path}")

    finally:
        await conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
