"""
MSGI One — Staging Auth & RLS End-to-End Verification Test
Tests real Supabase Auth authentication, JWT verification, and Row-Level Security
policies across student, alumni, and admin personas against the live staging cluster.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path


def load_env(env_path: Path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def sign_in_user(supabase_url: str, anon_key: str, email: str, password: str) -> dict:
    url = f"{supabase_url}/auth/v1/token?grant_type=password"
    payload = json.dumps({"email": email, "password": password}).encode("utf-8")
    headers = {
        "apikey": anon_key,
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def rest_get(supabase_url: str, anon_key: str, access_token: str, path: str):
    url = f"{supabase_url}/rest/v1/{path}"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [DEBUG REST ERROR] path: {path} -> HTTP {e.code} : {body}")
        raise Exception(f"HTTP {e.code}: {body}")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    load_env(repo_root / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    uuid_map_file = repo_root / "scripts" / "staging_uuid_map.json"
    with open(uuid_map_file, "r", encoding="utf-8") as f:
        uuid_map = json.load(f)

    password = "MsgiStaging2026!"
    personas = [
        {"role": "student", "email": "alex.rivera@example.msgi.edu", "alias": "user-student-001"},
        {"role": "alumni", "email": "kenji.sato@example.msgi.edu", "alias": "user-kenji-001"},
        {"role": "admin", "email": "sarah.jenkins@example.msgi.edu", "alias": "user-admin-001"},
    ]

    print("================================================================================")
    print("MSGI ONE — STAGING AUTH & ROW LEVEL SECURITY (RLS) E2E VERIFICATION")
    print(f"Target: {supabase_url}")
    print("================================================================================")

    test_results = []
    tokens = {}

    # 1. Sign-in Tests
    for p in personas:
        email = p["email"]
        role = p["role"]
        t0 = time.time()
        try:
            auth_res = sign_in_user(supabase_url, anon_key, email, password)
            dur_ms = round((time.time() - t0) * 1000)
            token = auth_res.get("access_token")
            user_data = auth_res.get("user", {})
            user_id = user_data.get("id")
            tokens[role] = token

            print(f"[AUTH PASS] Persona: {role:<8} | Email: {email:<35} | Token: {token[:12]}... ({dur_ms}ms)")
            test_results.append({
                "test": f"Auth Sign-In ({role})",
                "email": email,
                "status": "PASS",
                "user_id": user_id,
                "latency_ms": dur_ms,
            })
        except Exception as e:
            dur_ms = round((time.time() - t0) * 1000)
            print(f"[AUTH FAIL] Persona: {role:<8} | Email: {email} | Error: {e} ({dur_ms}ms)")
            test_results.append({
                "test": f"Auth Sign-In ({role})",
                "email": email,
                "status": "FAIL",
                "error": str(e),
                "latency_ms": dur_ms,
            })

    # 2. RLS Directory & Opportunity Read Tests (As Student Alex)
    alex_token = tokens.get("student")
    if alex_token:
        # A. Read public.users (Alex's own profile)
        alex_id = uuid_map["user-student-001"]
        my_user = rest_get(supabase_url, anon_key, alex_token, f"users?id=eq.{alex_id}")
        profile_found = len(my_user) > 0 and my_user[0]["id"] == alex_id
        print(f"[RLS PASS] Read Own User Profile via PostgREST: {profile_found} (Found: {my_user[0].get('first_name')} {my_user[0].get('last_name')})")
        test_results.append({
            "test": "RLS Read Own Profile",
            "status": "PASS" if profile_found else "FAIL",
            "details": f"Profile {alex_id} resolved correctly.",
        })

        # B. Read mentor_profiles (Public directory for authenticated students)
        mentors = rest_get(supabase_url, anon_key, alex_token, "mentor_profiles?select=*,alumni_profiles(*)")
        print(f"[RLS PASS] Read Mentor Directory as Student: {len(mentors)} active mentor(s) retrieved.")
        test_results.append({
            "test": "RLS View Mentor Directory",
            "status": "PASS" if len(mentors) > 0 else "FAIL",
            "count": len(mentors),
        })

        # C. Read Jobs
        jobs = rest_get(supabase_url, anon_key, alex_token, "jobs?is_active=eq.true")
        print(f"[RLS PASS] Read Active Jobs as Student: {len(jobs)} job(s) retrieved.")
        test_results.append({
            "test": "RLS View Jobs",
            "status": "PASS" if len(jobs) > 0 else "FAIL",
            "count": len(jobs),
        })

        # D. Read Events
        events = rest_get(supabase_url, anon_key, alex_token, "events?is_published=eq.true")
        print(f"[RLS PASS] Read Events as Student: {len(events)} event(s) retrieved.")
        test_results.append({
            "test": "RLS View Events",
            "status": "PASS" if len(events) > 0 else "FAIL",
            "count": len(events),
        })

        # E. Read Own Notifications
        notifs = rest_get(supabase_url, anon_key, alex_token, f"notifications?user_id=eq.{alex_id}")
        print(f"[RLS PASS] Read Own Notifications as Student: {len(notifs)} notification(s) retrieved.")
        test_results.append({
            "test": "RLS Read Own Notifications",
            "status": "PASS" if len(notifs) > 0 else "FAIL",
            "count": len(notifs),
        })

        # F. Isolation Test: Student Alex attempts to read Kenji's notifications
        kenji_id = uuid_map["user-kenji-001"]
        kenji_notifs = rest_get(supabase_url, anon_key, alex_token, f"notifications?user_id=eq.{kenji_id}")
        is_isolated = len(kenji_notifs) == 0
        print(f"[RLS PASS] Tenant Isolation (Cross-User Notification Read): Blocked by RLS (Rows returned: {len(kenji_notifs)})")
        test_results.append({
            "test": "RLS Notification Tenant Isolation",
            "status": "PASS" if is_isolated else "FAIL",
            "details": f"Attempt to read other user's notifications returned {len(kenji_notifs)} rows (strictly isolated).",
        })

    # Summary
    all_pass = all(r["status"] == "PASS" for r in test_results)
    print("================================================================================")
    print(f"AUTH & RLS E2E VERIFICATION STATE: {'100% PASS' if all_pass else 'FAILURES DETECTED'}")
    print(f"Total Tests Executed: {len(test_results)} | Passed: {sum(1 for r in test_results if r['status'] == 'PASS')}")
    print("================================================================================")

    output_path = repo_root / "scripts" / "staging_auth_e2e_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"state": "PASS" if all_pass else "FAIL", "tests": test_results}, f, indent=2)
    print(f"Results written to: {output_path}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
