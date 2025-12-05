#!/bin/bash
set -e

# Navigate to project root
cd "$(dirname "$0")/.."

echo "🧹 Cleaning up old local containers..."
docker stop chatdvc_local 2>/dev/null || true
docker rm chatdvc_local 2>/dev/null || true

echo "🏗️  Building local Docker image (this ensures requirements.txt is fresh)..."
docker build --no-cache -t chatdvc:local .

echo "🏃 Starting container on port 8080..."
# Generate a valid Fernet key for testing
TEST_ENC_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "BJY_8U701h8v7y-8v7y8v7y8v7y8v7y8v7y8v7y8v7y=")

# We pass a dummy key if env var is missing, just to let it start up without crashing on os.getenv
docker run -d \
  -p 8080:80 \
  -e DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-dummy_key_for_local_test}" \
  -e ENCRYPTION_KEY="${TEST_ENC_KEY}" \
  --name chatdvc_local \
  chatdvc:local

echo "⏳ Waiting 5 seconds for services to start..."
sleep 5

echo "🔍 Checking container status..."
docker ps | grep chatdvc_local || { echo "❌ Container died!"; docker logs chatdvc_local; exit 1; }

echo "📋 Container Logs (last 20 lines):"
docker logs --tail 20 chatdvc_local

echo "🧪 Testing HTTP Connectivity (Frontend)..."
curl -I http://localhost:8080 || { echo "❌ Frontend unreachable"; exit 1; }
echo "✅ Frontend reachable."

echo "🧪 Testing API Connectivity (Backend)..."
# We expect a 405 Method Not Allowed for GET on /api/ask (since it accepts POST), or 200 for /api/user
# /api/user accepts GET
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/user)
echo "API Response Code for GET /api/user: $CODE"

if [ "$CODE" == "200" ] || [ "$CODE" == "201" ]; then
    echo "✅ API is working!"
else
    echo "❌ API Check Failed (Expected 200, got $CODE)"
    echo "Fetching full response for debug:"
    curl -v http://localhost:8080/api/user
    exit 1
fi

echo "🎉 Local Verification Complete. The app is running at http://localhost:8080"

