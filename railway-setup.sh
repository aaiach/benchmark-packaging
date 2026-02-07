#!/bin/bash
# =============================================================================
# Railway Auto-Setup Script using CLI
# =============================================================================
# This script uses Railway CLI to create and configure all services
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗"
echo -e "║   Railway Auto-Deploy Setup (CLI)     ║"
echo -e "╚════════════════════════════════════════╝${NC}\n"

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}✗ Railway CLI not found${NC}"
    echo "Install: npm i -g @railway/cli"
    exit 1
fi

# Check auth
if ! railway whoami &> /dev/null 2>&1; then
    echo -e "${RED}✗ Not logged in${NC}"
    echo "Run: railway login"
    exit 1
fi

USER=$(railway whoami 2>&1 || echo "Unknown")
echo -e "${GREEN}✓ Logged in as: $USER${NC}"

# Check project link
if ! railway status &> /dev/null 2>&1; then
    echo -e "${RED}✗ No project linked${NC}"
    echo "Run: railway link"
    exit 1
fi

echo -e "${GREEN}✓ Project linked${NC}\n"

# Get project info
echo -e "${BLUE}Current Project:${NC}"
railway status
echo ""

# Prompt for API keys
echo -e "${YELLOW}We'll need your API keys. Have them ready:${NC}"
read -p "ANTHROPIC_API_KEY: " ANTHROPIC_KEY
read -p "OPENAI_API_KEY: " OPENAI_KEY
read -p "PINECONE_API_KEY: " PINECONE_KEY
read -p "FLOWER_BASIC_AUTH (e.g., admin:password): " FLOWER_AUTH
echo ""

echo -e "${BLUE}Creating services...${NC}\n"

# Function to create service and set variables
create_service() {
    local SERVICE_NAME=$1
    shift
    local VARS=("$@")

    echo -e "${YELLOW}→ Creating service: $SERVICE_NAME${NC}"

    # Add service
    railway add --service "$SERVICE_NAME" || echo "Service may already exist"

    # Link to service for variable setting
    railway service "$SERVICE_NAME" || true

    # Set variables
    for VAR in "${VARS[@]}"; do
        KEY="${VAR%%=*}"
        VALUE="${VAR#*=}"
        echo "  Setting: $KEY"
        railway variables set "$KEY=$VALUE" || echo "  Failed to set $KEY"
    done

    echo -e "${GREEN}✓ Service $SERVICE_NAME configured${NC}\n"
}

# 1. Create Redis (database)
echo -e "${YELLOW}→ Creating Redis database${NC}"
railway add --database redis || echo "Redis may already exist"
echo -e "${GREEN}✓ Redis created${NC}\n"

# 2. Create API service
create_service "api" \
    "FLASK_ENV=production" \
    "FLASK_DEBUG=0" \
    "FLASK_APP=src.app:create_app" \
    "CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0" \
    "CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1" \
    "OUTPUT_DIR=/app/data/output" \
    "CORS_ORIGINS=*" \
    "ANTHROPIC_API_KEY=$ANTHROPIC_KEY" \
    "OPENAI_API_KEY=$OPENAI_KEY" \
    "PINECONE_API_KEY=$PINECONE_KEY"

# 3. Create Worker service
create_service "worker" \
    "CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0" \
    "CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1" \
    "OUTPUT_DIR=/app/data/output" \
    "ANTHROPIC_API_KEY=$ANTHROPIC_KEY" \
    "OPENAI_API_KEY=$OPENAI_KEY" \
    "PINECONE_API_KEY=$PINECONE_KEY"

# 4. Create Flower service
create_service "flower" \
    "CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0" \
    "CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1" \
    "FLOWER_BASIC_AUTH=$FLOWER_AUTH"

# 5. Create Frontend service
create_service "frontend"

echo -e "${GREEN}╔════════════════════════════════════════╗"
echo -e "║     Services Created Successfully!     ║"
echo -e "╚════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}⚠  IMPORTANT: Manual Configuration Required${NC}\n"

echo "You still need to configure build settings in Railway dashboard:"
echo ""
echo -e "${BLUE}1. API Service:${NC}"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile: docker/api.Dockerfile"
echo "     - Build Args: --target prod"
echo "   Settings → Deploy:"
echo "     - Health Check Path: /api/health"
echo "   Settings → Networking:"
echo "     - Generate Domain"
echo ""

echo -e "${BLUE}2. Worker Service:${NC}"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile: docker/worker.Dockerfile"
echo "     - Build Args: --target prod"
echo ""

echo -e "${BLUE}3. Flower Service:${NC}"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile: docker/worker.Dockerfile"
echo "     - Build Args: --target prod"
echo "   Settings → Deploy:"
echo "     - Start Command: celery -A api.celery_app flower --port=5555 --url_prefix="
echo "   Settings → Networking:"
echo "     - Generate Domain"
echo ""

echo -e "${BLUE}4. Frontend Service:${NC}"
echo "   Settings → Source:"
echo "     - Root Directory: frontend"
echo "   Settings → Build:"
echo "     - Builder: Docker"
echo "     - Dockerfile: docker/frontend.Dockerfile"
echo "     - Build Args: --target prod --build-arg VITE_API_URL=https://\${{api.RAILWAY_PUBLIC_DOMAIN}}"
echo "   Settings → Networking:"
echo "     - Generate Domain"
echo ""

echo -e "${GREEN}After configuration, push to main to deploy:${NC}"
echo "  git push origin main"
echo ""

echo -e "${YELLOW}Tip: Railway doesn't support full CLI-based build config yet.${NC}"
echo -e "${YELLOW}Use the dashboard for Dockerfile paths and build settings.${NC}"
