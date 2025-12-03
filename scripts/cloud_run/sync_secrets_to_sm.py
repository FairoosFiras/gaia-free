#!/usr/bin/env python3
"""Sync secrets from a .env file into Google Secret Manager and emit Cloud Run flags.

Given an input env file (typically decrypted from SOPS), this tool:
 - Classifies entries as 'secret' or 'plain env' using simple heuristics.
 - Creates or updates per-key secrets in Secret Manager (1 secret per key).
 - Writes a Cloud Run compatible env-vars file for non-secret entries.
 - Writes a list of KEY=secret-id:latest lines for use with --set-secrets.

Usage:
  python scripts/cloud_run/sync_secrets_to_sm.py \
    --input secrets/.secrets.env.decrypted \
    --project $PROJECT_ID \
    --env stg \
    --out-env-file runtime-env-vars.txt \
    --out-secrets-flags secrets_flags.txt
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


NON_SECRET_ALLOWLIST = {
    # Deployment/meta
    "PROJECT_ID",
    "REGION",
    "SERVICE_NAME",
    "ARTIFACT_REGISTRY_REPO",
    # Runtime knobs (safe)
    "ENV",
    "DEBUG",
    "APP_MODULE",
    "WORKERS",
    "PORT",
    # Buckets and mounts
    "CAMPAIGN_STORAGE_BUCKET",
    "MEDIA_BUCKET",
    "CAMPAIGN_STORAGE_PATH",
    # Cloud SQL connector (not a secret)
    "DB_INSTANCE_CONNECTION_NAME",
}


SECRET_SUFFIX_RE = re.compile(r"(_SECRET|_KEY|_TOKEN|_PASSWORD|_CREDENTIALS|_API_KEY|_USER|_HOST)$", re.IGNORECASE)


def parse_env_file(path: Path) -> List[Tuple[str, str]]:
    entries: List[Tuple[str, str]] = []
    seen = set()
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key in seen:
                continue
            seen.add(key)
            value = value.strip()
            if value and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            entries.append((key, value))
    return entries


def classify(entries: Iterable[Tuple[str, str]]) -> Tuple[Dict[str, str], Dict[str, str]]:
    env_plain: Dict[str, str] = {}
    env_secret: Dict[str, str] = {}
    for key, value in entries:
        # Heuristics: suffix-based or not in allowlist => secret
        if key in NON_SECRET_ALLOWLIST:
            env_plain[key] = value
        elif SECRET_SUFFIX_RE.search(key):
            env_secret[key] = value
        else:
            # Default to plain env; adjust here if you want more aggressive secret sync
            env_plain[key] = value
    return env_plain, env_secret


def ensure_secret(project: str, secret_id: str) -> None:
    # Create secret if missing (automatic replication)
    describe_cmd = [
        "gcloud",
        "secrets",
        "describe",
        secret_id,
        "--project",
        project,
        "--format=value(name)",
    ]
    create_cmd = [
        "gcloud",
        "secrets",
        "create",
        secret_id,
        "--replication-policy=automatic",
        "--project",
        project,
    ]
    try:
        res = subprocess.run(describe_cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            # Try to create the secret, but don't fail if it already exists
            create_res = subprocess.run(create_cmd, capture_output=True, text=True, check=False)
            if create_res.returncode != 0 and "already exists" not in create_res.stderr:
                # Only fail if it's not an "already exists" error
                print(f"Error creating secret {secret_id}: {create_res.stderr}")
                raise subprocess.CalledProcessError(create_res.returncode, create_cmd, create_res.stdout, create_res.stderr)
    except FileNotFoundError:
        raise SystemExit("gcloud CLI not found. Please install/setup gcloud in CI.")


def get_latest_secret_value(project: str, secret_id: str) -> Optional[str]:
    """Return the latest version payload for a secret, or None if not found."""
    try:
        res = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                "--secret",
                secret_id,
                "--project",
                project,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return None
        # gcloud prints a trailing newline for text payloads; normalize for compare
        return res.stdout.rstrip("\n")
    except FileNotFoundError:
        raise SystemExit("gcloud CLI not found. Please install/setup gcloud in CI.")


def add_secret_version(project: str, secret_id: str, value: str, *, skip_if_unchanged: bool = True) -> bool:
    # Skip empty values
    if not value or value.strip() == "":
        print(f"Skipping empty secret: {secret_id}")
        return False

    if skip_if_unchanged:
        latest = get_latest_secret_value(project, secret_id)
        # Normalize expected value similarly for fair comparison
        cmp_value = value.rstrip("\n")
        if latest is not None and latest == cmp_value:
            print(f"No change for {secret_id}; skipping new version")
            return False

    proc = subprocess.Popen(
        [
            "gcloud",
            "secrets",
            "versions",
            "add",
            secret_id,
            "--data-file=-",
            "--project",
            project,
        ],
        stdin=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdin is not None
        proc.stdin.write(value)
        proc.stdin.close()
        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"Failed to add version to secret {secret_id}")
        return True
    finally:
        try:
            proc.kill()
        except Exception:
            pass


def list_versions(project: str, secret_id: str) -> List[Tuple[str, str, str]]:
    """List versions as tuples (version_id, create_time, state)."""
    try:
        res = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "list",
                secret_id,
                "--project",
                project,
                "--format=value(name,createTime,state)",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return []
        out: List[Tuple[str, str, str]] = []
        for line in res.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                parts = re.split(r"\s+", line, maxsplit=2)
            if len(parts) != 3:
                continue
            name, ctime, state = parts
            # name format: projects/<proj>/secrets/<id>/versions/<vid>
            vid = name.rsplit("/", 1)[-1]
            out.append((vid, ctime, state))
        return out
    except FileNotFoundError:
        raise SystemExit("gcloud CLI not found. Please install/setup gcloud in CI.")


def prune_versions(project: str, secret_id: str, keep: int, *, dry_run: bool = False) -> int:
    """Destroy older versions, keeping the newest `keep` by createTime.

    Returns count of destroyed versions.
    """
    versions = list_versions(project, secret_id)
    # Sort by create time (lexicographic RFC3339 sorts correctly by time)
    versions.sort(key=lambda t: t[1])
    if len(versions) <= keep:
        return 0
    to_destroy = versions[: len(versions) - keep]
    destroyed = 0
    for vid, _, state in to_destroy:
        # Only destroy if not already destroyed; allow disabling states
        if state.upper() == "DESTROYED":
            continue
        cmd = [
            "gcloud",
            "secrets",
            "versions",
            "destroy",
            vid,
            "--secret",
            secret_id,
            "--project",
            project,
            "--quiet",
        ]
        print(("DRY RUN: " if dry_run else "") + f"Destroying {secret_id}@{vid}")
        if dry_run:
            destroyed += 1
            continue
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            destroyed += 1
        else:
            # Do not hard-fail a sync on prune errors
            print(f"Failed to destroy {secret_id}@{vid}: {res.stderr}")
    return destroyed


def to_secret_id(env_name: str, key: str) -> str:
    # Secret Manager IDs: start with letter, letters/numbers/dashes only
    # Transform KEY to 'key-name'
    transformed = key.lower().replace("_", "-")
    if not transformed[0].isalpha():
        transformed = f"s-{transformed}"
    return f"gaia-{env_name}-{transformed}"


def write_env_file(entries: Dict[str, str], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as fh:
        for k, v in entries.items():
            if "\n" in v:
                # Skip multi-line in env file; push as secret instead if needed
                continue
            fh.write(f"{k}={v}\n")


def write_secret_flags(secret_map: Dict[str, str], env_name: str, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as fh:
        for key in sorted(secret_map.keys()):
            # Skip empty values - they were not added to Secret Manager
            value = secret_map[key]
            if not value or value.strip() == "":
                continue
            secret_id = to_secret_id(env_name, key)
            fh.write(f"{key}={secret_id}:latest\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--env", required=True, help="Environment suffix (e.g., stg, prod)")
    ap.add_argument("--out-env-file", type=Path, required=True)
    ap.add_argument("--out-secrets-flags", type=Path, required=True)
    ap.add_argument("--no-skip-unchanged", action="store_true", help="Always add a new secret version, even if the value is identical to latest")
    ap.add_argument("--prune-keep", type=int, default=0, help="If > 0, destroy older versions keeping only the newest N per secret")
    ap.add_argument("--dry-run", action="store_true", help="Plan actions without mutating Secret Manager")
    ap.add_argument("--concurrency", type=int, default=8, help="Number of concurrent secret operations")
    args = ap.parse_args()

    entries = parse_env_file(args.input)
    plain, secrets = classify(entries)

    # Create/update secrets in parallel
    total_added = 0
    total_pruned = 0
    print_lock = threading.Lock()

    def process_one(item: Tuple[str, str]) -> Tuple[int, int]:
        key, value = item
        sid = to_secret_id(args.env, key)
        try:
            ensure_secret(args.project, sid)
        except SystemExit:
            raise
        except Exception as exc:
            with print_lock:
                print(f"Error ensuring secret {sid}: {exc}")
            return (0, 0)

        added_local = 0
        if args.dry_run:
            latest = get_latest_secret_value(args.project, sid)
            unchanged = (latest is not None and latest == value.rstrip("\n"))
            will_skip = (not args.no_skip_unchanged) and unchanged
            with print_lock:
                print(f"DRY RUN: {sid} -> {'skip (unchanged)' if will_skip else 'add new version'}")
            added_local = 0 if will_skip else 1
        else:
            try:
                did_add = add_secret_version(
                    args.project,
                    sid,
                    value,
                    skip_if_unchanged=not args.no_skip_unchanged,
                )
                added_local = 1 if did_add else 0
            except SystemExit:
                raise
            except Exception as exc:
                with print_lock:
                    print(f"Error adding version for {sid}: {exc}")
                added_local = 0

        pruned_local = 0
        if args.prune_keep and args.prune_keep > 0:
            try:
                pruned_local = prune_versions(args.project, sid, args.prune_keep, dry_run=args.dry_run)
            except SystemExit:
                raise
            except Exception as exc:
                with print_lock:
                    print(f"Error pruning versions for {sid}: {exc}")
                pruned_local = 0
        return (added_local, pruned_local)

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futures = [ex.submit(process_one, kv) for kv in secrets.items()]
        for fut in as_completed(futures):
            added_local, pruned_local = fut.result()
            total_added += added_local
            total_pruned += pruned_local

    # Write outputs
    write_env_file(plain, args.out_env_file)
    write_secret_flags(secrets, args.env, args.out_secrets_flags)

    print(
        f"Synced {len(secrets)} secret values (added {total_added} new versions, pruned {total_pruned}); wrote {len(plain)} envs to {args.out_env_file}"
    )


if __name__ == "__main__":
    main()