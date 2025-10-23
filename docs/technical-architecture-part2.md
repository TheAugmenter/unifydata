# Technical Architecture - Part 2

**UnifyData.AI - Enterprise Data Intelligence Platform MVP**
*"All Your Data, One Question Away"*

**Document Version:** 1.0
**Last Updated:** January 2025
**Target Audience:** Engineering team, data engineers, ML engineers

---

## Table of Contents

1. [Data Layer & Storage](#4-data-layer--storage)
2. [AI/ML Pipeline](#5-aiml-pipeline)
3. [Data Connectors](#6-data-connectors-initial-5)
4. [Data Sync & Processing Workflow](#7-data-sync--processing-workflow)

---

## 4. DATA LAYER & STORAGE

### Database Strategy (Multi-Database Approach)

UnifyData.AI uses a **polyglot persistence** strategy: different databases optimized for different data types and access patterns.

**Why Multi-Database:**
- **PostgreSQL:** ACID transactions, complex queries, metadata
- **Vector DB:** High-dimensional similarity search (embeddings)
- **Neo4j:** Graph traversal, relationship queries
- **Redis:** Fast caching, real-time operations
- **S3/R2:** Cheap, scalable object storage

---

#### 1. PostgreSQL (Relational Data)

**Purpose:** User accounts, organizations, data source metadata, transactional data, audit logs

**Version:** PostgreSQL 15+

**Key Tables & Schema:**

**`users` Table:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'user', 'viewer')),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    is_email_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_id ON users(org_id);
```

**`organizations` Table:**
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) NOT NULL CHECK (plan IN ('starter', 'professional', 'enterprise')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    max_data_sources INTEGER,
    max_users INTEGER,
    billing_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
```

**`data_sources` Table:**
```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('salesforce', 'slack', 'google_drive', 'notion', 'gmail')),
    name VARCHAR(255) NOT NULL,
    credentials_encrypted TEXT NOT NULL,  -- Fernet-encrypted JSON
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'connected', 'syncing', 'error', 'disconnected')),
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),
    sync_frequency_minutes INTEGER DEFAULT 30,
    config JSONB,  -- Source-specific config (e.g., selected Slack channels)
    error_message TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_data_sources_org_id ON data_sources(org_id);
CREATE INDEX idx_data_sources_status ON data_sources(status);
CREATE INDEX idx_data_sources_type ON data_sources(type);
```

**`search_history` Table:**
```sql
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    sources_used TEXT[],  -- Array of data source types used
    is_saved BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_timestamp ON search_history(timestamp DESC);
```

**`api_keys` Table:**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA-256 hash of API key
    key_prefix VARCHAR(10) NOT NULL,  -- First 8 chars for identification (e.g., "sk_live_")
    permissions JSONB DEFAULT '{"search": true, "admin": false}',
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_keys_org_id ON api_keys(org_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

**`sync_logs` Table:**
```sql
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('started', 'completed', 'failed')),
    documents_processed INTEGER DEFAULT 0,
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_sync_logs_data_source_id ON sync_logs(data_source_id);
CREATE INDEX idx_sync_logs_started_at ON sync_logs(started_at DESC);
```

**Backup & Replication:**
- **Daily backups** to S3 (automated via pg_dump or AWS RDS snapshots)
- **Read replicas** for read-heavy queries (search history, analytics)
- **Point-in-time recovery** enabled (retain 7 days)

---

#### 2. Vector Database (Embeddings)

**Options Comparison:**

| Feature | Pinecone | Weaviate | Qdrant |
|---------|----------|----------|--------|
| **Type** | Managed SaaS | Open-source | Open-source |
| **Deployment** | Cloud-only | Self-hosted or cloud | Self-hosted or cloud |
| **Performance** | Excellent | Very good | Excellent |
| **Scalability** | Auto-scales | Manual scaling | Manual scaling |
| **Cost (100K vectors)** | ~$70/month | ~$30/month (hosting) | ~$30/month (hosting) |
| **Features** | Metadata filtering, namespaces | Hybrid search, GraphQL | Filtering, payload search |
| **Ease of use** | Very easy (managed) | Moderate (setup required) | Moderate (setup required) |
| **Support** | Enterprise support | Community + paid | Community + paid |

**Recommendation:**
- **MVP (Months 0-6):** **Pinecone**
  - **Why:** Fastest to set up, managed infrastructure, auto-scaling, great DX
  - **Trade-off:** Higher cost at scale (~$140/month for 1M vectors)
- **Scale (Months 6+):** Migrate to **Weaviate** or **Qdrant**
  - **Why:** Lower cost (~$100/month for 1M vectors on self-hosted), more control
  - **When:** When vector count exceeds 1M or cost becomes significant (>$200/month)

---

**Pinecone Schema (MVP):**

```python
# Index configuration
index_name = "unifydata-production"
dimension = 1536  # OpenAI text-embedding-3-large
metric = "cosine"  # Cosine similarity

# Vector metadata structure
metadata = {
    "org_id": "uuid",             # Organization ID (for filtering)
    "source_id": "uuid",          # Data source ID
    "source_type": "salesforce",  # Type: salesforce, slack, google_drive, etc.
    "document_id": "uuid",        # Unique document ID
    "chunk_id": "uuid",           # Chunk ID within document
    "chunk_index": 0,             # Position in document (0, 1, 2, ...)
    "text": "chunk content",      # Original text (for display)
    "title": "document title",    # Document title
    "url": "source URL",          # Link back to source
    "author": "user@example.com", # Creator/author
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "permissions": ["user1", "user2"],  # User IDs with access
}
```

**Query Example:**
```python
import pinecone

# Initialize
pinecone.init(api_key="...")
index = pinecone.Index("unifydata-production")

# Query
query_embedding = [0.1, 0.2, ...]  # 1536-dimensional vector
results = index.query(
    vector=query_embedding,
    top_k=20,
    include_metadata=True,
    filter={
        "org_id": {"$eq": "org-uuid"},
        "source_type": {"$in": ["salesforce", "slack"]},
        "permissions": {"$in": ["user-uuid"]}
    }
)
```

**Migration Path to Weaviate:**
- Export vectors + metadata from Pinecone (batch API)
- Import into Weaviate (batch import)
- Update application code (swap Pinecone SDK with Weaviate SDK)
- Test thoroughly (ensure query results match)
- Cutover (update DNS/config)

---

#### 3. Graph Database (Knowledge Graph)

**Recommendation: Neo4j Community Edition**

**Why Neo4j:**
- **Industry standard** for graph databases (most mature)
- **Cypher query language:** Intuitive, SQL-like syntax for graphs
- **Visualization tools:** Built-in Neo4j Browser for exploring graphs
- **Performance:** Optimized for graph traversals (millions of nodes/edges)
- **Community:** Large ecosystem, plugins, support

**Alternatives:**
- **Amazon Neptune:** Managed service, but more expensive + vendor lock-in
- **ArangoDB:** Multi-model (graph + document), but less mature for pure graph use cases

---

**Graph Schema:**

**Node Types:**

1. **Person**
   - Properties: `id`, `name`, `email`, `title`, `company`
   - Example: John Doe, VP of Sales at Acme Corp

2. **Company**
   - Properties: `id`, `name`, `domain`, `industry`, `size`
   - Example: Acme Corp, SaaS, 500 employees

3. **Document**
   - Properties: `id`, `title`, `type`, `url`, `source_type`, `created_at`
   - Example: "Q4 Sales Report", PDF, Salesforce

4. **Product**
   - Properties: `id`, `name`, `category`, `price`
   - Example: UnifyData.AI Enterprise Plan

5. **Project**
   - Properties: `id`, `name`, `status`, `start_date`, `end_date`
   - Example: "Website Redesign", In Progress

6. **Topic** (extracted concepts)
   - Properties: `id`, `name`, `category`
   - Example: "Data Unification", Technology

**Relationship Types:**

1. **MENTIONED_IN** (Entity → Document)
   - Properties: `frequency`, `timestamp`
   - Example: "Acme Corp" MENTIONED_IN "Q4 Sales Report"

2. **CREATED_BY** (Document → Person)
   - Properties: `timestamp`
   - Example: "Q4 Sales Report" CREATED_BY "John Doe"

3. **WORKS_FOR** (Person → Company)
   - Properties: `start_date`, `title`
   - Example: "John Doe" WORKS_FOR "Acme Corp"

4. **RELATED_TO** (Document → Document)
   - Properties: `similarity_score`, `relationship_type`
   - Example: "Q4 Sales Report" RELATED_TO "Q3 Sales Report"

5. **ASSOCIATED_WITH** (Product → Company)
   - Properties: `relationship_type` (customer, prospect, partner)
   - Example: "Enterprise Plan" ASSOCIATED_WITH "Acme Corp"

6. **PART_OF** (Document → Project)
   - Properties: `timestamp`
   - Example: "Design Mockups" PART_OF "Website Redesign"

---

**Cypher Query Examples:**

**Find all documents mentioning a company:**
```cypher
MATCH (c:Company {name: "Acme Corp"})<-[:MENTIONED_IN]-(d:Document)
RETURN d.title, d.type, d.created_at
ORDER BY d.created_at DESC
LIMIT 10;
```

**Find related people (colleagues):**
```cypher
MATCH (p1:Person {email: "john@acme.com"})-[:WORKS_FOR]->(c:Company)<-[:WORKS_FOR]-(p2:Person)
RETURN p2.name, p2.email, p2.title;
```

**Find documents related to a topic:**
```cypher
MATCH (t:Topic {name: "Data Unification"})<-[:TAGGED_WITH]-(d:Document)
RETURN d.title, d.source_type, d.url
ORDER BY d.created_at DESC
LIMIT 20;
```

**Find knowledge path between two entities:**
```cypher
MATCH path = shortestPath(
  (e1:Company {name: "Acme Corp"})-[*..5]-(e2:Product {name: "Enterprise Plan"})
)
RETURN path;
```

---

**Data Ingestion to Graph:**

1. **Entity Extraction** (using Claude API):
   - Send document text to Claude
   - Prompt: "Extract entities (people, companies, products, topics) and relationships from this text"
   - Parse structured response (JSON)

2. **Create/Update Nodes:**
   - Check if entity exists (MERGE query)
   - Update properties if changed

3. **Create Relationships:**
   - Link entities based on extraction (e.g., Person WORKS_FOR Company)
   - Store relationship metadata (timestamp, confidence score)

4. **Deduplicate Entities:**
   - Use fuzzy matching for names (e.g., "Acme Corp" vs "Acme Corporation")
   - Merge duplicate nodes

---

#### 4. Object Storage (Files & Documents)

**Recommendation: AWS S3 or Cloudflare R2**

**Comparison:**

| Feature | AWS S3 | Cloudflare R2 |
|---------|--------|---------------|
| **Pricing (storage)** | $0.023/GB/month | $0.015/GB/month (35% cheaper) |
| **Egress (data out)** | $0.09/GB | **FREE** (huge savings) |
| **API compatibility** | S3 API (native) | S3-compatible API |
| **Reliability** | 99.99% SLA | 99.9% SLA |
| **Best for** | Full AWS ecosystem | High egress scenarios |

**Recommendation:**
- **MVP:** AWS S3 (if using AWS for everything else)
- **Cost optimization:** Cloudflare R2 (free egress saves money at scale)

---

**Bucket Structure:**

```
unifydata-documents/
├── orgs/
│   ├── {org_id}/
│   │   ├── sources/
│   │   │   ├── {source_id}/
│   │   │   │   ├── raw/              # Original files
│   │   │   │   │   ├── {file_id}.pdf
│   │   │   │   │   ├── {file_id}.docx
│   │   │   │   ├── processed/        # Extracted text
│   │   │   │   │   ├── {file_id}.txt
│   │   │   │   │   ├── {file_id}.json  # Metadata
```

**Security:**
- **Private buckets** (no public access)
- **Pre-signed URLs** for temporary access (1-hour expiry)
- **Encryption at rest** (S3 server-side encryption with AES-256)
- **IAM policies:** Fine-grained access control

**Lifecycle Policies:**
- Archive old versions to **Glacier** after 90 days
- Delete raw files after **2 years** (keep only processed text)

---

#### 5. Caching Layer (Redis)

**Purpose:** Speed up repetitive operations, reduce database load

**Version:** Redis 7+

**Use Cases:**

1. **Session Storage**
   - Store user sessions (JWT blacklist, refresh tokens)
   - TTL: 30 days (refresh token expiry)

2. **Query Result Caching**
   - Cache frequent search results
   - Key: `search:{query_hash}:{org_id}`
   - TTL: 1 hour (balance freshness vs performance)

3. **Rate Limiting**
   - Track API calls per user/org
   - Key: `rate_limit:{user_id}:{endpoint}:{minute}`
   - TTL: 1 minute (sliding window)

4. **Job Queue (Celery)**
   - Background task queue (sync jobs, indexing)
   - Celery uses Redis as message broker

5. **User Profile Cache**
   - Cache user data (reduce PostgreSQL reads)
   - Key: `user:{user_id}`
   - TTL: 1 hour

**Configuration:**
```python
# Redis connection
REDIS_URL = "redis://localhost:6379/0"

# Cache example
import redis
r = redis.from_url(REDIS_URL)

# Set with expiry
r.setex("search:abc123", 3600, json.dumps(results))

# Get
cached = r.get("search:abc123")
```

**Deployment:**
- **Development:** Single Redis instance
- **Production:** Redis Cluster (3+ nodes) or managed service (AWS ElastiCache, Redis Cloud)

---

## 5. AI/ML PIPELINE

### LLM Strategy

#### Primary LLM: Anthropic Claude

**Model:** Claude 3.5 Sonnet (`claude-3-5-sonnet-20250122`)

**Why Claude:**
1. **Best reasoning:** Excels at complex, multi-step reasoning (crucial for enterprise queries)
2. **Large context:** 200K token context window (can fit more retrieved chunks)
3. **Reliability:** Stable API, low downtime, good rate limits
4. **Safety:** Built-in safety features (reduces harmful outputs)
5. **Streaming:** Native support for streaming responses (better UX)

**Pricing:**
- **Input tokens:** $3 per 1M tokens
- **Output tokens:** $15 per 1M tokens
- **Typical query cost:** $0.01-0.05 per search (depends on context size)

**Cost Example (1,000 searches/day):**
- Avg input: 5,000 tokens (context) + 50 tokens (query) = 5,050 tokens
- Avg output: 500 tokens (answer)
- Daily cost: (5,050 × 1,000 × $3/1M) + (500 × 1,000 × $15/1M) = $15.15 + $7.50 = **$22.65/day**
- Monthly cost: **~$680/month** for 30K searches

---

#### Fallback LLM: OpenAI GPT-4

**Model:** GPT-4 Turbo (`gpt-4-turbo-preview`)

**When to Use:**
- Cost optimization (for simple queries, use GPT-3.5 Turbo at $0.50/$1.50 per 1M tokens)
- Specific tasks (e.g., classification, summarization)
- If Claude API is down (failover)

**Pricing:**
- **Input:** $10 per 1M tokens
- **Output:** $30 per 1M tokens
- **More expensive than Claude** (3× input cost, 2× output cost)

---

#### Cost Management

**Strategies:**

1. **Prompt Caching** (Anthropic feature):
   - Cache repeated context (e.g., system prompt, common docs)
   - Reduces input token cost by 90% for cached portions
   - Example: Cache system prompt (500 tokens) → pay once, reuse 1000× = 99.9% savings

2. **Shorter Prompts:**
   - Use concise system prompts (no fluff)
   - Only include relevant chunks (top 5-10, not 20)
   - Compress context (remove redundant info)

3. **Model Routing:**
   - **Simple queries** (e.g., "What is X?") → GPT-3.5 Turbo ($0.50/$1.50 per 1M)
   - **Complex queries** (e.g., "Compare X and Y across 5 dimensions") → Claude 3.5 Sonnet
   - **Classification:** Use smaller models (e.g., query intent detection)

4. **Monitoring & Alerts:**
   - Track cost per query (average, P95, P99)
   - Alert if cost exceeds threshold (e.g., >$0.10 per query)
   - Dashboard: Daily/monthly LLM spend

5. **User Quotas:**
   - Starter plan: 100 queries/day (limit LLM costs to ~$2.50/day)
   - Professional: 500 queries/day (~$12/day)
   - Enterprise: Unlimited (but still monitor for abuse)

---

### RAG Pipeline (5 Steps)

#### Step 1: Document Processing

**Input:** Raw files from data sources (PDFs, DOCX, HTML, emails, Slack messages, etc.)

**Processing Steps:**

1. **Text Extraction:**
   - **PDFs:** Use `pypdf` or `pdfplumber` (handles tables, images with OCR if needed)
   - **DOCX:** Use `python-docx` (preserves formatting, tables)
   - **HTML:** Use `BeautifulSoup4` (extract text, remove scripts/styles)
   - **Emails:** Use `email` library (parse headers, body, attachments)
   - **Slack messages:** JSON parsing (handle threads, formatting)

2. **Text Cleaning:**
   - Remove excessive whitespace, tabs, line breaks
   - Fix encoding issues (UTF-8 normalization)
   - Remove boilerplate (email signatures, footers)
   - Preserve structure (headings, lists, tables → markdown)

3. **Language Detection:**
   - Use `langdetect` library
   - Store language in metadata (for future multilingual support)
   - MVP: Focus on English only

4. **Metadata Extraction:**
   - Title, author, created/updated dates
   - Source information (file path, URL, original system)
   - Permissions (who can access this document)

**Output:** Clean text + metadata (JSON)

```python
{
    "document_id": "uuid",
    "title": "Q4 Sales Report",
    "content": "cleaned text...",
    "metadata": {
        "source_type": "google_drive",
        "source_id": "uuid",
        "author": "john@example.com",
        "created_at": "2025-01-15T10:30:00Z",
        "language": "en",
        "file_type": "pdf",
        "url": "https://drive.google.com/..."
    }
}
```

---

#### Step 2: Text Chunking

**Why Chunk:**
- **Embedding limitations:** Models have max token limits (8K for OpenAI embeddings)
- **Semantic granularity:** Smaller chunks = more precise retrieval
- **Context window:** LLMs have limited context (can't fit 100-page doc)

**Chunking Strategy: Semantic Chunking**

**Not recommended:** Fixed-size chunking (e.g., every 500 tokens)
- Problem: Splits sentences mid-way, loses context

**Recommended:** Semantic chunking (split by meaning)
- Split by paragraphs (preserve semantic units)
- Split by headings (preserve document structure)
- Recursive splitting: If chunk too large, split further

**Tool:** LangChain `RecursiveCharacterTextSplitter`

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # Target size in tokens
    chunk_overlap=100,     # Overlap between chunks (preserve context)
    separators=["\n\n", "\n", ". ", " ", ""],  # Try these in order
    length_function=len    # Token counting function
)

chunks = splitter.split_text(document_text)
```

**Chunk Size:**
- **500-1000 tokens:** Good balance (specific enough, enough context)
- **Too small (< 200):** Too granular, loses context
- **Too large (> 2000):** Too broad, less precise retrieval

**Overlap:**
- **50-100 tokens:** Ensures context isn't lost at chunk boundaries
- Example: If sentence is split across chunks, overlap captures it

**Metadata Preserved:**
- Each chunk stores: `document_id`, `chunk_index`, `title`, `source`, `timestamp`

---

#### Step 3: Embedding Generation

**Model Choice:**

**Primary: OpenAI `text-embedding-3-large`**
- **Dimensions:** 1536
- **Performance:** State-of-the-art (top of MTEB leaderboard)
- **Cost:** $0.13 per 1M tokens (~$0.13 for 100K words)
- **Speed:** ~1000 embeddings/minute

**Alternative (Cost Optimization): `sentence-transformers/all-MiniLM-L6-v2`**
- **Dimensions:** 384
- **Performance:** Good (not SOTA, but acceptable)
- **Cost:** FREE (self-hosted)
- **Speed:** Depends on GPU (100-500 embeddings/sec on V100)
- **Trade-off:** Lower quality (5-10% worse retrieval accuracy)

**Recommendation:**
- **MVP:** OpenAI embeddings (reliable, good quality, no infra)
- **Scale (>1M documents):** Evaluate self-hosted models (cost savings ~$500/month)

---

**Batch Processing:**

```python
import openai

# Batch embed (up to 2048 inputs per request)
texts = ["chunk 1 text...", "chunk 2 text...", ...]  # Up to 2048 chunks
response = openai.embeddings.create(
    model="text-embedding-3-large",
    input=texts
)

embeddings = [item.embedding for item in response.data]
```

**Rate Limiting:**
- OpenAI: 3,000 requests/minute (Tier 2)
- Strategy: Batch as many chunks as possible per request
- Use exponential backoff if rate limited

**Storage:**
- Store embeddings in Pinecone with metadata
- Store original text in metadata (for display in search results)

---

#### Step 4: Semantic Search

**Flow:**

1. **User Query → Embedding**
   ```python
   query = "What is our churn rate for enterprise customers?"
   query_embedding = openai.embeddings.create(
       model="text-embedding-3-large",
       input=query
   ).data[0].embedding
   ```

2. **Vector Similarity Search**
   ```python
   results = pinecone_index.query(
       vector=query_embedding,
       top_k=20,  # Retrieve top 20 candidates
       include_metadata=True,
       filter={
           "org_id": user.org_id,
           "permissions": {"$in": [user.id]}  # Only docs user can access
       }
   )
   ```

3. **Similarity Algorithm:**
   - **Cosine similarity:** Measures angle between vectors (most common)
   - **Dot product:** Faster, equivalent if vectors normalized
   - Pinecone handles this internally (configured at index creation)

4. **Re-Ranking (Improve Precision)**

   **Problem:** Vector search returns semantically similar docs, but may miss:
   - Recency (recent docs more relevant)
   - Source authority (some sources more trustworthy)
   - Keyword match (exact term matching)

   **Solution:** Re-rank top 20 candidates

   ```python
   def rerank(chunks, query, user_preferences):
       scored_chunks = []
       for chunk in chunks:
           score = chunk.similarity_score  # From Pinecone

           # Boost recent documents (exponential decay)
           days_old = (now - chunk.created_at).days
           recency_boost = 1.0 + (0.1 * math.exp(-days_old / 30))

           # Boost keyword match (BM25-style)
           keyword_boost = 1.0
           if query.lower() in chunk.text.lower():
               keyword_boost = 1.2

           # Boost preferred sources (e.g., user trusts Salesforce more)
           source_boost = user_preferences.get(chunk.source_type, 1.0)

           final_score = score * recency_boost * keyword_boost * source_boost
           scored_chunks.append((chunk, final_score))

       # Sort by final score, return top 10
       return sorted(scored_chunks, key=lambda x: x[1], reverse=True)[:10]
   ```

5. **Optional: Cross-Encoder Re-Ranking**
   - Use a cross-encoder model (e.g., `cross-encoder/ms-marco-MiniLM-L-12-v2`)
   - More accurate but slower (requires model inference)
   - Process top 20 candidates, re-rank to top 10
   - Trade-off: +100ms latency, +5-10% accuracy

---

#### Step 5: Response Generation

**Context Assembly:**

```python
# Take top 10 chunks
top_chunks = reranked_results[:10]

# Format context for LLM
context = "\n\n".join([
    f"[Source: {chunk.title} ({chunk.source_type})]\n{chunk.text}"
    for chunk in top_chunks
])
```

**Prompt Structure:**

```python
system_prompt = """You are UnifyData.AI, an enterprise data intelligence assistant.

Your role is to answer questions based on the provided context from the user's connected data sources (Salesforce, Slack, Google Drive, Notion, Gmail).

Guidelines:
- Answer based ONLY on the provided context
- If the context doesn't contain enough information, say so clearly
- Always cite sources using [Source: Title] format
- Be concise but comprehensive
- Use markdown formatting for better readability
"""

user_prompt = f"""Context from connected data sources:

{context}

User Question: {query}

Answer the question based on the context above. Cite specific sources."""

# Call Claude API with streaming
response = anthropic.messages.create(
    model="claude-3-5-sonnet-20250122",
    max_tokens=1024,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}],
    stream=True
)

# Stream tokens to frontend
for chunk in response:
    if chunk.type == "content_block_delta":
        yield chunk.delta.text
```

**Response Streaming:**
- Use Server-Sent Events (SSE) to stream tokens to frontend
- Frontend displays answer as it's generated (better UX)
- Reduces perceived latency (user sees progress)

**Citation Extraction:**
- Parse LLM response for `[Source: ...]` patterns
- Extract source references
- Return as structured data (links to original documents)

```python
citations = []
for chunk in top_chunks:
    if chunk.title in llm_response:
        citations.append({
            "title": chunk.title,
            "url": chunk.url,
            "source_type": chunk.source_type,
            "excerpt": chunk.text[:200] + "..."
        })
```

---

### Embeddings Strategy

**MVP Approach:**

**Use OpenAI Embeddings** (`text-embedding-3-large`)
- **Cost:** ~$0.13 per 1M tokens
- **For 100K documents** (~100M tokens): ~$13 one-time cost
- **Ongoing:** Only embed new/updated documents (~$5-20/month)

**Cost at Scale:**

| Documents | Tokens | One-Time Cost | Monthly Cost (1% change rate) |
|-----------|--------|---------------|-------------------------------|
| 100K | 100M | $13 | $0.13 |
| 1M | 1B | $130 | $1.30 |
| 10M | 10B | $1,300 | $13 |

**When to Switch to Self-Hosted:**
- **Threshold:** >1M documents OR >$100/month in embedding costs
- **Self-hosted option:** `sentence-transformers` on GPU (V100 or A100)
- **Cost comparison:**
  - OpenAI: $130 one-time for 1M docs
  - Self-hosted: ~$500/month GPU + $0 per embedding = Break-even at ~4 months
- **Trade-off:** Self-hosted requires infrastructure management + slightly lower quality

**Migration Path:**
- Keep OpenAI for new documents
- Re-embed old documents with self-hosted model (batch job)
- A/B test quality (measure retrieval accuracy on test queries)
- Gradually shift traffic to self-hosted if quality acceptable

---

## 6. DATA CONNECTORS (Initial 5)

### Connector Architecture Pattern

Each connector implements a common interface:

```python
class BaseConnector(ABC):
    @abstractmethod
    async def authenticate(self) -> bool:
        """Handle OAuth flow, store credentials"""
        pass

    @abstractmethod
    async def sync(self, incremental: bool = True) -> SyncResult:
        """Pull data from source"""
        pass

    @abstractmethod
    async def parse(self, raw_data: Any) -> List[Document]:
        """Transform to unified schema"""
        pass

    @abstractmethod
    async def webhook_handler(self, payload: dict) -> None:
        """Handle real-time updates (if supported)"""
        pass

    async def test_connection(self) -> bool:
        """Verify credentials are valid"""
        pass
```

---

### 1. Salesforce Connector

**Authentication:**

**OAuth 2.0 Flow:**
1. Redirect user to Salesforce OAuth URL:
   ```
   https://login.salesforce.com/services/oauth2/authorize?
       client_id={CLIENT_ID}&
       redirect_uri={REDIRECT_URI}&
       response_type=code&
       scope=api refresh_token offline_access
   ```

2. User authorizes → Salesforce redirects to callback with `code`

3. Exchange code for tokens:
   ```python
   response = requests.post(
       "https://login.salesforce.com/services/oauth2/token",
       data={
           "grant_type": "authorization_code",
           "code": code,
           "client_id": CLIENT_ID,
           "client_secret": CLIENT_SECRET,
           "redirect_uri": REDIRECT_URI
       }
   )
   tokens = response.json()  # access_token, refresh_token, instance_url
   ```

4. **Store credentials** (encrypted in PostgreSQL):
   ```python
   from cryptography.fernet import Fernet

   credentials = {
       "access_token": tokens["access_token"],
       "refresh_token": tokens["refresh_token"],
       "instance_url": tokens["instance_url"]
   }
   encrypted = fernet.encrypt(json.dumps(credentials).encode())
   ```

**Scopes Required:**
- `api`: Access to REST API
- `refresh_token`: Get refresh tokens
- `offline_access`: Refresh tokens don't expire

---

**Data Pulled:**

**Standard Objects:**
- **Account:** Company/organization records
- **Contact:** People records
- **Opportunity:** Sales deals
- **Case:** Customer support tickets
- **Task/Event:** Activities
- **Lead:** Prospective customers

**Custom Objects:** User can select which custom objects to sync

**Fields:** All standard + custom fields (configurable)

**API Used:**
- **REST API:** For metadata, small queries
- **SOQL (Salesforce Object Query Language):** Query data
- **Bulk API 2.0:** For large datasets (>10K records)

---

**Sync Strategy:**

**Full Sync (Initial Connection):**
```python
# Query all records
query = "SELECT Id, Name, Industry, CreatedDate, LastModifiedDate FROM Account"
records = sf_client.query_all(query)
```

**Incremental Sync:**
```python
# Only fetch records modified since last sync
last_sync = data_source.last_sync_at  # From PostgreSQL
query = f"""
    SELECT Id, Name, Industry, CreatedDate, LastModifiedDate
    FROM Account
    WHERE LastModifiedDate > {last_sync.isoformat()}
"""
records = sf_client.query_all(query)
```

**Frequency:**
- Default: Every 15 minutes
- Configurable: 5 min - 24 hours

**Rate Limits:**
- Salesforce limits vary by edition (e.g., Enterprise: 100K API calls/24 hours)
- Implement exponential backoff on 429 errors
- Use Bulk API for large datasets (counts as 1 API call for up to 200K records)

---

**Example Document Transform:**

```python
# Salesforce Account → Unified Document
sf_account = {
    "Id": "001...",
    "Name": "Acme Corp",
    "Industry": "Technology",
    "CreatedDate": "2025-01-01T00:00:00Z",
    "LastModifiedDate": "2025-01-15T10:30:00Z",
    "Owner": {"Name": "John Doe", "Email": "john@example.com"}
}

document = Document(
    id=f"salesforce_account_{sf_account['Id']}",
    source_type="salesforce",
    source_id=sf_account["Id"],
    title=sf_account["Name"],
    content=f"""
        Company: {sf_account["Name"]}
        Industry: {sf_account["Industry"]}
        Created: {sf_account["CreatedDate"]}
        Owner: {sf_account["Owner"]["Name"]}
    """,
    metadata={
        "object_type": "Account",
        "owner": sf_account["Owner"]["Email"],
        "url": f"{instance_url}/{sf_account['Id']}"
    },
    created_at=parse_datetime(sf_account["CreatedDate"]),
    updated_at=parse_datetime(sf_account["LastModifiedDate"]),
    permissions=[sf_account["Owner"]["Email"]]  # Simplified
)
```

---

### 2. Slack Connector

**Authentication:**

**OAuth 2.0 (Bot Token):**
1. Redirect to Slack OAuth:
   ```
   https://slack.com/oauth/v2/authorize?
       client_id={CLIENT_ID}&
       scope=channels:history,channels:read,files:read,users:read&
       user_scope=search:read
   ```

2. User authorizes → Slack redirects with `code`

3. Exchange for token:
   ```python
   response = requests.post(
       "https://slack.com/api/oauth.v2.access",
       data={
           "client_id": CLIENT_ID,
           "client_secret": CLIENT_SECRET,
           "code": code
       }
   )
   tokens = response.json()  # bot_token, team_id
   ```

**Scopes:**
- `channels:history`: Read messages from public channels
- `channels:read`: List channels
- `files:read`: Access shared files
- `users:read`: User profile info

---

**Data Pulled:**

**Public Channels (Default):**
- Messages + threads
- File attachments (metadata + download links)
- Reactions, edits, deletions

**Private Channels/DMs:** Opt-in only (requires explicit user consent)

**User Profiles:** For attribution (name, email, avatar)

---

**API Used:**

**Web API Methods:**
- `conversations.list`: List channels
- `conversations.history`: Fetch messages from channel
- `users.info`: Get user details
- `files.info`: Get file metadata

**Events API (Real-Time):**
- Subscribe to `message` events
- Receive webhook on new messages
- Process immediately (no polling)

---

**Sync Strategy:**

**Full Sync:**
```python
# Fetch last 90 days of messages from all public channels
channels = slack_client.conversations_list()
for channel in channels:
    messages = slack_client.conversations_history(
        channel=channel["id"],
        oldest=(now - timedelta(days=90)).timestamp()
    )
```

**Real-Time Updates:**
- Enable Slack Events API
- Subscribe to `message` event
- Receive webhook payload:
  ```json
  {
    "event": {
      "type": "message",
      "channel": "C123...",
      "user": "U456...",
      "text": "Hello world!",
      "ts": "1234567890.123456"
    }
  }
  ```
- Process message immediately (index within seconds)

---

**Privacy Considerations:**

**Default Behavior:**
- Only index **public channels**
- Exclude private channels, DMs, and group DMs

**Opt-In for Private Data:**
- User explicitly selects which private channels to index
- Requires additional OAuth scope (`groups:history`)
- Clear warning: "Private messages will be searchable by all org members"

**Sensitive Data Filtering:**
- Detect PII (emails, phone numbers, SSNs) using regex
- Redact or exclude from index
- Configurable sensitivity levels

---

### 3. Google Drive Connector

**Authentication:**

**OAuth 2.0:**
1. Redirect to Google OAuth:
   ```
   https://accounts.google.com/o/oauth2/v2/auth?
       client_id={CLIENT_ID}&
       redirect_uri={REDIRECT_URI}&
       scope=https://www.googleapis.com/auth/drive.readonly&
       response_type=code&
       access_type=offline
   ```

2. Exchange code for tokens (access + refresh)

**Scopes:**
- `drive.readonly`: Read-only access to all files
- `drive.metadata.readonly`: Metadata only (no file content)

---

**Data Pulled:**

**File Types:**
- Google Docs, Sheets, Slides (export as text/markdown/CSV)
- PDFs (extract text)
- Images (OCR if needed, future feature)
- Office files (DOCX, XLSX, PPTX) via export

**Metadata:**
- Title, created/modified dates
- Owner, permissions (sharing settings)
- Folder structure

**Comments:** Optional (enable in connector config)

---

**API Used:**

**Drive API v3:**
- `files.list`: List files with filtering
- `files.get`: Get file metadata
- `files.export`: Export Google Docs to text/markdown

**Example:**
```python
# List files modified since last sync
response = drive_service.files().list(
    q=f"modifiedTime > '{last_sync.isoformat()}'",
    fields="files(id, name, mimeType, createdTime, modifiedTime, owners, permissions)"
).execute()

files = response.get("files", [])
```

---

**Sync Strategy:**

**Full Sync:**
- Query all accessible files (user's drive + shared with user)
- Download and process each file

**Incremental Sync:**
- Query by `modifiedTime > last_sync`
- Only process changed files

**Real-Time Updates (Webhooks):**
- Google Drive supports push notifications (webhooks)
- Subscribe to changes:
  ```python
  drive_service.files().watch(
      fileId="root",  # Watch entire drive
      body={
          "type": "web_hook",
          "address": "https://api.unifydata.ai/webhooks/google_drive"
      }
  ).execute()
  ```
- Receive webhook on file changes
- Process immediately

**Frequency:** Every 30 minutes + webhooks

---

**File Processing:**

**Google Docs → Markdown:**
```python
# Export as plain text
content = drive_service.files().export(
    fileId=file_id,
    mimeType="text/plain"
).execute()

# Or export as markdown (custom parsing)
html_content = drive_service.files().export(
    fileId=file_id,
    mimeType="text/html"
).execute()

markdown = html_to_markdown(html_content)
```

**PDFs:**
```python
from pypdf import PdfReader

content = drive_service.files().get_media(fileId=file_id).execute()
pdf = PdfReader(BytesIO(content))
text = "\n".join([page.extract_text() for page in pdf.pages])
```

---

### 4. Notion Connector

**Authentication:**

**OAuth 2.0:**
1. Redirect to Notion OAuth:
   ```
   https://api.notion.com/v1/oauth/authorize?
       client_id={CLIENT_ID}&
       redirect_uri={REDIRECT_URI}&
       response_type=code
   ```

2. Exchange code for access token (Notion uses integration tokens, not refresh tokens)

**Note:** Notion OAuth is workspace-scoped (user grants access to specific pages/databases)

---

**Data Pulled:**

**Content Types:**
- **Pages:** All accessible pages (nested hierarchy)
- **Databases:** Database rows (like tables)
- **Blocks:** Content blocks (text, headings, lists, code, etc.)

**Metadata:**
- Title, created/edited time, created by, last edited by
- Properties (for database rows)

---

**API Used:**

**Notion API v1:**
- `search`: Search all accessible content
- `databases.query`: Query database rows
- `blocks.children.list`: Get page content (blocks)
- `pages.retrieve`: Get page metadata

---

**Sync Strategy:**

**Full Sync:**
```python
# Search all accessible pages
response = notion_client.search(
    filter={"property": "object", "value": "page"}
)

pages = response.get("results", [])
```

**Incremental Sync:**
```python
# Filter by last_edited_time
response = notion_client.search(
    filter={"property": "object", "value": "page"},
    sort={"timestamp": "last_edited_time", "direction": "descending"}
)

# Only process pages edited since last sync
new_pages = [
    page for page in response["results"]
    if parse_datetime(page["last_edited_time"]) > last_sync
]
```

**No Real-Time Webhooks:** Notion doesn't support webhooks yet (poll every 30 min)

---

**Content Processing:**

**Convert Blocks to Markdown:**
```python
def blocks_to_markdown(blocks):
    markdown = []
    for block in blocks:
        if block["type"] == "paragraph":
            text = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
            markdown.append(text)
        elif block["type"] == "heading_1":
            text = "".join([t["plain_text"] for t in block["heading_1"]["rich_text"]])
            markdown.append(f"# {text}")
        elif block["type"] == "bulleted_list_item":
            text = "".join([t["plain_text"] for t in block["bulleted_list_item"]["rich_text"]])
            markdown.append(f"- {text}")
        # ... handle other block types
    return "\n\n".join(markdown)
```

**Database Rows:**
```python
# Query database
response = notion_client.databases.query(database_id=db_id)

for row in response["results"]:
    title = row["properties"]["Name"]["title"][0]["plain_text"]
    # Extract other properties...
```

---

### 5. Gmail Connector

**Authentication:**

**OAuth 2.0:**
1. Redirect to Google OAuth (same as Drive)
2. Scope: `https://www.googleapis.com/auth/gmail.readonly`

---

**Data Pulled:**

**Default (Metadata Only):**
- Subject, from, to, cc, date, labels
- Thread structure
- Attachment metadata (filename, size, type)

**Opt-In (Full Content):**
- Email body (plain text + HTML)
- Attachment content (download files)

**Filters:**
- User selects which labels to index (e.g., only Inbox + Sent)
- Exclude spam, trash

---

**API Used:**

**Gmail API v1:**
- `users.messages.list`: List messages with filtering
- `users.messages.get`: Get message details
- `users.threads.list`: List threads

---

**Sync Strategy:**

**Full Sync:**
```python
# Fetch last 90 days of emails
response = gmail_service.users().messages().list(
    userId="me",
    q=f"after:{(now - timedelta(days=90)).strftime('%Y/%m/%d')}"
).execute()

messages = response.get("messages", [])
```

**Incremental Sync:**
```python
# Fetch emails received since last sync
response = gmail_service.users().messages().list(
    userId="me",
    q=f"after:{last_sync.strftime('%Y/%m/%d')}"
).execute()
```

**Real-Time Updates (Push Notifications):**
```python
# Subscribe to Gmail push notifications
gmail_service.users().watch(
    userId="me",
    body={
        "topicName": "projects/{PROJECT_ID}/topics/{TOPIC_NAME}",
        "labelIds": ["INBOX", "SENT"]
    }
).execute()

# Receive webhook at Pub/Sub endpoint
# Process new emails immediately
```

**Frequency:** Every 15 minutes + push notifications

---

**Privacy & Security:**

**Default Behavior:**
- **Metadata only** (no email body content indexed)
- Indexed: Subject, from, to, date, labels
- Use case: "Find all emails from john@acme.com about 'Q4 report'"

**Opt-In for Full Content:**
- User explicitly enables "Index email content"
- Warning: "Email bodies will be searchable by all org members with access"
- Requires additional OAuth consent

**PII Detection:**
- Scan email bodies for sensitive data (SSNs, credit cards)
- Redact or exclude flagged emails
- Configurable sensitivity levels

---

## 7. DATA SYNC & PROCESSING WORKFLOW

### End-to-End Sync Job Flow

**Trigger:** Scheduled (every 15-30 min) or manual (user clicks "Sync Now")

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SCHEDULER (Celery Beat)                                      │
│    - Cron job checks which sources need sync                    │
│    - Enqueues sync task for each source                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 2. CONNECTOR AUTHENTICATES                                       │
│    - Load encrypted credentials from PostgreSQL                 │
│    - Refresh OAuth token if expired                             │
│    - Test connection (API call to verify credentials valid)     │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 3. FETCH DATA (Incremental or Full)                             │
│    - If first sync: Full sync (all data)                        │
│    - If incremental: Query by last_modified_date > last_sync    │
│    - Handle pagination (large datasets split into pages)        │
│    - Retry on API errors (exponential backoff)                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 4. TRANSFORM TO UNIFIED SCHEMA                                   │
│    - Parse source-specific format (JSON, XML, etc.)             │
│    - Map fields to unified Document schema                      │
│    - Extract metadata (author, timestamps, permissions)         │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 5. STORE RAW DATA (S3)                                          │
│    - Save original files to S3 (for future reprocessing)        │
│    - Path: /orgs/{org_id}/sources/{source_id}/raw/{file_id}    │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 6. EXTRACT TEXT & METADATA                                       │
│    - PDFs: pypdf extraction                                     │
│    - DOCX: python-docx extraction                               │
│    - HTML: BeautifulSoup                                        │
│    - Clean text (remove formatting, fix encoding)               │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 7. CHUNK TEXT                                                    │
│    - Use LangChain RecursiveCharacterTextSplitter               │
│    - Chunk size: 500-1000 tokens, overlap: 100 tokens          │
│    - Preserve metadata in each chunk                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 8. GENERATE EMBEDDINGS (Batch)                                  │
│    - Batch chunks (up to 2048 per API call)                     │
│    - Call OpenAI embeddings API                                 │
│    - Handle rate limits (exponential backoff)                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 9. STORE VECTORS (Pinecone)                                     │
│    - Upsert vectors with metadata                               │
│    - Batch upsert (1000 vectors per request)                    │
│    - Include org_id, source_id, permissions in metadata         │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 10. EXTRACT ENTITIES & RELATIONSHIPS (Optional)                 │
│    - Call Claude API with entity extraction prompt              │
│    - Parse structured response (JSON)                           │
│    - Identify: People, Companies, Products, Topics, etc.        │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 11. UPDATE KNOWLEDGE GRAPH (Neo4j)                              │
│    - Create/update nodes (entities)                             │
│    - Create relationships (MENTIONED_IN, CREATED_BY, etc.)      │
│    - Deduplicate entities (fuzzy matching)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 12. UPDATE METADATA (PostgreSQL)                                │
│    - Update data_source.last_sync_at                            │
│    - Update data_source.status = 'connected'                    │
│    - Log sync metrics (docs processed, added, updated, deleted) │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 13. MARK SYNC COMPLETE                                          │
│    - Create sync_logs entry with metrics                        │
│    - Send notification (if errors occurred)                     │
│    - Update cache (invalidate old search results)               │
└─────────────────────────────────────────────────────────────────┘
```

---

### Error Handling

**1. API Errors (Rate Limits, Timeouts):**
- Retry with exponential backoff (1s, 2s, 4s, 8s, 16s)
- Max retries: 5
- If still failing: Log error, alert admin, mark source as "error" status

**2. Partial Sync Failures:**
- Don't fail entire sync if one document fails
- Log failed document IDs
- Continue processing remaining documents
- Report: "Synced 95/100 documents (5 failed)"

**3. OAuth Token Expiry:**
- Detect 401 Unauthorized errors
- Automatically refresh token using refresh_token
- Retry original request
- If refresh fails: Mark source as "disconnected", notify user to re-authenticate

**4. Connector-Specific Errors:**
- Salesforce API limits exceeded → Pause sync, retry after cooldown period
- Slack rate limit → Use rate limit headers to schedule retries
- Google Drive quota exceeded → Pause sync, notify admin

**5. Logging:**
- Log all errors with context:
  ```python
  logger.error(
      "Failed to sync Salesforce records",
      extra={
          "source_id": source.id,
          "org_id": source.org_id,
          "error": str(e),
          "records_processed": count
      }
  )
  ```

---

### Performance Optimization

**1. Parallel Processing:**
- Sync multiple data sources simultaneously (separate Celery tasks)
- Use asyncio for concurrent API calls within single connector
- Example: Fetch 10 Salesforce objects in parallel

**2. Batch Operations:**
- Embed 100-2048 documents per OpenAI API call (not one-by-one)
- Upsert 1000 vectors per Pinecone request (not individual)
- Batch PostgreSQL inserts (bulk insert 100+ rows)

**3. Avoid Re-Processing Unchanged Docs:**
- Check document hash before processing
- If hash unchanged since last sync → skip embedding generation
- Saves API costs + processing time

**4. Rate Limiting:**
- Respect API rate limits (avoid 429 errors)
- Use token bucket algorithm for self-throttling
- Example: Salesforce Enterprise allows 100K API calls/24h → max 70 calls/min

**5. Caching:**
- Cache frequent API responses (e.g., user profiles, metadata)
- Use Redis with short TTL (5-10 minutes)
- Reduces redundant API calls

---

**End of Technical Architecture - Part 2**

---

## Summary

This document covered:

1. **Data Layer:** Multi-database architecture (PostgreSQL, Pinecone, Neo4j, Redis, S3)
2. **AI/ML Pipeline:** RAG implementation (document processing, chunking, embeddings, semantic search, response generation)
3. **Data Connectors:** Detailed implementation for 5 sources (Salesforce, Slack, Google Drive, Notion, Gmail)
4. **Data Sync Workflow:** End-to-end sync process with error handling and optimization

**Next Steps for Implementation:**

1. Set up PostgreSQL schema (run migration scripts)
2. Create Pinecone index (configure dimensions, metric)
3. Deploy Neo4j instance (Community Edition on Docker)
4. Implement first connector (start with simplest: Notion or Google Drive)
5. Build RAG pipeline (chunking → embeddings → search → LLM)
6. Test end-to-end flow (connect source → sync → search → get answer)

Ready to start building! 🚀
