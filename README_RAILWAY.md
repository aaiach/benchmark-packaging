# Railway Deployment - Auto-Deploy from GitHub

This project is configured for automatic deployment from GitHub to Railway with 5 services.

## 📦 Services

1. **Redis** - Message broker (Railway managed database)
2. **API** - Flask REST backend
3. **Worker** - Celery task processor
4. **Flower** - Celery monitoring UI
5. **Frontend** - React SPA

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

Run the setup script:

```bash
./railway-cli-setup.sh
```

This will:
- Verify your Railway CLI is set up
- Create a Redis database
- Generate configuration files for each service
- Provide step-by-step instructions

### Option 2: Manual Setup

Follow the detailed guide in `RAILWAY_QUICK_START.md`

## 📁 Configuration Files

Each service has its own configuration in `.railway/`:

- `.railway/api.json` - API service configuration
- `.railway/worker.json` - Worker service configuration
- `.railway/flower.json` - Flower service configuration
- `.railway/frontend.json` - Frontend service configuration

These files define:
- Dockerfile paths
- Watch patterns (which files trigger redeployment)
- Health check settings
- Restart policies

## 🔄 Auto-Deploy Workflow

Once configured, Railway automatically deploys when you push to `main`:

```bash
git add .
git commit -m "Your changes"
git push origin main
# ✨ Railway automatically builds and deploys!
```

## ⚙️ Configuration per Service

### API Service
**Config File**: `.railway/api.json`
**Dockerfile**: `docker/api.Dockerfile`
**Port**: 5000
**Public**: Yes (generates domain)

**Environment Variables**:
```env
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_APP=src.app:create_app
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
CORS_ORIGINS=https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
PINECONE_API_KEY=<your-key>
```

### Worker Service
**Config File**: `.railway/worker.json`
**Dockerfile**: `docker/worker.Dockerfile`
**Public**: No (internal service)

**Environment Variables**:
```env
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
PINECONE_API_KEY=<your-key>
```

### Flower Service
**Config File**: `.railway/flower.json`
**Dockerfile**: `docker/worker.Dockerfile`
**Port**: 5555
**Public**: Yes (generates domain)

**Environment Variables**:
```env
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
FLOWER_BASIC_AUTH=username:password
```

### Frontend Service
**Config File**: `.railway/frontend.json`
**Dockerfile**: `docker/frontend.Dockerfile`
**Root Directory**: `frontend`
**Port**: 80
**Public**: Yes (generates domain)

**Build Args** (set in Railway dashboard):
```
VITE_API_URL=https://${{api.RAILWAY_PUBLIC_DOMAIN}}
```

## 🎯 Setup Checklist

- [ ] Railway CLI installed (`npm i -g @railway/cli`)
- [ ] Logged in to Railway (`railway login`)
- [ ] Project linked (`railway link`)
- [ ] Redis database created
- [ ] API service created from GitHub repo
- [ ] Worker service created from GitHub repo
- [ ] Flower service created from GitHub repo
- [ ] Frontend service created from GitHub repo
- [ ] Config file paths set for each service
- [ ] Environment variables set for each service
- [ ] Public domains generated for API, Flower, and Frontend
- [ ] Frontend root directory set to `frontend`
- [ ] Test deployment successful

## 📚 Documentation

- **RAILWAY_QUICK_START.md** - Step-by-step setup guide
- **RAILWAY_SETUP.md** - Detailed configuration reference
- **RAILWAY_DEPLOYMENT.md** - Advanced deployment topics
- **railway-cli-setup.sh** - Automated setup script

## 🔧 Troubleshooting

### Service won't build
- Verify Dockerfile path in service settings
- Check config file path is correct (`.railway/servicename.json`)
- View build logs in Railway dashboard

### Service won't start
- Check environment variables are set correctly
- Verify health check endpoint is responding
- View deployment logs in Railway dashboard

### Services can't communicate
- Use `${{service.VARIABLE}}` syntax for service references
- Ensure all services are in the same Railway project
- Verify Redis is running and accessible

### Auto-deploy not triggering
- Check the service is connected to GitHub repo
- Verify the correct branch is selected (main)
- Ensure watch patterns match changed files
- Check Railway dashboard for webhook status

## 💡 Tips

1. **Watch Patterns**: Services only redeploy when watched files change
2. **Service References**: Use `${{redis.REDIS_URL}}` to reference other services
3. **Build Args**: For frontend VITE_API_URL, set in service settings, not env vars
4. **Config Priority**: Config files override dashboard settings
5. **Logs**: Use `railway logs --service <name>` to view logs from CLI

## 🔗 Links

- Railway Docs: https://docs.railway.com/
- Railway CLI Reference: https://docs.railway.com/reference/cli-api
- Config-as-Code: https://docs.railway.com/guides/config-as-code

---

**Last Updated**: 2026-02-07
**Railway CLI Version**: 4.11.1
