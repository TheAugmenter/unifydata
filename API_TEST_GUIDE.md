# 🧪 API Testing Guide

Ghid complet pentru testarea API-ului UnifyData.AI.

## Prerequisites

- Backend API rulează la http://localhost:8000
- PostgreSQL, Redis, Neo4j disponibile

## 🚀 Quick Test

### Test 1: Health Check (cel mai simplu)

**Browser:**
```
http://localhost:8000/health
```

**curl:**
```bash
curl http://localhost:8000/health
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

**Răspuns așteptat:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## 📖 Interactive API Documentation

### Swagger UI (Recomandat)
```
http://localhost:8000/docs
```

Aici poți:
- ✅ Vezi toate endpoint-urile
- ✅ Vezi schema-urile request/response
- ✅ Testezi endpoint-urile direct din browser
- ✅ Vezi exemple de răspunsuri

### ReDoc (Alternative)
```
http://localhost:8000/redoc
```

---

## 🔐 Test Authentication Flow

### Step 1: Register New User

**Endpoint:** `POST /api/auth/register`

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "company_name": "Test Company"
  }'
```

**Request (PowerShell):**
```powershell
$body = @{
    email = "test@example.com"
    password = "SecurePass123!"
    full_name = "Test User"
    company_name = "Test Company"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/auth/register `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

**Răspuns așteptat (200 Created):**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "role": "admin",
    "org_id": "uuid-here",
    "is_email_verified": false,
    "onboarding_completed": false,
    "created_at": "2025-01-23T..."
  },
  "organization": {
    "id": "uuid-here",
    "name": "Test Company",
    "slug": "test-company",
    "plan": "trial",
    "trial_ends_at": "2025-02-06T...",
    "max_users": 5,
    "max_data_sources": 3
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

**Salvează token-ul pentru următoarele teste!**

### Step 2: Login

**Endpoint:** `POST /api/auth/login`

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

**Request (PowerShell):**
```powershell
$body = @{
    email = "test@example.com"
    password = "SecurePass123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/auth/login `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### Step 3: Refresh Token

**Endpoint:** `POST /api/auth/refresh`

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token-here"
  }'
```

---

## 🎯 Test Onboarding Flow

### Step 1: Get Onboarding Progress

**Endpoint:** `GET /api/onboarding/progress`

**Request (curl cu token):**
```bash
curl -X GET http://localhost:8000/api/onboarding/progress \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Request (PowerShell):**
```powershell
$token = "YOUR_ACCESS_TOKEN"
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri http://localhost:8000/api/onboarding/progress `
  -Headers $headers
```

**Răspuns așteptat:**
```json
{
  "onboarding_step": 0,
  "onboarding_completed": false,
  "message": "Onboarding progress retrieved successfully"
}
```

### Step 2: Update Progress

**Endpoint:** `PUT /api/onboarding/progress`

**Request (curl):**
```bash
curl -X PUT http://localhost:8000/api/onboarding/progress \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "onboarding_step": 1,
    "onboarding_completed": false
  }'
```

### Step 3: Complete Onboarding

**Endpoint:** `POST /api/onboarding/complete`

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/onboarding/complete \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🧪 Test with Python Script

Am creat un script de test Python care verifică toate module-urile:

```powershell
cd backend
python test_api.py
```

Scriptul va testa:
- ✅ Import-uri de module
- ✅ Configurare settings
- ✅ FastAPI app setup
- ✅ Endpoint responses (/, /health)

---

## 🔍 Test Error Handling

### Test 1: Invalid Email (Register)

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "company_name": "Test Company"
  }'
```

**Răspuns așteptat (400 Bad Request):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Test 2: Weak Password

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "weak",
    "full_name": "Test User",
    "company_name": "Test Company"
  }'
```

**Răspuns așteptat (400 Bad Request):**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long",
      "type": "value_error"
    }
  ]
}
```

### Test 3: Duplicate Email

Încearcă să te înregistrezi cu același email de două ori.

**Răspuns așteptat (400 Bad Request):**
```json
{
  "error": "email_already_exists",
  "message": "An account with this email already exists. Please log in or use a different email."
}
```

### Test 4: Invalid Credentials (Login)

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "WrongPassword123!"
  }'
```

**Răspuns așteptat (401 Unauthorized):**
```json
{
  "error": "invalid_credentials",
  "message": "Invalid email or password."
}
```

### Test 5: Missing Authorization Header

```bash
curl -X GET http://localhost:8000/api/onboarding/progress
```

**Răspuns așteptat (401 Unauthorized):**
```json
{
  "error": "missing_token",
  "message": "Authorization header is missing"
}
```

---

## 📊 Complete Test Suite

### Test toate endpoint-urile într-un workflow complet:

```powershell
# 1. Health check
curl http://localhost:8000/health

# 2. Register user
$registerBody = @{
    email = "testuser@example.com"
    password = "SecurePass123!"
    full_name = "Test User"
    company_name = "Test Company"
} | ConvertTo-Json

$registerResponse = Invoke-RestMethod -Uri http://localhost:8000/api/auth/register `
  -Method Post `
  -ContentType "application/json" `
  -Body $registerBody

$token = $registerResponse.tokens.access_token
Write-Host "Access Token: $token"

# 3. Get onboarding progress
$headers = @{ Authorization = "Bearer $token" }
$progress = Invoke-RestMethod -Uri http://localhost:8000/api/onboarding/progress `
  -Headers $headers
Write-Host "Onboarding Step: $($progress.onboarding_step)"

# 4. Update progress
$updateBody = @{
    onboarding_step = 1
    onboarding_completed = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/onboarding/progress `
  -Method Put `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $updateBody

# 5. Complete onboarding
Invoke-RestMethod -Uri http://localhost:8000/api/onboarding/complete `
  -Method Post `
  -Headers $headers

# 6. Login again
$loginBody = @{
    email = "testuser@example.com"
    password = "SecurePass123!"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri http://localhost:8000/api/auth/login `
  -Method Post `
  -ContentType "application/json" `
  -Body $loginBody

Write-Host "Login successful! New token: $($loginResponse.tokens.access_token)"
```

---

## ✅ Success Checklist

După testare, verifică că toate acestea funcționează:

- [ ] Health check returnează "ok"
- [ ] Registration creează user și organization
- [ ] Registration returnează JWT tokens
- [ ] Login cu credențiale corecte funcționează
- [ ] Login cu credențiale greșite returnează 401
- [ ] Onboarding progress poate fi citit cu token valid
- [ ] Onboarding progress poate fi actualizat
- [ ] Onboarding poate fi completat
- [ ] Duplicate email returnează eroare
- [ ] Weak password returnează eroare
- [ ] Missing auth header returnează 401
- [ ] Invalid token returnează 401

Dacă toate sunt ✅, **API-ul funcționează perfect!** 🎉

---

## 🐛 Debug Tips

### Vezi logs în real-time:
```powershell
# Docker
docker compose logs -f api

# Local
# Logs apar direct în terminal unde rulează uvicorn
```

### Verifică database:
```powershell
# Connect to PostgreSQL
docker compose exec postgres psql -U dev -d unifydata

# List tables
\dt

# Check users
SELECT email, role, onboarding_completed FROM users;

# Exit
\q
```

### Verifică Redis:
```powershell
docker compose exec redis redis-cli

# Test connection
PING

# Exit
exit
```

---

## 📚 Additional Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Backend README**: [backend/README.md](backend/README.md)
- **API Models**: [backend/app/models/](backend/app/models/)
- **API Schemas**: [backend/app/schemas/](backend/app/schemas/)

---

**Happy Testing! 🚀**
