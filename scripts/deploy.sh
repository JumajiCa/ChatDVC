#!/bin/bash
set -e

# ChatDVC Deployment Script
# Usage: ./scripts/deploy.sh [TARGET_IP]

# Navigate to project root
cd "$(dirname "$0")/.."

TARGET_IP=${1:-"206.189.77.227"}
USER="root"
REMOTE_DIR="/root/chatdvc"

# Load API Key from .env
if [ -f .env ]; then
    # Safely read .env file line by line
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip comments and empty lines
        [[ "$key" =~ ^# ]] && continue
        [[ -z "$key" ]] && continue
        
        # Trim whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        # Export the variable
        export "$key"="$value"
    done < .env
else
    echo "Error: .env file not found. Please create one with DEEPSEEK_API_KEY."
    exit 1
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "Error: DEEPSEEK_API_KEY is not set in .env."
    exit 1
fi

echo "🚀 Deploying ChatDVC to $USER@$TARGET_IP..."

# 1. Prerequisite Check: SSH Access
# We remove BatchMode=yes to allow interactive passphrase entry if ssh-agent isn't running
ssh -o ConnectTimeout=5 $USER@$TARGET_IP echo "SSH connection verified."
if [ $? -ne 0 ]; then
    echo "❌ Error: Cannot SSH into $USER@$TARGET_IP."
    echo "If you have a passphrase on your key, ensure you entered it correctly."
    echo "Tip: Run 'eval \$(ssh-agent) && ssh-add' to avoid typing your passphrase multiple times."
    exit 1
fi

# 2. Install Docker and rsync on Remote (if missing)
echo "📦 Checking Docker and rsync on remote server..."
ssh $USER@$TARGET_IP "apt-get update && apt-get install -y rsync; command -v docker >/dev/null 2>&1 || { echo 'Installing Docker...'; curl -fsSL https://get.docker.com | sh; }"

# 3. Copy Files to Remote
echo "📂 Copying project files..."
# Exclude venv, node_modules, git, etc.
rsync -avz --delete --exclude-from='.dockerignore' --exclude '.git' ./ $USER@$TARGET_IP:$REMOTE_DIR

# 4. Build and Run on Remote
echo "🔨 Building and Running Docker Container..."
ssh $USER@$TARGET_IP << EOF
    cd $REMOTE_DIR
    
    # Stop existing container if running
    docker stop chatdvc_container 2>/dev/null || true
    docker rm chatdvc_container 2>/dev/null || true
    
    # Build Image (Force no-cache to ensure requirements are fresh)
    docker build --no-cache -t chatdvc:latest .
    
    # Run Container
    # Persist data in ./data volume
    # Pass the API key
    docker run -d \
      -p 80:80 \
      -e DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
      -e ENCRYPTION_KEY="$ENCRYPTION_KEY" \
      -v \$(pwd)/data:/app/data \
      --name chatdvc_container \
      chatdvc:latest

    echo "✅ Deployment Complete!"
    docker ps | grep chatdvc
    echo "Check logs with: docker logs chatdvc_container"
EOF

