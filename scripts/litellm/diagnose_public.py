#!/usr/bin/env python3
"""
Public Tier Diagnostic Tool

Runs the public tier endpoint checks and outputs the results using
progressive disclosure (Levels 0, 1, and 2).

Usage:
    python scripts/litellm/diagnose_public.py [--level 0|1|2]
"""
import os
import sys
import argparse
import requests
import json
import re
from dotenv import load_dotenv
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore = False
        self.ignore_tags = {"script", "style", "head", "meta", "link", "noscript"}

    def handle_starttag(self, tag, attrs):
        if tag in self.ignore_tags:
            self.ignore = True

    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            self.ignore = False

    def handle_data(self, data):
        if not self.ignore and data.strip():
            self.text.append(data.strip())

# Load environment variables
load_dotenv()

# Categorized Endpoints for Dashboard View
CATEGORIES = {
    "Health & Performance": {
        "liveliness": "/health/liveliness",
        "readiness": "/health/readiness",
        "metrics": "/metrics"
    },
    "Security & Identity Surface": {
        "models": "/v1/models",
        "jwks": "/.well-known/jwks.json",
        "openid": "/.well-known/openid-configuration"
    },
    "UI & Client Configuration": {
        "model_hub": "/ui/model_hub/",
        "ui_config": "/.well-known/litellm-ui-config",
        "ui_settings": "/get/ui_settings",
        "model_hub_info": "/public/model_hub/info"
    },
    "Service Discovery & Capabilities": {
        "public_endpoints": "/public/endpoints",
        "providers_fields": "/public/providers/fields",
        "agents_fields": "/public/agents/fields",
        "claude_marketplace": "/claude-code/marketplace.json",
        "blog_posts": "/public/litellm_blog_posts"
    }
}

# Flatten for easy fetching
ENDPOINTS = {name: path for cat in CATEGORIES.values() for name, path in cat.items()}

def check_endpoints(base_url):
    results = {}
    for name, path in ENDPOINTS.items():
        try:
            r = requests.get(f"{base_url}{path}", timeout=5)
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
    print("│              LITELLM PUBLIC TIER DASHBOARD                │")
    print("└───────────────────────────────────────────────────────────┘\n")
    
    # 1. Health & Performance
    print("▶ HEALTH & PERFORMANCE")
    live = results.get("liveliness", {})
    ready = results.get("readiness", {})
    metrics = results.get("metrics", {})
    
    if live.get("status") == 200 and ready.get("status") in (200, 503):
        print("  ✅ Proxy Core:   Reachable & Responsive")
        if ready.get("status") == 503:
             print("  ⚠️ Dependencies: Degraded (Database or Cache failing)")
        else:
             print("  ✅ Dependencies: Healthy")
    else:
        print("  ❌ Proxy Core:   Unreachable or failing")
        
    if metrics.get("status") == 200:
        print("  📊 Observability: Prometheus /metrics exposed")
    else:
        print("  盲 Observability: Metrics disabled (404)")

    # 2. Security & Identity Surface
    print("\n▶ SECURITY & IDENTITY SURFACE")
    models = results.get("models", {})
    if models.get("status") in (401, 403):
        print("  🔒 Core API:     Auth-gated (Safe)")
    elif models.get("status") == 200:
        print("  ⚠️ Core API:     Publicly exposed (Vulnerable!)")
    
    jwks = results.get("jwks", {})
    openid = results.get("openid", {})
    if jwks.get("status") == 200 or openid.get("status") == 200:
        print("  🔑 Identity:     SSO/OIDC configuration exposed")
    else:
        print("  🛡️ Identity:     No SSO configuration exposed")

    # 3. UI & Client Configuration
    print("\n▶ UI & CLIENT CONFIGURATION")
    ui = results.get("model_hub", {})
    ui_cfg = [k for k in ["ui_config", "ui_settings", "model_hub_info"] if results.get(k, {}).get("status") == 200]
    
    if ui.get("status") == 200:
        print(f"  🖥️  Web UI:       Exposed (Model Hub)")
    else:
        print(f"  🖥️  Web UI:       Disabled")
    print(f"  ⚙️  Config Data:  {len(ui_cfg)} frontend settings endpoints exposed")

    # 4. Service Discovery
    print("\n▶ SERVICE DISCOVERY CAPABILITIES")
    disc_keys = ["public_endpoints", "providers_fields", "agents_fields", "claude_marketplace", "blog_posts"]
    exposed_disc = [k for k in disc_keys if results.get(k, {}).get("status") == 200]
    print(f"  📡 Discovery:    {len(exposed_disc)}/{len(disc_keys)} provider and capability endpoints exposed")

    print("\n" + "─"*59)
    print("💡 Next Step: To investigate why specific inference requests")
    print("   are failing, provide LITELLM_USER_KEY in your .env to")
    print("   unlock the USER TIER.")
    print("   (Run with `--level 1` or `--level 2` for deeper detail)")

def format_content(text, content_type, level=1):
    """Format content intelligently based on type and verbosity level."""
    if not text:
        return ""
        
    content_type = content_type.lower() if content_type else ""
    
    if "application/json" in content_type:
        try:
            parsed = json.loads(text)
            if level == 1:
                # Level 1: One-line compact JSON, truncated
                compact = json.dumps(parsed, separators=(',', ':'))
                return compact[:150] + ("..." if len(compact) > 150 else "")
            else:
                # Level 2: Pretty print, truncate safely if huge
                pretty = json.dumps(parsed, indent=2)
                return pretty[:1000] + ("\n... [JSON truncated]" if len(pretty) > 1000 else "")
        except json.JSONDecodeError:
            pass # Fall back to text
            
    if "text/html" in content_type:
        if level == 1:
            # Extract title for a neat summary
            match = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
            if match:
                return f"[HTML Document] Title: '{match.group(1).strip()}'"
            return f"[HTML Document] ({len(text)} bytes)"
        else:
            # Level 2: Extract readable text instead of raw markup
            try:
                parser = HTMLTextExtractor()
                parser.feed(text)
                extracted_text = " ".join(parser.text)
                if not extracted_text:
                    extracted_text = "[No visible text content]"
                return extracted_text[:1000] + ("\n... [HTML text truncated]" if len(extracted_text) > 1000 else "")
            except Exception:
                return text[:500] + ("\n... [HTML markup truncated]" if len(text) > 500 else "")

    # Default text formatting
    if level == 1:
        clean = text.replace('\n', ' ')
        return clean[:150] + ("..." if len(clean) > 150 else "")
    else:
        return text[:1000] + ("\n... [Text truncated]" if len(text) > 1000 else "")

def get_level_1_diagnostics(results):
    print("=== Level 1: Diagnostics ===\n")
    for name, data in results.items():
        print(f"Diagnostics for `{data['path']}`:")
        if data['error']:
            print(f"  * Error: {data['error']}\n")
            continue
            
        status = data['status']
        c_type = data['headers'].get('Content-Type', '')
        excerpt = format_content(data['text'], c_type, level=1)
        
        print(f"  * Status: {status}")
        print(f"  * Body Excerpt: {excerpt}\n")

def get_level_2_traces(results, base_url):
    print("=== Level 2: Traces ===\n")
    for name, data in results.items():
        if data['error']:
            continue
            
        path = data['path']
        status = data['status']
        headers = data['headers']
        c_type = headers.get('Content-Type', '')
        
        print(f"Full Trace for `{path}`:")
        print(f"```http\n> GET {path} HTTP/1.1\n> Host: {base_url.replace('https://', '').replace('http://', '').rstrip('/')}\n> Accept: */*\n")
        print(f"< HTTP/1.1 {status}")
        for k, v in headers.items():
            if k.lower() in ["content-type", "content-length", "date"]:
                print(f"< {k}: {v}")
        
        body = format_content(data['text'], c_type, level=2)
        print(f"\n{body}")
        print("```\n")
        print("Reproduction Command:")
        print(f"curl -v -H \"Accept: application/json\" {base_url.rstrip('/')}{path}\n")

def main():
    parser = argparse.ArgumentParser(description="LiteLLM Public Tier Diagnostics")
    parser.add_argument("--level", type=int, choices=[0, 1, 2], default=0, help="Verbosity level (0=Summary, 1=Diagnostics, 2=Traces)")
    args = parser.parse_args()

    base_url = os.getenv("LITELLM_BASE_URL")
    if not base_url:
        print("Error: LITELLM_BASE_URL is not set in .env")
        sys.exit(1)

    results = check_endpoints(base_url)

    if args.level >= 0:
        get_level_0_summary(results)
    if args.level >= 1:
        print("\n" + "="*50 + "\n")
        get_level_1_diagnostics(results)
    if args.level == 2:
        print("\n" + "="*50 + "\n")
        get_level_2_traces(results, base_url)

if __name__ == "__main__":
    main()
