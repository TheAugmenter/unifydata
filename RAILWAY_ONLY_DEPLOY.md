# 🚂 Railway-Only Deployment - UnifyData.AI MVP

Ghid complet pentru deploy pe **doar Railway** (Frontend + Backend + Databases).

---

## 💡 De Ce Railway-Only?

### Avantaje
- ✅ **Un singur loc** pentru tot: Frontend, Backend, Databases
- ✅ **Mai simplu** de configurat
- ✅ **Cost predictibil** - plătești doar pentru ce folosești
- ✅ **$5 credit gratuit/lună** pentru începători
- ✅ **Managed PostgreSQL** inclus
- ✅ **Auto-deploy** din GitHub
- ✅ **HTTPS automatic**
- ✅ **Logs centralizate**

### Dezavantaje vs Vercel
- ❌ Fără CDN global (Vercel e mai rapid pentru frontend)
- ❌ Fără edge functions
- ❌ Deploy mai lent pentru frontend (2-3 min vs <1 min)

### Când să folosești Railway-Only?
- ✅ MVP development & testing
- ✅ Internal tools
- ✅ Când vrei simplicitate maximă
- ✅ Când vrei cost predictibil
- ✅ Când nu ai nevoie de CDN global

---

## 💰 Railway Pricing - Analiza Completă

### Railway Pricing Model (Pay-as-you-go)

Railway folosește **usage-based pricing**:
- **$0.000231/GB-hour** (Memory)
- **$0.000463/vCPU-hour** (CPU)
- **$0.10/GB** (Network egress)
- **$0.25/GB/month** (Disk storage)

### Cost Estimate pentru UnifyData.AI MVP

#### **Configurație Recomandată pentru MVP**

**1. Backend (FastAPI)**
```
Memory: 512MB
vCPU: 0.5 cores
Disk: 1GB
Uptime: 24/7
```

**Cost/lună:**
- Memory: 512MB × 730 hours × $0.000231 = **$0.08**
- vCPU: 0.5 × 730 hours × $0.000463 = **$0.17**
- Disk: 1GB × $0.25 = **$0.25**
- **Total Backend: ~$0.50/lună**

**2. Frontend (Next.js)**
```
Memory: 512MB
vCPU: 0.5 cores
Disk: 500MB
Uptime: 24/7
```

**Cost/lună:**
- Memory: 512MB × 730 hours × $0.000231 = **$0.08**
- vCPU: 0.5 × 730 hours × $0.000463 = **$0.17**
- Disk: 0.5GB × $0.25 = **$0.12**
- **Total Frontend: ~$0.40/lună**

**3. PostgreSQL Database**
```
Memory: 512MB
vCPU: 0.5 cores
Disk: 5GB
Uptime: 24/7
```

**Cost/lună:**
- Memory: 512MB × 730 hours × $0.000231 = **$0.08**
- vCPU: 0.5 × 730 hours × $0.000463 = **$0.17**
- Disk: 5GB × $0.25 = **$1.25**
- **Total PostgreSQL: ~$1.50/lună**

**4. Redis (Optional - Upstash Free)**
```
Usar Upstash Redis (Free tier): $0/lună
```

**5. Network Egress**
```
Estimated: 5GB/lună × $0.10 = $0.50/lună
```

### 📊 **TOTAL COST ESTIMATE - Railway Only**

| Service | Monthly Cost |
|---------|-------------|
| Backend (FastAPI) | $0.50 |
| Frontend (Next.js) | $0.40 |
| PostgreSQL | $1.50 |
| Network Egress | $0.50 |
| **TOTAL** | **~$3/month** 💚 |

### ✅ **Railway Credit: $5/month FREE** ✅

Railway oferă **$5 credit gratuit/lună** pentru hobby projects!

**Rezultat: GRATUIT pentru MVP! 🎉**

---

## 📈 Cost Scaling

### Când crește traficul:

**Scenariul 1: 1,000 users/lună**
```
Backend: 1GB RAM, 1 vCPU = ~$1.50/lună
Frontend: 1GB RAM, 1 vCPU = ~$1.50/lună
PostgreSQL: 2GB RAM, 1 vCPU, 10GB disk = ~$4/lună
Network: 20GB egress = ~$2/lună
TOTAL: ~$9/lună
Cu $5 credit → ~$4/lună din buzunar
```

**Scenariul 2: 10,000 users/lună**
```
Backend: 2GB RAM, 2 vCPU = ~$6/lună
Frontend: 2GB RAM, 2 vCPU = ~$6/lună
PostgreSQL: 4GB RAM, 2 vCPU, 50GB disk = ~$18/lună
Network: 100GB egress = ~$10/lună
TOTAL: ~$40/lună
Cu $5 credit → ~$35/lună din buzunar
```

**Scenariul 3: 100,000+ users/lună**
```
La acest nivel, migrezi la:
- Vercel pentru frontend ($20/lună Pro)
- Railway Pro pentru backend (~$50-100/lună)
- Managed DB separat (~$25/lună)
TOTAL: ~$100-150/lună
```

---

## 🚀 Deploy pe Railway - Pas cu Pas

### Prerequisites
- GitHub account
- Railway account (sign up cu GitHub)
- Code pushed to GitHub

### Pasul 1: Sign Up Railway

1. Go to **https://railway.app**
2. Click **"Start a New Project"**
3. **Login with GitHub**
4. Verify email

✅ Primești automat **$5 credit/month**!

### Pasul 2: Deploy PostgreSQL

1. Click **"New Project"**
2. Select **"Provision PostgreSQL"**
3. Wait ~30 seconds
4. ✅ PostgreSQL deployed!

**Copy connection details** (vei avea nevoie):
- Database URL (disponibil ca variabilă)

### Pasul 3: Deploy Backend (FastAPI)

1. In same project, click **"New"**
2. Select **"GitHub Repo"**
3. Choose your repository
4. Railway detectează Python automat

**Configure:**
- **Name**: `unifydata-backend`
- **Root Directory**: `backend`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Add Environment Variables:**
```env
# Application
ENVIRONMENT=production
DEBUG=False
API_V1_PREFIX=/api/v1

# Database (Railway provides automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Secrets (generate with: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=your-generated-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis (optional - use Upstash free)
REDIS_URL=redis://default:password@upstash-url:6379

# AI Services
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-west1-gcp

# CORS (will update after frontend deploy)
WEB_URL=https://unifydata-frontend.up.railway.app
```

Click **"Deploy"**

⏱️ Wait 2-3 minutes for build & deploy

✅ Backend deployed at: `https://unifydata-backend.up.railway.app`

**Test it:**
```bash
curl https://unifydata-backend.up.railway.app/health
```

### Pasul 4: Deploy Frontend (Next.js)

1. In same project, click **"New"**
2. Select **"GitHub Repo"**
3. Choose your repository (same repo)
4. Railway detectează Node.js automat

**Configure:**
- **Name**: `unifydata-frontend`
- **Root Directory**: `web`
- **Build Command**: `npm run build`
- **Start Command**: `npm start`

**Add Environment Variables:**
```env
# Backend API URL (use the Railway backend URL)
NEXT_PUBLIC_API_URL=https://unifydata-backend.up.railway.app
```

Click **"Deploy"**

⏱️ Wait 3-5 minutes for build & deploy

✅ Frontend deployed at: `https://unifydata-frontend.up.railway.app`

### Pasul 5: Update CORS în Backend

1. Go to **Backend service** in Railway
2. Edit **Environment Variables**
3. Update `WEB_URL`:
   ```
   WEB_URL=https://unifydata-frontend.up.railway.app
   ```
4. Backend va face auto-redeploy

SAU update în cod (`backend/app/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://unifydata-frontend.up.railway.app",
        "http://localhost:3000",  # for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Pasul 6: Test End-to-End

1. **Frontend**: `https://unifydata-frontend.up.railway.app`
2. **Register** a new user
3. **Complete** onboarding
4. **Login** again
5. ✅ Verify everything works!

---

## 🔧 Railway Configuration Files

### railway.toml (Optional - pentru control avansat)

Creează în root directory:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Dockerfile (Optional - pentru control total)

Railway suportă și Dockerfile-uri custom dacă vrei mai mult control.

---

## 📊 Monitor & Manage

### Railway Dashboard

**Pentru fiecare service poți vedea:**
- ✅ **Metrics**: CPU, Memory, Network
- ✅ **Logs**: Real-time și historical
- ✅ **Deployments**: History și rollback
- ✅ **Environment Variables**: Edit anytime
- ✅ **Cost**: Usage tracking

### View Logs

**În Railway Dashboard:**
1. Click pe service (Backend/Frontend)
2. Tab **"Logs"**
3. Vezi real-time logs

**SAU cu Railway CLI:**
```bash
npm install -g @railway/cli
railway login
railway logs
```

### View Metrics

**În Dashboard:**
- CPU usage
- Memory usage
- Network traffic
- Request count
- Error rate

---

## 🔄 Continuous Deployment

### Auto-Deploy Enabled! ✅

**Workflow:**
```bash
# 1. Make changes locally
git add .
git commit -m "Add new feature"
git push origin main

# 2. Railway auto-deploys (2-3 min)
#    - Backend auto-deploys
#    - Frontend auto-deploys

# 3. Test at production URLs
```

**No manual deploy needed!**

### Manual Deploy (dacă e nevoie)

**Railway CLI:**
```bash
railway up
```

**Railway Dashboard:**
- Go to service → Deployments → "Deploy Latest"

---

## 💳 Billing & Cost Optimization

### Check Current Usage

**Railway Dashboard:**
1. Project Settings → Usage
2. Vezi usage pentru fiecare service
3. Vezi estimated monthly cost

### Cost Optimization Tips

**1. Scale Down When Not Needed**
```bash
# Development: Scale to 0 când nu lucrezi
# Production: Keep running 24/7
```

**2. Use Upstash Redis Instead of Railway Redis**
```
Upstash Free Tier: 10K requests/day
Railway Redis: ~$1.50/month
Savings: $1.50/month
```

**3. Optimize Images & Assets**
```
Reduce Network Egress:
- Compress images
- Use CDN for static assets (optional)
- Enable gzip compression
```

**4. Database Optimization**
```
- Regular vacuum (PostgreSQL)
- Index optimization
- Clean old logs
```

### Set Spending Limits

**Railway Dashboard:**
1. Project Settings → Billing
2. Set spending limit: e.g., $10/month
3. Get alerts when approaching limit

---

## 🆘 Troubleshooting

### Backend Issues

**Problem: Build fails**
```
Solution: Check logs in Railway dashboard
Common causes:
- Missing requirements.txt
- Python version mismatch
- Missing environment variables
```

**Problem: 500 errors**
```
Solution: Check runtime logs
railway logs

Common causes:
- Database connection failed
- Missing environment variables
- Code errors
```

**Problem: High memory usage**
```
Solution: Scale up memory allocation
Dashboard → Service → Settings → Resources
Increase from 512MB to 1GB
```

### Frontend Issues

**Problem: Build fails**
```
Solution: Check build logs
Common causes:
- Missing dependencies
- TypeScript errors
- Missing NEXT_PUBLIC_API_URL
```

**Problem: API calls failing**
```
Solution: Check CORS settings
Verify NEXT_PUBLIC_API_URL is correct
Update allow_origins in backend
```

### Database Issues

**Problem: Connection timeout**
```
Solution: Check DATABASE_URL is set
Verify PostgreSQL service is running
Check connection from backend logs
```

**Problem: Out of storage**
```
Solution: Increase disk allocation
Dashboard → PostgreSQL → Settings → Storage
Increase from 5GB to 10GB
```

---

## 🎯 Production Checklist

### Before Going Live

- [ ] All environment variables set
- [ ] Secrets generated (JWT, etc.)
- [ ] CORS configured correctly
- [ ] Database migrations applied
- [ ] Health check endpoint works
- [ ] API docs accessible
- [ ] Frontend loads without errors
- [ ] Registration flow tested
- [ ] Login flow tested
- [ ] Error tracking set up (Sentry)

### After Going Live

- [ ] Monitor logs daily
- [ ] Check usage/costs weekly
- [ ] Set up alerts
- [ ] Regular backups (PostgreSQL)
- [ ] Performance monitoring
- [ ] Security updates

---

## 📈 When to Migrate to Vercel

**Stick with Railway-Only when:**
- ✅ MVP testing
- ✅ Internal tools
- ✅ <1,000 users
- ✅ Cost is priority
- ✅ Simplicity is priority

**Migrate to Vercel + Railway when:**
- ❌ >10,000 users
- ❌ Global audience (need CDN)
- ❌ Need edge functions
- ❌ <1s page load is critical
- ❌ Advanced analytics needed

**Migration cost:** ~$20/month (Vercel Pro)

---

## 💰 Final Cost Summary

### Railway-Only MVP

| Tier | Users | Services | Cost/Month | Net Cost* |
|------|-------|----------|------------|-----------|
| **Free** | <100 | All | ~$3 | **$0** ✅ |
| **Hobby** | 100-1K | All | ~$9 | **$4** |
| **Growing** | 1K-10K | All | ~$25 | **$20** |
| **Scale** | 10K+ | All | ~$50 | **$45** |

*Net Cost = Total - $5 Railway Credit

### Comparație: Railway-Only vs Vercel + Railway

| Aspect | Railway-Only | Vercel + Railway |
|--------|--------------|------------------|
| **Cost (MVP)** | $0-4/month | $0-5/month |
| **Setup Time** | 30 min | 45 min |
| **Complexity** | ⭐⭐ Simple | ⭐⭐⭐ Medium |
| **Performance** | Good | Excellent |
| **CDN** | No | Yes (Global) |
| **Scalability** | Good | Excellent |
| **Best For** | MVP, Testing | Production, Global |

---

## 🎉 Concluzie

### Railway-Only este PERFECT pentru MVP! ✅

**Avantaje:**
- ✅ **$0-4/month** pentru MVP complet
- ✅ **Setup în 30 minute**
- ✅ **Tot într-un loc** (Frontend + Backend + DB)
- ✅ **Auto-deploy** din GitHub
- ✅ **Managed databases** incluse
- ✅ **Logs centralizate**
- ✅ **HTTPS automatic**
- ✅ **Scaling easy** când crești

**Când să migrezi:**
- Când ai >10K users active
- Când performance devine critic
- Când ai nevoie de CDN global
- Când costul nu mai e prioritatea #1

---

## 🚀 Quick Start

```bash
# 1. Push code to GitHub
git push origin main

# 2. Go to Railway
https://railway.app/new

# 3. Deploy in ordine:
1. PostgreSQL
2. Backend (root: backend)
3. Frontend (root: web)

# 4. Set environment variables
# 5. Test production!
```

**Estimated time:** 30-45 minutes
**Cost:** ~$0-3/month (covered by free credit!)

---

## 📚 Resources

- **Railway Docs**: https://docs.railway.app
- **Pricing Calculator**: https://railway.app/pricing
- **Railway Discord**: https://discord.gg/railway
- **This Project**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**🎉 Railway-Only = Simplitate + Cost Redus + Perfect pentru MVP! 🚀**
