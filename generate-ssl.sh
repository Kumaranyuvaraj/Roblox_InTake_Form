#!/bin/bash

# Create SSL directory
mkdir -p /etc/nginx/ssl

# Create a config file for the certificate with SAN
cat > /tmp/cert.conf <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=Organization
OU=OrgUnit
CN=roblox.nextkeylitigation.com

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = roblox.nextkeylitigation.com
DNS.2 = nextkeylitigation.com
DNS.3 = www.nextkeylitigation.com
DNS.4 = bullock.roblox.nextkeylitigation.com
DNS.5 = hilliard.roblox.nextkeylitigation.com
EOF

# Generate self-signed certificate for Cloudflare origin with multiple domains
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx-selfsigned.key \
    -out /etc/nginx/ssl/nginx-selfsigned.crt \
    -config /tmp/cert.conf \
    -extensions v3_req

# Set proper permissions
chmod 600 /etc/nginx/ssl/nginx-selfsigned.key
chmod 644 /etc/nginx/ssl/nginx-selfsigned.crt

# Clean up config file
rm /tmp/cert.conf

echo "SSL certificates generated successfully for all domains!"
