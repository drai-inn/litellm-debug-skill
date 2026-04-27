#!/usr/bin/env python3
"""
User Tier Diagnostic Tool

Runs the user tier endpoint checks and outputs the results using
progressive disclosure (Levels 0, 1, and 2).

Usage:
    python scripts/litellm/diagnose_user.py [--level 0|1|2]
"""
import os
import sys
import argparse
import requests
import json
from dotenv import load_dotenv

# Re-use content formatter from public diagnostics
sys.path.append(os.path.dirname(__file__))
try:
    from diagnose_public import format_content
except ImportError:
    def format_content(text, content_type, level=1):
        return text[:100] + "..."

load_dotenv()

CATEGORIES = {
    "Identity & Scoping": {
        "key_info": "/key/info",
        "user_info": "/user/info"
    },
    "Model Access": {
        "models": "/v1/models"
    }
}

ENDPOINTS = {name: path for cat in CATEGORIES.values() for name, path in cat.items()}

def check_endpoints(base_url, user_key):
    results = {}
    headers = {"Authorization": f"Bearer {user_key}"}
    for name, path in ENDPOINTS.items():
        try:
            r = requests.get(f"{base_url}{path}", headers=headers, timeout=5)
            results[name] = {
                "status": r.status_code,
                "headers": dict(r.headers),
                "text": r.text,
                "path": path,
                "error": None
            }
        except Exception as e:
            results[name] = {
                "status": None,
                "headers": {},
                "text": "",
                "path": path,
                "error": str(e)
            }
    return results

def get_level_0_summary(results):
    print("┌───────────────────────────────────────────────────────────┐")
    print("│               LITELLM USER TIER DASHBOARD                 │")
    print("└───────────────────────────────────────────────────────────┘\n")
    
    # Parse Key Info
    key_info = results.get("key_info", {})
    key_data = {}
    if key_info.get("status") == 200:
        try:
            parsed = json.loads(key_info["text"])
            key_data = parsed.get("info", parsed) # Handles wrapped 'info' vs unwrapped
        except:
            pass

    # Parse User Info
    user_info = results.get("user_info", {})
    user_data = {}
    if user_info.get("status") == 200:
        try:
            parsed = json.loads(user_info["text"])
            user_data = parsed.get("user_info", parsed)
        except:
            pass

    # 1. Identity & Scoping
    print("▶ IDENTITY & SCOPING")
    if key_info.get("status") in (401, 403):
        print("  ❌ Key Identity: Invalid or Unauthenticated")
    else:
        alias = key_data.get("key_alias") or key_data.get("key_name") or "Unknown"
        print(f"  🔑 Key Identity: Valid (Alias: `{alias}`)")
        
        team_alias = key_data.get("team_alias")
        team_id = key_data.get("team_id")
        user_email = user_data.get("user_email")
        owner_str = f"User `{user_email}`" if user_email else "Unknown User"
        if team_alias and team_alias != "None":
            owner_str += f", Team `{team_alias}`"
        elif team_id:
            owner_str += f", Team ID `{team_id}`"
        print(f"  🛡️  Owner:        {owner_str}")
        
        spend = key_data.get("spend", 0.0)
        max_budget = key_data.get("max_budget")
        budget_str = f"${spend:.4f} / ${max_budget:.2f} spent" if max_budget else f"${spend:.4f} spent (No limit)"
        print(f"  💰 Budget:       {budget_str}")
        
        tpm = key_data.get("tpm_limit")
        rpm = key_data.get("rpm_limit")
        rate_str = []
        if tpm: rate_str.append(f"{tpm} TPM")
        if rpm: rate_str.append(f"{rpm} RPM")
        print(f"  🚦 Rate Limits:  {' / '.join(rate_str) if rate_str else 'No limits configured'}")

    # 2. Model Access
    print("\n▶ MODEL ACCESS")
    models = results.get("models", {})
    if models.get("status") == 200:
        try:
            parsed = json.loads(models["text"])
            model_list = parsed.get("data", [])
            print(f"  🤖 Permitted:    {len(model_list)} models available via this key")
            # If the list is short, show a few
            if 0 < len(model_list) <= 5:
                names = [m.get("id", "unknown") for m in model_list]
                print(f"                   ({', '.join(names)})")
        except:
            print("  🤖 Permitted:    Could not parse model list")
    elif models.get("status") in (401, 403):
         print("  ❌ Permitted:    Key lacks permission to list models")
    else:
         print(f"  ❓ Permitted:    Unexpected status {models.get('status')}")

    print("\n" + "─"*59)
    print("💡 Next Step: To view the raw JSON payloads containing your")
    print("   permissions and models, run with `--level 1` or `--level 2`.")

def get_level_1_diagnostics(results, base_url, user_key):
    print("=== Level 1: Diagnostics ===\n")
    for name, data in results.items():
        print(f"Diagnostics for `{data['path']}`:")
        if data['error']:
            print(f"  * Error: {data['error']}\n")
            continue
            
        status = data['status']
        c_type = data['headers'].get('Content-Type', '')
        excerpt = format_content(data['text'], c_type, level=1)
        url = f"{base_url.rstrip('/')}{data['path']}"
        
        print(f"  * Status: {status}")
        print(f"  * Body Excerpt: {excerpt}")
        print(f"  * Drill Down: Run with `--level 2` or `curl -s -H \"Authorization: Bearer $LITELLM_USER_KEY\" {url}`\n")

def get_level_2_traces(results, base_url, user_key):
    print("=== Level 2: Traces ===\n")
    for name, data in results.items():
        if data['error']:
            continue
            
        path = data['path']
        status = data['status']
        headers = data['headers']
        c_type = headers.get('Content-Type', '')
        
        print(f"Full Trace for `{path}`:")
        print(f"```http\n> GET {path} HTTP/1.1\n> Host: {base_url.replace('https://', '').replace('http://', '').rstrip('/')}")
        print(f"> Authorization: Bearer {user_key[:8]}...[REDACTED]\n> Accept: */*\n")
        print(f"< HTTP/1.1 {status}")
        for k, v in headers.items():
            if k.lower() in ["content-type", "content-length", "date"]:
                print(f"< {k}: {v}")
        
        body = format_content(data['text'], c_type, level=2)
        print(f"\n{body}")
        print("```\n")
        
        url = f"{base_url.rstrip('/')}{path}"
        print("Reproduction Commands:")
        print(f"  Raw Trace:   curl -v -H \"Authorization: Bearer $LITELLM_USER_KEY\" {url}")
        if "application/json" in c_type.lower():
            print(f"  Pretty JSON: curl -s -H \"Authorization: Bearer $LITELLM_USER_KEY\" {url} | jq")
        print()

def main():
    parser = argparse.ArgumentParser(description="LiteLLM User Tier Diagnostics")
    parser.add_argument("--level", type=int, choices=[0, 1, 2], default=0, help="Verbosity level (0=Summary, 1=Diagnostics, 2=Traces)")
    args = parser.parse_args()

    base_url = os.getenv("LITELLM_BASE_URL")
    user_key = os.getenv("LITELLM_USER_KEY")
    
    if not base_url or not user_key:
        print("Error: LITELLM_BASE_URL and LITELLM_USER_KEY must be set in .env")
        sys.exit(1)

    results = check_endpoints(base_url, user_key)

    if args.level >= 0:
        get_level_0_summary(results)
    if args.level >= 1:
        print("\n" + "="*50 + "\n")
        get_level_1_diagnostics(results, base_url, user_key)
    if args.level == 2:
        print("\n" + "="*50 + "\n")
        get_level_2_traces(results, base_url, user_key)

if __name__ == "__main__":
    main()
