# 🚀 Quick Start Guide - UnifyData.AI

Ghid rapid pentru a porni UnifyData.AI în mai puțin de 5 minute!

## ⚡ Opțiunea 1: Automatic (Recomandat pentru Windows)

### Pasul 1: Deschide PowerShell în directorul proiectului

```powershell
cd c:\Users\Tavi\Desktop\Work\UnifyData.ai
```

### Pasul 2: Rulează scriptul de start

```powershell
.\start-dev.ps1
```

Scriptul va:
- ✅ Verifica prerequisitele (Docker, Python, Node.js)
- ✅ Crea .env dacă lipsește
- ✅ Îți va permite să alegi ce servicii să pornească
- ✅ Porni serviciile automat

### Opțiuni disponibile:
1. **All services with Docker** - Cel mai simplu, pornește tot (recomandat!)
2. **Only Docker services** - Postgres, Redis, Neo4j
3. **Only Backend** - API local
4. **Only Frontend** - UI local
5. **Backend + Frontend** - Ambele local

---

## ⚡ Opțiunea 2: Manual cu Docker Compose

### O singură comandă pornește tot:

```powershell
docker compose up -d
```

**Gata! 🎉** Acum ai:
- ✅ Backend API la http://localhost:8000
- ✅ API Docs la http://localhost:8000/docs
- ✅ PostgreSQL la localhost:5432
- ✅ Redis la localhost:6379
- ✅ Neo4j la http://localhost:7474
- ✅ Frontend la http://localhost:3000 (după `cd web && npm run dev`)

### Vezi logs:
```powershell
docker compose logs -f
```

### Oprește serviciile:
```powershell
docker compose down
```

---

## ⚡ Opțiunea 3: Doar Backend (fără Docker)

### Pasul 1: Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Pasul 2: Asigură-te că PostgreSQL și Redis rulează
- PostgreSQL pe localhost:5432
- Redis pe localhost:6379

### Pasul 3: Pornește API
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Pasul 4: Testează
```powershell
# În alt terminal
python test_api.py
```

**Gata!** API la http://localhost:8000

---

## ⚡ Opțiunea 4: Doar Frontend (fără Docker)

### Pasul 1: Setup
```powershell
cd web
npm install
```

### Pasul 2: Verifică că backend rulează
Backend trebuie să fie pornit la http://localhost:8000

### Pasul 3: Pornește frontend
```powershell
npm run dev
```

**Gata!** Frontend la http://localhost:3000

---

## 🧪 Test Rapid

### Test 1: Backend Health Check
```powershell
curl http://localhost:8000/health

# SAU în browser
# http://localhost:8000/health
```

Răspuns așteptat:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development"
}
```

### Test 2: API Docs
Deschide în browser: http://localhost:8000/docs

Ar trebui să vezi Swagger UI cu toate endpoint-urile.

### Test 3: Frontend
Deschide în browser: http://localhost:3000

Ar trebui să vezi pagina de login/register.

---

## 📋 Checklist de Start

După pornire, verifică:

- [ ] Backend răspunde la http://localhost:8000
- [ ] API Docs accesibil la http://localhost:8000/docs
- [ ] Health check return "ok" la http://localhost:8000/health
- [ ] Frontend se încarcă la http://localhost:3000
- [ ] Poți face register la http://localhost:3000/auth/register
- [ ] Poți face login la http://localhost:3000/auth/login

Dacă toate sunt ✅, **ești gata să dezvolți!** 🎉

---

## 🔧 Troubleshooting Rapid

### Problem: Docker not found
```powershell
# Instalează Docker Desktop
# https://www.docker.com/products/docker-desktop/
```

### Problem: Port 8000 in use
```powershell
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# SAU schimbă portul
# În docker-compose.yml: "8001:8000"
```

### Problem: Python import errors
```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

### Problem: npm install fails
```powershell
cd web
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

---

## 📚 Documentație Completă

Pentru detalii complete, vezi:
- **[START_SERVICES.md](START_SERVICES.md)** - Ghid complet de pornire
- **[backend/README.md](backend/README.md)** - Backend documentation
- **[README.md](README.md)** - Project overview

---

## 🎯 Next Steps

După ce serviciile rulează:

1. **Testează Authentication**
   - Mergi la http://localhost:3000/auth/register
   - Creează un cont nou
   - Login cu contul creat

2. **Explorează Onboarding**
   - După login, vei vedea onboarding flow-ul
   - Welcome tour → Connect source → First search

3. **Explorează API**
   - Deschide http://localhost:8000/docs
   - Încearcă endpoint-urile interactive
   - Vezi schema-urile Pydantic

4. **Dezvoltă Features**
   - Backend: Adaugă routes în `backend/app/api/routes/`
   - Frontend: Adaugă pages în `web/src/app/`

---

## ✅ Success Indicators

Știi că totul funcționează când:
- ✅ Nu vezi erori în terminal
- ✅ Docker containers sunt "Up" (`docker compose ps`)
- ✅ API Docs se încarcă complet
- ✅ Frontend se încarcă fără erori în console
- ✅ Poți crea un user și face login

**Dacă vezi toate ✅, ești gata! 🚀**

Pentru întrebări sau probleme, vezi [START_SERVICES.md](START_SERVICES.md) pentru troubleshooting detaliat.
