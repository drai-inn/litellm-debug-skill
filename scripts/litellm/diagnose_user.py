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
import concurrent.futures
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

def check_inference(base_url, user_key, results):
    test_model_env = os.getenv("LITELLM_TEST_MODEL", "first")
    models_to_test = []
    
    if test_model_env not in ("all", "first"):
        models_to_test = [m.strip() for m in test_model_env.split(",") if m.strip()]
    else:
        # Fallback to fetch from /v1/models
        models_data = results.get("models", {})
        if models_data.get("status") == 200:
            try:
                parsed = json.loads(models_data["text"])
                models = parsed.get("data", [])
                if models:
                    if test_model_env == "first":
                        models_to_test = [models[0].get("id")]
                    elif test_model_env == "all":
                        models_to_test = [m.get("id") for m in models]
            except:
                pass
                
    if not models_to_test:
        return
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    
    results["inference"] = {}
    
    print("Testing inference capabilities across models...", file=sys.stderr)
    
    # Pre-populate the results structure
    for test_model in models_to_test:
        results["inference"][test_model] = {}
        
    def test_single_capability(test_model, name, payload):
        try:
            r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20)
            status_symbol = "✅" if r.status_code == 200 else ("⚠️" if r.status_code in (400, 403, 404) else "❌")
            print(f"  [{status_symbol}] {test_model[:15]:<15} - {name}", file=sys.stderr)
            return test_model, name, {
                "status": r.status_code,
                "headers": dict(r.headers),
                "text": r.text,
                "path": "/v1/chat/completions",
                "method": "POST",
                "payload": payload,
                "error": None
            }
        except Exception as e:
            print(f"  [❌] {test_model[:15]:<15} - {name} (Error)", file=sys.stderr)
            return test_model, name, {
                "status": None,
                "headers": {},
                "text": "",
                "path": "/v1/chat/completions",
                "method": "POST",
                "payload": payload,
                "error": str(e)
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for test_model in models_to_test:
            payloads = {
                "text": {
                    "model": test_model,
                    "messages": [{"role": "user", "content": "Hello, this is a diagnostic test. Please reply with 'OK'."}],
                    "max_tokens": 10
                },
                "tools": {
                    "model": test_model,
                    "messages": [{"role": "user", "content": "What is the weather in London?"}],
                    "tools": [{"type": "function", "function": {"name": "get_weather", "description": "Get current weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}],
                    "tool_choice": "auto",
                    "max_tokens": 20
                },
                "vision": {
                    "model": test_model,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": "What is in this image?"}, {"type": "image_url", "image_url": {"url": "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"}}]}],
                    "max_tokens": 10
                },
                "roundtrip": {
                    "model": test_model,
                    "messages": [
                        {"role": "user", "content": "What is the weather in London?"},
                        {"role": "assistant", "content": "I should check the weather.", "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"London\"}"}}]},
                        {"role": "tool", "tool_call_id": "call_123", "name": "get_weather", "content": "It is raining."}
                    ],
                    "max_tokens": 20
                }
            }
            
            for name, payload in payloads.items():
                futures.append(executor.submit(test_single_capability, test_model, name, payload))
                
        for future in concurrent.futures.as_completed(futures):
            test_model, name, res = future.result()
            results["inference"][test_model][name] = res
            
    print("Inference testing complete.\n", file=sys.stderr)

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
                "method": "GET",
                "error": None
            }
        except Exception as e:
            results[name] = {
                "status": None,
                "headers": {},
                "text": "",
                "path": path,
                "method": "GET",
                "error": str(e)
            }
            
    # Check Inference Capabilities
    check_inference(base_url, user_key, results)
    
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

    # 3. Inference Readiness
    print("\n▶ INFERENCE READINESS")
    if "inference" not in results or not results["inference"]:
        print("  ⚠️ Skipped:      No test model available.")
    else:
        # Helper to format capability status
        def format_cap(res):
            if not res: return " ➖ "
            if res.get("status") == 200:
                return " ✅ "
            elif res.get("status") in (400, 403, 404):
                return " ⚠️ "
            else:
                return " ❌ "
                
        print("  Model                           | Text | Tools | Vision | Round-Trip |")
        print("  --------------------------------+------+-------+--------+------------|")
        for test_model, caps in results["inference"].items():
            t_text = format_cap(caps.get("text"))
            t_tools = format_cap(caps.get("tools"))
            t_vis = format_cap(caps.get("vision"))
            t_rt = format_cap(caps.get("roundtrip"))
            
            # Truncate model name if too long
            disp_model = test_model[:29] + ("…" if len(test_model) > 30 else " " * (31 - len(test_model)))
            print(f"  {disp_model} | {t_text} | {t_tools}  | {t_vis}   | {t_rt}       |")

    print("\n" + "─"*59)
    print("💡 Next Step: To view the raw JSON payloads containing your")
    print("   permissions and models, run with `--level 1` or `--level 2`.")

def get_level_1_diagnostics(results, base_url, user_key):
    print("=== Level 1: Diagnostics ===\n")
    
    # Flatten results for unified printing
    flat_results = {k: v for k, v in results.items() if k != "inference"}
    if "inference" in results:
        for model, caps in results["inference"].items():
            for cap_name, data in caps.items():
                flat_results[f"inference_{model}_{cap_name}"] = data
                
    for name, data in flat_results.items():
        print(f"Diagnostics for `{name}` ({data['path']}):")
        if data['error']:
            print(f"  * Error: {data['error']}\n")
            continue
            
        status = data['status']
        c_type = data['headers'].get('Content-Type', '')
        excerpt = format_content(data['text'], c_type, level=1)
        url = f"{base_url.rstrip('/')}{data['path']}"
        method = data.get('method', 'GET')
        
        print(f"  * Status: {status}")
        print(f"  * Body Excerpt: {excerpt}")
        
        if method == "POST":
            payload_str = json.dumps(data.get('payload', {}))
            print(f"  * Drill Down: Run with `--level 2` or `curl -s -X POST -H \"Authorization: Bearer $LITELLM_USER_KEY\" -H \"Content-Type: application/json\" -d '{payload_str}' {url}`\n")
        else:
            print(f"  * Drill Down: Run with `--level 2` or `curl -s -H \"Authorization: Bearer $LITELLM_USER_KEY\" {url}`\n")

def get_level_2_traces(results, base_url, user_key):
    print("=== Level 2: Traces ===\n")
    
    flat_results = {k: v for k, v in results.items() if k != "inference"}
    if "inference" in results:
        for model, caps in results["inference"].items():
            for cap_name, data in caps.items():
                flat_results[f"inference_{model}_{cap_name}"] = data
                
    for name, data in flat_results.items():
        if data['error']:
            continue
            
        path = data['path']
        status = data['status']
        headers = data['headers']
        c_type = headers.get('Content-Type', '')
        method = data.get('method', 'GET')
        payload = data.get('payload', {})
        
        print(f"Full Trace for `{name}` ({path}):")
        print(f"```http\n> {method} {path} HTTP/1.1\n> Host: {base_url.replace('https://', '').replace('http://', '').rstrip('/')}")
        print(f"> Authorization: Bearer {user_key[:8]}...[REDACTED]\n> Accept: */*")
        
        if method == "POST":
            print("> Content-Type: application/json")
            print(f"\n{json.dumps(payload, indent=2)}\n")
            
        print(f"< HTTP/1.1 {status}")
        for k, v in headers.items():
            if k.lower() in ["content-type", "content-length", "date"]:
                print(f"< {k}: {v}")
        
        body = format_content(data['text'], c_type, level=2)
        print(f"\n{body}")
        print("```\n")
        
        url = f"{base_url.rstrip('/')}{path}"
        print("Reproduction Commands:")
        if method == "POST":
            payload_str = json.dumps(payload)
            print(f"  Raw Trace:   curl -v -X POST -H \"Authorization: Bearer $LITELLM_USER_KEY\" -H \"Content-Type: application/json\" -d '{payload_str}' {url}")
            if "application/json" in c_type.lower():
                print(f"  Pretty JSON: curl -s -X POST -H \"Authorization: Bearer $LITELLM_USER_KEY\" -H \"Content-Type: application/json\" -d '{payload_str}' {url} | jq")
        else:
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
