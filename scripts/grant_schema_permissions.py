import os
import ssl
import asyncio
from urllib.parse import urlparse, unquote
import asyncpg

env = {}
with open(".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

orig_db_url = env.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
parsed = urlparse(orig_db_url)
user = parsed.username
password = unquote(parsed.password or "")
host = parsed.hostname or "aws-1-ap-south-1.pooler.supabase.com"
port = parsed.port or 6543
dbname = parsed.path.lstrip("/") or "postgres"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

async def main():
    conn = await asyncpg.connect(
        user=user,
        password=password,
        database=dbname,
        host=host,
        port=port,
        ssl=ssl_ctx,
        statement_cache_size=0
    )
    print("Granting schema permissions to anon, authenticated, and service_role ...")
    await conn.execute("""
        GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
        GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
        GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO anon, authenticated, service_role;
        NOTIFY pgrst, 'reload schema';
    """)
    print("Permissions granted and pgrst notified successfully!")
    await conn.close()

asyncio.run(main())
