#!/bin/bash

# Setup script for environment configuration

echo "Setting up Roblox Intake Form environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please update the values as needed."
else
    echo "✓ .env file already exists."
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Generate nginx.conf from template
if [ -f "nginx.conf.template" ]; then
    echo "Generating nginx.conf from template..."
    envsubst '${NGINX_SERVER_NAME}' < nginx.conf.template > nginx.conf
    echo "✓ nginx.conf generated with server name: ${NGINX_SERVER_NAME:-localhost}"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Run: docker-compose up --build"
