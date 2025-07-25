#!/bin/bash

# Create SSL directory
mkdir -p /etc/nginx/ssl

# Generate self-signed certificate for Cloudflare origin
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx-selfsigned.key \
    -out /etc/nginx/ssl/nginx-selfsigned.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=roblox.nextkeylitigation.com"

# Set proper permissions
chmod 600 /etc/nginx/ssl/nginx-selfsigned.key
chmod 644 /etc/nginx/ssl/nginx-selfsigned.crt

echo "SSL certificates generated successfully!"
