# CashUp 量化交易系统

This repository contains two versions of the CashUp quantitative trading system:

1.  **CashUp (V1):** A microservices-based architecture.
2.  **CashUp_v2:** A simplified, modular monolith architecture.

---

## CashUp (V1)

### Project Overview

This is a quantitative trading platform named "CashUp" with a microservices architecture. The backend is built with Python and FastAPI, and the frontend is a React application. The system uses Docker and Docker Compose for containerization and orchestration.

**Key Technologies:**

*   **Frontend:** React, TypeScript, Vite, Tailwind CSS, Zustand, React Router, Recharts, Lucide React Icons
*   **Backend:** Python, FastAPI, SQLAlchemy 2.0, UV, CCXT, Celery, NumPy, Pandas, Prometheus
*   **Database:** PostgreSQL
*   **Cache:** Redis
*   **Message Queue:** RabbitMQ
*   **Deployment:** Docker, Docker Compose

**External Integrations:**

*   **Exchanges:** Gate.io API
*   **Notification Channels:** QANotify, WXPusher, PushPlus, Telegram Bot, Email (SMTP)

**Architecture:**

The project is structured as a set of microservices, each responsible for a specific domain:

*   **User Service:** Manages user authentication and authorization.
*   **Trading Service:** Executes trades with various exchanges.
*   **Strategy Service:** Manages and backtests trading strategies.
*   **Market Service:** Provides real-time market data.
*   **Notification Service:** Sends notifications to users.
*   **Order Service:** Manages order lifecycle.
*   **Config Service:** Manages system-wide configuration.
*   **Monitoring Service:** Monitors the health and performance of the system.

### Building and Running

The project includes a `Makefile` and several scripts that simplify common development tasks.

**Using the `start_project.sh` script:**

The `start_project.sh` script provides an interactive way to start the project's services.

```bash
./start_project.sh
```

**Using the `test_system.sh` script:**

The `test_system.sh` script is a comprehensive testing script that starts and tests the entire system in stages.

```bash
./test_system.sh [command]
```

**Using the `Makefile`:**

The `Makefile` provides a set of convenient commands for managing the project.

**Key Commands:**

*   `make install`
*   `make up`
*   `make down`
*   `make logs`
*   `make test`
*   `make lint`
*   `make format`

### Development Conventions

*   **Git Workflow:** Feature branch workflow with pull requests.
*   **Code Style:**
    *   **Python:** PEP 8, with `black` (line length 88), `isort`, and `flake8`.
    *   **Type Checking:** `mypy` is used for static type checking.
    *   **React:** Functional components with hooks. TypeScript is used for type safety.
*   **Database:** SQLAlchemy for ORM.
*   **API Design:** FastAPI with Pydantic models.
*   **Security:**
    *   JWT for authentication.
    *   RBAC for authorization.
    *   `bcrypt` for password hashing.
    *   No hardcoded secrets.
    *   `bandit` is used for security analysis.
*   **Testing:**
    *   `pytest` is used for unit and integration testing.
    *   `coverage` is used to measure test coverage.
    *   Tests are organized into `unit`, `integration`, `api`, `database`, and `redis` categories.

---

## CashUp_v2

### Project Overview

`CashUp_v2` is a new version of the quantitative trading system, designed as a modular monolith. This version simplifies the architecture and improves development efficiency.

**Key Technologies:**

*   **Backend:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
*   **Frontend:** React 18, TypeScript, Ant Design
*   **Containerization:** Docker, Docker Compose
*   **Package Management:** UV, npm

**Architecture:**

The project is divided into four core services:

*   **core-service (8001):** Handles authentication, configuration, and user management.
*   **trading-engine (8002):** Manages trade execution, order management, and exchange integration.
*   **strategy-platform (8003):** Provides strategy management, backtesting, and data analysis.
*   **notification-service (8004):** Manages notifications.

### Core Functionalities

*   **Strategy Development:** Provides a base class and a framework for creating custom trading strategies.
*   **Backtesting Engine:** An event-driven backtesting engine to test strategies against historical data.
*   **Exchange Integration:** A unified interface for connecting to multiple cryptocurrency exchanges.

### API Endpoints

*   **Core Service:**
    *   `POST /api/auth/login`
    *   `POST /api/auth/register`
    *   `GET /api/users/me`
*   **Strategy Platform:**
    *   `GET /api/strategies`
    *   `POST /api/strategies`
    *   `PUT /api/strategies/{id}`
    *   `DELETE /api/strategies/{id}`
    *   `POST /api/strategies/{id}/backtest`
*   **Trading Engine:**
    *   `GET /api/exchanges`
    *   `POST /api/orders`
    *   `GET /api/orders`
    *   `DELETE /api/orders/{id}`

### Building and Running

`CashUp_v2` also uses a `Makefile` and `docker-compose.yml` for building and running the project. The commands are similar to the V1 project.

**Key Files:**

*   `CashUp_v2/docker-compose.yml`
*   `CashUp_v2/Makefile`
*   `CashUp_v2/README.md`

### Development Conventions

*   **Architecture:** Modular monolith.
*   **Strategy Development:** Includes a strategy base class, manager, and templates.
*   **Backtesting:** Event-driven backtesting engine with performance analysis.
*   **Exchange Integration:** Abstracted exchange layer for supporting multiple exchanges.
