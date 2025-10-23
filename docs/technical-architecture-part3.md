# Technical Architecture - Part 3

**UnifyData.AI - Enterprise Data Intelligence Platform MVP**
*"All Your Data, One Question Away"*

**Document Version:** 1.0
**Last Updated:** January 2025
**Target Audience:** Engineering team, DevOps, security engineers, CTO

---

## Table of Contents

1. [Security Architecture](#7-security-architecture)
2. [Infrastructure & Deployment](#8-infrastructure--deployment)
3. [Monitoring & Observability](#9-monitoring--observability)
4. [Development Environment](#10-development-environment)
5. [Technical Risks & Mitigations](#11-technical-risks--mitigations)
6. [MVP vs Future State](#12-mvp-vs-future-state)
7. [Success Criteria](#13-success-criteria-for-mvp)

---

## 7. SECURITY ARCHITECTURE

### Data Security

#### Encryption at Rest

**Database Encryption:**

**PostgreSQL (AWS RDS):**
- **Method:** AWS RDS encryption using AES-256
- **Key management:** AWS KMS (Key Management Service)
- **Scope:** All database data, backups, read replicas
- **Configuration:**
  ```python
  # RDS creation with encryption
  rds_instance = rds.create_db_instance(
      DBInstanceIdentifier="unifydata-postgres",
      Engine="postgres",
      EngineVersion="15.3",
      StorageEncrypted=True,
      KmsKeyId="arn:aws:kms:us-east-1:123456789:key/..."
  )
  ```

**Neo4j:**
- **Method:** File system encryption (Linux dm-crypt or AWS EBS encryption)
- **Scope:** All database files, transaction logs, backups
- **Note:** Neo4j Community Edition doesn't have built-in encryption; rely on OS-level encryption

**Redis (ElastiCache):**
- **Method:** AWS ElastiCache encryption at rest
- **Scope:** All cached data on disk
- **Configuration:** Enable via `AtRestEncryptionEnabled=True`

**Vector Database (Pinecone):**
- **Handled automatically:** Pinecone encrypts all data at rest by default
- **No configuration needed:** Managed service handles encryption

**Object Storage (S3):**
- **Method:** Server-side encryption (SSE-S3 or SSE-KMS)
- **Configuration:**
  ```python
  # Enable default encryption for bucket
  s3.put_bucket_encryption(
      Bucket="unifydata-documents",
      ServerSideEncryptionConfiguration={
          'Rules': [{
              'ApplyServerSideEncryptionByDefault': {
                  'SSEAlgorithm': 'AES256'  # or 'aws:kms'
              }
          }]
      }
  )
  ```

---

**Application-Level Encryption (Credentials):**

**Connector Credentials Encryption:**
- **Method:** Fernet symmetric encryption (Python `cryptography` library)
- **Key management:** **One encryption key per organization** (tenant isolation)
- **Key storage:** AWS KMS or HashiCorp Vault
- **Implementation:**
  ```python
  from cryptography.fernet import Fernet
  import boto3

  # Retrieve org-specific encryption key from KMS
  kms = boto3.client('kms')
  data_key = kms.generate_data_key(
      KeyId="arn:aws:kms:...",
      KeySpec="AES_256"
  )

  # Encrypt credentials
  fernet = Fernet(data_key['Plaintext'])
  encrypted_creds = fernet.encrypt(
      json.dumps(credentials).encode()
  )

  # Store in PostgreSQL
  data_source.credentials_encrypted = encrypted_creds.decode()
  ```

**Why org-specific keys:**
- **Tenant isolation:** If one key is compromised, only one org affected
- **Key rotation:** Can rotate keys per org without affecting others
- **Compliance:** Meets requirements for logical data separation

---

#### Encryption in Transit

**All APIs:**
- **Protocol:** TLS 1.3 (mandatory, no fallback to TLS 1.2)
- **Certificates:** Let's Encrypt with auto-renewal (Certbot)
- **HSTS:** HTTP Strict Transport Security header enabled
  ```python
  # FastAPI middleware
  @app.middleware("http")
  async def add_security_headers(request: Request, call_next):
      response = await call_next(request)
      response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
      return response
  ```

**Internal Service-to-Service Communication:**
- **Method:** Mutual TLS (mTLS)
- **Use case:** Backend API → PostgreSQL, Backend → Neo4j, etc.
- **Certificate management:** AWS Certificate Manager or cert-manager (Kubernetes)
- **Verification:** Both client and server verify each other's certificates

**Data in Motion (External APIs):**
- **LLM APIs (Claude, OpenAI):** HTTPS only (enforced by providers)
- **Data source APIs (Salesforce, Slack, etc.):** OAuth over HTTPS
- **Webhooks:** Verify webhook signatures (HMAC) to prevent man-in-the-middle

---

#### Credential Management

**OAuth Token Storage:**
- **Access tokens:** Short-lived (15 minutes), stored encrypted in PostgreSQL
- **Refresh tokens:** Long-lived (7-30 days), stored encrypted with KMS-backed keys
- **Token refresh strategy:**
  ```python
  async def refresh_oauth_token(data_source_id: str):
      # Retrieve refresh token (decrypt)
      refresh_token = decrypt_credentials(data_source.credentials_encrypted)['refresh_token']

      # Request new access token
      response = requests.post(
          TOKEN_ENDPOINT,
          data={
              'grant_type': 'refresh_token',
              'refresh_token': refresh_token,
              'client_id': CLIENT_ID,
              'client_secret': CLIENT_SECRET
          }
      )

      new_tokens = response.json()

      # Update stored credentials
      credentials['access_token'] = new_tokens['access_token']
      if 'refresh_token' in new_tokens:
          credentials['refresh_token'] = new_tokens['refresh_token']

      # Re-encrypt and save
      data_source.credentials_encrypted = encrypt_credentials(credentials)
      db.commit()
  ```

**Auto-Refresh Before Expiry:**
- Background job checks tokens expiring within 5 minutes
- Proactively refreshes to avoid sync failures
- Runs every 1 minute

**Secrets Rotation Policy:**
- **Frequency:** Every 90 days (automated)
- **Scope:** JWT secrets, KMS keys, API keys
- **Process:**
  1. Generate new secret
  2. Add to secrets manager (both old + new active)
  3. Deploy new version (validates with new secret)
  4. After 24 hours, revoke old secret
- **Monitoring:** Alert if rotation fails

---

### Access Control

#### Authentication

**Method: JWT (JSON Web Tokens)**

**Token Types:**

1. **Access Token:**
   - **Expiry:** 15 minutes
   - **Storage:** In-memory (frontend JavaScript variable, NOT localStorage)
   - **Payload:**
     ```json
     {
       "sub": "user_id_uuid",
       "org_id": "org_uuid",
       "role": "admin",
       "exp": 1705330800
     }
     ```
   - **Signature:** HS256 (HMAC with SHA-256)

2. **Refresh Token:**
   - **Expiry:** 7 days (configurable: 7-30 days)
   - **Storage:** HTTPOnly, Secure, SameSite=Strict cookie
   - **Rotation:** New refresh token issued on each refresh (old one blacklisted)
   - **Blacklist:** Stored in Redis with TTL = token expiry

**Why HTTPOnly cookies for refresh tokens:**
- JavaScript can't access it → XSS protection
- SameSite=Strict → CSRF protection
- Secure flag → Only sent over HTTPS

---

**Password Requirements:**

**Minimum Standards:**
- **Length:** 12 characters minimum (encourage 16+)
- **Complexity:**
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - At least 1 special character (!@#$%^&*)
- **No common passwords:** Check against top 10K breached passwords (e.g., "Password123!")

**Hashing:**
- **Algorithm:** bcrypt
- **Cost factor:** 12 (2^12 rounds = ~250ms per hash on modern CPU)
- **Salt:** Unique per password (bcrypt handles automatically)
- **Implementation:**
  ```python
  from passlib.context import CryptContext

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  # Hash password
  hashed = pwd_context.hash("user_password")

  # Verify password
  is_valid = pwd_context.verify("user_password", hashed)
  ```

**Why bcrypt:**
- **Slow by design:** Makes brute-force attacks expensive
- **Adaptive:** Can increase cost factor as hardware improves
- **Industry standard:** Battle-tested, widely audited

---

**Multi-Factor Authentication (MFA) - Future:**
- **MVP:** Single-factor (password only) to reduce friction
- **Phase 2 (Month 6+):**
  - TOTP (Time-based One-Time Password) via Google Authenticator, Authy
  - SMS backup (less secure, but better than nothing)
  - Recovery codes (10 single-use codes for account recovery)
- **Enforcement:** Optional for Starter/Professional, mandatory for Enterprise

---

#### Authorization (RBAC)

**Role-Based Access Control (RBAC):**

**3 Roles:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | - Full access to all org data<br>- User management (invite, remove, change roles)<br>- Billing & subscription management<br>- Connect/disconnect data sources<br>- API key generation<br>- View audit logs | Founders, IT admins, department heads |
| **User** | - Search across all connected data sources<br>- View knowledge graph<br>- Manage own profile<br>- View search history<br>- Connect personal data sources (if enabled by admin)<br>- Cannot modify org settings or billing | Most employees (sales, CS, ops, marketing) |
| **Viewer** | - Search across connected data sources (read-only)<br>- View knowledge graph<br>- View own search history<br>- Cannot connect data sources<br>- Cannot modify anything | External contractors, auditors, read-only access, interns |

---

**Permissions Matrix:**

| Action | Admin | User | Viewer |
|--------|-------|------|--------|
| Search data | ✅ | ✅ | ✅ |
| View knowledge graph | ✅ | ✅ | ✅ |
| Connect data source | ✅ | ✅* | ❌ |
| Disconnect data source | ✅ | ❌ | ❌ |
| Invite users | ✅ | ❌ | ❌ |
| Remove users | ✅ | ❌ | ❌ |
| Change user roles | ✅ | ❌ | ❌ |
| Manage billing | ✅ | ❌ | ❌ |
| Generate API keys | ✅ | ❌ | ❌ |
| View audit logs | ✅ | ❌ | ❌ |
| Modify org settings | ✅ | ❌ | ❌ |

*Users can connect data sources if admin enables "User self-service connections" setting

---

**Row-Level Security (Multi-Tenancy):**

**Principle:** Users can only access data from their organization

**Implementation:**
- **PostgreSQL:** Every query filters by `org_id`
  ```python
  # BAD (no org filter)
  data_sources = db.query(DataSource).all()

  # GOOD (org filter)
  data_sources = db.query(DataSource).filter(
      DataSource.org_id == current_user.org_id
  ).all()
  ```

- **Vector DB (Pinecone):** Metadata filter on every query
  ```python
  results = pinecone_index.query(
      vector=query_embedding,
      filter={"org_id": {"$eq": current_user.org_id}}
  )
  ```

- **Neo4j:** Cypher queries include org filter
  ```cypher
  MATCH (d:Document {org_id: $org_id})
  WHERE d.title CONTAINS $query
  RETURN d
  ```

**Enforcement:**
- **Middleware:** FastAPI dependency injection validates `org_id` on every request
- **ORM hooks:** SQLAlchemy event listeners auto-add `org_id` filter
- **Testing:** Integration tests verify cross-tenant isolation (user A can't access org B's data)

---

#### API Security

**Rate Limiting:**

**Limits by User Type:**

| User Type | Limit | Window | Purpose |
|-----------|-------|--------|---------|
| **Authenticated (Starter)** | 100 requests | 1 hour | Prevent abuse, fair usage |
| **Authenticated (Professional)** | 500 requests | 1 hour | Higher tier, more generous |
| **Authenticated (Enterprise)** | 1000 requests | 1 hour | Enterprise needs |
| **Unauthenticated** | 10 requests | 1 hour | Prevent scraping, DDoS |
| **Admin endpoints** | 100 requests | 1 hour | Sensitive operations (user mgmt, billing) |

**Implementation (Redis + Sliding Window):**
```python
from fastapi import HTTPException
import redis

async def rate_limit(user_id: str, limit: int, window: int):
    key = f"rate_limit:{user_id}:{int(time.time() / window)}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window)
    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

**Response Headers:**
```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 487
X-RateLimit-Reset: 1705330800
```

---

**API Keys (Programmatic Access):**

**Format:** `sk_live_1234567890abcdef` (prefix + 16 random chars)

**Creation:**
```python
import secrets
import hashlib

# Generate API key
api_key = f"sk_live_{secrets.token_urlsafe(16)}"

# Hash before storing (never store plaintext)
key_hash = hashlib.sha256(api_key.encode()).hexdigest()

# Store hash + prefix (for display)
api_key_record = APIKey(
    org_id=org.id,
    key_hash=key_hash,
    key_prefix=api_key[:10],  # "sk_live_12"
    permissions={"search": True, "admin": False}
)
```

**Authentication:**
```python
# Client sends: Authorization: Bearer sk_live_1234567890abcdef
# Server hashes incoming key and looks up in database
```

**Security:**
- API keys have **scoped permissions** (search-only, admin, etc.)
- Can be **revoked** instantly (delete from database)
- **Expiration:** Optional expiry date
- **Audit log:** All API key usage logged

---

**CORS (Cross-Origin Resource Sharing):**

**Allowed Origins:**
- **Production:** `https://app.unifydata.ai`
- **Staging:** `https://staging.unifydata.ai`
- **Development:** `http://localhost:3000`

**Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.unifydata.ai",
        "https://staging.unifydata.ai",
        "http://localhost:3000"  # Dev only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)
```

**Why whitelist only:**
- Prevents malicious sites from making requests to API
- Protects against CSRF attacks

---

**Request Validation (Pydantic):**

**All API inputs validated:**
```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=12, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)

@app.post("/auth/register")
async def register(user: UserCreate):
    # Pydantic automatically validates:
    # - email is valid format
    # - password is 12-128 chars
    # - first_name is 1-100 chars
    # Returns 422 Unprocessable Entity if invalid
    pass
```

**Benefits:**
- **Type safety:** Catches type errors at runtime
- **Auto documentation:** OpenAPI spec shows validation rules
- **Security:** Rejects malformed inputs before they reach business logic

---

**SQL Injection Prevention:**

**Use ORMs, not raw SQL:**
```python
# BAD (SQL injection vulnerable)
query = f"SELECT * FROM users WHERE email = '{user_input}'"
db.execute(query)

# GOOD (parameterized query via ORM)
user = db.query(User).filter(User.email == user_input).first()
```

**SQLAlchemy parameterizes all queries automatically:**
- User input treated as data, not code
- Impossible to inject SQL commands

---

### Application Security

#### Input Validation & Sanitization

**File Upload Validation:**

**Restrictions:**
- **File types:** Only allow specific extensions (PDF, DOCX, TXT, CSV, etc.)
- **File size:** Max 50MB per file
- **Content scanning:** Use `python-magic` to verify actual file type (not just extension)
- **Virus scanning:** Integrate ClamAV or AWS GuardDuty (future)

**Implementation:**
```python
import magic

ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/csv'
]

async def validate_file(file: UploadFile):
    # Check size
    if file.size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(400, "File too large")

    # Read first 2048 bytes (magic number detection)
    content = await file.read(2048)
    mime_type = magic.from_buffer(content, mime=True)

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"File type not allowed: {mime_type}")

    await file.seek(0)  # Reset file pointer
    return file
```

---

**XSS (Cross-Site Scripting) Prevention:**

**Output Escaping:**
- **Frontend:** React automatically escapes JSX (prevents XSS by default)
- **Backend:** Don't return raw HTML (return JSON only)
- **If HTML needed:** Use `bleach` library to sanitize
  ```python
  import bleach

  sanitized = bleach.clean(
      user_input,
      tags=['p', 'b', 'i', 'a'],  # Allow only safe tags
      attributes={'a': ['href']},
      strip=True
  )
  ```

**Content Security Policy (CSP) Headers:**
```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.vercel.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https://api.unifydata.ai"
)
```

---

**CSRF (Cross-Site Request Forgery) Protection:**

**For State-Changing Operations:**
- **Cookies:** SameSite=Strict (blocks cross-site cookie sending)
- **CSRF Tokens:** Generate unique token per session, validate on POST/PUT/DELETE
  ```python
  from fastapi_csrf_protect import CsrfProtect

  @app.post("/data-sources/{id}/delete")
  async def delete_source(id: str, csrf_protect: CsrfProtect = Depends()):
      await csrf_protect.validate_csrf_token(request)
      # Delete logic...
  ```

**Why SameSite=Strict is not enough:**
- Protects against most CSRF, but not all (e.g., same-site subdomain attacks)
- CSRF token adds defense-in-depth

---

#### Dependency Security

**Tools:**
- **Dependabot (GitHub):** Auto-creates PRs for dependency updates
- **Snyk:** Scans for known vulnerabilities in dependencies
- **pip-audit (Python):** Audits Python packages against CVE database
- **npm audit (Node.js):** Audits npm packages

**Policy:**
- **Critical vulnerabilities:** Fix within 24 hours
- **High vulnerabilities:** Fix within 1 week
- **Medium/Low:** Fix in next sprint
- **Monthly updates:** Update all dependencies monthly (not just security patches)

**CI/CD Integration:**
```yaml
# GitHub Actions workflow
- name: Security Scan
  run: |
    pip install pip-audit
    pip-audit --requirement requirements.txt
    # Fail build if critical vulnerabilities found
```

**Lock Files:**
- **Python:** `requirements.txt` with exact versions (`fastapi==0.104.1`)
- **Node.js:** `package-lock.json` (committed to repo)
- **Why:** Ensures reproducible builds, prevents supply chain attacks (malicious updates)

---

#### Logging & Audit Trail

**What to Log:**

**Security Events:**
- ✅ Login attempts (success/failure, IP, user agent)
- ✅ Password changes
- ✅ Failed authorization attempts (403 errors)
- ✅ API key creation/revocation
- ✅ User role changes
- ✅ Data source connections/disconnections
- ✅ Unusual activity (e.g., 100 failed logins in 1 minute)

**Data Access:**
- ✅ Search queries (user, query, timestamp, results returned)
- ✅ Document access (who accessed which document)
- ✅ Data exports (who, what, when)

**Configuration Changes:**
- ✅ Org settings modified (who, what changed, old/new values)
- ✅ Billing changes
- ✅ API endpoint deployments

---

**What NOT to Log:**

**Sensitive Data:**
- ❌ Passwords (even hashed ones)
- ❌ OAuth tokens, API keys
- ❌ Full email content (log metadata only: subject, from, to)
- ❌ PII unless necessary (SSNs, credit cards, etc.)
- ❌ Full document content (log document IDs, not content)

**Why:**
- **Compliance:** GDPR prohibits unnecessary PII logging
- **Security:** If logs are breached, sensitive data not exposed
- **Storage:** Logs with full content are massive (expensive to store)

---

**Log Format (Structured JSON):**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "event": "login_success",
  "user_id": "uuid",
  "org_id": "uuid",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "request_id": "req_abc123"
}
```

**Retention:**
- **Security logs (auth, access):** 90 days
- **Audit logs (changes, actions):** 1 year (or longer for compliance)
- **Application logs (errors, debug):** 30 days
- **Archived logs:** Move to S3 Glacier after retention period (cheaper, immutable)

---

**Audit Log API (For Customers):**
```python
# Enterprise customers can query their audit logs
GET /api/audit-logs?start_date=2025-01-01&end_date=2025-01-15&event_type=login
```

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "event": "login_success",
      "user": "john@acme.com",
      "ip": "192.168.1.1"
    }
  ],
  "total": 142,
  "page": 1
}
```

---

### Compliance Readiness

#### GDPR Compliance

**Data Subject Rights:**

**1. Right to Access (GDPR Article 15):**
- User can request all data we have about them
- **Implementation:**
  ```python
  @app.get("/user/export")
  async def export_user_data(current_user: User = Depends(get_current_user)):
      # Export user data as JSON
      data = {
          "profile": current_user.to_dict(),
          "search_history": get_search_history(current_user.id),
          "connected_sources": get_data_sources(current_user.org_id),
          # ...
      }
      return JSONResponse(content=data)
  ```

**2. Right to Deletion (GDPR Article 17 - "Right to be Forgotten"):**
- User can request account deletion
- **Implementation:**
  - Hard delete from PostgreSQL (cascading deletes)
  - Delete vectors from Pinecone (filter by `user_id`)
  - Delete graph nodes from Neo4j
  - Delete files from S3
  - Delete from Redis cache
- **Timeline:** Complete within 30 days

**3. Right to Portability (GDPR Article 20):**
- User can export data in machine-readable format (JSON)
- Same as "Right to Access" above

**4. Right to Rectification (GDPR Article 16):**
- User can update their profile (name, email, etc.)
- Implemented via `/user/profile` PUT endpoint

---

**Consent Management:**
- **Explicit consent** for data indexing (checkbox during data source connection)
- **Granular consent:** User chooses which data sources to index (e.g., index Slack, but not Gmail)
- **Consent log:** Store when user gave consent (timestamp, IP, user agent)
- **Withdrawal:** User can revoke consent (disconnect data source)

**Data Minimization:**
- Only index data needed for search (don't store unnecessary fields)
- Example: For emails, store subject/from/to (metadata), but make body content opt-in

**Data Retention Policies:**
- **Active data:** No expiry (as long as user is customer)
- **After account deletion:** Delete all data within 30 days
- **Inactive accounts:** Notify after 12 months of inactivity, delete after 18 months (if no response)

---

#### SOC 2 Preparation (Future)

**SOC 2 Type II Requirements:**

**Trust Service Criteria:**

1. **Security:** Access controls, encryption, monitoring (covered above)
2. **Availability:** Uptime targets, disaster recovery, backups
3. **Processing Integrity:** Data accuracy, error handling, monitoring
4. **Confidentiality:** Data classification, NDAs, encryption
5. **Privacy:** GDPR compliance, consent management, data retention

**Required Documentation:**
- ✅ Information security policy
- ✅ Access control policy
- ✅ Incident response plan
- ✅ Change management process
- ✅ Vendor risk management
- ✅ Security awareness training (for employees)
- ✅ Penetration test reports (annual)
- ✅ Audit logs (evidence of compliance)

**Timeline:**
- **Month 0-6 (MVP):** Implement controls (encryption, logging, access control)
- **Month 6-12:** Document policies, run gap analysis
- **Month 12-18:** Hire auditor, begin SOC 2 Type I (point-in-time audit)
- **Month 18-24:** Complete SOC 2 Type II (6-12 month observation period)

---

#### Data Residency

**Regions Supported:**

| Region | Cloud | Availability | Notes |
|--------|-------|--------------|-------|
| **US (East)** | AWS us-east-1 | MVP (Month 1) | Primary region |
| **EU (Ireland)** | AWS eu-west-1 | Phase 2 (Month 9) | GDPR compliance |
| **APAC (future)** | AWS ap-southeast-1 | Phase 3 (Month 18) | Future expansion |

**Region Selection:**
- User chooses region during org creation (cannot change later without migration)
- **Why:** Compliance (GDPR requires EU data stay in EU)

**Data Isolation:**
- **Separate databases per region** (PostgreSQL, Neo4j, Redis)
- **Separate S3 buckets per region**
- **Pinecone:** Use separate indexes per region (`unifydata-us-east`, `unifydata-eu-west`)
- **Cross-region access:** Prohibited (no data leakage across regions)

**Legal Compliance:**
- **GDPR (EU):** Personal data of EU citizens must stay in EU
- **CCPA (California):** No region requirement, but must honor deletion requests
- **Future:** Brazil (LGPD), India (DPDP), China (PIPL) may require local data residency

---

## 8. INFRASTRUCTURE & DEPLOYMENT

### Cloud Provider Strategy

#### Recommended Setup (Hybrid Multi-Cloud)

**Frontend:** Vercel
- **Why:** Next.js optimized, edge functions, auto-scaling, zero DevOps
- **Cost:** ~$20-50/month (Pro plan)

**Backend & Databases:** AWS
- **Why:** Mature, comprehensive services, better for heavy compute/data workloads
- **Services:**
  - **Compute:** ECS Fargate (containers) or Lambda (serverless)
  - **Databases:** RDS (PostgreSQL), ElastiCache (Redis), EC2 (Neo4j)
  - **Storage:** S3
  - **Networking:** VPC, ALB, Route 53

**Vector DB:** Pinecone (SaaS)
- **Why:** Managed, no infrastructure, auto-scaling
- **Cost:** ~$70/month (Starter plan)

**CDN:** Cloudflare
- **Why:** Fast, DDoS protection, cheaper than CloudFront
- **Cost:** Free plan for MVP (20/month for Pro if needed)

---

#### Alternative: Full AWS Stack

**Pros:**
- Single vendor (simpler billing, support)
- Better VPC networking (all services in same VPC)
- AWS credits for startups (up to $100K)

**Cons:**
- Vercel has better Next.js DX than AWS Amplify
- More DevOps work (manage everything yourself)

**If choosing full AWS:**
- **Frontend:** AWS Amplify (or S3 + CloudFront for static)
- **Backend:** ECS Fargate or Lambda
- **Databases:** Same as hybrid

---

#### Alternative: Google Cloud Platform

**Pros:**
- **AI/ML tools:** Vertex AI, AutoML (if building custom models)
- **Pricing:** Often 10-20% cheaper than AWS
- **BigQuery:** Great for analytics (future feature)

**Cons:**
- Less mature than AWS (fewer case studies, smaller ecosystem)
- Pinecone might not be available in all GCP regions

**If choosing GCP:**
- **Frontend:** Cloud Run (containerized Next.js) or Firebase Hosting
- **Backend:** Cloud Run (containers) or Cloud Functions
- **Databases:** Cloud SQL (PostgreSQL), Memorystore (Redis), GCE (Neo4j)

---

**DECISION for MVP:** **Vercel (frontend) + AWS (backend)** = Best developer experience + proven scalability

---

### Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                         INTERNET                              │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                          ↓
┌───────────────────────────────────────────────────────────────┐
│               CLOUDFLARE (CDN + DDoS Protection)              │
│  - Static asset caching                                       │
│  - DDoS mitigation (L3/L4/L7)                                 │
│  - TLS termination                                            │
└──────────────┬────────────────────────────────────────────────┘
               │
               ↓
┌───────────────────────────────────────────────────────────────┐
│              VERCEL (Next.js Frontend)                        │
│  - Server-side rendering                                      │
│  - Static site generation                                     │
│  - Edge functions                                             │
│  - Auto-scaling (serverless)                                  │
└──────────────┬────────────────────────────────────────────────┘
               │ HTTPS API calls
               ↓
┌───────────────────────────────────────────────────────────────┐
│                      AWS VPC                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  APPLICATION LOAD BALANCER (ALB)                        │ │
│  │  - HTTPS termination                                    │ │
│  │  - Health checks                                        │ │
│  │  - Request routing                                      │ │
│  └───────────────────┬─────────────────────────────────────┘ │
│                      │                                        │
│                      ↓                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  BACKEND API (ECS Fargate - 2+ containers)             │ │
│  │  - FastAPI application                                  │ │
│  │  - Auto-scaling (target CPU 70%)                        │ │
│  │  - Private subnet (no public IPs)                       │ │
│  └────┬────────────────────────┬─────────────────┬─────────┘ │
│       │                        │                 │           │
│       ↓                        ↓                 ↓           │
│  ┌─────────────┐        ┌──────────────┐  ┌──────────────┐ │
│  │ PostgreSQL  │        │ Redis Cache  │  │ S3 Bucket    │ │
│  │ (RDS)       │        │ (ElastiCache)│  │ (Private)    │ │
│  │ - Multi-AZ  │        │ - 1 node     │  │ - Encrypted  │ │
│  │ - Encrypted │        │ - 0.5GB RAM  │  │ - Versioned  │ │
│  └─────────────┘        └──────────────┘  └──────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  BACKGROUND WORKERS (ECS Fargate - 2+ containers)      │ │
│  │  - Data sync jobs                                       │ │
│  │  - Embedding generation                                 │ │
│  │  - Knowledge graph updates                              │ │
│  │  - Celery workers                                       │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│                       ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  JOB QUEUE (SQS or Redis)                              │ │
│  │  - Sync job queue                                       │ │
│  │  - Indexing job queue                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                       │                 │
                       ↓                 ↓
┌──────────────────────┐  ┌──────────────────────────────────┐
│ PINECONE (Vector DB) │  │ NEO4J (Graph DB)                 │
│ - Managed service    │  │ - EC2 t3.medium OR               │
│ - Auto-scaling       │  │ - Neo4j Aura (managed)           │
│ - External to AWS    │  │ - Inside VPC (if EC2)            │
└──────────────────────┘  └──────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│              EXTERNAL APIs                                   │
│  - Anthropic Claude (LLM)                                    │
│  - OpenAI (Embeddings)                                       │
│  - Data Source APIs (Salesforce, Slack, Google, etc.)       │
└──────────────────────────────────────────────────────────────┘
```

---

### Compute Resources (MVP Sizing)

#### Cost Breakdown (Monthly)

| Service | Specs | Quantity | Cost/Unit | Total |
|---------|-------|----------|-----------|-------|
| **Vercel (Frontend)** | Pro plan | 1 team | $20/month | $20 |
| **ECS Fargate (API)** | 2 vCPU, 4GB RAM | 2 tasks | $60/month | $120 |
| **ECS Fargate (Workers)** | 2 vCPU, 4GB RAM | 2 tasks | $60/month | $120 |
| **RDS PostgreSQL** | db.t3.medium (2 vCPU, 4GB) | 1 instance | $80/month | $80 |
| **ElastiCache Redis** | cache.t3.micro (0.5GB) | 1 node | $15/month | $15 |
| **EC2 Neo4j** | t3.medium (2 vCPU, 4GB) | 1 instance | $35/month | $35 |
| **S3 Storage** | 100GB + 500GB egress | - | - | $15 |
| **Pinecone** | Starter plan (100K vectors) | 1 index | $70/month | $70 |
| **ALB (Load Balancer)** | Application Load Balancer | 1 | $20/month | $20 |
| **Data Transfer** | Egress from AWS | ~200GB | - | $15 |
| **CloudWatch Logs** | Logs + metrics | - | - | $10 |

**Total MVP Infrastructure Cost: ~$520/month**

**Note:** This supports ~500-1000 searches/day, 50-100 concurrent users

---

#### Scaling Costs (Projected)

**At 10K searches/day (100× MVP):**
- **Backend API:** Scale to 5 containers = $300/month (+$180)
- **Workers:** Scale to 5 containers = $300/month (+$180)
- **PostgreSQL:** Upgrade to db.r5.large = $180/month (+$100)
- **Redis:** Upgrade to cache.m5.large = $120/month (+$105)
- **Pinecone:** 1M vectors = $140/month (+$70)
- **S3 + Data Transfer:** $100/month (+$85)

**Total at Scale: ~$1,240/month**

---

### Containerization (Docker)

#### Backend API Dockerfile

```dockerfile
# Use official Python slim image (smaller than full image)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for psycopg2, cryptography, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application (Uvicorn ASGI server)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**Why slim image:**
- Smaller size (150MB vs 1GB for full image) → faster builds, less storage
- Security: Fewer packages = smaller attack surface

**Why `--no-cache-dir`:**
- Reduces image size by not storing pip cache

---

#### Worker Dockerfile (Celery)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run Celery worker
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
```

---

#### Docker Compose (Local Development)

```yaml
version: '3.8'

services:
  # Backend API
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app  # Hot reload during development
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Background workers
  worker:
    build: ./backend
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.celery_app worker --loglevel=info

  # PostgreSQL database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: unifydata
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis cache + queue
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Neo4j graph database
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/devpass
      NEO4J_PLUGINS: '["apoc"]'  # APOC procedures
    volumes:
      - neo4j_data:/data

volumes:
  postgres_data:
  neo4j_data:
```

**Usage:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

---

### CI/CD Pipeline (GitHub Actions)

#### Workflow File (`.github/workflows/deploy.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  # Job 1: Lint & Format Check
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ruff black mypy
          pip install -r backend/requirements.txt

      - name: Lint with Ruff
        run: ruff check backend/

      - name: Format check with Black
        run: black --check backend/

      - name: Type check with mypy
        run: mypy backend/

  # Job 2: Unit Tests
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-asyncio
          pip install -r backend/requirements.txt

      - name: Run tests
        run: pytest backend/tests/ --cov=backend --cov-report=xml
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  # Job 3: Build Docker Image
  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to AWS ECR
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            ${{ secrets.AWS_ECR_REGISTRY }}/unifydata-api:${{ github.sha }}
            ${{ secrets.AWS_ECR_REGISTRY }}/unifydata-api:latest

      - name: Security scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ secrets.AWS_ECR_REGISTRY }}/unifydata-api:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # Job 4: Deploy to Staging
  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to ECS (Staging)
        run: |
          aws ecs update-service \
            --cluster unifydata-staging \
            --service api-service \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster unifydata-staging \
            --services api-service

      - name: Smoke tests
        run: |
          curl -f https://staging.unifydata.ai/health || exit 1

  # Job 5: Deploy to Production (Manual Approval)
  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval in GitHub
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to ECS (Production)
        run: |
          aws ecs update-service \
            --cluster unifydata-production \
            --service api-service \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster unifydata-production \
            --services api-service

      - name: Post-deployment tests
        run: |
          curl -f https://app.unifydata.ai/health || exit 1
          # Add more critical path tests here

      - name: Notify team (Slack)
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 Deployed to production: ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

#### Deployment Environments

| Environment | Branch | Auto-Deploy | Approval Required | URL |
|-------------|--------|-------------|-------------------|-----|
| **Development** | `feature/*` | No | No | Local only |
| **Staging** | `main` | Yes | No | staging.unifydata.ai |
| **Production** | `main` | Yes | **Manual approval** | app.unifydata.ai |

---

### Deployment Strategy

#### Blue-Green Deployment

**How it works:**
1. **Blue environment:** Current production (serving traffic)
2. **Green environment:** New version (not serving traffic yet)
3. Deploy to green
4. Run tests on green
5. Switch ALB target group from blue to green (instant cutover)
6. Keep blue running for 24 hours (quick rollback if needed)

**Benefits:**
- **Zero downtime:** Traffic switches instantly
- **Easy rollback:** Just switch ALB back to blue
- **Test in production:** Can test green before switching traffic

**Implementation (ECS):**
```bash
# Deploy new task definition to green target group
aws ecs update-service \
  --cluster unifydata-production \
  --service api-service-green \
  --task-definition unifydata-api:123

# Wait for green to be healthy
aws ecs wait services-stable \
  --cluster unifydata-production \
  --services api-service-green

# Switch ALB target group (blue → green)
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:.../green
```

---

#### Rollback Plan

**Automated Rollback:**
- **Health check failures:** If green fails health checks, don't switch traffic
- **Error rate spike:** If 5xx errors >10% after deployment, auto-rollback

**Manual Rollback:**
- **One-click rollback:** Switch ALB back to blue target group
- **CI/CD trigger:** Re-run deployment workflow with previous commit SHA

**Database Migrations:**
- **Additive only:** New columns/tables are okay (old code ignores them)
- **No breaking changes:** Don't drop columns/tables in same deployment as code change
- **Two-phase migration:**
  1. Deploy code that works with both old + new schema
  2. Run migration
  3. Deploy code that only uses new schema

---

## 9. MONITORING & OBSERVABILITY

### Application Performance Monitoring (APM)

#### Error Tracking: Sentry

**Setup:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    environment="production",  # or "staging"
    traces_sample_rate=0.1,  # 10% of transactions traced
    integrations=[
        FastApiIntegration(),
    ]
)
```

**What Gets Tracked:**
- **Frontend errors:** JavaScript exceptions, network failures, React errors
- **Backend errors:** Unhandled exceptions, API errors (500s)
- **Performance:** Slow API endpoints (>2s), database queries (>500ms)
- **Release tracking:** Link errors to specific deployments (git SHA)

**Alerting:**
- **Critical:** >10 errors in 5 minutes → Page on-call engineer
- **Warning:** New error type detected → Slack notification
- **Info:** Error rate increased 50% → Email notification

---

#### Logging Strategy

**Log Levels:**

| Level | Use Case | Example | Retention |
|-------|----------|---------|-----------|
| **DEBUG** | Development only, verbose details | "Query took 50ms" | Not in production |
| **INFO** | Normal operations | "User logged in" | 30 days |
| **WARNING** | Degraded performance, non-critical | "API response >2s" | 60 days |
| **ERROR** | Failures that don't stop service | "Failed to sync Salesforce (retrying)" | 90 days |
| **CRITICAL** | Service-breaking issues | "Database connection lost" | 1 year |

**Structured Logging (JSON):**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "user_login",
    user_id="uuid",
    org_id="uuid",
    ip="192.168.1.1",
    success=True
)
```

**Output:**
```json
{
  "event": "user_login",
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "user_id": "uuid",
  "org_id": "uuid",
  "ip": "192.168.1.1",
  "success": true
}
```

**Why structured logging:**
- **Searchable:** Query logs by field (e.g., "show all failed logins for user_id=X")
- **Aggregatable:** Count events (e.g., "how many logins per day?")
- **Machine-readable:** Easy to parse by log aggregation tools

---

**Log Aggregation: AWS CloudWatch Logs or Datadog**

**CloudWatch Logs:**
- **Pros:** Native AWS integration, cheap
- **Cons:** Basic UI, slower search

**Datadog:**
- **Pros:** Better UI, powerful search, built-in dashboards
- **Cons:** More expensive (~$15/month/GB ingested)

**Choice:** Start with CloudWatch (cheaper), migrate to Datadog if needed

---

#### Metrics & Dashboards

**Tool: Datadog or Grafana + Prometheus**

**Key Metrics to Track:**

**Application Metrics:**
- **Request rate:** Requests per second (RPS)
- **Response time:** P50, P95, P99 latency
- **Error rate:** Percentage of 4xx and 5xx responses
- **Active users:** Concurrent authenticated sessions

**Business Metrics:**
- **Searches per day:** Total searches
- **Avg searches per user:** Engagement metric
- **Data sources connected:** Feature adoption
- **Trial → paid conversion:** Funnel metric

**Infrastructure Metrics:**
- **CPU usage:** % utilization per container
- **Memory usage:** MB used + % of limit
- **Disk I/O:** Read/write ops per second
- **Network throughput:** MB/s in/out

**Database Metrics:**
- **Query performance:** Slow queries (>1s)
- **Connection pool:** Active connections vs pool size
- **Cache hit rate:** Redis hit rate (target >90%)
- **Replication lag:** Seconds behind primary (for read replicas)

**AI/ML Metrics:**
- **LLM API latency:** Time to first token, time to completion
- **Embedding generation time:** Seconds per 100 chunks
- **Cost per query:** $ spent on LLM + embeddings per search
- **Search relevance:** Click-through rate (CTR) on results

---

**Dashboard Example (Grafana):**

**Panel 1: Request Rate**
- Graph: RPS over last 24 hours
- Alert: >1000 RPS (capacity threshold)

**Panel 2: Response Time**
- Graph: P50, P95, P99 latency
- Alert: P95 >3s for 5 minutes

**Panel 3: Error Rate**
- Graph: % of 5xx errors
- Alert: >1% for 10 minutes

**Panel 4: Active Users**
- Single stat: Current concurrent users
- Goal: Track growth

**Panel 5: LLM Cost**
- Graph: $ spent per hour
- Alert: >$50/hour (unusual usage)

---

#### Alerting Rules

**Tool: PagerDuty (critical), Slack (warnings), Email (info)**

**Critical Alerts (PagerDuty + Phone):**
- API down (5xx errors >10% for 2 min)
- Database connection failures (>5 in 1 min)
- Authentication service down (cannot validate JWTs)
- Disk space >95% on any server

**Warning Alerts (Slack):**
- Response time P95 >3s for 5 min
- Error rate >1% for 10 min
- Redis memory usage >80%
- LLM API costs >$100/hour

**Info Alerts (Email):**
- Daily summary report (requests, errors, new users)
- Weekly performance report (compare to last week)
- Monthly cost report (AWS bill breakdown)

---

### Uptime Monitoring

**Tool: UptimeRobot (free plan) or Pingdom**

**Endpoints to Monitor:**
- **Frontend:** `https://app.unifydata.ai` (200 OK expected)
- **API health:** `https://api.unifydata.ai/health` (200 OK + JSON response)
- **Authentication:** `https://api.unifydata.ai/auth/health` (200 OK)

**Frequency:** Every 1 minute

**Alerting:**
- If down for **3 consecutive checks** (3 minutes) → Alert
- Escalation: Slack → Email → PagerDuty (if still down after 10 min)

**Public Status Page:**
- Use StatusPage.io or similar
- Show uptime % for each service
- Incident history
- URL: `status.unifydata.ai`

---

## 10. DEVELOPMENT ENVIRONMENT

### Local Development Setup

#### Prerequisites

**Required:**
- Docker 24+ & Docker Compose
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- Git

**Optional but Recommended:**
- Visual Studio Code (with Python, TypeScript extensions)
- Postman or Insomnia (API testing)
- TablePlus or pgAdmin (database GUI)

---

#### Setup Steps

**1. Clone Repository:**
```bash
git clone https://github.com/unifydata/unifydata.git
cd unifydata
```

**2. Copy Environment Variables:**
```bash
cp .env.example .env
```

**3. Fill in API Keys (`.env`):**
```bash
# Required for MVP
ANTHROPIC_API_KEY=sk-ant-...          # Get from console.anthropic.com
OPENAI_API_KEY=sk-...                  # Get from platform.openai.com
PINECONE_API_KEY=...                   # Get from pinecone.io
PINECONE_ENVIRONMENT=us-west1-gcp

# OAuth credentials (optional for local testing)
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
# ... (rest of connectors)
```

**4. Start Local Databases (Docker):**
```bash
docker-compose up -d postgres redis neo4j
```

**5. Run Database Migrations:**
```bash
cd backend
alembic upgrade head
```

**6. Start Backend API:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API runs at http://localhost:8000
```

**7. Start Frontend:**
```bash
cd web
npm install
npm run dev
# Frontend runs at http://localhost:3000
```

**8. Access Application:**
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432` (username: dev, password: devpass)
- Neo4j Browser: `http://localhost:7474` (username: neo4j, password: devpass)

---

#### Environment Variables (`.env`)

```bash
# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql://dev:devpass@localhost:5432/unifydata
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=devpass

# ============================================
# AI/ML APIs
# ============================================
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-west1-gcp

# ============================================
# AUTHENTICATION
# ============================================
JWT_SECRET=your-secret-key-change-in-production-to-random-256-bit-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# DATA CONNECTORS (OAuth)
# ============================================
# Salesforce
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
SALESFORCE_REDIRECT_URI=http://localhost:3000/integrations/salesforce/callback

# Slack
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
SLACK_REDIRECT_URI=http://localhost:3000/integrations/slack/callback

# Google (Drive, Gmail)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:3000/integrations/google/callback

# Notion
NOTION_CLIENT_ID=...
NOTION_CLIENT_SECRET=...
NOTION_REDIRECT_URI=http://localhost:3000/integrations/notion/callback

# ============================================
# AWS (for S3)
# ============================================
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=unifydata-dev

# ============================================
# APPLICATION
# ============================================
ENVIRONMENT=development
LOG_LEVEL=DEBUG
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# ============================================
# MONITORING (optional for local)
# ============================================
SENTRY_DSN=https://...@sentry.io/...  # Optional
```

---

### Code Organization (Monorepo)

```
unifydata/
├── .github/
│   └── workflows/              # GitHub Actions CI/CD
│       ├── deploy.yml
│       └── pr-checks.yml
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── api/               # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── data_sources.py
│   │   │   ├── search.py
│   │   │   └── ...
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── data_source.py
│   │   │   └── ...
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── search.py
│   │   │   └── ...
│   │   ├── services/          # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── connector_service.py
│   │   │   ├── ingestion_service.py
│   │   │   ├── indexing_service.py
│   │   │   ├── search_service.py
│   │   │   └── ...
│   │   ├── connectors/        # Data source integrations
│   │   │   ├── base.py        # Base connector interface
│   │   │   ├── salesforce.py
│   │   │   ├── slack.py
│   │   │   ├── google_drive.py
│   │   │   ├── notion.py
│   │   │   ├── gmail.py
│   │   │   └── ...
│   │   ├── db/                # Database clients
│   │   │   ├── postgres.py    # SQLAlchemy session
│   │   │   ├── pinecone_client.py
│   │   │   ├── neo4j_client.py
│   │   │   └── redis_client.py
│   │   ├── core/              # Core utilities
│   │   │   ├── config.py      # Settings (env vars)
│   │   │   ├── security.py    # Auth, encryption
│   │   │   └── logging.py     # Logging setup
│   │   └── workers/           # Background job workers
│   │       ├── celery_app.py
│   │       ├── sync_worker.py
│   │       └── ...
│   ├── tests/                 # Tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── alembic/               # Database migrations
│   │   └── versions/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── web/                       # Next.js frontend
│   ├── app/                   # App router pages
│   │   ├── page.tsx           # Homepage
│   │   ├── login/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── search/page.tsx
│   │   └── ...
│   ├── components/            # React components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultsList.tsx
│   │   │   └── ...
│   │   └── ...
│   ├── lib/                   # Utilities
│   │   ├── api-client.ts      # API fetch wrapper
│   │   ├── auth.ts            # Auth helpers
│   │   └── utils.ts
│   ├── public/                # Static assets
│   ├── package.json
│   └── tsconfig.json
├── shared/                    # Shared code (types, constants)
│   └── types.ts
├── docs/                      # Documentation
│   ├── technical-architecture-part1.md
│   ├── technical-architecture-part2.md
│   └── technical-architecture-part3.md  # This document!
├── scripts/                   # Utility scripts
│   ├── seed-db.py             # Seed dev database
│   └── migrate-prod.sh        # Production migration
├── docker-compose.yml         # Local dev services
├── .env.example               # Example environment variables
├── .gitignore
└── README.md
```

---

### Development Best Practices

#### Code Quality

**Linting (Catch Bugs Early):**
- **Python:** Ruff (fast, modern linter + formatter)
  ```bash
  ruff check backend/  # Check for issues
  ruff format backend/  # Auto-format code
  ```
- **TypeScript:** ESLint
  ```bash
  npm run lint  # Check for issues
  npm run lint:fix  # Auto-fix issues
  ```

**Formatting (Consistent Style):**
- **Python:** Black or Ruff formatter
- **TypeScript:** Prettier

**Type Checking (Prevent Type Errors):**
- **Python:** mypy
  ```bash
  mypy backend/  # Check type annotations
  ```
- **TypeScript:** TypeScript compiler (strict mode enabled)

**Pre-commit Hooks (Enforce Standards):**
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Now hooks run automatically on git commit
# Runs: linting, formatting, type checking
```

---

#### Testing Strategy

**Unit Tests:**
- **Coverage target:** 80%+ (focus on business logic, not boilerplate)
- **Tools:** pytest (Python), Vitest (TypeScript)
- **Example:**
  ```python
  def test_search_service_filters_by_org():
      # Given
      user = create_user(org_id="org1")
      create_document(org_id="org1", title="Doc 1")
      create_document(org_id="org2", title="Doc 2")

      # When
      results = search_service.search("Doc", user)

      # Then
      assert len(results) == 1
      assert results[0].title == "Doc 1"
  ```

**Integration Tests:**
- **Scope:** API endpoints (end-to-end request → response)
- **Tools:** pytest + TestClient (FastAPI), Playwright (E2E)
- **Example:**
  ```python
  def test_api_search_requires_auth():
      # When
      response = client.post("/api/search/query", json={"query": "test"})

      # Then
      assert response.status_code == 401
  ```

**E2E Tests (Critical User Flows):**
- **Scenarios:**
  1. User registers → verifies email → logs in → connects Slack → searches
  2. Admin invites user → user accepts → user searches
- **Tools:** Playwright (browser automation)
- **Run:** Weekly (slower, more flaky than unit/integration tests)

**Load Tests (Performance):**
- **Tools:** Locust (Python), k6 (Go)
- **Scenarios:**
  - Simulate 100 concurrent users searching
  - Measure: P95 latency, error rate, throughput
- **Target:** P95 <3s, 0 errors
- **Run:** Monthly (or before major releases)

---

#### Git Workflow

**Branching Strategy:**
- `main`: Production-ready code (always deployable)
- `feature/<feature-name>`: New features (e.g., `feature/slack-connector`)
- `bugfix/<bug-name>`: Bug fixes (e.g., `bugfix/search-empty-query`)
- `hotfix/<issue>`: Urgent production fixes (merged directly to main)

**Commit Conventions (Conventional Commits):**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature (e.g., `feat(search): add semantic search`)
- `fix`: Bug fix (e.g., `fix(auth): handle expired tokens`)
- `docs`: Documentation (e.g., `docs(readme): update setup instructions`)
- `refactor`: Code refactoring (no feature/behavior change)
- `test`: Add/update tests
- `chore`: Tooling, dependencies (e.g., `chore(deps): bump fastapi to 0.104`)

**Pull Request Process:**
1. Create branch from `main`
2. Make changes, write tests
3. Push branch, open PR
4. **CI checks run:** Linting, formatting, tests, security scan
5. **Code review:** Require 1 approval
6. **Merge to main** (squash commits for clean history)
7. **Auto-deploy to staging** (via CI/CD)

**Main Branch Protection:**
- Cannot push directly (must use PRs)
- Require passing checks (all tests, linting)
- Require 1 approval from code owner

---

## 11. TECHNICAL RISKS & MITIGATIONS

### Risk 1: Vector Database Costs at Scale

**Risk Level:** 🔴 HIGH

**Description:**
- Pinecone costs scale linearly with vector count
- At 1M vectors: ~$140/month
- At 10M vectors: ~$1,400/month
- If we over-chunk or don't deduplicate, costs spiral

**Impact:**
- **Financial:** Could hit $1000+/month unexpectedly
- **Product:** Might need to limit features to control costs

**Mitigation Strategies:**

1. **Start with Pinecone, plan migration:**
   - Use Pinecone for MVP (fast setup, managed)
   - At 500K vectors, plan migration to Weaviate (self-hosted, ~$100/month infra)
   - At 1M vectors, execute migration

2. **Aggressive deduplication:**
   - Hash document content before indexing
   - If hash exists, skip embedding generation
   - Saves both embedding costs + vector storage

3. **Smart chunking:**
   - Don't over-chunk (e.g., every 100 tokens = 10× more vectors)
   - Use semantic chunking (fewer, more meaningful chunks)
   - Target: 10-20 chunks per document (not 50+)

4. **Archive old data:**
   - Data older than 2 years: Move to "cold storage" (cheaper tier or S3)
   - Still searchable, but slower (batch retrieval)

**Monitoring:**
- Dashboard: Track vector count weekly
- Alert: 80% of Pinecone plan limit
- Projection: Estimate cost 3 months ahead based on growth rate

**Contingency Plan:**
- If costs hit $500/month unexpectedly: Pause new data ingestion, execute Weaviate migration immediately

---

### Risk 2: LLM API Costs Spiraling

**Risk Level:** 🟡 MEDIUM-HIGH

**Description:**
- Claude API costs $3-15 per 1M tokens
- If context windows are large (10K tokens per query) and volume is high (10K queries/day), costs reach $1K+/month
- Abuse scenarios (user spams queries) could spike costs

**Impact:**
- **Financial:** Unpredictable monthly costs
- **Product:** Might need to limit free tier or raise prices

**Mitigation Strategies:**

1. **Aggressive query caching:**
   - Cache responses for identical queries (Redis, 1 hour TTL)
   - Fuzzy matching: "What is our churn rate?" ≈ "What's our churn rate?"
   - Hit rate: Aim for 30-40% cache hits

2. **Prompt optimization:**
   - Use **shorter system prompts** (500 tokens → 200 tokens = 60% savings)
   - Include only top 5-10 chunks (not 20) = 50% smaller context
   - Anthropic **prompt caching** (cache system prompt, pay 90% less on repeated use)

3. **Model selection (routing):**
   - **Simple queries** (e.g., "What is X?") → GPT-3.5 Turbo ($0.50/$1.50 per 1M = 10× cheaper)
   - **Complex queries** (e.g., "Compare X and Y") → Claude 3.5 Sonnet
   - Use heuristic: Query length <50 chars + no "compare/analyze" keywords → use GPT-3.5

4. **Rate limiting per user:**
   - Starter: 100 queries/day (limits max cost to ~$2.50/day)
   - Professional: 500 queries/day (~$12/day)
   - Enterprise: 1000 queries/day (~$25/day)

5. **Cost alerts:**
   - Daily spend alert: >$50/day (email)
   - Hourly spike alert: >$10/hour (Slack)
   - Per-customer tracking: Flag customers using >10× avg queries

**Monitoring:**
- **Cost per query:** Track average + P95 (target: <$0.05)
- **Daily/weekly spend:** Trend over time
- **Per-customer usage:** Identify power users or abuse

**Contingency Plan:**
- If monthly cost exceeds $1000: Implement aggressive caching, switch to GPT-3.5 for 50% of queries

---

### Risk 3: Slow Search Performance

**Risk Level:** 🟡 MEDIUM

**Description:**
- Users expect sub-2s search responses
- If semantic search (Pinecone) + LLM call (Claude) + graph query (Neo4j) take too long, UX suffers
- At scale (1M+ vectors), search latency increases

**Impact:**
- **Product:** Poor UX → user churn
- **Competitive:** Slower than competitors (Glean, etc.)

**Mitigation Strategies:**

1. **Query result caching:**
   - Cache top 100 popular queries (Redis, 1 hour TTL)
   - 30-40% hit rate = instant results for cached queries

2. **Vector DB optimization:**
   - Pinecone: Use **pod-based indexes** (not serverless) for consistent low latency
   - Weaviate: Tune HNSW parameters (ef, M) for speed vs accuracy trade-off

3. **Smaller context windows:**
   - Send only top 5-10 chunks to Claude (not 20)
   - Reduces LLM latency by 50%

4. **Async processing + streaming:**
   - Show **partial results** immediately (before LLM finishes)
   - Stream LLM response token-by-token (perceived latency is lower)

5. **CDN caching:**
   - Cache static assets (JS, CSS, images) on Cloudflare
   - Reduces initial page load time

**Monitoring:**
- **P95 response time:** Target <3s, alert if >5s for 5 consecutive queries
- **Breakdown by step:** Track latency for vector search, LLM call, graph query separately
- **User feedback:** Track "slow search" complaints

**Contingency Plan:**
- If P95 >5s: Reduce context size to 5 chunks, enable aggressive caching

---

### Risk 4: Data Connector Failures

**Risk Level:** 🟡 MEDIUM

**Description:**
- Data source APIs (Salesforce, Slack, Google) can fail:
  - Rate limits exceeded
  - OAuth tokens expired
  - API downtime
  - Schema changes (breaking our parser)
- If sync fails, data becomes stale → users complain

**Impact:**
- **Product:** Stale search results, user frustration
- **Support:** High support ticket volume

**Mitigation Strategies:**

1. **Retry logic with exponential backoff:**
   - Retry failed API calls 5× (1s, 2s, 4s, 8s, 16s delays)
   - If all retries fail, mark sync as "error" and alert

2. **Health monitoring per connector:**
   - Track success rate per connector (Salesforce: 98%, Slack: 99%, etc.)
   - Alert if success rate drops below 95%

3. **Fallback strategies:**
   - If Salesforce sync fails, continue syncing Slack, Google, etc. (don't fail entire job)
   - Partial sync: Process 80% of docs successfully, log 20% failures

4. **User notifications:**
   - If sync fails 3× consecutively: Email user ("Salesforce sync failing, please re-authenticate")
   - In-app banner: "Last sync failed 2 hours ago. [Retry now]"

5. **Manual retry:**
   - User can click "Sync Now" button to trigger manual sync

**Monitoring:**
- **Success rate per connector:** Target >98%
- **Alert:** 3 consecutive failures for any connector
- **Dashboard:** Show sync status for all connected sources

**Contingency Plan:**
- If a connector consistently fails (e.g., Google API down): Disable connector temporarily, notify affected users, provide ETA for fix

---

### Risk 5: Security Breach (Data Leak)

**Risk Level:** 🔴 LOW (if mitigated properly) / 🔴🔴🔴 CATASTROPHIC (if it happens)

**Description:**
- Attacker gains access to database or API
- Customer data leaked (documents, search queries, credentials)
- Reputational damage, lawsuits, regulatory fines (GDPR: up to 4% of revenue)

**Impact:**
- **Legal:** GDPR fines, lawsuits
- **Reputational:** Loss of trust, customers leave
- **Financial:** Incident response costs, potential shutdown

**Mitigation Strategies:**

1. **Defense in depth:**
   - Multiple layers of security (encryption, access control, monitoring)
   - If one layer fails, others still protect

2. **Security audits:**
   - **Quarterly penetration testing** (hire external security firm)
   - **Annual security audit** (review code, infrastructure, policies)

3. **Dependency updates:**
   - **Weekly automated updates** (Dependabot)
   - **Critical vulnerabilities:** Fix within 24 hours

4. **Bug bounty program:**
   - Reward security researchers for responsible disclosure
   - Platforms: HackerOne, Bugcrowd
   - Start at $500 for critical bugs

5. **Incident response plan:**
   - **Documented playbook:** Who to call, how to contain, how to notify customers
   - **Tested:** Run tabletop exercises quarterly
   - **Cyber insurance:** $1M+ coverage

6. **Monitoring & intrusion detection:**
   - **AWS GuardDuty:** Detects unusual API activity
   - **Audit logs:** Review monthly for suspicious activity (e.g., 1000 failed logins from single IP)

**Monitoring:**
- **Security scanning:** CI/CD pipeline (Trivy, Snyk)
- **Intrusion detection:** AWS GuardDuty alerts
- **Audit log review:** Monthly (automate anomaly detection)

**Contingency Plan (If Breach Occurs):**
1. **Contain:** Isolate affected systems (block IPs, revoke tokens)
2. **Investigate:** Determine scope (what data accessed, how many customers affected)
3. **Notify:** Within 72 hours (GDPR requirement), be transparent
4. **Remediate:** Fix vulnerability, rotate all credentials
5. **Post-mortem:** Document lessons learned, improve security

---

### Risk 6: Scaling Bottlenecks

**Risk Level:** 🟡 MEDIUM

**Description:**
- System designed for 100 users, but suddenly 1000 users sign up
- Database, API, or vector DB can't handle load
- Performance degrades (slow searches, timeouts, errors)

**Impact:**
- **Product:** Poor UX, downtime
- **Growth:** Can't onboard new customers (hitting capacity limits)

**Mitigation Strategies:**

1. **Load testing:**
   - **Monthly:** Simulate 10× current traffic
   - **Tools:** Locust (Python), k6 (Go)
   - **Target:** Identify bottlenecks before they hit production

2. **Horizontal scaling:**
   - **Stateless services:** Backend API, workers (easy to scale)
   - **Auto-scaling:** ECS Fargate auto-scales based on CPU/memory

3. **Database optimization:**
   - **Read replicas:** PostgreSQL read replicas for read-heavy queries
   - **Connection pooling:** PgBouncer (reduce connection overhead)
   - **Query optimization:** Index slow queries

4. **Caching (offload databases):**
   - **Redis:** Cache frequently accessed data (user profiles, org settings)
   - **CDN:** Cloudflare for static assets

5. **Queue system:**
   - **Async processing:** Heavy tasks (data sync, embedding generation) go to queue
   - **Celery workers:** Scale workers independently from API

**Monitoring:**
- **Load tests:** Run monthly, track P95 latency trends
- **Capacity planning:** Project usage 3 months ahead
- **Alerts:** CPU >80%, memory >85%, queue depth >1000

**Contingency Plan:**
- If load suddenly spikes: Auto-scale backend (2 → 10 containers), add PostgreSQL read replica, enable aggressive caching

---

## 12. MVP vs FUTURE STATE

### MVP Scope (Months 1-3)

**Goal:** Validate product-market fit with 10-15 beta customers

**Must Have (In Scope):**

✅ **5 Data Connectors:**
- Salesforce (CRM)
- Slack (communication)
- Google Drive (documents)
- Notion (knowledge base)
- Gmail (emails - metadata only by default)

✅ **Core Features:**
- Semantic search (RAG pipeline)
- Natural language queries
- Source attribution (links to original docs)
- Basic knowledge graph (entities + relationships)
- Search history

✅ **Authentication & Authorization:**
- Email/password login
- 3 roles (Admin, User, Viewer)
- Org-level multi-tenancy

✅ **UI:**
- Web application (responsive)
- Search interface
- Data source management (connect/disconnect, sync status)
- User settings

✅ **Security:**
- Encryption (at rest + in transit)
- OAuth for connectors
- RBAC

✅ **Deployment:**
- Staging + production environments
- CI/CD pipeline (automated tests, deployment)
- Monitoring (errors, performance)

---

**Intentionally Excluded (Out of Scope for MVP):**

❌ **Advanced features:**
- Custom connectors (user-built)
- Advanced analytics/dashboards
- Saved queries + alerts
- Workflow automation
- API for developers

❌ **Enterprise features:**
- SSO/SAML
- SOC 2 certification
- Multi-region deployment
- White-label
- Dedicated instances

❌ **Additional connectors:**
- Zendesk, Jira, HubSpot, Confluence, etc. (add in Phase 2)

❌ **Mobile apps:**
- iOS, Android (future)

❌ **Self-service onboarding:**
- MVP: Founder does setup calls with each customer (learn, iterate)
- Future: Automated onboarding flow

---

**Success Criteria for MVP:**

**Technical:**
- ✅ Uptime >99% (max 7 hours downtime/month)
- ✅ Search response time <3s (P95)
- ✅ Data sync success rate >95%
- ✅ Zero critical security vulnerabilities

**Product:**
- ✅ 10-15 beta customers actively using daily
- ✅ NPS (Net Promoter Score) >40
- ✅ 5+ customer testimonials/case studies
- ✅ 20+ searches per user per week (engagement)
- ✅ 3+ data sources connected per customer (feature adoption)

**Business:**
- ✅ Product-market fit validated (customers love it, willing to pay)
- ✅ 15-25% trial → paid conversion rate
- ✅ <5% monthly churn
- ✅ Clear path to €10K MRR within 6 months

---

### Phase 2: Growth (Months 4-6)

**Goal:** Scale to 50-100 paying customers, expand features

**Features:**
- **10 additional connectors:** Zendesk, Jira, HubSpot, Confluence, Linear, Asana, Dropbox, OneDrive, Intercom, Front
- **Self-service onboarding:** Automated setup flow (no founder involvement)
- **Improved knowledge graph:** Better visualization, entity exploration
- **Usage analytics dashboard:** Show ROI (time saved, searches per team, etc.)
- **API (beta):** Let customers build custom integrations
- **Saved searches + alerts:** Save frequent queries, get alerts on new results

**Infrastructure:**
- Migrate to Weaviate (if vector costs >$200/month)
- PostgreSQL read replicas (for read-heavy workloads)
- Multi-AZ deployment (high availability)

**Team:**
- Hire: 1 backend engineer, 1 frontend engineer
- Founders: Focus on sales, customer success, fundraising

---

### Phase 3: Enterprise-Ready (Months 6-12)

**Goal:** Land enterprise customers, achieve SOC 2 certification

**Features:**
- **20+ total connectors** (most requested by customers)
- **Custom connector builder:** No-code tool for customers to build their own connectors
- **Advanced analytics:** Dashboards, insights, recommendations
- **SSO/SAML:** Enterprise authentication
- **Workflow automation:** Trigger actions based on search results (e.g., "Alert me when churn risk >80%")
- **Slack/Teams bot:** Search from Slack without opening web app

**Infrastructure:**
- SOC 2 Type II certification
- Multi-tenant optimizations (dedicated schemas per customer)
- Multi-region deployment (US + EU)

**Team:**
- Total: 8-10 people (engineering, sales, CS, marketing)
- Raise: Seed round ($2-3M) to fund growth

---

### Long-term Vision (Year 2+)

**Goal:** Become category leader, expand to 1000+ customers

**Features:**
- **50+ connectors + marketplace** (3rd-party developers build connectors)
- **White-label option:** Resell UnifyData.AI as your own product
- **Multi-region:** US, EU, APAC data residency
- **Advanced AI:** Predictive insights ("Customer X likely to churn"), proactive suggestions
- **Workflow automation studio:** No-code workflow builder
- **Mobile apps:** iOS, Android (native)

**Infrastructure:**
- Global CDN (edge computing)
- Kubernetes (advanced orchestration)
- Dedicated instances for enterprise customers

**Business:**
- **ARR:** €10M+
- **Team:** 30-50 people
- **Funding:** Series A ($10-15M) to expand internationally

---

## 13. SUCCESS CRITERIA FOR MVP

### Technical Success Metrics

**Reliability:**
- ✅ **Uptime:** >99.5% (max 3.6 hours downtime/month)
  - Measured: External uptime monitoring (UptimeRobot)
  - Excludes: Planned maintenance (announced 48h ahead)

**Performance:**
- ✅ **Search response time:** <3s (P95), <5s (P99)
  - Measured: API response time (CloudWatch or Datadog)
  - Includes: Vector search + LLM call + graph query
- ✅ **Page load time:** <2s (Lighthouse score >90)
  - Measured: Vercel Analytics

**Data Quality:**
- ✅ **Successful data sync rate:** >95%
  - Measured: (Successful syncs / Total sync attempts) × 100
  - Excludes: User error (invalid credentials)
- ✅ **Search relevance:** >80% of searches return useful results
  - Measured: User feedback ("Was this helpful?" thumbs up/down)

**Security:**
- ✅ **Zero critical security vulnerabilities**
  - Measured: Snyk + Trivy scans, penetration test results
  - Definition: CVSS score >9.0 = critical

**Code Quality:**
- ✅ **Test coverage:** >70%
  - Measured: pytest --cov (backend), Vitest (frontend)
  - Focus: Business logic (not boilerplate)

---

### Product Success Metrics

**Adoption:**
- ✅ **10-15 beta customers** using daily
  - Measured: Active orgs with >10 searches/week
- ✅ **3+ data sources connected** per customer (avg)
  - Measured: Avg connected sources per org
  - Goal: Customers use multiple integrations (not just one)

**Engagement:**
- ✅ **20+ searches per user per week**
  - Measured: Avg searches per active user
  - Definition: Active user = logged in + searched at least once in past 7 days
- ✅ **Weekly active users (WAU):** >70% of total users
  - Measured: (Users who searched in past 7 days / Total users) × 100

**Satisfaction:**
- ✅ **NPS (Net Promoter Score):** >40
  - Measured: Quarterly NPS survey ("How likely are you to recommend UnifyData.AI?")
  - Formula: % Promoters (9-10) - % Detractors (0-6)
  - Benchmark: >40 is good for B2B SaaS
- ✅ **5+ customer testimonials/case studies**
  - Measured: Written testimonials + case studies published on website
  - Goal: Social proof for marketing

**Retention:**
- ✅ **Monthly churn:** <5%
  - Measured: (Customers lost in month / Customers at start of month) × 100
  - Goal: Low churn = product-market fit

---

### Business Success Metrics

**Product-Market Fit:**
- ✅ **Customers love it** (qualitative feedback)
  - Measured: Customer interviews ("Would you be disappointed if UnifyData.AI went away?" >40% say "very disappointed")
  - Measured: Testimonials, referrals, word-of-mouth

**Conversion:**
- ✅ **Trial → paid conversion:** 15-25%
  - Measured: (Paying customers / Trial signups) × 100
  - Benchmark: 15-20% is good for B2B SaaS with 14-day trial

**Revenue:**
- ✅ **Clear path to €10K MRR** within 6 months
  - Measured: Monthly recurring revenue (MRR)
  - Target: 15 customers at €799/month (Professional plan) = €11,985 MRR

**Growth:**
- ✅ **10-15% month-over-month customer growth**
  - Measured: (Customers this month - Customers last month) / Customers last month × 100

---

## NEXT STEPS AFTER MVP

**Month 3 (End of MVP):**
1. **Retrospective:** What worked, what didn't?
2. **Customer feedback analysis:** Top feature requests, pain points
3. **Roadmap prioritization:** Decide what to build in Phase 2 based on feedback
4. **Hiring plan:** When to hire next engineer?

**Month 4-6 (Phase 2):**
1. **Expand connectors:** Add top 5 requested connectors (based on customer survey)
2. **Self-service onboarding:** Reduce founder's manual setup work
3. **Scale infrastructure:** Migrate to Weaviate (if needed), add read replicas
4. **Iterate on product:** Polish UI, improve search relevance, add requested features

**Month 6+ (Fundraising):**
1. **Prepare for Seed round:** Financial model, pitch deck, investor outreach
2. **Metrics to hit before fundraising:**
   - €10K+ MRR
   - 50+ paying customers
   - <5% churn
   - Strong NPS (>50)
   - Clear growth trajectory (20%+ MoM growth)

---

**END OF TECHNICAL ARCHITECTURE DOCUMENTATION**

---

## Summary

This document (Part 3) covered:

1. **Security Architecture:** Encryption, access control, API security, compliance (GDPR, SOC 2)
2. **Infrastructure & Deployment:** Cloud strategy, architecture diagram, compute resources, Docker, CI/CD
3. **Monitoring & Observability:** Error tracking (Sentry), logging, metrics, alerting, uptime monitoring
4. **Development Environment:** Local setup, code organization, best practices (linting, testing, git workflow)
5. **Technical Risks & Mitigations:** 6 key risks (vector DB costs, LLM costs, performance, connector failures, security, scaling)
6. **MVP vs Future State:** Phase roadmap (MVP → Phase 2 → Phase 3 → Long-term)
7. **Success Criteria:** Technical, product, and business metrics for MVP

**You now have a complete technical blueprint for building UnifyData.AI MVP!** 🚀

Ready to start coding! 💻
