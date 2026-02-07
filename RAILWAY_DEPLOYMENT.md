# Railway Deployment Guide

This guide explains how to deploy the Lead Gen application to Railway with multiple services.

## Architecture

The application consists of 5 services:
1. **Redis** - Message broker and cache (Railway managed service)
2. **API** - Flask REST API backend
3. **Worker** - Celery task worker for async processing
4. **Flower** - Celery monitoring dashboard
5. **Frontend** - React SPA served by Nginx

## Prerequisites

- Railway CLI installed (`npm i -g @railway/cli`)
- Logged into Railway (`railway login`)
- Project linked to GitHub repository

## Deployment Steps

### Step 1: Create Redis Service

In Railway dashboard:
1. Click "New" → "Database" → "Add Redis"
2. Name it "redis"
3. Note: Railway will auto-generate `REDIS_URL` variable

### Step 2: Deploy API Service

```bash
# Link to the API service (create if doesn't exist)
railway service

# Deploy with the API Dockerfile
railway up --service api
```

**API Environment Variables** (set in Railway dashboard):
```
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_APP=src.app:create_app
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
CORS_ORIGINS=https://your-domain.railway.app
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

**API Build Configuration:**
- Dockerfile Path: `docker/api.Dockerfile`
- Docker Build Args: `--target prod`
- Root Directory: `/`
- Port: `5000`

### Step 3: Deploy Worker Service

```bash
# Create/link worker service
railway service

# Deploy with Worker Dockerfile
railway up --service worker
```

**Worker Environment Variables:**
```
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
OUTPUT_DIR=/app/data/output
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

**Worker Build Configuration:**
- Dockerfile Path: `docker/worker.Dockerfile`
- Docker Build Args: `--target prod`
- Root Directory: `/`

### Step 4: Deploy Flower Service

```bash
# Create/link flower service
railway service

# Deploy with Worker Dockerfile (same as worker)
railway up --service flower
```

**Flower Environment Variables:**
```
CELERY_BROKER_URL=${{redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{redis.REDIS_URL}}/1
FLOWER_BASIC_AUTH=username:password
```

**Flower Build Configuration:**
- Dockerfile Path: `docker/worker.Dockerfile`
- Docker Build Args: `--target prod`
- Start Command: `celery -A api.celery_app flower --port=5555 --url_prefix=`
- Root Directory: `/`
- Port: `5555`

### Step 5: Deploy Frontend Service

```bash
# Create/link frontend service
railway service

# Deploy with Frontend Dockerfile
railway up --service frontend
```

**Frontend Build Configuration:**
- Dockerfile Path: `docker/frontend.Dockerfile`
- Docker Build Args: `--target prod --build-arg VITE_API_URL=https://api-service.railway.app`
- Root Directory: `/frontend`
- Port: `80`

Replace `https://api-service.railway.app` with your actual API service Railway URL.

## Alternative: Manual Dashboard Configuration

If you prefer to configure via Railway dashboard:

1. Go to your project in Railway dashboard
2. Click "New" → "Empty Service" for each service (api, worker, flower, frontend)
3. For each service:
   - Go to "Settings" → "Build"
   - Set Dockerfile path and build args
   - Set root directory
   - Configure environment variables
   - Enable public domain (for api and frontend)
4. Deploy by connecting to GitHub repo or using `railway up`

## Service Dependencies

- **API** depends on Redis
- **Worker** depends on Redis and API
- **Flower** depends on Redis
- **Frontend** depends on API

Set these in Railway by configuring service references in environment variables using `${{service.VARIABLE}}` syntax.

## Shared Data Volume

Railway doesn't support shared volumes between services like Docker Compose does. For the `/app/data` volume:

Options:
1. Use Railway Volumes (each service gets its own)
2. Use external S3/GCS for shared file storage
3. Store results in Redis or a database

Recommended: Modify the application to use S3/GCS for shared file storage instead of local volumes.

## Monitoring

- **API Health**: `https://api-service.railway.app/api/health`
- **Flower Dashboard**: `https://flower-service.railway.app/`
- **Railway Logs**: Use `railway logs` or check dashboard

## Troubleshooting

### Services can't communicate
- Make sure service references are set correctly: `${{redis.REDIS_URL}}`
- Check that services are in the same project

### Build failures
- Verify Dockerfile paths are correct relative to root
- Check that all required build args are provided
- Ensure buildTarget is set to "prod" for production builds

### Worker not processing tasks
- Verify CELERY_BROKER_URL and CELERY_RESULT_BACKEND are set correctly
- Check worker logs: `railway logs --service worker`
- Ensure API service is healthy before worker starts

## Cost Optimization

Railway charges per service. To reduce costs:
1. Combine Flower with Worker (optional monitoring)
2. Use Railway's free Redis tier
3. Use appropriate instance sizes
4. Enable auto-scaling only if needed
