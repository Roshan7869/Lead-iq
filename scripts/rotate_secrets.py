#!/usr/bin/env python3
"""
rotate_secrets.py — Key Rotation Automation (Day 29)

Rotates all API keys and secrets for Lead-iq.
Usage: python scripts/rotate_secrets.py [--dry-run] [--service=<name>]

Services tracked: GEMINI_API_KEY, GITHUB_TOKEN, REDDIT_CLIENT_SECRET,
                   HUNTER_API_KEY, TELEGRAM_BOT_TOKEN, SECRET_KEY, JWT_SECRET_KEY
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROTATION_LOG = ROOT / ".secrets" / "rotation_log.jsonl"

SECRETS_ROTATED = [
    "GEMINI_API_KEY",
    "GITHUB_TOKEN",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_CLIENT_ID",
    "HUNTER_API_KEY",
    "CLEARBIT_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "SECRET_KEY",
    "JWT_SECRET_KEY",
]

# Services that need restart after rotation
DEPENDS_ON: dict[str, list[str]] = {
    "GEMINI_API_KEY": ["backend", "celery"],
    "GITHUB_TOKEN": ["celery"],
    "TELEGRAM_BOT_TOKEN": ["celery"],
    "SECRET_KEY": ["backend"],
    "JWT_SECRET_KEY": ["backend"],
}


def log_rotation(service: str, old_hash: str, new_hash: str, dry_run: bool) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "old_hash": old_hash,
        "new_hash": new_hash,
        "dry_run": dry_run,
    }
    ROTATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ROTATION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_current_hash(key: str) -> str:
    """Get SHA256 of current env var value (or 'unset')."""
    import hashlib
    import os
    val = os.getenv(key, "")
    if not val:
        return "unset"
    return hashlib.sha256(val.encode()).hexdigest()[:16]


def verify_new_value(key: str, new_value: str) -> bool:
    """Basic validation for new secrets."""
    if not new_value or len(new_value) < 8:
        return False
    if key in ("SECRET_KEY", "JWT_SECRET_KEY") and len(new_value) < 32:
        return False
    return True


def rotate_key(service: str, new_value: str, dry_run: bool = False) -> bool:
    """Rotate a single key. Returns True on success."""
    old_hash = get_current_hash(service)
    new_hash = "set" if new_value else "unset"

    if dry_run:
        print(f"[DRY RUN] Would rotate {service}: {old_hash} → {new_hash}")
        return True

    print(f"Rotating {service}: {old_hash} → {new_hash}")

    # Update .env file
    env_file = ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text()
        updated_lines = []
        found = False
        for line in content.splitlines():
            if line.startswith(f"{service}="):
                updated_lines.append(f"{service}={new_value}")
                found = True
            else:
                updated_lines.append(line)
        if not found:
            updated_lines.append(f"{service}={new_value}")
        env_file.write_text("\n".join(updated_lines) + "\n")

    log_rotation(service, old_hash, new_hash, dry_run)
    return True


def check_platform_service(service: str) -> str | None:
    """Check if this key is configured in a platform (Vercel/Railway)."""
    # Vercel
    try:
        result = subprocess.run(
            ["npx", "vercel", "env", "ls", "--environment", "production"],
            capture_output=True, text=True, timeout=15, cwd=ROOT,
        )
        if service.lower() in result.stdout.lower():
            return "vercel"
    except Exception:
        pass
    return None


def notify_rotation(service: str) -> None:
    """Log rotation event for audit trail."""
    print(f"[AUDIT] {service} rotated at {datetime.now(timezone.utc).isoformat()}")
    deps = DEPENDS_ON.get(service, [])
    if deps:
        print(f"[ACTION] Restart required for: {', '.join(deps)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotate Lead-iq secrets")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--service", type=str, help="Rotate a specific service")
    parser.add_argument("--all", action="store_true", help="Rotate all secrets")
    parser.add_argument("--list", action="store_true", help="List tracked secrets")
    parser.add_argument("--audit", action="store_true", help="Audit current secrets status")
    args = parser.parse_args()

    if args.list:
        print("Tracked secrets:")
        for s in SECRETS_ROTATED:
            current = get_current_hash(s)
            print(f"  {s}: {current}")
        return

    if args.audit:
        print("Secrets audit:")
        for s in SECRETS_ROTATED:
            current = get_current_hash(s)
            platform = check_platform_service(s)
            status = "set" if current != "unset" else "MISSING"
            deps = ", ".join(DEPENDS_ON.get(s, []))
            print(f"  {s}: {status} | platform={platform or 'env-file'} | deps={deps}")
        return

    services = [args.service] if args.service else SECRETS_ROTATED if args.all else []

    if not services:
        parser.print_help()
        return

    for service in services:
        if service not in SECRETS_ROTATED:
            print(f"Unknown service: {service}")
            continue

        new_val = input(f"New value for {service} (or press Enter to skip): ").strip()
        if not new_val:
            print(f"  Skipped {service}")
            continue

        if not verify_new_value(service, new_val):
            print(f"  Invalid value for {service} — must be >= 8 chars (32 for JWT)")
            continue

        if rotate_key(service, new_val, args.dry_run):
            notify_rotation(service)

    print("Done. Restart affected services to apply changes.")


if __name__ == "__main__":
    main()
