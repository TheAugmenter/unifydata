# UnifyData.AI - Enterprise AI-Powered Unified Search Platform

UnifyData.AI is an enterprise-grade AI-powered search platform that allows organizations to search across all their business tools (Salesforce, Slack, Google Drive, Notion, Gmail, and more) from a single interface.

## Features

- **Unified Search**: Search across all connected data sources simultaneously
- **AI-Powered Intelligence**: Natural language queries with semantic search
- **Knowledge Graph**: Visualize relationships between entities across data sources
- **Multi-Source Connectors**: Salesforce, Slack, Google Drive, Notion, Gmail support
- **Enterprise Security**: Role-based access control, encryption at rest and in transit
- **Real-time Sync**: Keep your data up-to-date with scheduled syncing

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **Vector DB**: Pinecone
- **Graph DB**: Neo4j
- **Cache**: Redis
- **Task Queue**: Celery
- **AI/ML**: Anthropic Claude 3.5 Sonnet, OpenAI Embeddings

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: TanStack Query + Zustand
- **Forms**: React Hook Form + Zod

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/unifydata-ai.git
cd unifydata-ai
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `JWT_SECRET_KEY`: Generate with `openssl rand -hex 32`
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com
- `OPENAI_API_KEY`: Get from https://platform.openai.com
- `PINECONE_API_KEY`: Get from https://www.pinecone.io

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Neo4j (port 7474, 7687)
- Backend API (port 8000)
- Celery Worker
- Celery Beat

### 4. Set Up Frontend

```bash
cd web
npm install
cp .env.local.example .env.local
npm run dev
```

The frontend will be available at http://localhost:3000

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Neo4j Browser**: http://localhost:7474

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Frontend Development

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Build for production
npm run build
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Project Structure

```
unifydata-ai/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Core utilities (config, security, db)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── main.py          # Application entry point
│   ├── tests/               # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── web/                      # Next.js frontend
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   └── lib/             # Utilities and API client
│   ├── public/              # Static assets
│   └── package.json
├── docs/                     # Documentation
├── docker-compose.yml        # Docker services
└── .env.example             # Environment variables template
```

## API Documentation

### Authentication Endpoints

#### Register New User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "john@company.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "company_name": "Acme Corp"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@company.com",
  "password": "SecurePass123!"
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

Full API documentation is available at http://localhost:8000/api/docs when running the backend.

## Testing

### Backend Tests

```bash
cd backend
pytest                           # Run all tests
pytest tests/test_auth.py       # Run specific test file
pytest --cov=app                # Run with coverage
pytest -v                       # Verbose output
```

### Frontend Tests

```bash
cd web
npm test                        # Run all tests
npm test -- --watch            # Run in watch mode
npm test -- --coverage         # Run with coverage
```

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=false` in `.env`
- [ ] Generate secure `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure production database
- [ ] Set up SSL certificates
- [ ] Configure CORS origins
- [ ] Set up monitoring (Sentry)
- [ ] Configure email service (SendGrid)
- [ ] Set up backup strategy
- [ ] Configure rate limiting
- [ ] Set up CI/CD pipeline

### Deployment Options

- **Backend**: AWS ECS Fargate, Google Cloud Run, or DigitalOcean App Platform
- **Frontend**: Vercel (recommended), Netlify, or AWS Amplify
- **Database**: AWS RDS, Google Cloud SQL, or DigitalOcean Managed Database

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication (15-minute access, 30-day refresh)
- Rate limiting on all API endpoints
- CORS protection
- SQL injection protection via SQLAlchemy ORM
- XSS protection via React
- HTTPS required in production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For support, email support@unifydata.ai or open an issue on GitHub.

## Roadmap

### MVP (Current)
- [x] User authentication & registration
- [x] Basic project structure
- [ ] Onboarding flow
- [ ] Data source connectors (Salesforce, Slack, Google Drive, Notion, Gmail)
- [ ] Natural language search
- [ ] Search results display
- [ ] Knowledge graph visualization

### Phase 2
- [ ] Advanced search filters
- [ ] Team collaboration features
- [ ] API rate limiting & usage tracking
- [ ] Billing & subscription management
- [ ] Analytics dashboard

### Phase 3
- [ ] Custom connectors SDK
- [ ] Webhooks & integrations
- [ ] Advanced AI features (query suggestions, auto-categorization)
- [ ] Mobile app

## Credits

Built with by the UnifyData.AI team.
