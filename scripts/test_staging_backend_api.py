"""
MSGI One — Staging FastAPI Backend Integration Test
Executes comprehensive end-to-end API requests against the FastAPI application
using authentic JWT tokens issued by the live Supabase Auth staging cluster.
"""

import sys
import os
import json
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "services" / "api"))

# Load staging environment
from src.core.config import settings

# Test client
from fastapi.testclient import TestClient
from src.main import app

def main():
    print("================================================================================")
    print("MSGI ONE — STAGING FASTAPI BACKEND API VERIFICATION")
    print(f"Project: {settings.PROJECT_NAME} | Environment: {settings.ENVIRONMENT}")
    print("================================================================================")

    # Load authentic tokens
    uuid_map_file = repo_root / "scripts" / "staging_uuid_map.json"
    with open(uuid_map_file, "r", encoding="utf-8") as f:
        uuid_map = json.load(f)

    auth_results_file = repo_root / "scripts" / "staging_auth_e2e_results.json"
    
    # We fetch a fresh student token via Supabase Auth
    import urllib.request
    login_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
    login_payload = json.dumps({"email": "alex.rivera@example.msgi.edu", "password": "MsgiStaging2026!"}).encode()
    login_headers = {"apikey": settings.SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    
    req = urllib.request.Request(login_url, data=login_payload, headers=login_headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        alex_token = json.loads(resp.read().decode())["access_token"]
    
    print(f"Acquired live Supabase Bearer token for Alex Rivera (student).")

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {alex_token}"}

    endpoints_to_test = [
        {"method": "GET", "url": "/health", "auth": False, "name": "System Health Check"},
        {"method": "GET", "url": "/api/v1/health", "auth": False, "name": "Versioned Health Check"},
        {"method": "GET", "url": "/api/v1/users/me", "auth": True, "name": "Current Profile (/users/me)"},
        {"method": "GET", "url": "/api/v1/alumni", "auth": True, "name": "Alumni Directory"},
        {"method": "GET", "url": "/api/v1/jobs", "auth": True, "name": "CareerBridge Job Listings"},
        {"method": "GET", "url": "/api/v1/mentors", "auth": True, "name": "MentorMatch Roster"},
        {"method": "GET", "url": "/api/v1/events", "auth": True, "name": "Events & Reunions"},
        {"method": "GET", "url": "/api/v1/communities", "auth": True, "name": "Communities & Interest Groups"},
        {"method": "GET", "url": "/api/v1/notifications", "auth": True, "name": "Realtime Notifications Roster"},
        {"method": "POST", "url": "/api/v1/ai/chat", "auth": True, "name": "AI Command Centre Chat", "json": {"prompt": "I need guidance on machine learning engineer careers"}},
    ]

    results = []
    print(f"\n{'ENDPOINT':<35} | {'STATUS':<7} | {'HTTP':<5} | {'LATENCY':<8}")
    print("-" * 65)

    all_pass = True
    for ep in endpoints_to_test:
        req_headers = headers if ep["auth"] else {}
        t0 = time.time()
        
        if ep["method"] == "GET":
            response = client.get(ep["url"], headers=req_headers)
        else:
            response = client.post(ep["url"], headers=req_headers, json=ep.get("json", {}))
            
        latency_ms = round((time.time() - t0) * 1000)
        status_code = response.status_code
        is_ok = status_code in (200, 201)

        if not is_ok:
            all_pass = False

        status_label = "PASS" if is_ok else "FAIL"
        print(f"{ep['name']:<35} | {status_label:<7} | {status_code:<5} | {latency_ms:<5}ms")

        results.append({
            "name": ep["name"],
            "url": ep["url"],
            "method": ep["method"],
            "status": status_label,
            "http_status": status_code,
            "latency_ms": latency_ms,
        })

    print("================================================================================")
    print(f"FASTAPI BACKEND VERIFICATION STATE: {'100% PASS' if all_pass else 'FAILURES DETECTED'}")
    print(f"Total Tested: {len(results)} | Passed: {sum(1 for r in results if r['status'] == 'PASS')}")
    print("================================================================================")

    out_path = repo_root / "scripts" / "staging_backend_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"state": "PASS" if all_pass else "FAIL", "endpoints": results}, f, indent=2)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
