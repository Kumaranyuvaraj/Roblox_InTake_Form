#!/bin/bash

echo "🚀 Starting Multi-Domain Deployment..."

# Stop any existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove old images to ensure fresh builds
echo "🗑️  Cleaning up old images..."
docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true

# Build and start all services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Show container logs for debugging
echo "📋 Service logs (last 20 lines):"
echo "=== Web Service ==="
docker-compose logs --tail=20 web

echo "=== FB Landing Page ==="
docker-compose logs --tail=20 fb-landing-page

echo "=== Nginx ==="
docker-compose logs --tail=20 nginx

echo "✅ Deployment complete!"
echo ""
echo "🌐 Available domains:"
echo "  Main Django App: https://roblox.nextkeylitigation.com"
echo "  FB Landing Page: https://fb.nextkeylitigation.com"
echo "  Alternative Landing: https://landing.nextkeylitigation.com"
echo ""
echo "🔧 To view logs: docker-compose logs -f [service-name]"
echo "🛑 To stop: docker-compose down"
