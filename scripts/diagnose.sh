#!/bin/bash

# ChatDVC Diagnostic Script
# Usage: ./diagnose.sh [TARGET_IP]

TARGET_IP=${1:-"206.189.77.227"}
USER="root"

echo "🔍 Diagnosing Connection Issues on $USER@$TARGET_IP..."

ssh $USER@$TARGET_IP << 'EOF'
    echo "--- 1. Host Ports (Listening?) ---"
    # Check if anything is listening on port 80
    ss -tuln | grep :80 || echo "❌ No process listening on port 80!"

    echo -e "\n--- 2. Container Processes ---"
    # Check if Nginx is actually running inside the container
    docker exec chatdvc_container ps aux

    echo -e "\n--- 3. Nginx Configuration Check ---"
    # Test Nginx configuration syntax
    docker exec chatdvc_container nginx -t

    echo -e "\n--- 4. Local Connectivity Test ---"
    # Try to connect to localhost from within the server
    curl -I -v http://localhost:80 2>&1 | grep -E "Connected|HTTP" || echo "❌ Could not connect locally via curl"
EOF

