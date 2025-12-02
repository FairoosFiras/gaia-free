#!/bin/bash
# Docker entrypoint script that runs cloudflared tunnel and Gaia app

set -e

# Function to handle shutdown gracefully
cleanup() {
    echo "Shutting down services..."
    if [ ! -z "$CLOUDFLARED_PID" ]; then
        kill $CLOUDFLARED_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start Cloudflare Tunnel if token is provided and not explicitly disabled
if [ "$DISABLE_CLOUDFLARE_TUNNEL" = "true" ]; then
    echo "Cloudflare Tunnel disabled via DISABLE_CLOUDFLARE_TUNNEL flag"
elif [ ! -z "$CLOUDFLARE_TUNNEL" ]; then
    echo "Starting Cloudflare Tunnel..."
    cloudflared tunnel --no-autoupdate run --token $CLOUDFLARE_TUNNEL &
    CLOUDFLARED_PID=$!
    echo "Cloudflare Tunnel started with PID $CLOUDFLARED_PID"

    # Give tunnel time to establish
    sleep 3
else
    echo "No CLOUDFLARE_TUNNEL token provided, skipping tunnel setup"
fi

# Start the main application
echo "Starting Gaia backend..."
cd /home/gaia

# Respect Cloud Run/Heroku style dynamic port assignment
TARGET_PORT=${PORT:-8000}

# Run the Python application
if [ "$1" = "dev" ]; then
    echo "Running in development mode with hot reload on port ${TARGET_PORT}..."
    exec python3 -m uvicorn gaia.api.app:app --host 0.0.0.0 --port "${TARGET_PORT}" --reload --reload-dir src
else
    echo "Running in production mode on port ${TARGET_PORT}..."
    exec python3 -m uvicorn gaia.api.app:app --host 0.0.0.0 --port "${TARGET_PORT}" --workers ${WORKERS:-1}
fi
