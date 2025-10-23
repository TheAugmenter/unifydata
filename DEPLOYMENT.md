# 🚀 Deployment Guide - UnifyData.AI

Ghid complet pentru deployment pe production (Vercel + Railway/Render).

---

## 📋 Deployment Strategy

### Architecture Overview
```
┌─────────────────┐
│   Vercel CDN    │  <- Next.js Frontend (Static + SSR)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Railway/Render │  <- FastAPI Backend + PostgreSQL
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Managed DBs    │  <- Redis, Neo4j, Pinecone (Cloud)
└─────────────────┘
```

### Services
1. **Frontend**: Vercel (Next.js)
2. **Backend**: Railway/Render/Fly.io (FastAPI)
3. **Database**: Railway PostgreSQL / Neon / Supabase
4. **Redis**: Upstash Redis
5. **Neo4j**: Neo4j Aura
6. **Vector DB**: Pinecone

---

## 🌐 Part 1: Deploy Frontend to Vercel

### Prerequisites
- GitHub account
- Vercel account (free tier OK)
- Git repository with code pushed

### Step 1: Prepare Repository

#### 1.1 Initialize Git (if not done)
```bash
git init
git add .
git commit -m "Initial commit - Ready for deployment"
```

#### 1.2 Create GitHub Repository
```bash
# On GitHub, create new repository: unifydata-ai
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/unifydata-ai.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

#### 2.1 Connect Repository
1. Go to https://vercel.com
2. Click "Add New Project"
3. Import your GitHub repository
4. Select "unifydata-ai"

#### 2.2 Configure Build Settings
```
Framework Preset: Next.js
Root Directory: web
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

#### 2.3 Set Environment Variables
Add these in Vercel Dashboard → Settings → Environment Variables:

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

#### 2.4 Deploy
Click "Deploy" - Vercel will:
- ✅ Install dependencies
- ✅ Build Next.js app
- ✅ Deploy to CDN
- ✅ Assign URL: https://unifydata-ai-xxx.vercel.app

### Step 3: Configure Custom Domain (Optional)
1. Go to Settings → Domains
2. Add your domain: `app.unifydata.ai`
3. Follow DNS configuration instructions

---

## 🔧 Part 2: Deploy Backend to Railway

Railway oferă hosting gratuit pentru PostgreSQL + Python apps.

### Step 1: Sign Up for Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. You get $5/month free credit

### Step 2: Create New Project

#### 2.1 Deploy PostgreSQL
1. Click "New Project"
2. Select "Provision PostgreSQL"
3. Wait for deployment (~1 minute)
4. Copy connection details:
   - Database URL
   - Host, Port, Username, Password

#### 2.2 Deploy FastAPI Backend
1. Click "New" → "GitHub Repo"
2. Select your repository
3. Railway auto-detects Python
4. Configure:
   - Root Directory: `backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### 2.3 Set Environment Variables
In Railway Dashboard → Variables:

```env
# Application
ENVIRONMENT=production
DEBUG=False
API_V1_PREFIX=/api/v1

# Database (Railway provides DATABASE_URL automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (use Upstash - see below)
REDIS_URL=your-upstash-redis-url

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

#### 2.4 Deploy
Railway will:
- ✅ Install Python dependencies
- ✅ Start FastAPI server
- ✅ Assign URL: https://your-app-production.up.railway.app

### Step 3: Update Vercel Environment
Update `NEXT_PUBLIC_API_URL` in Vercel with Railway backend URL:
```
NEXT_PUBLIC_API_URL=https://your-app-production.up.railway.app
```

Redeploy frontend.

---

## 🗄️ Part 3: Set Up Managed Databases

### 3.1 PostgreSQL
Already set up in Railway! ✅

### 3.2 Redis - Upstash (Free Tier)
1. Go to https://upstash.com
2. Create account
3. Create Redis database
4. Copy Redis URL
5. Add to Railway env: `REDIS_URL=...`

### 3.3 Neo4j - Neo4j Aura (Free Tier)
1. Go to https://neo4j.com/cloud/aura/
2. Create free instance
3. Copy connection details:
   - URI: `neo4j+s://xxx.databases.neo4j.io`
   - Username: `neo4j`
   - Password: `your-password`
4. Add to Railway env:
   ```
   NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   ```

### 3.4 Pinecone (Free Tier)
1. Already have API key
2. Ensure it's in Railway env variables

---

## 🔐 Part 4: Secure Production Setup

### 4.1 Generate Secure Secrets
```bash
# JWT Secret
openssl rand -hex 32

# App Secret Key
openssl rand -hex 32
```

### 4.2 Update Environment Variables
Replace all placeholder secrets with real ones.

### 4.3 Configure CORS
Update `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://unifydata-ai-xxx.vercel.app",
        "https://app.unifydata.ai",  # Your custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.4 Enable HTTPS Only
Both Vercel and Railway provide SSL automatically! ✅

---

## 🧪 Part 5: Test Production Deployment

### Test Checklist

#### Frontend (Vercel)
- [ ] App loads at Vercel URL
- [ ] No console errors
- [ ] Registration page works
- [ ] Login page works
- [ ] Images/assets load correctly

#### Backend (Railway)
- [ ] Health check: `https://your-backend.railway.app/health`
- [ ] API docs: `https://your-backend.railway.app/docs`
- [ ] CORS allows frontend requests
- [ ] Database connection works
- [ ] Redis connection works

#### End-to-End Flow
- [ ] Register new user
- [ ] Receive JWT tokens
- [ ] Complete onboarding
- [ ] Login with credentials
- [ ] Token refresh works
- [ ] Session persists across reloads

### Test Commands
```bash
# Test backend health
curl https://your-backend.railway.app/health

# Test registration
curl -X POST https://your-backend.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "company_name": "Test Company"
  }'
```

---

## 📊 Part 6: Monitor Production

### Railway Dashboard
- View logs: `railway logs`
- Monitor CPU/Memory usage
- Check database metrics

### Vercel Dashboard
- View deployment logs
- Monitor function invocations
- Check analytics

### Set Up Monitoring (Optional)
1. **Sentry** for error tracking
2. **LogRocket** for session replay
3. **Datadog** for APM

---

## 🔄 Part 7: CI/CD - Automatic Deployments

### Vercel Auto-Deploy
Already configured! ✅
- Push to `main` → Auto-deploy production
- Push to other branches → Preview deployments

### Railway Auto-Deploy
Already configured! ✅
- Push to `main` → Auto-deploy backend

### Workflow
```bash
# Make changes locally
git add .
git commit -m "Add new feature"
git push origin main

# Vercel auto-deploys frontend
# Railway auto-deploys backend
# Wait ~2-3 minutes
# Test at production URLs
```

---

## 📝 Part 8: Deployment Checklist

### Before First Deploy
- [ ] All environment variables set
- [ ] Secrets generated (JWT, etc.)
- [ ] CORS configured for production URLs
- [ ] Database migrations ready
- [ ] Test all endpoints locally

### After Deploy
- [ ] Frontend loads correctly
- [ ] Backend health check passes
- [ ] Database connected
- [ ] Redis connected
- [ ] Register/login flow works
- [ ] Monitor logs for errors

### Regular Updates
- [ ] Test locally first
- [ ] Commit and push to GitHub
- [ ] Wait for auto-deploy
- [ ] Test production
- [ ] Monitor for issues

---

## 🆘 Troubleshooting Production

### Frontend Issues

#### Problem: "Failed to fetch" errors
**Solution**: Check `NEXT_PUBLIC_API_URL` in Vercel env vars

#### Problem: 404 on page refresh
**Solution**: Already handled by Next.js! No action needed.

#### Problem: Slow page loads
**Solution**: Check Vercel Analytics for bottlenecks

### Backend Issues

#### Problem: 500 Internal Server Error
**Solution**: Check Railway logs:
```bash
railway logs
```

#### Problem: Database connection timeout
**Solution**: Check DATABASE_URL in Railway env vars

#### Problem: CORS errors
**Solution**: Add frontend URL to CORS origins in `app/main.py`

### Database Issues

#### Problem: Connection refused
**Solution**: Check PostgreSQL is running in Railway dashboard

#### Problem: Migration errors
**Solution**: Run migrations manually:
```bash
railway run alembic upgrade head
```

---

## 💰 Cost Estimate

### Free Tier Usage
- **Vercel**: Free for personal projects (100GB bandwidth)
- **Railway**: $5/month credit (enough for small MVP)
- **Upstash Redis**: Free tier (10K requests/day)
- **Neo4j Aura**: Free tier (50MB storage)
- **Pinecone**: Free tier (1 index, 100K vectors)

### Paid Tier (when scaling)
- **Vercel Pro**: $20/month
- **Railway**: ~$20-50/month (depending on usage)
- **Databases**: ~$10-30/month each

**Total MVP Cost**: ~$0-5/month (free tiers)
**Total Paid**: ~$50-100/month (after scaling)

---

## 🎯 Quick Deploy Commands

### Deploy Everything
```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to production"
git push origin main

# 2. Vercel auto-deploys frontend
# 3. Railway auto-deploys backend

# Wait 2-3 minutes, then test:
# Frontend: https://unifydata-ai-xxx.vercel.app
# Backend: https://your-app-production.up.railway.app
```

### Manual Deploy (if needed)
```bash
# Vercel CLI
npm i -g vercel
cd web
vercel --prod

# Railway CLI
npm i -g @railway/cli
railway login
railway up
```

---

## 📚 Additional Resources

### Documentation
- **Vercel**: https://vercel.com/docs
- **Railway**: https://docs.railway.app
- **Next.js Deployment**: https://nextjs.org/docs/deployment

### Support
- **Vercel Discord**: https://vercel.com/discord
- **Railway Discord**: https://discord.gg/railway

---

## ✅ Success Criteria

Your deployment is successful when:
- ✅ Frontend loads at Vercel URL
- ✅ Backend responds at Railway URL
- ✅ Database connections work
- ✅ Registration flow works end-to-end
- ✅ Login persists across sessions
- ✅ No console errors
- ✅ API docs accessible
- ✅ SSL enabled (https://)

---

**Ready to deploy? Follow the steps above! 🚀**

**Quick Start:**
1. Push code to GitHub
2. Connect to Vercel
3. Deploy backend to Railway
4. Set environment variables
5. Test production!

**Estimated Time**: 30-45 minutes for first deploy
