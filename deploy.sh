#!/bin/bash
# ==============================================================================
# AccountsCS Deployment Script for Zima Server / Linux
# ==============================================================================

set -e

echo "🚀 Starting Deployment..."

# 1. Pull latest code
echo "📦 Pulling latest code from main..."
git pull origin main

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️ Warning: .env file not found! Copying from .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit .env with your TUNNEL_TOKEN before running!"
    exit 1
fi

# 3. Build & start containers
echo "🐳 Rebuilding and starting Docker containers..."
docker compose up -d --build --remove-orphans

# 4. Clean up old dangling images to save disk space on Zima
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

# 5. Display container status
echo "✅ Deployment successful! Active containers:"
docker compose ps

