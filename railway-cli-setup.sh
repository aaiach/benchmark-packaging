#!/bin/bash
# =============================================================================
# Railway Multi-Service Setup via CLI
# =============================================================================
# Based on Railway CLI documentation (docs.railway.com)
# This script creates all services and sets environment variables
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check prerequisites
if ! command -v railway &> /dev/null; then
    print_error "Railway CLI not installed"
    echo "Install: npm i -g @railway/cli"
    exit 1
fi

if ! railway whoami &> /dev/null 2>&1; then
    print_error "Not logged in to Railway"
    echo "Run: railway login"
    exit 1
fi

if ! railway status &> /dev/null 2>&1; then
    print_error "No Railway project linked"
    echo "Run: railway link"
    exit 1
fi

print_header "Railway Multi-Service Setup"

USER=$(railway whoami 2>&1)
print_success "Logged in as: $USER"

echo ""
railway status
echo ""

# Collect API keys
print_header "API Keys Configuration"
echo "Enter your API keys (they'll be stored in Railway):"
read -p "ANTHROPIC_API_KEY: " ANTHROPIC_KEY
read -p "OPENAI_API_KEY: " OPENAI_KEY
read -p "PINECONE_API_KEY: " PINECONE_KEY
read -p "FLOWER_BASIC_AUTH (format: username:password): " FLOWER_AUTH

# Step 1: Add Redis
print_header "Step 1: Creating Redis Database"
print_info "Adding Redis database..."
railway add --database redis || print_error "Redis might already exist - continuing..."
print_success "Redis database configured"

# Step 2: Add services from GitHub repo
print_header "Step 2: Creating Services"

echo ""
print_info "We need to create 4 services from your GitHub repo:"
echo "  1. api (Flask backend)"
echo "  2. worker (Celery worker)"
echo "  3. flower (Celery monitoring)"
echo "  4. frontend (React app)"
echo ""
echo "Railway CLI requires interactive selection for GitHub repos."
echo "You'll need to manually create these services in the dashboard."
echo ""
print_info "Opening Railway dashboard..."
echo ""
echo "In the dashboard, for EACH service:"
echo "  1. Click 'New' → 'GitHub Repo'"
echo "  2. Select: aaiach/benchmark-packaging"
echo "  3. Name the service: api, worker, flower, or frontend"
echo ""
read -p "Press Enter when you've created all 4 services in the dashboard..."

# Step 3: Configure API service
print_header "Step 3: Configuring API Service"
print_info "Setting environment variables for API..."

# Note: railway variable requires being in service context
# We'll create a config file instead

cat > railway.api.json <<EOF
{
  "\$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/api.Dockerfile",
    "watchPatterns": ["api/**", "analysis_engine/**", "docker/api.Dockerfile"]
  },
  "deploy": {
    "startCommand": null,
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

print_success "Created railway.api.json"
echo ""
print_info "Copy railway.api.json as 'railway.json' in your repo root"
print_info "Then set these environment variables in API service dashboard:"
echo ""
echo "FLASK_ENV=production"
echo "FLASK_DEBUG=0"
echo "FLASK_APP=src.app:create_app"
echo "CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0"
echo "CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1"
echo "OUTPUT_DIR=/app/data/output"
echo "CORS_ORIGINS=https://\${{frontend.RAILWAY_PUBLIC_DOMAIN}}"
echo "ANTHROPIC_API_KEY=$ANTHROPIC_KEY"
echo "OPENAI_API_KEY=$OPENAI_KEY"
echo "PINECONE_API_KEY=$PINECONE_KEY"

# Step 4: Configure Worker service
print_header "Step 4: Configuring Worker Service"

cat > railway.worker.json <<EOF
{
  "\$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/worker.Dockerfile",
    "watchPatterns": ["api/**", "analysis_engine/**", "docker/worker.Dockerfile"]
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

print_success "Created railway.worker.json"
echo ""
print_info "Set these environment variables in Worker service dashboard:"
echo ""
echo "CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0"
echo "CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1"
echo "OUTPUT_DIR=/app/data/output"
echo "ANTHROPIC_API_KEY=$ANTHROPIC_KEY"
echo "OPENAI_API_KEY=$OPENAI_KEY"
echo "PINECONE_API_KEY=$PINECONE_KEY"

# Step 5: Configure Flower service
print_header "Step 5: Configuring Flower Service"

cat > railway.flower.json <<EOF
{
  "\$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/worker.Dockerfile",
    "watchPatterns": ["api/**", "docker/worker.Dockerfile"]
  },
  "deploy": {
    "startCommand": "celery -A api.celery_app flower --port=5555 --url_prefix=",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

print_success "Created railway.flower.json"
echo ""
print_info "Set these environment variables in Flower service dashboard:"
echo ""
echo "CELERY_BROKER_URL=\${{redis.REDIS_URL}}/0"
echo "CELERY_RESULT_BACKEND=\${{redis.REDIS_URL}}/1"
echo "FLOWER_BASIC_AUTH=$FLOWER_AUTH"

# Step 6: Configure Frontend service
print_header "Step 6: Configuring Frontend Service"

cat > railway.frontend.json <<EOF
{
  "\$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/frontend.Dockerfile",
    "watchPatterns": ["frontend/**", "docker/frontend.Dockerfile"]
  },
  "deploy": {
    "healthcheckPath": "/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

print_success "Created railway.frontend.json"
echo ""
print_info "Set root directory in Frontend service settings: frontend"
print_info "Set build arg in service settings:"
echo "  VITE_API_URL=https://\${{api.RAILWAY_PUBLIC_DOMAIN}}"

# Final instructions
print_header "Setup Complete!"

echo "Generated configuration files:"
echo "  • railway.api.json"
echo "  • railway.worker.json"
echo "  • railway.flower.json"
echo "  • railway.frontend.json"
echo ""
echo "${YELLOW}Next steps:${NC}"
echo ""
echo "1. For each service in Railway dashboard:"
echo "   a. Go to Settings → Config File Path"
echo "   b. Set the path to the corresponding railway.*.json file"
echo "      - API: railway.api.json"
echo "      - Worker: railway.worker.json"
echo "      - Flower: railway.flower.json"
echo "      - Frontend: railway.frontend.json"
echo ""
echo "2. For Frontend service only:"
echo "   - Settings → Source → Root Directory: frontend"
echo ""
echo "3. Copy the environment variables shown above into each service's"
echo "   Variables section in the Railway dashboard"
echo ""
echo "4. Enable public domains:"
echo "   - API: Settings → Networking → Generate Domain"
echo "   - Frontend: Settings → Networking → Generate Domain"
echo "   - Flower: Settings → Networking → Generate Domain"
echo ""
echo "5. Commit the config files to your repo:"
echo "   git add railway.*.json"
echo "   git commit -m 'Add Railway service configurations'"
echo "   git push origin main"
echo ""
echo "6. Railway will automatically deploy when you push to main!"
echo ""
print_success "All configuration files generated!"
