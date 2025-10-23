# 📚 UnifyData.AI - Documentation Index

Ghid complet pentru navigarea în documentația proiectului.

---

## 🚀 Getting Started (START HERE!)

### Pentru Prima Dată
1. **[QUICK_START.md](QUICK_START.md)** ⭐ START AICI
   - Ghid rapid <5 minute
   - Cele mai simple comenzi pentru a porni tot
   - Perfect pentru prima rulare

2. **[SETUP_SUCCESS.md](SETUP_SUCCESS.md)**
   - Verifică ce a fost creat
   - Vezi feature-urile implementate
   - Checklist complet de setup

### Pornire Servicii
3. **[START_SERVICES.md](START_SERVICES.md)**
   - Ghid detaliat pentru pornirea serviciilor
   - 3 opțiuni: Docker / Local / Hybrid
   - Troubleshooting complet

4. **[start-dev.ps1](start-dev.ps1)**
   - Script PowerShell automatic pentru Windows
   - Meniu interactiv
   - Verificare prerequisite

---

## 🧪 Testing & Development

### API Testing
5. **[API_TEST_GUIDE.md](API_TEST_GUIDE.md)**
   - Testare completă API
   - Exemple curl și PowerShell
   - Test flow complet (register → login → onboarding)
   - Error handling examples

6. **[backend/test_api.py](backend/test_api.py)**
   - Script Python pentru test automat
   - Verifică imports, config, endpoints
   - Rulează cu: `python backend/test_api.py`

### API Documentation
7. **Swagger UI**: http://localhost:8000/docs
   - Interactive API documentation
   - Test endpoints direct din browser
   - Vezi toate schema-urile

8. **ReDoc**: http://localhost:8000/redoc
   - Alternative API documentation
   - Mai clean design
   - Perfect pentru reading

---

## 📖 Project Documentation

### Overview
9. **[README.md](README.md)**
   - Project overview
   - Tech stack
   - Features list
   - Quick setup
   - Deployment info

### Backend Documentation
10. **[backend/README.md](backend/README.md)**
    - Backend architecture
    - Installation steps
    - Configuration details
    - API endpoints
    - Development guide
    - Deployment checklist

11. **[backend/SETUP_COMPLETE.md](backend/SETUP_COMPLETE.md)**
    - Backend structure explanation
    - All files created
    - Features implemented
    - How to run backend

---

## 🏗️ Architecture & Specifications

### Product Specifications
12. **[docs/mvp-features-part1.md](docs/mvp-features-part1.md)**
    - Authentication features (1.1-1.3)
    - Onboarding flow (2.1-2.3)
    - Data source connections (3.1-3.6)
    - Complete with acceptance criteria, API specs, UI mockups

13. **[docs/mvp-features-part2.md](docs/mvp-features-part2.md)**
    - Search features (4.1-4.4)
    - Search results display (5.1-5.4)
    - Knowledge graph (6.1-6.2)
    - User & org settings (7.x, 8.x)
    - Admin dashboard (9.x)

### Technical Architecture
14. **[docs/technical-architecture-part3.md](docs/technical-architecture-part3.md)**
    - Security architecture
    - Infrastructure & deployment
    - Monitoring & observability
    - Development environment
    - Technical risks & mitigations
    - MVP vs future state roadmap

---

## 📂 Code Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/              # API routes and endpoints
│   │   ├── routes/       # Route modules
│   │   ├── endpoints/    # Endpoint implementations
│   │   └── dependencies.py  # Auth middleware
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   ├── database.py   # DB setup
│   │   └── security.py   # JWT & hashing
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── organization.py
│   │   └── data_source.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   └── onboarding.py
│   ├── services/         # Business logic
│   ├── connectors/       # Data source integrations
│   └── main.py           # FastAPI app entry
├── tests/                # Test suite
└── test_api.py           # API test script
```

### Frontend Structure
```
web/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── auth/         # Auth pages
│   │   ├── onboarding/   # Onboarding flow
│   │   └── dashboard/    # Main app
│   ├── components/       # React components
│   │   ├── onboarding/   # Onboarding UI
│   │   └── ui/           # shadcn/ui components
│   ├── hooks/            # Custom hooks
│   │   ├── use-auth.ts
│   │   └── use-onboarding.ts
│   └── lib/              # Utilities
│       ├── api-client.ts # Axios client
│       ├── auth.ts       # Auth utilities
│       └── types.ts      # TypeScript types
└── public/               # Static assets
```

---

## 🔧 Configuration Files

### Environment Variables
- **[.env.example](.env.example)** - Template cu toate variabilele
- **[.env](.env)** - Fișierul tău local (creat automat)
- **[backend/.env.example](backend/.env.example)** - Backend specific

### Docker
- **[docker-compose.yml](docker-compose.yml)** - Orchestration pentru toate serviciile
- **[backend/Dockerfile](backend/Dockerfile)** - Backend container
- **[backend/.dockerignore](backend/.dockerignore)** - Files to exclude

### Dependencies
- **[backend/requirements.txt](backend/requirements.txt)** - Python packages
- **[web/package.json](web/package.json)** - Node.js packages

---

## 📊 Quick Reference

### Common Commands

#### Start Everything
```powershell
# Automatic
.\start-dev.ps1

# Docker Compose
docker compose up -d

# Manual backend
cd backend && uvicorn app.main:app --reload

# Manual frontend
cd web && npm run dev
```

#### View Logs
```powershell
docker compose logs -f           # All services
docker compose logs -f api       # Backend only
docker compose logs -f postgres  # Database only
```

#### Stop Services
```powershell
docker compose stop      # Stop, keep data
docker compose down      # Stop, remove containers
docker compose down -v   # Stop, remove everything
```

#### Database Commands
```powershell
# Connect to PostgreSQL
docker compose exec postgres psql -U dev -d unifydata

# List tables
\dt

# View users
SELECT email, role FROM users;
```

#### Test Commands
```powershell
# Test API
python backend/test_api.py

# Health check
curl http://localhost:8000/health

# View API docs
# http://localhost:8000/docs
```

---

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | Status endpoint |
| Frontend | http://localhost:3000 | Next.js UI |
| Neo4j Browser | http://localhost:7474 | Graph DB UI |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |

---

## 🎯 Learning Paths

### Path 1: Quick Start (Beginner)
1. [QUICK_START.md](QUICK_START.md) - Get running fast
2. [API_TEST_GUIDE.md](API_TEST_GUIDE.md) - Test the API
3. Play with http://localhost:8000/docs - Interactive docs

### Path 2: Development (Developer)
1. [backend/README.md](backend/README.md) - Backend guide
2. [docs/mvp-features-part1.md](docs/mvp-features-part1.md) - Feature specs
3. Start coding new features!

### Path 3: Deep Dive (Architect)
1. [README.md](README.md) - Full overview
2. [docs/technical-architecture-part3.md](docs/technical-architecture-part3.md) - Architecture
3. [backend/SETUP_COMPLETE.md](backend/SETUP_COMPLETE.md) - Implementation details
4. Review code in `backend/app/` and `web/src/`

---

## 🆘 Troubleshooting

### Quick Fixes
- **Services won't start**: `docker compose down && docker compose up -d`
- **Port in use**: Change ports in `docker-compose.yml`
- **Import errors**: `pip install -r backend/requirements.txt --force-reinstall`
- **Frontend errors**: `cd web && rm -rf node_modules && npm install`

### Detailed Help
- See **[START_SERVICES.md](START_SERVICES.md)** - Troubleshooting section
- Check logs: `docker compose logs -f`
- Run test: `python backend/test_api.py`

---

## 📈 Development Workflow

### 1. Start Development
```powershell
.\start-dev.ps1
# Choose option 1 (All services)
```

### 2. Make Changes
- Backend: Edit files in `backend/app/`
- Frontend: Edit files in `web/src/`
- Auto-reload is enabled for both

### 3. Test Changes
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000
- API test: `python backend/test_api.py`

### 4. Commit Changes
```powershell
git add .
git commit -m "Description of changes"
git push
```

---

## 📦 What's Implemented

### ✅ Complete (MVP Phase 1)
- [x] Backend FastAPI structure
- [x] Database models (User, Organization, DataSource)
- [x] Authentication (Register, Login, Token refresh)
- [x] Onboarding flow (3 steps with UI)
- [x] Frontend Next.js structure
- [x] API client with auto token refresh
- [x] Form validation
- [x] Docker Compose setup
- [x] Complete documentation

### 🚧 In Progress (MVP Phase 2)
- [ ] Data source connectors (OAuth flows)
- [ ] Data sync engine
- [ ] Natural language search
- [ ] Search results display
- [ ] Knowledge graph visualization

### 📋 Planned (MVP Phase 3)
- [ ] User settings
- [ ] Organization settings
- [ ] Team management
- [ ] Admin dashboard
- [ ] Analytics

---

## 🎓 Best Practices

### Code Style
- **Backend**: Follow PEP 8, use type hints
- **Frontend**: Follow ESLint rules, use TypeScript
- **Git**: Descriptive commit messages

### Testing
- Test API endpoints in Swagger UI before frontend integration
- Use `test_api.py` for quick backend verification
- Check browser console for frontend errors

### Documentation
- Update README when adding major features
- Add docstrings to new functions
- Update API docs automatically (FastAPI generates from code)

---

## 🤝 Contributing

### Adding New Features
1. Check feature specs in `docs/mvp-features-*`
2. Backend: Add route in `backend/app/api/routes/`
3. Frontend: Add page in `web/src/app/`
4. Test thoroughly
5. Update documentation

### Code Review Checklist
- [ ] Code follows style guide
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No sensitive data in code
- [ ] Error handling implemented

---

## 📞 Support & Resources

### Internal Resources
- All documentation files in this directory
- Code comments throughout codebase
- API docs at http://localhost:8000/docs

### External Resources
- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs
- SQLAlchemy: https://docs.sqlalchemy.org/
- React Query: https://tanstack.com/query/latest

---

## 🎉 Quick Links

**Start Developing:**
- [QUICK_START.md](QUICK_START.md) ← Start here!
- [start-dev.ps1](start-dev.ps1) ← Windows script
- http://localhost:8000/docs ← API docs

**Learn the System:**
- [SETUP_SUCCESS.md](SETUP_SUCCESS.md) ← What's built
- [docs/mvp-features-part1.md](docs/mvp-features-part1.md) ← Features
- [backend/README.md](backend/README.md) ← Backend guide

**Test & Debug:**
- [API_TEST_GUIDE.md](API_TEST_GUIDE.md) ← Testing guide
- [START_SERVICES.md](START_SERVICES.md) ← Troubleshooting
- `python backend/test_api.py` ← Quick test

---

**Last Updated**: 2025-01-23
**Version**: MVP v0.1.0
**Status**: ✅ Ready for Development

**Happy Coding! 🚀**
