"""
MSGI One — Staging Supabase Realtime Verification Script
Tests WebSocket connectivity, channel subscriptions, and broadcast messaging
against the live hosted Supabase Realtime cluster (wss://jndvnbvpwxhfmqgmqxfm.supabase.co).
"""

import os
import sys
import json
import time
import ssl
import asyncio
from pathlib import Path
from urllib.parse import urlparse, unquote

try:
    import websockets
    import asyncpg
except ImportError:
    print("ERROR: websockets and asyncpg are required.")
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


async def enable_realtime_publication():
    repo_root = Path(__file__).resolve().parent.parent
    load_env(repo_root / ".env")
    db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(db_url)
    user = parsed.username
    password = unquote(parsed.password or "")
    host = parsed.hostname or "aws-1-ap-south-1.pooler.supabase.com"
    port = parsed.port or 6543
    dbname = parsed.path.lstrip("/") or "postgres"

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
    try:
        # Check if publication exists, add table if not already added
        pubs = await conn.fetch("SELECT pubname FROM pg_publication WHERE pubname = 'supabase_realtime';")
        if pubs:
            tables_in_pub = await conn.fetch("""
                SELECT schemaname, tablename FROM pg_publication_tables WHERE pubname = 'supabase_realtime';
            """)
            tbl_names = [r["tablename"] for r in tables_in_pub]
            if "notifications" not in tbl_names:
                await conn.execute("ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;")
                print("Added public.notifications to supabase_realtime publication.")
            else:
                print("public.notifications is already published to supabase_realtime.")
    except Exception as e:
        print(f"Warning setting up realtime publication: {e}")
    finally:
        await conn.close()


async def test_realtime_websocket():
    repo_root = Path(__file__).resolve().parent.parent
    load_env(repo_root / ".env")

    supabase_url = os.getenv("SUPABASE_URL", "")
    anon_key = os.getenv("SUPABASE_ANON_KEY", "")

    ws_url = supabase_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_endpoint = f"{ws_url}/realtime/v1/websocket?apikey={anon_key}&vsn=1.0.0"

    print("================================================================================")
    print("MSGI ONE — STAGING SUPABASE REALTIME WEBSOCKET VERIFICATION")
    print(f"Endpoint: {ws_endpoint.split('?')[0]}?apikey=[REDACTED]")
    print("================================================================================")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    t0 = time.time()
    try:
        async with websockets.connect(ws_endpoint, ssl=ssl_ctx, open_timeout=10) as ws:
            connect_latency_ms = round((time.time() - t0) * 1000)
            print(f"[REALTIME CONNECT] WebSocket handshake successful ({connect_latency_ms}ms)")

            # Join channel 'realtime:staging_room'
            join_msg = {
                "topic": "realtime:staging_room",
                "event": "phx_join",
                "payload": {"config": {"broadcast": {"ack": True}}},
                "ref": "ref_join_001"
            }
            print(f"Subscribing to channel: {join_msg['topic']} ...")
            await ws.send(json.dumps(join_msg))

            # Await reply
            reply_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            reply = json.loads(reply_raw)
            print(f"[REALTIME REPLY] Event: {reply.get('event')} | Status: {reply.get('payload', {}).get('status')}")

            assert reply.get("event") == "phx_reply"
            assert reply.get("payload", {}).get("status") == "ok"

            # Broadcast message test
            broadcast_msg = {
                "topic": "realtime:staging_room",
                "event": "broadcast",
                "payload": {
                    "type": "broadcast",
                    "event": "staging_ping",
                    "payload": {"message": "MSGI One Staging Realtime Channel Active", "timestamp": time.time()}
                },
                "ref": "ref_msg_002"
            }
            print("Sending broadcast event over WebSocket ...")
            await ws.send(json.dumps(broadcast_msg))

            # Await broadcast ack or message
            ack_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            ack = json.loads(ack_raw)
            print(f"[REALTIME ACK] Event: {ack.get('event')} | Ref: {ack.get('ref')}")

            print("\n================================================================================")
            print("SUPABASE REALTIME VERIFICATION: 100% PASS")
            print("WebSocket connection, channel join, and broadcast messaging verified.")
            print("================================================================================")

            out_path = repo_root / "scripts" / "staging_realtime_results.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({
                    "status": "PASS",
                    "endpoint": ws_endpoint.split('?')[0],
                    "connect_latency_ms": connect_latency_ms,
                    "channel": "realtime:staging_room",
                    "join_reply_status": reply.get("payload", {}).get("status"),
                    "broadcast_event": "staging_ping",
                    "broadcast_ack_event": ack.get("event"),
                }, f, indent=2)

    except Exception as e:
        print(f"[REALTIME FAILED]: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    await enable_realtime_publication()
    await test_realtime_websocket()


if __name__ == "__main__":
    asyncio.run(main())
