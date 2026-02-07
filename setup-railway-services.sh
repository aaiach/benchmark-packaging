#!/bin/bash
# =============================================================================
# Railway Services Setup Script
# =============================================================================
# This script helps set up all services in Railway for auto-deployment from GitHub
#
# Prerequisites:
# - Railway CLI installed
# - Logged in to Railway
# - Project created and linked to GitHub repo
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==================================="
echo "Railway Multi-Service Setup"
echo -e "===================================${NC}\n"

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Railway CLI not found. Install it with:${NC}"
    echo "  npm i -g @railway/cli"
    exit 1
fi

# Check auth
if ! railway whoami &> /dev/null; then
    echo -e "${RED}Not logged in. Run:${NC} railway login"
    exit 1
fi

echo -e "${GREEN}✓ Railway CLI ready${NC}\n"

echo -e "${YELLOW}Current project status:${NC}"
railway status
echo ""

echo -e "${BLUE}This script will guide you through setting up services.${NC}"
echo -e "${YELLOW}You'll need to do the following in Railway Dashboard:${NC}\n"

echo "1. CREATE REDIS DATABASE:"
echo "   - Go to your Railway project"
echo "   - Click 'New' → 'Database' → 'Add Redis'"
echo "   - Name it: 'redis'"
echo ""

echo "2. ADD SERVICES FROM GITHUB:"
echo "   For EACH service (api, worker, flower, frontend):"
echo "   - Click 'New' → 'GitHub Repo'"
echo "   - Select: aaiach/benchmark-packaging"
echo "   - Name the service (api, worker, flower, or frontend)"
echo ""

echo "3. CONFIGURE EACH SERVICE:"
echo ""
echo "   📦 API SERVICE:"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile Path: docker/api.Dockerfile"
echo "     - Docker Build Args: --target prod"
echo "   Settings → Deploy:"
echo "     - Health Check Path: /api/health"
echo "   Settings → Variables:"
echo "     FLASK_ENV=production"
echo "     FLASK_DEBUG=0"
echo "     FLASK_APP=src.app:create_app"
echo "     CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0"
echo "     CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1"
echo "     OUTPUT_DIR=/app/data/output"
echo "     CORS_ORIGINS=https://\${{frontend.RAILWAY_PUBLIC_DOMAIN}}"
echo "     ANTHROPIC_API_KEY=<your_key>"
echo "     OPENAI_API_KEY=<your_key>"
echo "     PINECONE_API_KEY=<your_key>"
echo "   Settings → Networking:"
echo "     - Generate Domain (enable public access)"
echo ""

echo "   ⚙️  WORKER SERVICE:"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile Path: docker/worker.Dockerfile"
echo "     - Docker Build Args: --target prod"
echo "   Settings → Variables:"
echo "     CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0"
echo "     CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1"
echo "     OUTPUT_DIR=/app/data/output"
echo "     ANTHROPIC_API_KEY=<your_key>"
echo "     OPENAI_API_KEY=<your_key>"
echo "     PINECONE_API_KEY=<your_key>"
echo ""

echo "   🌸 FLOWER SERVICE:"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile Path: docker/worker.Dockerfile"
echo "     - Docker Build Args: --target prod"
echo "   Settings → Deploy:"
echo "     - Start Command: celery -A api.celery_app flower --port=5555 --url_prefix="
echo "   Settings → Variables:"
echo "     CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0"
echo "     CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1"
echo "     FLOWER_BASIC_AUTH=admin:yourpassword"
echo "   Settings → Networking:"
echo "     - Generate Domain (to access Flower UI)"
echo ""

echo "   🎨 FRONTEND SERVICE:"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile Path: docker/frontend.Dockerfile"
echo "     - Root Directory: frontend"
echo "     - Docker Build Args: --target prod --build-arg VITE_API_URL=https://\${{api.RAILWAY_PUBLIC_DOMAIN}}"
echo "   Settings → Networking:"
echo "     - Generate Domain (main app URL)"
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}After setup, Railway will auto-deploy when${NC}"
echo -e "${GREEN}you push to the 'main' branch on GitHub!${NC}"
echo -e "${GREEN}============================================${NC}"

echo ""
echo -e "${YELLOW}Open Railway dashboard now?${NC}"
read -p "Press Enter to open dashboard, or Ctrl+C to exit..."

# Get project URL from status
PROJECT_URL=$(railway status 2>&1 | grep -i "project" | head -1 | awk '{print $2}' || echo "")

if [ -n "$PROJECT_URL" ]; then
    echo "Opening Railway dashboard..."
    open "https://railway.app/project" || xdg-open "https://railway.app/project" || echo "Please open https://railway.app/project manually"
else
    echo "Please open https://railway.app/project manually"
fi
