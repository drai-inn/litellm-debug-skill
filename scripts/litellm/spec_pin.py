#!/usr/bin/env python3
"""
Spec Pin Tool

Pins reference LiteLLM versions and snapshots the contracts (OpenAPI, Prisma schema).
Sourced directly from LiteLLM upstream (github.com/BerriAI/litellm).
Idempotent: skips if the version is already pinned.

Usage:
    python scripts/litellm/spec_pin.py
"""
import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LITELLM_REPO = "BerriAI/litellm"
SPEC_DIR = Path("references/litellm/spec")

def get_latest_release():
    """Fetch the latest stable release tag from GitHub."""
    url = f"https://api.github.com/repos/{LITELLM_REPO}/releases/latest"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()["tag_name"]
    except requests.RequestException as e:
        print(f"Error fetching latest release from GitHub: {e}")
        sys.exit(1)

def fetch_file_from_github(tag, filepath):
    """Fetch a raw file from the GitHub repository at a specific tag."""
    url = f"https://raw.githubusercontent.com/{LITELLM_REPO}/{tag}/{filepath}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 404:
            print(f"Warning: File {filepath} not found in {LITELLM_REPO} at tag {tag}.")
            return None
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"Error fetching {filepath} at {tag}: {e}")
        return None

def fetch_openapi_from_proxy(base_url):
    """Attempt to fetch openapi.json directly from the proxy first."""
    if not base_url:
        return None
    url = f"{base_url.rstrip('/')}/openapi.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        # Verify it's valid JSON
        json.loads(r.text)
        return r.text
    except Exception as e:
        print(f"Failed to fetch openapi.json from proxy: {e}")
        return None

def pin_version(version, base_url=None):
    """Pin the specified version."""
    target_dir = SPEC_DIR / version
    target_dir.mkdir(parents=True, exist_ok=True)
    
    openapi_path = target_dir / "openapi.json"
    schema_path = target_dir / "schema.prisma"
    
    # 1. Fetch OpenAPI
    if not openapi_path.exists():
        print(f"[{version}] Pinning openapi.json...")
        openapi_content = None
        # Try proxy first if available
        if base_url:
            print(f"[{version}] Attempting to fetch from proxy: {base_url}...")
            openapi_content = fetch_openapi_from_proxy(base_url)
            
        # Fallback or if proxy failed/unavailable, we'd normally generate or fetch.
        # LiteLLM upstream doesn't check in openapi.json, so we might only rely on proxy
        # but let's try to fetch if they happen to have it or we just rely on proxy.
        if openapi_content:
            with open(openapi_path, "w") as f:
                # Format JSON nicely
                parsed = json.loads(openapi_content)
                json.dump(parsed, f, indent=2)
            print(f"[{version}] Pinned openapi.json")
        else:
            print(f"[{version}] Could not pin openapi.json (only available via live proxy currently).")
    else:
        print(f"[{version}] openapi.json already pinned.")

    # 2. Fetch Prisma Schema
    if not schema_path.exists():
        print(f"[{version}] Pinning schema.prisma...")
        # Try paths in the litellm repo
        schema_content = fetch_file_from_github(version, "litellm/proxy/schema.prisma")
        if not schema_content:
            schema_content = fetch_file_from_github(version, "schema.prisma")
            
        if schema_content:
            with open(schema_path, "w") as f:
                f.write(schema_content)
            print(f"[{version}] Pinned schema.prisma")
        else:
            print(f"[{version}] Could not find schema.prisma in upstream repo.")
    else:
        print(f"[{version}] schema.prisma already pinned.")

def main():
    latest_version = get_latest_release()
    print(f"Latest LiteLLM stable release is {latest_version}")

    version_primary = os.environ.get("LITELLM_VERSION_PRIMARY", latest_version)
    version_comparison = os.environ.get("LITELLM_VERSION_COMPARISON", latest_version)
    base_url = os.environ.get("LITELLM_BASE_URL")

    print(f"\n--- Pinning Primary Slot: {version_primary} ---")
    pin_version(version_primary, base_url)

    if version_primary != version_comparison:
        print(f"\n--- Pinning Comparison Slot: {version_comparison} ---")
        pin_version(version_comparison, base_url)
    else:
        print("\nPrimary and Comparison versions are identical. Skipping Comparison slot.")

if __name__ == "__main__":
    main()
