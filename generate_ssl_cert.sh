#!/bin/bash

# Generate self-signed SSL certificate for IP address
# This allows HTTPS without a domain name

echo "Generating self-signed SSL certificate for IP: 167.71.238.114"
echo ""

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate private key
openssl genrsa -out ssl/key.pem 2048

# Generate certificate signing request (CSR) with IP address
openssl req -new -key ssl/key.pem -out ssl/cert.csr -subj "/CN=167.71.238.114" \
  -addext "subjectAltName=IP:167.71.238.114"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in ssl/cert.csr -signkey ssl/key.pem -out ssl/cert.pem \
  -extensions v3_req -extfile <(
    echo "[v3_req]"
    echo "subjectAltName=IP:167.71.238.114"
  )

# Clean up CSR
rm ssl/cert.csr

# Set proper permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo ""
echo "✅ SSL certificate generated successfully!"
echo "   Certificate: ssl/cert.pem"
echo "   Private Key: ssl/key.pem"
echo ""
echo "⚠️  Note: This is a self-signed certificate."
echo "   Browsers will show a security warning that you need to accept."
echo "   This is normal for self-signed certs and safe for your use case."

