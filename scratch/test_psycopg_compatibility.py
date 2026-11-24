"""
Investigate psycopg compatibility with Supabase port 6543 (transaction pooler)
and port 5432 (session pooler) with WindowsSelectorEventLoopPolicy and exact credentials.
Evaluates prepare_threshold, autocommit, and dict_row.
"""

import asyncio
import sys
import psycopg
from psycopg.rows import dict_row
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

vals = dotenv_values(".env")
url = make_url(vals.get("DATABASE_URL"))

async def test_port(port_num, prepare_threshold):
    conninfo = f"host={url.host} port={port_num} dbname={url.database} user={url.username} password={url.password} sslmode=require"
    try:
        async with await psycopg.AsyncConnection.connect(
            conninfo,
            autocommit=True,
            prepare_threshold=prepare_threshold,
            row_factory=dict_row
        ) as aconn:
            for i in range(7):
                async with aconn.cursor() as cur:
                    await cur.execute("SELECT 1 as num, now() as current_time;")
                    row = await cur.fetchone()
            print(f"[SUCCESS] Port {port_num} (prepare_threshold={prepare_threshold}): executed 7 queries cleanly.")
            return True
    except Exception as e:
        print(f"[FAILED] Port {port_num} (prepare_threshold={prepare_threshold}): {type(e).__name__} - {e}")
        return False

async def main():
    print("Testing Port 6543 with default prepare_threshold=5...")
    await test_port(6543, 5)

    print("Testing Port 6543 with prepare_threshold=None (disabled prepared statements)...")
    await test_port(6543, None)

    print("Testing Port 5432 with default prepare_threshold=5 (Session Pooler)...")
    await test_port(5432, 5)

asyncio.run(main())
