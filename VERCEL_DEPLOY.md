# ⚡ Quick Vercel Deploy - UnifyData.AI

Ghid rapid pentru deploy pe Vercel în 10 minute!

---

## 🚀 Quick Start (3 Pași Simpli)

### Pasul 1: Push Code to GitHub (2 minute)

```powershell
# Run the deploy script
.\deploy.ps1

# SAU manual:
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### Pasul 2: Deploy pe Vercel (5 minute)

1. **Mergi la**: https://vercel.com/new
2. **Import Repository**: Selectează repo-ul tău GitHub
3. **Configure Project**:
   ```
   Framework Preset: Next.js
   Root Directory: web
   Build Command: npm run build
   Output Directory: (leave default: .next)
   Install Command: npm install
   ```

4. **Add Environment Variable**:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `http://localhost:8000` (temporary - will update later)

5. **Click "Deploy"** 🚀

### Pasul 3: Test Deployment (3 minute)

După deploy (2-3 minute), Vercel îți dă un URL:
- `https://unifydata-ai-xxx.vercel.app`

Testează:
- ✅ Site se încarcă
- ✅ Registration page funcționează
- ✅ No console errors

---

## 🔧 Pentru Backend

Ai 2 opțiuni:

### Opțiunea 1: Railway (Recomandat)

1. **Mergi la**: https://railway.app/new
2. **Deploy from GitHub**
3. **Configure**:
   - Root Directory: `backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add Environment Variables** (vezi lista mai jos)
5. **Deploy**

Railway îți dă URL: `https://your-app.railway.app`

### Opțiunea 2: Render

1. **Mergi la**: https://render.com/
2. **New Web Service**
3. **Connect GitHub repo**
4. **Configure**:
   - Name: `unifydata-api`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables**
6. **Create Web Service**

---

## 📝 Backend Environment Variables

Copy-paste acestea în Railway/Render dashboard:

```env
# Application
ENVIRONMENT=production
DEBUG=False
API_V1_PREFIX=/api/v1
SECRET_KEY=YOUR_SECRET_KEY_HERE
API_URL=https://your-backend-url.railway.app
WEB_URL=https://your-vercel-url.vercel.app

# Database (Railway provides automatically if you add PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (Use Upstash free tier)
REDIS_URL=redis://default:password@upstash-url:6379

# JWT
JWT_SECRET_KEY=YOUR_JWT_SECRET_HERE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# AI Services (get free trial keys)
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

**Generate secrets**:
```powershell
# JWT Secret
openssl rand -hex 32

# App Secret
openssl rand -hex 32
```

---

## 🔗 Update Frontend to Use Backend

După ce backend-ul e deployed:

1. **Copy backend URL** din Railway/Render
2. **Go to Vercel Dashboard** → Your Project → Settings → Environment Variables
3. **Edit `NEXT_PUBLIC_API_URL`**:
   ```
   https://your-backend-url.railway.app
   ```
4. **Redeploy**: Deployments → Click "..." → Redeploy

---

## ✅ Verification Checklist

### Frontend (Vercel)
- [ ] App loads at Vercel URL
- [ ] No 404 errors
- [ ] Console shows no errors
- [ ] Can navigate between pages

### Backend (Railway/Render)
- [ ] Health check works: `https://your-backend.railway.app/health`
- [ ] API docs accessible: `https://your-backend.railway.app/docs`
- [ ] Returns JSON response

### End-to-End
- [ ] Can register new user from Vercel frontend
- [ ] Can login
- [ ] Tokens are received
- [ ] Onboarding flow works

---

## 🐛 Troubleshooting

### Frontend Issues

**Problem**: "Network Error" when trying to register
- **Solution**: Check `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- **Verify**: Go to Vercel → Settings → Environment Variables

**Problem**: App works locally but not on Vercel
- **Solution**: Check build logs in Vercel dashboard
- **Common cause**: Missing environment variables

### Backend Issues

**Problem**: 500 Internal Server Error
- **Solution**: Check Railway/Render logs
- **Common cause**: Missing environment variables

**Problem**: Database connection error
- **Solution**: Ensure PostgreSQL is added in Railway/Render
- **Verify**: DATABASE_URL is set correctly

### CORS Issues

**Problem**: CORS error in browser console
- **Solution**: Update CORS in `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-url.vercel.app",
        "https://app.unifydata.ai",  # custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 💰 Cost

### Free Tiers
- **Vercel**: Free (hobby plan) - 100GB bandwidth
- **Railway**: $5 free credit/month
- **Render**: 750 hours/month free

**Total**: $0-5/month pentru MVP

---

## 🎯 Test Production

### Quick Test Commands

```powershell
# Test backend health
curl https://your-backend.railway.app/health

# Test registration
$body = @{
    email = "test@example.com"
    password = "SecurePass123!"
    full_name = "Test User"
    company_name = "Test Company"
} | ConvertTo-Json

Invoke-RestMethod -Uri https://your-backend.railway.app/api/auth/register `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### Test in Browser
1. Go to your Vercel URL
2. Click "Create Account"
3. Fill in form
4. Submit
5. Should redirect to onboarding

---

## 🔄 Continuous Deployment

### Auto-Deploy is Enabled! ✅

**Workflow**:
```powershell
# 1. Make changes locally
git add .
git commit -m "Add new feature"
git push origin main

# 2. Vercel auto-deploys frontend (2-3 min)
# 3. Railway auto-deploys backend (2-3 min)

# 4. Test at production URLs
```

**No manual deploy needed!** Just push to GitHub.

---

## 📊 Monitor Deployments

### Vercel Dashboard
- **Deployments**: See all deploys
- **Logs**: View build logs
- **Analytics**: See traffic stats

### Railway Dashboard
- **Logs**: `railway logs`
- **Metrics**: CPU, Memory, Network
- **Environment**: Manage env vars

---

## 🎉 Success!

Când vezi:
- ✅ Frontend la Vercel URL
- ✅ Backend la Railway URL
- ✅ Health check returnează "ok"
- ✅ Registration funcționează end-to-end

**Ești live pe production! 🚀**

---

## 📞 Support

### Issues?
- Check logs în Vercel/Railway dashboard
- Vezi [DEPLOYMENT.md](DEPLOYMENT.md) pentru troubleshooting detaliat
- Test local first: `.\start-dev.ps1`

### Resources
- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **This Project**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Ready? Run `.\deploy.ps1` to start! 🚀**
