# Railway Auto-Deploy Quick Start

## 🚀 Goal
Auto-deploy from GitHub `single-analysis` branch with 5 services: Redis, API, Worker, Flower, Frontend

---

## Step 1: Create Services in Railway Dashboard

Go to https://railway.app/project and create these services:

### 1. Redis Database
- Click: **New → Database → Add Redis**
- Name: `redis`

### 2. API Service
- Click: **New → GitHub Repo → aaiach/benchmark-packaging**
- Name: `api`
- Settings → Source:
  - Root Directory: `/` (leave default)
  - Production Branch: `single-analysis`
- Settings → Build:
  - Builder: `Docker`
  - Dockerfile Path: `docker/api.Dockerfile`
  - Build Command: `docker build --target prod -f docker/api.Dockerfile .`
- Settings → Deploy:
  - Health Check Path: `/api/health`
  - Health Check Timeout: `10`
- Settings → Networking:
  - ✅ Generate Domain
- Settings → Variables (add these):
```env
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_APP=src.app:create_app
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
CORS_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
ANTHROPIC_API_KEY=<paste-your-key>
OPENAI_API_KEY=<paste-your-key>
PINECONE_API_KEY=<paste-your-key>
```

### 3. Worker Service
- Click: **New → GitHub Repo → aaiach/benchmark-packaging**
- Name: `worker`
- Settings → Source:
  - Production Branch: `single-analysis`
- Settings → Build:
  - Builder: `Docker`
  - Dockerfile Path: `docker/worker.Dockerfile`
  - Build Command: `docker build --target prod -f docker/worker.Dockerfile .`
- Settings → Variables:
```env
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
ANTHROPIC_API_KEY=<paste-your-key>
OPENAI_API_KEY=<paste-your-key>
PINECONE_API_KEY=<paste-your-key>
```

### 4. Flower Service (Optional - for monitoring)
- Click: **New → GitHub Repo → aaiach/benchmark-packaging**
- Name: `flower`
- Settings → Source:
  - Production Branch: `single-analysis`
- Settings → Build:
  - Builder: `Docker`
  - Dockerfile Path: `docker/worker.Dockerfile`
  - Build Command: `docker build --target prod -f docker/worker.Dockerfile .`
- Settings → Deploy:
  - Start Command: `celery -A api.celery_app flower --port=5555 --url_prefix=`
- Settings → Networking:
  - ✅ Generate Domain
- Settings → Variables:
```env
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
FLOWER_BASIC_AUTH=admin:changeme123
```

### 5. Frontend Service
- Click: **New → GitHub Repo → aaiach/benchmark-packaging**
- Name: `frontend`
- Settings → Source:
  - Root Directory: `frontend`
  - Production Branch: `single-analysis`
- Settings → Build:
  - Builder: `Docker`
  - Dockerfile Path: `docker/frontend.Dockerfile`
  - Build Command: `docker build --target prod --build-arg VITE_API_URL=https://${{api.RAILWAY_PUBLIC_DOMAIN}} -f ../docker/frontend.Dockerfile .`
- Settings → Deploy:
  - Health Check Path: `/`
- Settings → Networking:
  - ✅ Generate Domain
  - Optional: Add custom domain `packaging-benchmark.tryiceberg.ai`

---

## Step 2: Update CORS Origins

Once frontend domain is generated:

1. Go to **API service → Variables**
2. Update `CORS_ORIGINS` to include frontend domain:
```env
CORS_ORIGINS=https://<frontend-domain>.railway.app,https://packaging-benchmark.tryiceberg.ai
```

---

## Step 3: Test the Deployment

Push a change to trigger auto-deploy:

```bash
git add .
git commit -m "Configure Railway auto-deploy"
git push origin single-analysis
```

Railway will automatically:
1. Detect the push to `main` branch
2. Build all services with their Dockerfiles
3. Deploy updated services
4. Run health checks

---

## Step 4: Verify Services

Check each service is running:

- **Redis**: Should show "Active" in dashboard
- **API**: Visit `https://<api-domain>.railway.app/api/health` → Should return `{"status": "healthy"}`
- **Worker**: Check logs for "celery@worker ready"
- **Flower**: Visit `https://<flower-domain>.railway.app/` → Should show Flower UI
- **Frontend**: Visit `https://<frontend-domain>.railway.app/` → Should load your app

---

## 🎯 Auto-Deploy Workflow

From now on, every time you push to `single-analysis`:

```bash
# Make changes
git add .
git commit -m "Your changes"
git push origin single-analysis

# Railway automatically:
# 1. Detects push
# 2. Builds affected services
# 3. Deploys new versions
# 4. No manual intervention needed!
```

---

## 📊 Monitoring

**View Logs:**
```bash
railway logs --service api
railway logs --service worker
railway logs --service flower
```

**Check Status:**
```bash
railway status
```

**View Deployments:**
- Go to each service in dashboard
- Click "Deployments" tab
- See history and rollback if needed

---

## 🔧 Troubleshooting

### API won't start
- Check environment variables are set correctly
- Verify Redis service is running
- Check logs: `railway logs --service api`

### Worker not processing tasks
- Verify `CELERY_BROKER_URL` matches Redis URL
- Check API is healthy first
- View worker logs: `railway logs --service worker`

### Frontend shows "Network Error"
- Update API's `CORS_ORIGINS` with frontend domain
- Verify VITE_API_URL was set correctly at build time
- Rebuild frontend if API URL changed

### Services can't reach Redis
- Use `${{redis.REDIS_URL}}` syntax (not hardcoded URLs)
- Verify Redis service is in same project
- Check Redis is running

---

## 🎛️ Advanced: Branch-Based Deployments

**Staging Environment:**
1. Create new environment in Railway: "staging"
2. Link to branch: `staging`
3. Deploy to staging first, then merge to `main` for production

**Preview Deployments:**
- Railway can create preview deployments for PRs
- Enable in Settings → Deployments → PR Deploys

---

## 💰 Cost Optimization

- **Flower**: Optional, disable if not needed for monitoring
- **Worker**: Scale down replicas during low usage
- **Redis**: Use Railway's free tier (500MB)

---

## 📝 Environment Variables Reference

Copy these templates to each service:

**API:**
```env
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_APP=src.app:create_app
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
CORS_ORIGINS=https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
PINECONE_API_KEY=
```

**Worker:**
```env
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
PINECONE_API_KEY=
```

**Flower:**
```env
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
FLOWER_BASIC_AUTH=admin:password
```

---

## ✅ Success Checklist

- [ ] Redis database created and running
- [ ] API service deployed and health check passing
- [ ] Worker service deployed and logs show "ready"
- [ ] Flower service accessible (optional)
- [ ] Frontend service loads in browser
- [ ] API calls from frontend work correctly
- [ ] Test job runs successfully end-to-end
- [ ] Push to `main` triggers auto-deployment
- [ ] Custom domain configured (if needed)

---

**Need help?** Check Railway docs: https://docs.railway.app/
