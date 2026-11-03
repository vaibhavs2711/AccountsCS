#!/bin/bash
# ==============================================================================
# AccountsCS Deployment Script for Zima Server / Linux
# ==============================================================================

set -e

echo "🚀 Starting Deployment..."

# 1. Fetch latest code and reset to origin/main (prevents local conflict errors)
echo "📦 Updating code to match main branch..."
git fetch origin main
git reset --hard origin/main

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️ Warning: .env file not found! Copying from .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit .env with your TUNNEL_TOKEN before running!"
    exit 1
fi

# 3. Ensure .env has the active Cloudflare tunnel token for cityscope.tech
touch .env
ACTIVE_TOKEN="eyJhIjoiMjYyNmIxYzliNmE2YzA0ZWQwNTJhN2ZhNTBlMTYxYzkiLCJ0IjoiZDFiNmNiY2MtNGY2Yy00NWY5LWExNGMtMGI5OTlhZmViY2NmIiwicyI6Ik5qWTNOak5tTmpndE9UQTRNUzAwWVRFeExXRTNNVGd0WmpnNU9UWTJOemRoTldWayJ9"
if grep -q "^TUNNEL_TOKEN=" .env; then
  sed -i "s|^TUNNEL_TOKEN=.*|TUNNEL_TOKEN=$ACTIVE_TOKEN|" .env
else
  echo "TUNNEL_TOKEN=$ACTIVE_TOKEN" >> .env
fi
if ! grep -q "^SECRET_KEY=" .env; then
  echo "SECRET_KEY=cityscope-secret-key-change-in-production-2024" >> .env
fi

# 4. Clean up any conflicting standalone tunnel container if present
docker rm -f cityscope-cloudflare-tunnel 2>/dev/null || true

# 5. Build & start containers
echo "🐳 Rebuilding and starting Docker containers..."
docker compose up -d --build --remove-orphans

# 6. Clean up old dangling images to save disk space on Zima
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

# 7. Display container status
echo "✅ Deployment successful! Active containers:"
docker compose ps

