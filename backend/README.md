# UnifyData.AI Backend

FastAPI-based backend for UnifyData.AI enterprise search platform.

## Setup Development Environment

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Virtual environment tool (venv or virtualenv)

### Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your configuration values
   ```

4. **Run database migrations** (Coming soon)
   ```bash
   alembic upgrade head
   ```

5. **Start development server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Running Locally

Development server with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running with Docker

Build Docker image:
```bash
docker build -t unifydata-api .
```

Run container:
```bash
docker run -p 8000:8000 --env-file .env unifydata-api
```

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes and endpoints
│   │   └── routes/       # Route modules
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings and configuration
│   │   └── security.py   # Security utilities (JWT, hashing)
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic schemas for validation
│   ├── services/         # Business logic layer
│   ├── connectors/       # Data source connectors (Salesforce, Slack, etc.)
│   ├── db/               # Database utilities and session management
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
└── .env.example          # Environment variables template
```

## Configuration

All configuration is managed through environment variables defined in `.env` file.

### Core Settings

- `APP_NAME`: Application name (default: "UnifyData.AI")
- `VERSION`: API version (default: "0.1.0")
- `ENVIRONMENT`: Environment (development, staging, production)
- `DEBUG`: Debug mode (True/False)
- `API_V1_PREFIX`: API path prefix (default: "/api/v1")

### Database

- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`

### Redis

- `REDIS_URL`: Redis connection string
  - Format: `redis://host:port/db`

### Authentication

- `JWT_SECRET`: Secret key for JWT token signing (must be secure in production)
- `JWT_ALGORITHM`: JWT algorithm (default: "HS256")
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration (default: 15 minutes)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: 7 days)

### AI Services

- `ANTHROPIC_API_KEY`: Anthropic API key for Claude
- `OPENAI_API_KEY`: OpenAI API key for embeddings

### Vector Database

- `PINECONE_API_KEY`: Pinecone API key
- `PINECONE_ENVIRONMENT`: Pinecone environment

## API Endpoints

### Health & Status

- `GET /`: API information
- `GET /health`: Health check endpoint

### Authentication (Coming soon)

- `POST /api/v1/auth/register`: User registration
- `POST /api/v1/auth/login`: User login
- `POST /api/v1/auth/refresh`: Refresh access token

## Development

### Code Style

This project follows PEP 8 style guidelines. Use tools like:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

### Adding New Routes

1. Create route module in `app/api/routes/`
2. Import and include router in `app/api/routes/__init__.py`
3. Add appropriate tests in `tests/`

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `JWT_SECRET`
- [ ] Configure production database
- [ ] Set up Redis
- [ ] Configure CORS origins properly
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Environment-Specific Settings

Use different `.env` files for different environments:
- `.env.development`
- `.env.staging`
- `.env.production`

## Troubleshooting

### Common Issues

**Connection to database fails**
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Verify database exists

**Import errors**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Port already in use**
- Change port: `uvicorn app.main:app --port 8001`
- Or kill process using port 8000

## Support

For issues and questions:
- Check documentation: `/docs`
- Review logs: Application logs provide detailed error information
- Open an issue on GitHub

## License

Proprietary - All rights reserved
