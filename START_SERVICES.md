# 🚀 Ghid pentru Pornirea Serviciilor UnifyData.AI

## Opțiunea 1: Cu Docker (Recomandat)

### Pasul 1: Verifică Docker
```powershell
# Verifică că Docker Desktop este instalat și pornit
docker --version
docker compose version
```

### Pasul 2: Pornește toate serviciile
```powershell
# Din root directory (UnifyData.ai/)
docker compose up -d
```

Acest command pornește:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Neo4j (port 7474, 7687)
- ✅ Backend API (port 8000)
- ✅ Celery Worker
- ✅ Celery Beat

### Pasul 3: Verifică că serviciile rulează
```powershell
docker compose ps
```

Ar trebui să vezi toate serviciile cu status "Up".

### Pasul 4: Vezi logs
```powershell
# Toate serviciile
docker compose logs -f

# Doar API
docker compose logs -f api

# Doar PostgreSQL
docker compose logs -f postgres
```

### Pasul 5: Testează API-ul
Deschide browser la:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Neo4j Browser**: http://localhost:7474

### Oprește serviciile
```powershell
# Oprește dar păstrează datele
docker compose stop

# Oprește și șterge containerele (păstrează volumes)
docker compose down

# Oprește și șterge tot (inclusiv datele!)
docker compose down -v
```

---

## Opțiunea 2: Local Development (fără Docker)

Această opțiune necesită instalarea manuală a dependințelor.

### Prerequisite
1. **PostgreSQL 15+** instalat și rulând
2. **Redis 7+** instalat și rulând
3. **Python 3.11+** instalat
4. **Node.js 18+** instalat (pentru frontend)

### Backend (FastAPI)

#### Pasul 1: Setup Python environment
```powershell
# Creează virtual environment
cd backend
python -m venv venv

# Activează virtual environment
.\venv\Scripts\activate  # Windows PowerShell
# SAU
source venv/bin/activate  # Linux/Mac/Git Bash

# Verifică că este activat (ar trebui să vezi (venv) în prompt)
```

#### Pasul 2: Instalează dependencies
```powershell
pip install -r requirements.txt
```

#### Pasul 3: Setup environment variables
```powershell
# Verifică că .env există în root directory
# Dacă nu, copiază .env.example
cd ..
cp .env.example .env

# Editează .env și asigură-te că DATABASE_URL și REDIS_URL sunt corecte
```

#### Pasul 4: Pornește serviciile de bază

**PostgreSQL:**
- Windows: Pornește serviciul din Services
- Mac: `brew services start postgresql@15`
- Linux: `sudo systemctl start postgresql`

**Redis:**
- Windows: `redis-server`
- Mac: `brew services start redis`
- Linux: `sudo systemctl start redis`

#### Pasul 5: Rulează migrările (când vor fi create)
```powershell
cd backend
alembic upgrade head
```

#### Pasul 6: Pornește backend API
```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API va fi disponibil la: http://localhost:8000

#### Pasul 7: Testează backend
```powershell
# În alt terminal
cd backend
python test_api.py
```

### Frontend (Next.js)

#### Pasul 1: Instalează dependencies
```powershell
cd web
npm install
```

#### Pasul 2: Setup environment variables
```powershell
# Creează .env.local
cp .env.local.example .env.local

# Verifică că NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Pasul 3: Pornește development server
```powershell
npm run dev
```

Frontend va fi disponibil la: http://localhost:3000

---

## Opțiunea 3: Hybrid (Backend în Docker, Frontend local)

Această opțiune este utilă când vrei să dezvolți doar frontend-ul.

### Pasul 1: Pornește doar serviciile backend
```powershell
# Pornește PostgreSQL, Redis, Neo4j, API
docker compose up -d postgres redis neo4j api
```

### Pasul 2: Pornește frontend local
```powershell
cd web
npm install
npm run dev
```

---

## 🧪 Testare Completă

### Test 1: Backend API
```powershell
# Test cu curl
curl http://localhost:8000/health

# SAU cu PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

Răspuns așteptat:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development"
}
```

### Test 2: Test complet backend
```powershell
cd backend
python test_api.py
```

### Test 3: PostgreSQL
```powershell
# Din docker
docker compose exec postgres psql -U dev -d unifydata -c "\dt"

# SAU local
psql -U dev -d unifydata -c "\dt"
```

### Test 4: Redis
```powershell
# Din docker
docker compose exec redis redis-cli ping

# SAU local
redis-cli ping
```

Răspuns așteptat: `PONG`

### Test 5: Frontend
Deschide browser la http://localhost:3000

---

## 🔍 Troubleshooting

### Problem: Docker not found
**Soluție**: Instalează Docker Desktop de la https://www.docker.com/products/docker-desktop/

### Problem: Port 8000 already in use
**Soluție**:
```powershell
# Windows - găsește procesul
netstat -ano | findstr :8000
# Omoară procesul (înlocuiește PID)
taskkill /PID <PID> /F

# SAU schimbă portul în docker-compose.yml
```

### Problem: PostgreSQL connection failed
**Soluție**:
1. Verifică că PostgreSQL rulează: `docker compose ps postgres`
2. Verifică DATABASE_URL în .env
3. Verifică logs: `docker compose logs postgres`

### Problem: Module import errors în Python
**Soluție**:
```powershell
# Verifică că virtual environment este activat
which python  # Ar trebui să arate calea către venv

# Reinstalează dependencies
pip install -r requirements.txt --force-reinstall
```

### Problem: npm install fails
**Soluție**:
```powershell
# Șterge node_modules și package-lock.json
rm -rf node_modules package-lock.json

# Reinstalează
npm install
```

---

## 📊 Status Check Complete

După pornirea serviciilor, verifică că toate sunt OK:

### Backend Checklist
- [ ] PostgreSQL rulează (port 5432)
- [ ] Redis rulează (port 6379)
- [ ] Neo4j rulează (port 7474, 7687)
- [ ] Backend API răspunde la http://localhost:8000/health
- [ ] API Docs accesibil la http://localhost:8000/docs
- [ ] Test script rulează fără erori: `python backend/test_api.py`

### Frontend Checklist
- [ ] npm install completat fără erori
- [ ] Development server pornit (port 3000)
- [ ] Page loads la http://localhost:3000
- [ ] Nu sunt erori în browser console

---

## 🎯 Quick Start Commands

**Pornește tot (Docker):**
```powershell
docker compose up -d
```

**Pornește doar backend:**
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload
```

**Pornește doar frontend:**
```powershell
cd web
npm run dev
```

**Vezi logs:**
```powershell
docker compose logs -f
```

**Oprește tot:**
```powershell
docker compose down
```

---

## ✅ Success!

Când vezi:
- ✅ Backend API la http://localhost:8000
- ✅ Swagger Docs la http://localhost:8000/docs
- ✅ Frontend la http://localhost:3000
- ✅ Toate testele pass

**Ești gata să dezvolți! 🎉**
