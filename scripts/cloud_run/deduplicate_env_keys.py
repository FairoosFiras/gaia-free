#!/usr/bin/env python3
"""
Deduplicate environment variable keys in .env files.

When multiple definitions of the same key exist, keeps the last occurrence.
This is useful for merging base config with environment-specific overrides.

Usage:
    python3 deduplicate_env_keys.py <env_file>

Example:
    python3 deduplicate_env_keys.py /tmp/backend.cloudrun.env
"""

import sys
from collections import OrderedDict


def deduplicate_env_file(filepath):
    """
    Remove duplicate keys from env file, keeping last occurrence.

    Args:
        filepath: Path to the .env file to deduplicate
    """
    result = OrderedDict()

    with open(filepath, 'r') as f:
        for line in f:
            line = line.rstrip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Parse key=value pairs
            if '=' in line:
                key = line.split('=', 1)[0]
                result[key] = line

    # Write back to file
    with open(filepath, 'w') as f:
        for line in result.values():
            f.write(line + '\n')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: deduplicate_env_keys.py <env_file>", file=sys.stderr)
        sys.exit(1)

    deduplicate_env_file(sys.argv[1])