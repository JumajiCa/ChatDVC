#!/bin/bash

# ChatDVC Troubleshooting Script
# Usage: ./troubleshoot.sh [TARGET_IP]

TARGET_IP=${1:-"206.189.77.227"}
USER="root"

echo "🔍 Troubleshooting ChatDVC on $USER@$TARGET_IP..."

ssh $USER@$TARGET_IP << EOF
    echo "--- 1. Docker Container Status ---"
    docker ps -a | grep chatdvc

    echo -e "\n--- 2. Container Logs (Last 20 lines) ---"
    docker logs --tail 20 chatdvc_container

    echo -e "\n--- 3. Port Listening Status ---"
    netstat -tuln | grep :80

    echo -e "\n--- 4. Firewall Status (UFW) ---"
    ufw status verbose
EOF

