# Railway Auto-Deploy from GitHub Setup

This guide configures automatic deployments from GitHub for all services.

## Overview

Railway will automatically deploy all services when you push to the `main` branch on GitHub.

## Services Configuration

### 1. Redis Service (Managed Database)

**Setup in Railway Dashboard:**
1. Go to your Railway project
2. Click "New" → "Database" → "Add Redis"
3. Name it: `redis`
4. This will auto-generate `REDIS_URL` variable that other services can reference

---

### 2. API Service (Flask Backend)

**Create Service:**
```bash
# In Railway dashboard:
# New → GitHub Repo → Select your repo → Add Service
```

**Service Settings:**

**Build Configuration:**
- **Builder**: Docker
- **Dockerfile Path**: `docker/api.Dockerfile`
- **Docker Build Arguments**: `--target prod`
- **Watch Paths**: `/api/**`, `/analysis_engine/**`, `/docker/api.Dockerfile`

**Deploy Configuration:**
- **Start Command**: (leave empty - uses Dockerfile CMD)
- **Port**: `5000`
- **Health Check Path**: `/api/health`
- **Restart Policy**: On Failure

**Environment Variables:**
```bash
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_APP=src.app:create_app
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
CORS_ORIGINS=${{RAILWAY_PUBLIC_DOMAIN}}

# API Keys (set these manually):
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

**Public Networking:**
- Enable "Generate Domain" to get a public URL

---

### 3. Worker Service (Celery Worker)

**Create Service:**
```bash
# In Railway dashboard:
# New → GitHub Repo → Select your repo → Add Service
```

**Service Settings:**

**Build Configuration:**
- **Builder**: Docker
- **Dockerfile Path**: `docker/worker.Dockerfile`
- **Docker Build Arguments**: `--target prod`
- **Watch Paths**: `/api/**`, `/analysis_engine/**`, `/docker/worker.Dockerfile`

**Deploy Configuration:**
- **Start Command**: (leave empty - uses Dockerfile CMD)
- **Restart Policy**: On Failure

**Environment Variables:**
```bash
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output

# API Keys (set these manually):
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

**Public Networking:**
- Not required (internal service)

---

### 4. Flower Service (Celery Monitoring)

**Create Service:**
```bash
# In Railway dashboard:
# New → GitHub Repo → Select your repo → Add Service
```

**Service Settings:**

**Build Configuration:**
- **Builder**: Docker
- **Dockerfile Path**: `docker/worker.Dockerfile`
- **Docker Build Arguments**: `--target prod`
- **Watch Paths**: `/api/**`, `/docker/worker.Dockerfile`

**Deploy Configuration:**
- **Start Command**: `celery -A api.celery_app flower --port=5555 --url_prefix=`
- **Port**: `5555`
- **Restart Policy**: On Failure

**Environment Variables:**
```bash
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
FLOWER_BASIC_AUTH=admin:your_password_here
```

**Public Networking:**
- Enable "Generate Domain" to access Flower UI

---

### 5. Frontend Service (React SPA)

**Create Service:**
```bash
# In Railway dashboard:
# New → GitHub Repo → Select your repo → Add Service
```

**Service Settings:**

**Build Configuration:**
- **Builder**: Docker
- **Dockerfile Path**: `docker/frontend.Dockerfile`
- **Docker Build Arguments**: `--target prod --build-arg VITE_API_URL=https://${{api.RAILWAY_PUBLIC_DOMAIN}}`
- **Root Directory**: `frontend`
- **Watch Paths**: `/frontend/**`, `/docker/frontend.Dockerfile`

**Deploy Configuration:**
- **Start Command**: (leave empty - uses Dockerfile CMD)
- **Port**: `80`
- **Health Check Path**: `/`
- **Restart Policy**: On Failure

**Environment Variables:**
```bash
# The API URL is set via build arg, but you can also set it here if needed:
VITE_API_URL=https://${{api.RAILWAY_PUBLIC_DOMAIN}}
```

**Public Networking:**
- Enable "Generate Domain" to get public URL for your app

---

## Service Dependencies

Configure service start order (in Railway dashboard under Settings → Deploy):

1. **Redis** → No dependencies
2. **API** → Depends on: `redis`
3. **Worker** → Depends on: `redis`, `api`
4. **Flower** → Depends on: `redis`
5. **Frontend** → Depends on: `api`

---

## Auto-Deploy Triggers

**Default Setup:**
- Railway automatically deploys when you push to `main` branch
- Each service watches its relevant paths (configured above)
- Only affected services redeploy when their watch paths change

**Branch Configuration:**
To deploy from a different branch:
1. Go to Service Settings → Source
2. Change "Production Branch" to your desired branch (e.g., `production`)

---

## Deployment Workflow

### For Development:
```bash
git checkout main
# Make changes
git add .
git commit -m "Your changes"
git push origin main
# Railway automatically deploys affected services
```

### For Production with Staging:
```bash
# Work on feature branch
git checkout -b feature/new-feature
# Make changes
git push origin feature/new-feature

# Create PR, review, merge to main
# Railway auto-deploys to production
```

---

## Environment-Based Deployments

**Production Environment:**
- Branch: `main`
- Domain: `packaging-benchmark.tryiceberg.ai`
- Environment: Set in Railway dashboard

**Staging Environment (Optional):**
1. Create a new environment in Railway dashboard
2. Set branch to `staging`
3. Deploy with different domains/settings

---

## Custom Domain Setup

**For Frontend:**
1. Go to Frontend Service → Settings → Networking
2. Click "Custom Domain"
3. Add: `packaging-benchmark.tryiceberg.ai`
4. Set CNAME record in your DNS: `packaging-benchmark.tryiceberg.ai` → `<railway-domain>`

**For API:**
1. Go to API Service → Settings → Networking
2. Click "Custom Domain"
3. Add: `api.packaging-benchmark.tryiceberg.ai`

**For Flower:**
1. Go to Flower Service → Settings → Networking
2. Click "Custom Domain"
3. Add: `flower.packaging-benchmark.tryiceberg.ai`

---

## Monitoring Deployments

**Via Dashboard:**
- Go to Railway project
- Click on any service to see deployment logs
- View deployment history and rollback if needed

**Via CLI:**
```bash
# Watch deployment logs
railway logs --service api

# Check deployment status
railway status

# List recent deployments
railway deployment list
```

---

## Rollback Strategy

If a deployment fails:
1. Go to Service → Deployments
2. Find the last working deployment
3. Click "Redeploy" on that version

Or via CLI:
```bash
railway redeploy --service api
```

---

## Important Notes

### Shared Volumes
Railway doesn't support shared volumes between services. For the `/app/data` directory:

**Option 1: Service-specific volumes (current)**
- Each service gets its own persistent volume
- Not shared between services

**Option 2: External storage (recommended)**
- Use S3/GCS for shared file storage
- Modify code to upload/download from cloud storage

### Build Caching
Railway caches Docker layers. To force a rebuild:
1. Go to Service Settings → Builds
2. Enable "Force Rebuild" or clear build cache

### Environment Variables
- Use `${{service.VARIABLE}}` to reference variables from other services
- Use `${{RAILWAY_PUBLIC_DOMAIN}}` for the service's public domain
- Set sensitive variables (API keys) manually in dashboard, not in code

---

## Troubleshooting

### Service fails to build
- Check Dockerfile path is correct relative to repo root
- Verify all dependencies are in the repo
- Check build logs in Railway dashboard

### Service fails to deploy
- Check environment variables are set correctly
- Verify health check endpoint is responding
- Check service logs for errors

### Services can't communicate
- Verify service references use correct syntax: `${{redis.REDIS_URL}}`
- Check all services are in the same project
- Use Railway's private networking (services can reach each other via service names)

### Frontend can't reach API
- Verify VITE_API_URL is set correctly at build time
- Check CORS_ORIGINS in API includes frontend domain
- Ensure API service has public networking enabled
