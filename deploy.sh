#!/bin/bash

echo "🚀 Building and starting the Django application with Docker..."

# Stop any existing containers
echo "📦 Stopping existing containers..."
sudo docker compose down

# Build and start all services including fb-landing-page
echo "🔨 Building and starting all services..."
sudo docker compose -f docker-compose.yml up --build -d

# Collect static files
echo "📁 Collecting static files..."
sudo docker compose exec web python manage.py collectstatic --noinput

echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
sudo docker compose exec web python manage.py migrate

echo "🔍 Checking service status..."
sudo docker compose ps

echo "📋 Service logs (last 10 lines):"
echo "=== Web Service ==="
sudo docker compose logs --tail=10 web

echo "=== FB Landing Page ==="
sudo docker compose logs --tail=10 fb-landing-page

echo "=== Nginx ==="
sudo docker compose logs --tail=10 nginx

echo "✅ Multi-Domain Django application is now running!"
echo ""
echo "🌐 Available domains:"
echo "  Main Django App: https://roblox.nextkeylitigation.com/"
echo "  FB Landing Pages:"
echo "    - https://facebook.nextkeylitigation.com"
echo "    - https://bullock.nextkeystack.com"
echo "    - https://hilliard.nextkeystack.com"
echo ""
echo "🔧 Management commands:"
echo "  Stop: sudo docker compose down"
echo "  View logs: sudo docker compose logs -f [service-name]"
echo "  Restart: sudo docker compose restart [service-name]"
