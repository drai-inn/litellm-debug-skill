#!/usr/bin/env python3
"""
Spec Diff Tool

Calculates diffs between the primary and comparison LiteLLM spec snapshots.
Usage:
    python scripts/litellm/spec_diff.py
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
SPEC_DIR = Path("references/litellm/spec")

def get_pinned_versions():
    # In reality, you could list dirs or use env vars
    from spec_pin import get_latest_release
    latest_version = get_latest_release()
    v_pri = os.environ.get("LITELLM_VERSION_PRIMARY", latest_version)
    v_comp = os.environ.get("LITELLM_VERSION_COMPARISON", latest_version)
    return v_pri, v_comp

def run_diff(file1, file2):
    try:
        # Use unified diff (-u)
        result = subprocess.run(
            ["diff", "-u", str(file1), str(file2)],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error running diff: {e}"

def main():
    v_pri, v_comp = get_pinned_versions()
    print(f"Comparing Primary ({v_pri}) with Comparison ({v_comp})\n")
    
    if v_pri == v_comp:
        print("Primary and Comparison versions are identical. No diff required.")
        return

    dir_pri = SPEC_DIR / v_pri
    dir_comp = SPEC_DIR / v_comp

    if not dir_pri.exists() or not dir_comp.exists():
        print(f"Missing pinned snapshots. Please run `python scripts/litellm/spec_pin.py` first.")
        sys.exit(1)

    print("=== schema.prisma ===")
    diff_schema = run_diff(dir_pri / "schema.prisma", dir_comp / "schema.prisma")
    if not diff_schema:
        print("No changes in schema.prisma")
    else:
        print(diff_schema[:1000] + ("\n... [truncated]" if len(diff_schema) > 1000 else ""))

    print("\n=== openapi.json (structural overview only) ===")
    # Full JSON diff is huge, recommend visual tool or parsing keys
    print("Full JSON diffs are usually too large for CLI.")
    print(f"Run `diff -u {dir_pri}/openapi.json {dir_comp}/openapi.json` to view or use a visual diff tool.")

if __name__ == "__main__":
    main()
