#!/bin/bash

echo "Building and starting the Django application with Docker..."

sudo docker compose -f docker-compose.yml up --build -d

echo "Waiting for database to be ready..."
sleep 10

sudo docker compose exec web python manage.py migrate

echo "Django application is now running!"
echo "You can access it at: http://3.147.221.152"
echo ""
echo "To stop the application, run: docker compose down"
echo "To view logs, run: docker compose logs -f"
