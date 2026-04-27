#!/usr/bin/env python3
"""
Find Public Endpoints Tool

Analyzes a pinned LiteLLM openapi.json file to discover all endpoints
that do not require authentication. 

This script is part of our development and contribution loop to ensure
our Public Tier tests remain comprehensive as LiteLLM evolves.

Usage:
    python scripts/dev/find_public_endpoints.py [path_to_openapi.json]

If no path is provided, it defaults to the LITELLM_VERSION_PRIMARY spec.
"""
import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SPEC_DIR = Path("references/litellm/spec")

def get_openapi_path(provided_path=None):
    if provided_path:
        return Path(provided_path)
    
    # Try to find primary version
    version = os.environ.get("LITELLM_VERSION_PRIMARY")
    if not version:
        # Fallback to looking in the spec dir
        if SPEC_DIR.exists():
            dirs = [d for d in SPEC_DIR.iterdir() if d.is_dir()]
            if dirs:
                # Just grab the first one if we don't have an env var
                version = dirs[0].name
    
    if version:
        p = SPEC_DIR / version / "openapi.json"
        if p.exists():
            return p
            
    return None

def analyze_endpoints(openapi_path):
    try:
        with open(openapi_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {openapi_path}: {e}")
        return []

    public_endpoints = []
    
    for path, methods in data.get("paths", {}).items():
        for method, details in methods.items():
            # Check if security is explicitly empty or missing
            if "security" not in details or not details["security"]:
                public_endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": details.get("summary", "No summary")
                })
                
    return public_endpoints

def verify_live(endpoints, base_url):
    print(f"\nVerifying endpoints against live proxy: {base_url}")
    print("=" * 60)
    
    alive = []
    for ep in endpoints:
        if ep["method"] != "GET":
            continue # Only auto-test GET requests to be safe
            
        # Skip parameterized endpoints for the generic ping
        if "{" in ep["path"]:
            continue
            
        url = f"{base_url.rstrip('/')}{ep['path']}"
        try:
            r = requests.get(url, timeout=5)
            # We consider 200 a successful public endpoint finding.
            # 401/403 means it's actually gated despite openapi.json.
            # 404/405/422/500 means it exists but requires specific payloads or isn't enabled.
            if r.status_code == 200:
                alive.append(ep['path'])
                print(f"✅ {ep['path']} -> {r.status_code}")
            else:
                print(f"⚠️ {ep['path']} -> {r.status_code}")
        except Exception as e:
            print(f"❌ {ep['path']} -> ERROR: {e}")
            
    return alive

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = get_openapi_path()
        
    if not path or not os.path.exists(path):
        print("Error: Could not find openapi.json.")
        print("Run `python scripts/litellm/spec_pin.py` first to download specs.")
        sys.exit(1)
        
    print(f"Analyzing {path}...")
    endpoints = analyze_endpoints(path)
    
    print("\nPublic Endpoints (No Security Required):")
    print("=" * 60)
    for ep in sorted(endpoints, key=lambda x: x["path"]):
        print(f"{ep['method']:<7} {ep['path']:<40} ({ep['summary']})")
        
    print(f"\nTotal endpoints found: {len(endpoints)}")
    
    # Try to verify against live proxy
    base_url = os.environ.get("LITELLM_BASE_URL")
    if base_url:
        verify_live(endpoints, base_url)
    else:
        print("\nTip: Set LITELLM_BASE_URL in .env to automatically ping these endpoints.")

if __name__ == "__main__":
    main()
