# Technical Architecture - Part 1

**UnifyData.AI - Enterprise Data Intelligence Platform MVP**
*"All Your Data, One Question Away"*

**Document Version:** 1.0
**Last Updated:** January 2025
**Target Audience:** Engineering team, technical co-founders, technical advisors

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Frontend Architecture](#2-frontend-architecture)
3. [Backend Architecture](#3-backend-architecture)

---

## 1. SYSTEM OVERVIEW

### High-Level Architecture

UnifyData.AI follows a modern **3-tier architecture** designed for scalability, security, and developer productivity:

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND TIER                            │
│  Next.js 14 (App Router) + React + Tailwind + shadcn/ui        │
│  - Web Application (responsive)                                  │
│  - Search Interface                                              │
│  - Data Source Management                                        │
│  - Knowledge Graph Visualization                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS/REST API
                       │ WebSocket (real-time)
┌──────────────────────▼──────────────────────────────────────────┐
│                        BACKEND TIER                              │
│  Python + FastAPI (Async)                                        │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐           │
│  │ Auth Service │ │ Connector     │ │ Search       │           │
│  │              │ │ Service       │ │ Service      │           │
│  └──────────────┘ └───────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌───────────────┐                            │
│  │ Ingestion    │ │ Indexing      │                            │
│  │ Service      │ │ Service       │                            │
│  └──────────────┘ └───────────────┘                            │
│                                                                  │
│  Background Workers (Celery + Redis)                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL  │  │ Pinecone     │  │ Neo4j        │          │
│  │ (Metadata)  │  │ (Vectors)    │  │ (Graph)      │          │
│  └─────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐           │
│  │ AWS S3 / Cloudflare R2 (Object Storage)        │           │
│  └─────────────────────────────────────────────────┘           │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐           │
│  │ Redis (Cache + Queue)                           │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Anthropic    │  │ OpenAI       │  │ Data Sources │         │
│  │ Claude API   │  │ Embeddings   │  │ (Salesforce, │         │
│  │              │  │              │  │  Slack, etc.) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

### Component Interaction Flow

**Typical User Search Flow:**

1. **User enters query** in frontend search interface
2. **Frontend** sends `POST /api/search/query` to Backend API
3. **Search Service** receives request:
   - Validates authentication (JWT)
   - Checks user permissions
   - Generates query embedding (OpenAI)
4. **Vector search** in Pinecone:
   - Semantic similarity search
   - Returns top 20 relevant chunks
5. **Re-ranking & filtering**:
   - Filter by user's accessible data sources
   - Re-rank by relevance + recency
   - Select top 10 chunks
6. **Context assembly**:
   - Retrieve full document metadata from PostgreSQL
   - Assemble context window for LLM
7. **LLM query** (Claude API):
   - Send context + user query
   - Stream response back
8. **Response enrichment**:
   - Extract source citations
   - Query knowledge graph for related entities
9. **Return to frontend**:
   - Streaming response via SSE (Server-Sent Events)
   - Frontend displays answer + sources + graph

**Data Ingestion Flow:**

1. **User connects data source** (e.g., Salesforce)
2. **OAuth flow** handled by Connector Service
3. **Credentials stored** (encrypted) in PostgreSQL
4. **Background job triggered** (Celery):
   - Pull data from source API
   - Transform to unified schema
5. **Document processing**:
   - Extract text, metadata
   - Chunk documents (500-1000 tokens)
6. **Embedding generation** (OpenAI):
   - Batch process chunks
   - Generate 1536-dim vectors
7. **Store in Pinecone**:
   - Vector + metadata (source, timestamp, permissions)
8. **Entity extraction** (Claude):
   - Identify entities (people, companies, products)
   - Extract relationships
9. **Store in Neo4j**:
   - Create nodes + edges
   - Update knowledge graph
10. **Metadata update** (PostgreSQL):
    - Update sync status
    - Log ingestion metrics

---

### Key Design Principles

#### 1. Monolith for MVP, Microservices-Ready

**Decision:** Start with a **modular monolith** architecture.

**Rationale:**
- **Speed:** Faster to develop, deploy, and debug a single codebase for MVP
- **Simplicity:** No distributed system complexity (no service mesh, no inter-service communication overhead)
- **Cost:** Single deployment = lower infrastructure costs
- **Team size:** Small team (2-4 developers) benefits from shared codebase

**Microservices-ready design:**
- Services are **loosely coupled** with clear boundaries
- Each service has its own:
  - Domain logic (in `/services` directory)
  - Data access patterns
  - API endpoints (grouped by service)
- **Future migration path:** Extract services when needed (e.g., when Search Service needs independent scaling)

**When to split:**
- Team grows beyond 8 engineers
- Individual services need different scaling characteristics
- Deployment frequency becomes bottleneck

---

#### 2. Scalability Approach

**Horizontal Scaling Strategy:**

**Frontend (Next.js):**
- Deploy to Vercel or similar serverless platform
- Auto-scales with traffic
- CDN caching for static assets
- Edge functions for API routes (if needed)

**Backend (FastAPI):**
- Containerized (Docker)
- Deploy to Kubernetes or ECS
- Horizontal pod autoscaling (HPA):
  - Scale based on CPU/memory
  - Scale based on request queue depth
- Load balancer (ALB/NLB) distributes traffic

**Background Workers (Celery):**
- Separate worker pools for different task types:
  - `ingestion_workers`: Data pulling + processing
  - `indexing_workers`: Embedding generation
  - `graph_workers`: Knowledge graph updates
- Auto-scale workers based on queue length (Redis queue depth)

**Databases:**
- **PostgreSQL:** Read replicas for read-heavy queries
- **Pinecone:** Managed scaling (handles automatically)
- **Neo4j:** Cluster deployment for HA (high availability)
- **Redis:** Redis Cluster for distributed caching

**Caching Strategy:**
- **Frontend:** SWR (Stale-While-Revalidate) pattern
- **Backend:** Redis caching for:
  - Frequently accessed data (user profiles, org settings)
  - Search results (short TTL, 5-10 minutes)
  - Embeddings of common queries
- **CDN:** Cloudflare for static assets + API caching

**Rate Limiting:**
- Per-user rate limits (based on plan):
  - Starter: 100 queries/day
  - Professional: 500 queries/day
  - Enterprise: Unlimited
- Per-IP rate limits for public endpoints (prevent abuse)

---

#### 3. Security-First Design

**Authentication:**
- JWT tokens (access + refresh)
- Access token: 15 minutes expiry
- Refresh token: 30 days expiry, stored in HTTPOnly cookie
- Token rotation on refresh
- Logout: Blacklist refresh tokens (Redis)

**Authorization:**
- **Role-Based Access Control (RBAC):**
  - `admin`: Full access to org settings + all data
  - `user`: Standard access to connected data sources
  - `viewer`: Read-only access
- **Data-level permissions:** Respect source system permissions
  - If user can't access Salesforce record, they can't search it
  - Permission sync every 6 hours

**Data Encryption:**
- **In transit:** TLS 1.3 for all API calls
- **At rest:**
  - Database encryption (PostgreSQL native encryption)
  - Object storage encryption (S3 server-side encryption)
  - Secrets encrypted with KMS (AWS KMS or Vault)
- **Credentials:** OAuth tokens encrypted with Fernet (Python cryptography)

**API Security:**
- CORS: Whitelist frontend domains only
- CSRF protection: SameSite cookies + CSRF tokens
- Input validation: Pydantic models for all API inputs
- SQL injection prevention: ORMs only (SQLAlchemy)
- Rate limiting: Redis-based rate limiter

**Compliance:**
- **GDPR:**
  - User data deletion: Cascade deletes across all DBs
  - Data export: JSON export of user's data
  - Consent management: Explicit consent for data indexing
- **SOC 2 (future):** Audit logging for all data access
- **ISO 27001 (future):** Security controls documentation

---

#### 4. API-First Architecture

**Principles:**
- Backend is **pure API** (no server-side rendering)
- Frontend consumes APIs via REST (and WebSocket for real-time)
- **OpenAPI spec** (auto-generated by FastAPI) is source of truth
- All features accessible via API (enables future mobile apps, CLI, integrations)

**API Versioning:**
- URL-based versioning: `/api/v1/search/query`
- Maintain backward compatibility for 6 months after new version
- Deprecation warnings in response headers

**API Documentation:**
- Auto-generated Swagger UI: `/docs`
- ReDoc: `/redoc`
- Public API docs for enterprise customers (future)

**API Response Format:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "req_abc123"
  },
  "error": null
}
```

**Error Format:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query cannot be empty",
    "details": { ... }
  }
}
```

---

### Technology Stack Summary

| Layer | Technology | Purpose | Why This Choice |
|-------|-----------|---------|-----------------|
| **Frontend** | Next.js 14 | Web framework | SSR, routing, API routes, modern React |
| | React 18 | UI library | Component-based, huge ecosystem |
| | Tailwind CSS | Styling | Utility-first, fast development |
| | shadcn/ui | Component library | Accessible, customizable, copy-paste |
| | TanStack Query | Server state | Caching, sync, mutations |
| | React Context | Client state | Simple state needs |
| **Backend** | Python 3.11+ | Language | AI/ML ecosystem, async support |
| | FastAPI | API framework | Fast, async, auto docs, type hints |
| | Pydantic | Validation | Type-safe request/response models |
| | SQLAlchemy | ORM | PostgreSQL interaction |
| | Celery | Task queue | Background jobs, distributed workers |
| **Data Storage** | PostgreSQL 15+ | Relational DB | User data, metadata, transactional |
| | Pinecone | Vector DB | Semantic search, managed scaling |
| | Neo4j | Graph DB | Knowledge graph, relationships |
| | Redis 7+ | Cache + Queue | Session cache, Celery queue |
| | S3/R2 | Object storage | Documents, files, attachments |
| **AI/ML** | Anthropic Claude | LLM | Reasoning, RAG, response generation |
| | OpenAI Embeddings | Vector embeddings | text-embedding-3-large model |
| **Infrastructure** | Docker | Containerization | Consistent environments |
| | Kubernetes/ECS | Orchestration | Container management, scaling |
| | GitHub Actions | CI/CD | Automated testing + deployment |
| | AWS/GCP/Azure | Cloud provider | Compute, storage, networking |
| **Monitoring** | Sentry | Error tracking | Exception monitoring |
| | DataDog/Grafana | Metrics + logs | System health, performance |
| | PostHog | Product analytics | User behavior, feature usage |

---

## 2. FRONTEND ARCHITECTURE

### Framework Choice

**Decision: Next.js 14 (App Router)**

**Why Next.js:**
1. **Server-Side Rendering (SSR):** Fast initial page loads, great for SEO (important for marketing site + blog)
2. **App Router:** Modern, file-based routing with Server Components (reduces JavaScript bundle size)
3. **API Routes:** Built-in API endpoints for BFF (Backend-for-Frontend) pattern if needed
4. **Image Optimization:** Automatic image optimization with `<Image>` component (faster loading)
5. **Developer Experience:** Fast refresh, TypeScript support, great documentation
6. **Deployment:** Vercel deployment is seamless (but can deploy anywhere)
7. **Ecosystem:** Huge React ecosystem, easy to hire developers

**Alternatives Considered:**

| Framework | Pros | Cons | Why Not Chosen |
|-----------|------|------|----------------|
| **Vue.js (Nuxt 3)** | Easy to learn, great docs | Smaller ecosystem than React | Team more familiar with React |
| **SvelteKit** | Fastest performance, smallest bundles | Smaller ecosystem, fewer devs | Less mature for enterprise apps |
| **Remix** | Great UX patterns, nested routing | Newer (less battle-tested) | Next.js more proven at scale |

---

### UI Component Library

**Decision: shadcn/ui + Tailwind CSS**

**Why shadcn/ui + Tailwind:**
1. **Customizable:** Components are copy-pasted into your codebase (not npm dependency), so you own the code
2. **Accessible:** Built on Radix UI primitives (WCAG 2.1 compliant, keyboard navigation, screen reader support)
3. **Modern Design:** Clean, professional aesthetic suitable for enterprise SaaS
4. **Tailwind Integration:** Seamless integration with Tailwind's utility-first approach
5. **No Bundle Bloat:** Only include components you use (tree-shakeable)
6. **Rapid Development:** Pre-built components (buttons, forms, modals, etc.) accelerate UI development
7. **Dark Mode:** Built-in dark mode support (important for developer tools)

**Alternatives Considered:**

| Library | Pros | Cons | Why Not Chosen |
|---------|------|------|----------------|
| **Material UI** | Comprehensive, widely used | Heavy bundle size, harder to customize | Too opinionated, "Google" aesthetic |
| **Chakra UI** | Easy to use, great DX | Less customizable, larger bundle | shadcn/ui gives more control |
| **Ant Design** | Enterprise-focused, lots of components | Very opinionated, "Chinese" aesthetic | Design doesn't fit our brand |

---

### State Management

**Decision: React Context + TanStack Query (React Query)**

**Why This Combination:**

**Server State (TanStack Query):**
- Handles all **server-side data** (user profile, data sources, search results)
- **Automatic caching:** No need to manually cache API responses
- **Automatic refetching:** Keeps data fresh (refetch on window focus, network reconnect)
- **Optimistic updates:** Update UI immediately, rollback on error
- **Pagination + infinite scroll:** Built-in support
- **DevTools:** Excellent debugging experience

**Client State (React Context):**
- Handles **local UI state** (theme, sidebar open/closed, active tab)
- **Simple needs:** No complex state logic in MVP
- **Lightweight:** No external dependencies for simple state

**Why Not Redux:**
- **Overkill for MVP:** Redux adds boilerplate and complexity
- **Server state:** TanStack Query handles 80% of state needs
- **When to migrate:** If client state becomes complex (e.g., multi-step forms, undo/redo), consider Zustand (simpler than Redux)

**State Management Pattern:**
```typescript
// Server state (TanStack Query)
const { data: dataSources, isLoading } = useQuery({
  queryKey: ['dataSources'],
  queryFn: fetchDataSources
});

// Client state (React Context)
const { theme, setTheme } = useTheme(); // from ThemeContext
```

---

### Key Pages/Routes

| Route | Description | Auth Required | Key Features |
|-------|-------------|---------------|--------------|
| `/` | Homepage (marketing) | No | Hero, features, pricing, CTA |
| `/login` | Login page | No | Email/password, OAuth (Google, Microsoft) |
| `/signup` | Registration page | No | Email/password, plan selection |
| `/forgot-password` | Password reset | No | Email verification link |
| `/dashboard` | Main dashboard | Yes | Overview, recent searches, activity feed |
| `/search` | Search interface | Yes | Natural language query, results, sources |
| `/data-sources` | Manage connections | Yes | Connect/disconnect sources, sync status |
| `/data-sources/connect/:type` | Connection wizard | Yes | OAuth flow, credential input |
| `/knowledge-graph` | Graph visualization | Yes | Interactive graph, entity explorer |
| `/history` | Search history | Yes | Past queries, saved searches |
| `/settings/profile` | User profile | Yes | Name, email, password, preferences |
| `/settings/organization` | Org settings | Yes (admin) | Org name, billing, members |
| `/settings/billing` | Billing & subscription | Yes (admin) | Plan, payment method, invoices |
| `/settings/api-keys` | API key management | Yes (admin) | Generate, revoke API keys |
| `/admin` | Admin panel | Yes (admin) | User management, analytics, logs |

---

### Frontend Features MVP

**1. User Authentication**
- Email/password login + signup
- OAuth integration (Google, Microsoft) for SSO
- Password reset flow (email verification)
- JWT token management (auto-refresh)
- Session persistence (remember me)

**2. Data Source Connection Wizard**
- Step-by-step wizard for each source type
- OAuth flow handling (redirect to provider, callback)
- Connection status indicators (connected, syncing, error)
- Test connection before saving
- Error handling + retry logic

**3. Natural Language Search Interface**
- Large search input (prominent on page)
- Query suggestions (as user types)
- Search history dropdown (recent queries)
- Filters: date range, data source, content type
- Advanced search toggle (Boolean operators)

**4. Search Results Display**
- Streaming response (show answer as it's generated)
- Source attribution (links to original documents)
- Relevance scoring (visual indicator)
- Result grouping by source type
- Expandable result cards (show full context)

**5. Knowledge Graph Visualization (Basic)**
- Interactive graph using D3.js or Vis.js
- Nodes: Entities (people, companies, documents)
- Edges: Relationships (mentioned in, related to)
- Click to explore entity details
- Filter by entity type

**6. Data Source Management**
- List of connected sources (with icons)
- Sync status + last sync time
- Manual sync trigger
- Disconnect source (with confirmation)
- View sync logs (for debugging)

**7. Search History**
- List of past queries (chronological)
- Saved searches (star to save)
- Delete individual queries
- Export history (CSV)

**8. Settings & Preferences**
- User profile (name, email, avatar)
- Change password
- Notification preferences (email alerts for sync errors)
- Theme toggle (light/dark mode)
- Language selection (future: i18n support)

**9. Organization Management (Admin Only)**
- Invite team members (email invitations)
- User role assignment (admin, user, viewer)
- Remove users
- View org usage (queries per day, data sources connected)

**10. Responsive Design (Mobile-Friendly)**
- Mobile-first CSS (Tailwind breakpoints)
- Hamburger menu for mobile navigation
- Touch-friendly UI elements (large tap targets)
- Progressive Web App (PWA) manifest (future)

---

## 3. BACKEND ARCHITECTURE

### Framework Choice

**Decision: Python 3.11+ with FastAPI**

**Why Python + FastAPI:**

1. **Best AI/ML Ecosystem:**
   - Native support for AI libraries: `langchain`, `openai`, `anthropic`, `transformers`
   - Easy integration with embedding models, LLMs, vector databases
   - Python is lingua franca of AI/ML (most research code is Python)

2. **Async Support:**
   - FastAPI built on `asyncio` + `uvicorn` (async ASGI server)
   - Non-blocking I/O for high concurrency (handle 1000+ concurrent requests)
   - Perfect for I/O-bound workloads (API calls to LLMs, vector DBs, data sources)

3. **Auto-Generated Documentation:**
   - OpenAPI schema auto-generated from code
   - Interactive API docs at `/docs` (Swagger UI)
   - No manual API doc maintenance

4. **Type Safety:**
   - Pydantic models for request/response validation
   - IDE autocomplete + type checking (catch bugs early)
   - Automatic validation errors (returns 422 for invalid input)

5. **Performance:**
   - Benchmarks show FastAPI is **2-3× faster** than Flask/Django
   - Comparable performance to Node.js for I/O-bound tasks
   - Async reduces memory footprint (fewer threads needed)

6. **Developer Experience:**
   - Clean, intuitive API design
   - Hot reload during development
   - Excellent documentation + community

**Why Not Node.js + Express:**

1. **Weaker AI/ML Ecosystem:**
   - Most AI libraries (Hugging Face, LangChain) are Python-first
   - Node.js AI libraries are less mature, less documented
   - Python has better support for custom ML pipelines

2. **Type Safety:**
   - TypeScript helps, but Python's Pydantic is more robust for API validation
   - FastAPI's auto-validation is superior to manual Express validation

3. **Team Skillset:**
   - AI/ML engineers are more familiar with Python
   - Data scientists can contribute to backend code (if needed)

**Note:** Node.js is still great for real-time features (WebSockets, SSE). If we need heavy real-time, we can add a thin Node.js layer later.

---

### API Design

**RESTful API Structure**

Base URL: `https://api.unifydata.ai/v1`

#### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/auth/register` | Create new user account | No |
| `POST` | `/auth/login` | Login with email/password | No |
| `POST` | `/auth/refresh` | Refresh access token | Refresh token |
| `POST` | `/auth/logout` | Logout (blacklist refresh token) | Yes |
| `POST` | `/auth/forgot-password` | Request password reset email | No |
| `POST` | `/auth/reset-password` | Reset password with token | No |

#### Data Source Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/data-sources` | List all connected data sources | Yes |
| `GET` | `/data-sources/{id}` | Get details of specific source | Yes |
| `POST` | `/data-sources/connect` | Initiate connection to new source | Yes |
| `POST` | `/data-sources/{id}/sync` | Manually trigger sync | Yes |
| `DELETE` | `/data-sources/{id}` | Disconnect data source | Yes |
| `GET` | `/data-sources/{id}/status` | Get sync status + logs | Yes |
| `GET` | `/data-sources/types` | List available source types | Yes |

#### Search Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/search/query` | Execute natural language search | Yes |
| `GET` | `/search/history` | Get user's search history | Yes |
| `DELETE` | `/search/history/{id}` | Delete search from history | Yes |
| `POST` | `/search/suggestions` | Get query suggestions (autocomplete) | Yes |
| `POST` | `/search/save` | Save search to favorites | Yes |

#### Knowledge Graph Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/knowledge-graph/entities` | List all entities (paginated) | Yes |
| `GET` | `/knowledge-graph/entities/{id}` | Get entity details + relationships | Yes |
| `GET` | `/knowledge-graph/relationships` | Query relationships by type | Yes |
| `POST` | `/knowledge-graph/explore` | Get subgraph around entity | Yes |

#### User & Organization Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/user/profile` | Get current user profile | Yes |
| `PUT` | `/user/profile` | Update user profile | Yes |
| `PUT` | `/user/password` | Change password | Yes |
| `GET` | `/organization` | Get organization details | Yes |
| `PUT` | `/organization` | Update org settings | Yes (admin) |
| `GET` | `/organization/members` | List org members | Yes |
| `POST` | `/organization/invite` | Invite new member | Yes (admin) |
| `DELETE` | `/organization/members/{id}` | Remove member | Yes (admin) |

---

### Authentication & Authorization

**JWT Token Strategy**

**Token Types:**
1. **Access Token:**
   - Short-lived (15 minutes)
   - Contains: user_id, org_id, role, permissions
   - Sent in `Authorization: Bearer <token>` header
   - Used for API authentication

2. **Refresh Token:**
   - Long-lived (30 days)
   - Stored in HTTPOnly, Secure, SameSite cookie
   - Used to obtain new access token
   - Rotated on each refresh (old token blacklisted)

**Login Flow:**
```python
# 1. User submits email + password
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword123"
}

# 2. Backend validates credentials
# 3. Generate access + refresh tokens
# 4. Response:
{
  "access_token": "eyJhbGc...",  # 15 min expiry
  "token_type": "bearer",
  "expires_in": 900  # seconds
}
# + Set-Cookie header with refresh token (HTTPOnly)
```

**Token Refresh Flow:**
```python
# 1. Access token expires (15 min)
# 2. Frontend detects 401 Unauthorized
# 3. Automatically call refresh endpoint:
POST /auth/refresh
# (Refresh token sent in cookie automatically)

# 4. Backend validates refresh token
# 5. Generate new access token + rotate refresh token
# 6. Response:
{
  "access_token": "newToken123...",
  "expires_in": 900
}
# + Set-Cookie with new refresh token
```

**Storage Approach:**
- **Access Token:** Store in memory (JavaScript variable, not localStorage)
  - Reason: Prevents XSS attacks (localStorage is vulnerable)
  - Trade-off: Token lost on page refresh (just refresh immediately)
- **Refresh Token:** HTTPOnly cookie
  - Reason: JavaScript can't access it (XSS protection)
  - SameSite=Strict (CSRF protection)

**Logout:**
- Blacklist refresh token in Redis (key: token hash, TTL: 30 days)
- Clear access token from memory
- Clear refresh token cookie

---

**Permissions Model**

**3 Roles:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | - Full access to all org data<br>- Manage users (invite, remove, change roles)<br>- Manage billing & subscription<br>- Connect/disconnect data sources<br>- View all audit logs | Founders, IT admins, department heads |
| **User** | - Search across connected data sources<br>- View knowledge graph<br>- Manage own profile<br>- Connect personal data sources (optional)<br>- View own search history | Most employees (sales, CS, ops) |
| **Viewer** | - Search across connected data sources (read-only)<br>- View knowledge graph<br>- Cannot connect data sources<br>- Cannot modify settings | External contractors, auditors, read-only access |

**Permission Enforcement:**
```python
# In FastAPI endpoint:
@router.delete("/organization/members/{user_id}")
async def remove_member(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Remove user logic...
```

**Data-Level Permissions:**
- **Principle:** Users can only search data they have permission to access in source systems
- **Implementation:**
  - When indexing data, store **permission metadata** (e.g., Salesforce record visibility)
  - At search time, filter results by user's permissions
  - Re-sync permissions every 6 hours (background job)

**Example:** If a Salesforce Opportunity is "Private" and user doesn't have access, that Opportunity won't appear in their search results.

---

**SSO Preparation (Future)**

**For Enterprise Plan:**
- SAML 2.0 integration (Okta, Azure AD, OneLogin)
- SCIM for user provisioning
- Just-In-Time (JIT) provisioning (auto-create user on first SSO login)

**Architecture Preparation:**
- Abstract authentication logic into `AuthService` class
- Easy to add new auth providers (OAuth, SAML) without changing core logic

---

### Core Backend Services

**Modular Monolith Structure:**

All services live in the same codebase but are logically separated:

```
backend/
├── api/                     # FastAPI app + routes
│   ├── auth.py             # Auth endpoints
│   ├── data_sources.py     # Data source endpoints
│   ├── search.py           # Search endpoints
│   ├── knowledge_graph.py  # Graph endpoints
│   └── user.py             # User/org endpoints
├── services/                # Business logic (services)
│   ├── auth_service.py
│   ├── connector_service.py
│   ├── ingestion_service.py
│   ├── indexing_service.py
│   └── search_service.py
├── models/                  # Database models (SQLAlchemy)
├── schemas/                 # Pydantic schemas (request/response)
├── db/                      # Database clients
│   ├── postgres.py
│   ├── pinecone.py
│   ├── neo4j.py
│   └── redis.py
├── workers/                 # Celery workers (background jobs)
│   ├── ingestion_worker.py
│   ├── indexing_worker.py
│   └── graph_worker.py
├── integrations/            # Data source connectors
│   ├── salesforce.py
│   ├── slack.py
│   ├── google_drive.py
│   ├── notion.py
│   └── gmail.py
└── utils/                   # Utilities (logging, auth helpers, etc.)
```

---

#### 1. Authentication Service

**Responsibilities:**
- User registration + email verification
- Login (email/password) + token generation
- Token validation + refresh
- Password reset flow
- OAuth integration (Google, Microsoft)
- Session management (logout, blacklist)

**Key Technologies:**
- `passlib` (bcrypt) for password hashing
- `python-jose` (JWT) for token generation
- `fastapi-mail` for email verification
- Redis for token blacklist

**Key Methods:**
```python
class AuthService:
    async def register_user(email: str, password: str) -> User
    async def login(email: str, password: str) -> TokenPair
    async def refresh_token(refresh_token: str) -> str
    async def logout(refresh_token: str) -> None
    async def verify_email(token: str) -> bool
    async def reset_password(token: str, new_password: str) -> bool
```

---

#### 2. Data Connector Service

**Responsibilities:**
- Handle OAuth flows for each data source (Salesforce, Slack, Google, etc.)
- Store encrypted credentials in PostgreSQL
- Test connections (validate API access)
- Monitor connection health (periodic health checks)
- Handle credential refresh (OAuth token refresh)

**Key Technologies:**
- `authlib` for OAuth 2.0 flows
- `cryptography` (Fernet) for credential encryption
- Individual SDKs for each source (e.g., `simple-salesforce`, `slack-sdk`)

**Key Methods:**
```python
class ConnectorService:
    async def initiate_oauth_flow(source_type: str, org_id: str) -> str  # Returns OAuth URL
    async def handle_oauth_callback(code: str, state: str) -> DataSource
    async def test_connection(data_source_id: str) -> bool
    async def refresh_credentials(data_source_id: str) -> None
    async def disconnect(data_source_id: str) -> None
```

**Supported Sources (MVP):**
- Salesforce (OAuth 2.0)
- Slack (OAuth 2.0)
- Google Drive (OAuth 2.0)
- Notion (OAuth 2.0)
- Gmail (OAuth 2.0)

---

#### 3. Data Ingestion Service

**Responsibilities:**
- Pull data from connected sources via APIs
- Transform data to unified schema (normalize structure)
- Handle incremental syncs (only fetch new/updated data)
- Process different data types (documents, emails, CRM records, messages)
- Error handling + retry logic (exponential backoff)

**Key Technologies:**
- `celery` for background jobs (async data pulling)
- Source-specific SDKs (`simple-salesforce`, `slack-sdk`, etc.)
- `python-dateutil` for date parsing
- Redis for job queue

**Key Methods:**
```python
class IngestionService:
    async def sync_data_source(data_source_id: str) -> SyncResult
    async def incremental_sync(data_source_id: str, since: datetime) -> SyncResult
    async def process_salesforce_records(records: List[Dict]) -> List[Document]
    async def process_slack_messages(messages: List[Dict]) -> List[Document]
    async def process_google_drive_files(files: List[Dict]) -> List[Document]
```

**Unified Document Schema:**
```python
@dataclass
class Document:
    id: str                    # Unique ID
    source_type: str           # "salesforce", "slack", etc.
    source_id: str             # Original ID in source system
    title: str                 # Document title
    content: str               # Full text content
    metadata: Dict[str, Any]   # Source-specific metadata
    created_at: datetime
    updated_at: datetime
    author: Optional[str]      # Creator/author
    permissions: List[str]     # User IDs who can access
```

---

#### 4. Indexing Service

**Responsibilities:**
- Generate embeddings for documents (via OpenAI API)
- Chunk large documents (semantic chunking strategy)
- Store embeddings + metadata in Pinecone
- Update index on document changes (update/delete)
- Batch processing (process 100s of docs efficiently)

**Key Technologies:**
- `openai` SDK for embeddings API
- `langchain` for text chunking utilities
- `pinecone-client` for vector DB
- Celery for background processing

**Key Methods:**
```python
class IndexingService:
    async def index_document(document: Document) -> None
    async def batch_index(documents: List[Document]) -> None
    async def generate_embedding(text: str) -> List[float]
    async def chunk_document(document: Document) -> List[Chunk]
    async def update_index(document_id: str, new_content: str) -> None
    async def delete_from_index(document_id: str) -> None
```

**Chunking Strategy:**
- **Semantic chunking:** Split by paragraphs, sentences (not just token count)
- **Chunk size:** 500-1000 tokens (balance context vs granularity)
- **Overlap:** 100 tokens overlap between chunks (preserve context)
- Use `langchain.text_splitter.RecursiveCharacterTextSplitter`

---

#### 5. Search Service

**Responsibilities:**
- Process user queries (intent understanding)
- Generate query embeddings
- Perform semantic search in Pinecone (vector similarity)
- Re-rank results by relevance + recency
- Filter by permissions (user can only see accessible data)
- Assemble context for LLM
- Call Claude API (generate answer)
- Extract source citations
- Stream response to frontend

**Key Technologies:**
- `openai` for query embeddings
- `pinecone-client` for vector search
- `anthropic` SDK for Claude API
- `sse-starlette` for Server-Sent Events (streaming)

**Key Methods:**
```python
class SearchService:
    async def search(query: str, user: User, filters: Dict) -> SearchResult
    async def semantic_search(query_embedding: List[float], top_k: int) -> List[Chunk]
    async def rerank_results(chunks: List[Chunk], query: str) -> List[Chunk]
    async def filter_by_permissions(chunks: List[Chunk], user: User) -> List[Chunk]
    async def generate_answer(query: str, context: str) -> AsyncIterator[str]
    async def extract_citations(answer: str, chunks: List[Chunk]) -> List[Citation]
```

**RAG Flow (in code):**
```python
async def search(query: str, user: User):
    # 1. Generate query embedding
    query_embedding = await generate_embedding(query)

    # 2. Semantic search in Pinecone
    chunks = await pinecone.search(query_embedding, top_k=20)

    # 3. Filter by permissions
    accessible_chunks = filter_by_permissions(chunks, user)

    # 4. Re-rank by relevance
    top_chunks = rerank_results(accessible_chunks, query)[:10]

    # 5. Assemble context
    context = "\n\n".join([chunk.content for chunk in top_chunks])

    # 6. Generate answer (streaming)
    async for token in claude.stream(query, context):
        yield token  # Stream to frontend
```

---

**End of Part 1**

---

## Next Steps

**Technical Architecture - Part 2** will include:
- **Data Layer & Storage** (PostgreSQL schema, Pinecone setup, Neo4j graph design)
- **AI/ML Pipeline** (RAG implementation details, embedding strategy, LLM optimization)
- **Data Connectors** (detailed implementation for each of 5 connectors)
- **Infrastructure & Deployment** (Docker, Kubernetes, CI/CD, monitoring)
- **Security & Compliance** (encryption, audit logging, GDPR compliance)

Ready to create Part 2?
