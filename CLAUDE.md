# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CashUp** is a professional quantitative trading system built with a microservices architecture. It supports multi-exchange integration, strategy backtesting, real-time monitoring, and intelligent notifications.

## Architecture

### Microservices Structure
- **Frontend**: React 18 + TypeScript + Vite (port 3000)
- **Backend Services**: 8 Python microservices using FastAPI
  - user-service (8001): Authentication and authorization
  - trading-service (8002): Trade execution engine
  - strategy-service (8003): Strategy management and backtesting
  - market-service (8004): Market data and WebSocket connections
  - order-service (8005): Order lifecycle management
  - notification-service (8006): Multi-channel notifications
  - config-service (8007): Configuration management
  - monitoring-service (8008): System monitoring and alerts

### Infrastructure
- **Database**: PostgreSQL 15 (primary) + Redis 7 (caching)
- **Message Queue**: RabbitMQ 3 (management UI at http://localhost:15672)
- **Containerization**: Docker + Docker Compose
- **Package Management**: UV for Python, npm for Node.js

## Development Environment Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- UV (Python package manager)

### Initial Setup
```bash
# 1. Create Python virtual environment
uv venv cashup
source cashup/bin/activate

# 2. Start infrastructure services
docker-compose up -d postgres redis rabbitmq

# 3. Install dependencies
make install
```

### Working with Services
Each microservice is independent. To work on a specific service:
```bash
# Activate virtual environment
source cashup/bin/activate

# Navigate to service directory
cd backend/<service-name>

# Install dependencies (if not using global virtual env)
uv pip install -r requirements.txt

# Start service
uvicorn main:app --reload --host 0.0.0.0 --port <service-port>
```

## Common Development Commands

### Makefile Commands
```bash
make install      # Install all dependencies
make dev          # Start development environment
make build        # Build all Docker images
make up           # Start all services
make down         # Stop all services
make test         # Run all tests
make lint         # Code quality checks
make format       # Format code
make clean        # Clean up containers and images
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev       # Start development server
npm run build     # Build for production
npm run lint      # Run ESLint
```

### Backend Development
```bash
# For any backend service:
cd backend/<service-name>
source ../../cashup/bin/activate
uv pip install -r requirements.txt
uvicorn main:app --reload
```

## Key Technical Details

### Package Management
- **Python**: Uses UV for faster dependency management
- **Virtual Environment**: Named `cashup` in project root
- **Dependencies**: Each service has both `requirements.txt` and `pyproject.toml`

### Database Setup
- PostgreSQL runs in Docker at localhost:5432
- Database name: `cashup`
- Connection pooling with asyncpg
- Migrations managed with Alembic

### WebSocket Integration
- Market data service connects to Gate.io WebSocket
- Real-time notifications via WebSocket
- Frontend uses socket.io-client

### External Integrations
- **Exchange**: Gate.io API (REST + WebSocket)
- **Notifications**: QANotify, WXPusher, PushPlus, Telegram, Email
- **Monitoring**: Prometheus + Grafana

## Code Structure Patterns

### Backend Service Structure
```
backend/<service-name>/
├── main.py              # FastAPI app entry point
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── crud/                # Database operations
├── api/                 # API endpoints
├── services/            # Business logic
├── utils/               # Utility functions
├── requirements.txt     # Dependencies
└── pyproject.toml      # Modern Python project config
```

### Shared Code
- `backend/shared/gateio/` contains shared exchange client code
- Common utilities and configurations are shared across services

## Testing and Quality

### Running Tests
```bash
# All tests
make test

# Individual service tests
cd backend/<service-name>
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

### Code Quality Tools
- **Python**: Black (formatting), isort (imports), flake8 (linting), mypy (types)
- **TypeScript**: ESLint, TypeScript compiler
- **Database**: Alembic for migrations

## Current Development Status

### Completed Features
- ✅ Microservices architecture setup
- ✅ Notification service with multi-channel support
- ✅ Docker containerization
- ✅ UV package management integration
- ✅ Shared library for exchange client

### In Development
- 🔄 Market service WebSocket connection debugging
- 🔄 Trading service implementation
- 🔄 User authentication system

### Known Issues
- Market service has coroutine handling issues with WebSocket connections
- Some services have duplicate exchange client code (being resolved through shared library)

## Environment Configuration

### Environment Variables
- Copy `.env.example` to `.env` and configure:
  - Database credentials
  - API keys for exchanges
  - Notification service credentials
  - JWT secret keys

### Service Ports
- Frontend: 3000
- User Service: 8001
- Trading Service: 8002
- Strategy Service: 8003
- Market Service: 8004
- Order Service: 8005
- Notification Service: 8006
- Config Service: 8007
- Monitoring Service: 8008

## Docker Development

### Building Services
```bash
# Build all services
make build

# Build specific service
docker-compose build <service-name>

# Run with hot reload
docker-compose up -d <service-name>
```

### Database Management
```bash
# Run migrations
make migrate

# Reset database
make reset-db

# Access database directly
docker-compose exec postgres psql -U cashup -d cashup
```

## Performance Considerations

- Use async/await patterns throughout the codebase
- Implement proper connection pooling for database connections
- Cache frequently accessed data in Redis
- Use WebSocket for real-time data streaming
- Monitor service health and performance metrics

## Security Guidelines

- Never commit API keys or sensitive credentials
- Use environment variables for configuration
- Implement proper authentication and authorization
- Validate all user inputs
- Use HTTPS for all external communications
- Regularly update dependencies for security patches