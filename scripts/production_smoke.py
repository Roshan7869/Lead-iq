#!/usr/bin/env python3
"""
production_smoke.py — Post-deployment smoke test (Day 30)

Runs a quick health verification against a deployed instance.
Usage: python scripts/production_smoke.py [--url=https://api.dreampal.io]
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.request
import json as _json


ENDPOINTS = [
    ("GET", "/api/health", 200),
    ("GET", "/api/health/live", 200),
    ("GET", "/api/health/ready", 200),
    ("GET", "/api/admin/deploy-check", 200),
    ("GET", "/api/stream/health", 200),
]


def smoke_test(base_url: str) -> tuple[int, int]:
    passed = 0
    failed = 0

    for method, path, expected_status in ENDPOINTS:
        url = f"{base_url.rstrip('/')}{path}"
        start = time.monotonic()
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                body = resp.read().decode()[:500]
                duration_ms = (time.monotonic() - start) * 1000

            if status == expected_status:
                print(f"  PASS {method} {path} → {status} ({duration_ms:.0f}ms)")
                passed += 1
            else:
                print(f"  FAIL {method} {path} → {status} (expected {expected_status})")
                failed += 1
        except Exception as e:
            print(f"  FAIL {method} {path} → ERROR: {e}")
            failed += 1

    return passed, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Lead-iq production smoke test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL")
    args = parser.parse_args()

    print(f"Smoke testing: {args.url}\n")

    passed, failed = smoke_test(args.url)

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("DEPLOY CHECK FAILED — do not proceed to production.")
        sys.exit(1)
    else:
        print("All smoke tests passed. Production is healthy.")
        sys.exit(0)


if __name__ == "__main__":
    main()
