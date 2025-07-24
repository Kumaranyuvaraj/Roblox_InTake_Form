#!/bin/bash

echo "Building and starting the Django application with Docker..."

sudo docker compose -f docker-compose.yml up --build -d

sudo docker compose exec web python manage.py collectstatic --noinput

echo "Waiting for database to be ready..."
sleep 5

sudo docker compose exec web python manage.py migrate

echo "Django application is now running!"
echo "You can access it at: roblox.nextkeylitigation.com"
echo ""
echo "To stop the application, run: docker compose down"
echo "To view logs, run: docker compose logs -f"
