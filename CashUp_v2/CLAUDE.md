# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
项目回复都使用中文。

## Project Overview

**CashUp** is a professional quantitative trading system built with a modular monolithic architecture. It provides comprehensive tools for individual quantitative traders including strategy development, backtesting, real-time trading, and multi-exchange integration.

## Architecture

### Core Services Structure
- **Core Service (8001)**: Authentication, configuration management, and user management
- **Trading Engine (8002)**: Order management, position tracking, and trade execution  
- **Strategy Platform (8003)**: Strategy development, backtesting, and market data
- **Notification Service (8004)**: Multi-channel notifications and alerts
- **Frontend (3000)**: React web interface with authentication

### Infrastructure
- **Database**: PostgreSQL 15 with asyncpg driver
- **Caching**: Redis 7 for session management and caching
- **Containerization**: Docker + Docker Compose with service orchestration
- **Reverse Proxy**: Nginx for load balancing and static file serving
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
docker-compose up -d postgres redis

# 3. Install dependencies
make install

# 4. Start development environment
make dev
```

### Working with Individual Services
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
make install      # Install all dependencies (UV + npm)
make dev          # Start development environment
make build        # Build all Docker images
make up           # Start all services
make down         # Stop all services
make test         # Run all tests
make lint         # Code quality checks
make format       # Format code
make migrate      # Run database migrations
make backup-db    # Backup database
make reset-db     # Reset database
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev       # Start development server
npm run build     # Build for production
npm run test      # Run tests
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

### Database Commands
```bash
# Access database directly
docker-compose exec postgres psql -U cashup -d cashup

# Run SQL scripts
docker-compose exec -T postgres psql -U cashup -d cashup -f scripts/init.sql
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
- Schema initialization via `scripts/init.sql`

### Frontend Authentication
- Uses React Context API for authentication state management
- Session-based authentication with Bearer tokens
- Protected routes with automatic redirect to login
- API interceptors automatically add Authorization headers
- Default admin account: `admin` / `admin123`

### API Endpoints Structure
All backend APIs follow consistent patterns:
```
Core Service (8001): /api/auth/*, /api/users/*, /api/config/*
Trading Engine (8002): /api/v1/orders, /api/v1/positions, /api/v1/account/*
Strategy Platform (8003): /api/strategies, /api/backtest, /api/data/*
Notification Service (8004): /api/notifications, /api/webhooks
```

### Service Communication
- Services communicate via HTTP APIs
- Core service acts as central authentication hub
- Trading engine handles order execution and position management
- Strategy platform manages strategy development and backtesting
- Notification service handles multi-channel alerts

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

### Frontend Structure
```
frontend/src/
├── contexts/AuthContext.tsx    # Authentication state
├── components/ProtectedRoute.tsx # Route protection
├── pages/                     # Page components
├── services/api.ts           # API client with interceptors
└── utils/                    # Utility functions
```

### Configuration
- Environment variables via `.env` file
- Exchange API settings in `configs/exchanges.yaml`
- Database connection strings via Docker Compose
- CORS configuration per service environment

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

## Current Development Status

### Completed Features
- ✅ Modular monolithic architecture setup
- ✅ Authentication and authorization system
- ✅ Database schema and migrations
- ✅ Docker containerization
- ✅ Frontend with authentication
- ✅ Multi-exchange integration framework
- ✅ Professional backtesting engine structure
- ✅ Notification service architecture

### In Development
- 🔄 Exchange client implementations (Binance, Gate.io)
- 🔄 Real-time WebSocket connections
- 🔄 Strategy execution engine
- 🔄 Risk management system

### Known Issues
- Market service WebSocket handling needs refinement
- Some duplicate exchange client code being consolidated
- Production deployment monitoring setup incomplete

## Environment Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
- Database credentials
- API keys for exchanges
- Notification service credentials
- Session secret keys

### Service Ports
- Frontend: 3000
- Core Service: 8001
- Trading Engine: 8002
- Strategy Platform: 8003
- Notification Service: 8004
- Nginx: 80, 443

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

### Service Health Checks
Each service provides health check endpoints:
- Core Service: `/health`
- Trading Engine: `/health`
- Strategy Platform: `/health`
- Notification Service: `/health`

## Performance Considerations

- Use async/await patterns throughout the codebase
- Implement proper connection pooling for database connections
- Cache frequently accessed data in Redis
- Use WebSocket for real-time data streaming
- Monitor service health and performance metrics

## Security Guidelines

- Session-based authentication with Bearer tokens
- Never commit API keys or sensitive credentials
- Use environment variables for configuration
- Implement proper authentication and authorization
- Validate all user inputs
- Configure CORS appropriately per environment