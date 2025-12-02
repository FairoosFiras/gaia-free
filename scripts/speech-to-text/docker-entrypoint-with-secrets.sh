#!/bin/bash
# Docker entrypoint that decrypts SOPS secrets before starting STT service
set -e

echo "=== STT Service Startup with Secrets Decryption ==="

# Check if SOPS key file is available
if [ -n "$SOPS_AGE_KEY_FILE" ] && [ -f "$SOPS_AGE_KEY_FILE" ]; then
    echo "✓ Using SOPS AGE key file: $SOPS_AGE_KEY_FILE"
    # SOPS will use SOPS_AGE_KEY_FILE directly - no need to export contents
else
    echo "WARNING: No SOPS key found. Secrets will not be decrypted."
    echo "To enable secrets decryption:"
    echo "  - Mount AGE key file and set SOPS_AGE_KEY_FILE"
fi

# Path to encrypted secrets (configurable via env var)
ENCRYPTED_SECRETS="${ENCRYPTED_SECRETS_PATH:-/app/secrets/.secrets.env}"
if [ -f "$ENCRYPTED_SECRETS" ]; then
    echo "Decrypting secrets from $ENCRYPTED_SECRETS..."

    # Decrypt and export each secret as environment variable
    if command -v sops &> /dev/null; then
        # Create temporary file for decrypted secrets
        TEMP_SECRETS=$(mktemp)
        trap "rm -f $TEMP_SECRETS" EXIT

        # Decrypt to temp file
        if sops -d "$ENCRYPTED_SECRETS" > "$TEMP_SECRETS" 2>/dev/null; then
            # Source the secrets into environment
            set -a  # Auto-export all variables
            source "$TEMP_SECRETS"
            set +a
            echo "✓ Secrets decrypted and loaded into environment"
        else
            echo "WARNING: Failed to decrypt secrets. Check SOPS_AGE_KEY_FILE points to a valid key."
            echo "Continuing without SOPS-decrypted secrets (may use Secret Manager or env vars)..."
        fi
    else
        echo "WARNING: sops not found in container"
        echo "Continuing without SOPS decryption (may use Secret Manager or env vars)..."
    fi
else
    echo "WARNING: No encrypted secrets file found at $ENCRYPTED_SECRETS"
    echo "Continuing without decrypted secrets..."
fi

# Execute the original command
exec "$@"
