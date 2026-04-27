#!/usr/bin/env python3
"""
Source Sync Tool

Clones or updates the LiteLLM source code locally to the specified pinned versions.
Caches it outside the repo to avoid polluting the debug skill workspace.
Usage:
    python scripts/litellm/source_sync.py
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
LITELLM_REPO_URL = "https://github.com/BerriAI/litellm.git"
CACHE_DIR = Path.home() / ".cache" / "litellm-debug" / "sources"

def sync_version(version):
    target_dir = CACHE_DIR / f"litellm@{version}"
    
    if not target_dir.exists():
        print(f"[{version}] Cloning LiteLLM source to {target_dir}...")
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Shallow clone for specific tag/branch
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", version, LITELLM_REPO_URL, str(target_dir)],
                check=True,
                capture_output=True
            )
            print(f"[{version}] Clone successful.")
        except subprocess.CalledProcessError as e:
            print(f"[{version}] Error cloning: {e.stderr.decode()}")
            sys.exit(1)
    else:
        print(f"[{version}] Source already exists at {target_dir}.")

def main():
    sys.path.append(str(Path(__file__).parent))
    from spec_pin import get_latest_release
    latest_version = get_latest_release()
    v_pri = os.environ.get("LITELLM_VERSION_PRIMARY", latest_version)
    v_comp = os.environ.get("LITELLM_VERSION_COMPARISON", latest_version)

    print(f"Syncing Source for Primary Slot: {v_pri}")
    sync_version(v_pri)

    if v_pri != v_comp:
        print(f"\nSyncing Source for Comparison Slot: {v_comp}")
        sync_version(v_comp)

if __name__ == "__main__":
    main()
