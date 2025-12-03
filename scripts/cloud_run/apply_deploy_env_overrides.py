#!/usr/bin/env python3
"""Merge deploy_vars JSON overrides into a Cloud Run env file safely."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


def load_secret_keys(path: Path | None) -> Set[str]:
    if path is None or not path.exists():
        return set()
    keys: Set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if value:
            keys.add(value)
    return keys


def parse_deploy_vars(raw: str) -> Dict[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return {}

    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        raw = raw[1:-1]
    raw = raw.strip()
    if not raw or raw == "{}":
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: Failed to parse deploy_vars JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("ERROR: deploy_vars must decode to a JSON object")

    result: Dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            print(f"   Warning: Skipping non-string key: {key!r}")
            continue
        key = key.strip()
        if value is None:
            print(f"   Warning: Skipping {key} (null value)")
            continue
        value_str = str(value)
        if not value_str:
            print(f"   Warning: Skipping {key} (empty value)")
            continue
        if "\n" in value_str:
            print(f"   Warning: Skipping {key} (multi-line values are not supported)")
            continue
        result[key] = value_str
    return result


def read_env_file(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def set_env_line(lines: List[str], key: str, value: str) -> None:
    assignment = f"{key}={value}"
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        current_key = line.split("=", 1)[0].strip()
        if current_key == key:
            lines[idx] = assignment
            return
    lines.append(assignment)


def apply_overrides(
    env_path: Path,
    deploy_vars: Dict[str, str],
    secret_keys: Iterable[str],
) -> Tuple[List[str], List[Tuple[str, str]]]:
    secret_lookup = set(secret_keys)
    lines = read_env_file(env_path)
    applied: List[Tuple[str, str]] = []

    if deploy_vars:
        print("Applying deployment environment overrides from workflow input")
    for key, value in deploy_vars.items():
        if key in secret_lookup:
            print(f"   Warning: Skipping {key} (managed via Secret Manager)")
            continue
        set_env_line(lines, key, value)
        applied.append((key, value))
        print(f"   {key}={value}")
    return lines, applied


def write_env_file(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines)
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge deploy_vars JSON overrides into Cloud Run env file.",
    )
    parser.add_argument("--env-file", required=True, type=Path, help="Path to Cloud Run env file to update.")
    parser.add_argument(
        "--deploy-vars",
        required=False,
        default="",
        help="JSON string of deploy overrides (as passed via workflow input).",
    )
    parser.add_argument(
        "--secret-keys-file",
        type=Path,
        required=False,
        help="Optional path to newline-delimited list of secret-managed keys.",
    )

    args = parser.parse_args()

    secret_keys = load_secret_keys(args.secret_keys_file)
    deploy_vars = parse_deploy_vars(args.deploy_vars)
    if not deploy_vars:
        return

    lines, applied = apply_overrides(args.env_file, deploy_vars, secret_keys)
    if applied:
        write_env_file(args.env_file, lines)


if __name__ == "__main__":
    main()