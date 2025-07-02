# expense-tracker
Expense tracker application in FastAPI

## Quick Start with Docker

### Development (with hot reload)
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Production
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## Manual Setup

### Prerequisites
- Python 3.11+
- UV package manager
- PostgreSQL (if not using Docker)

### Installation
```bash
# Create virtual environment and install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
uv run alembic upgrade head

# Start the application
uv run uvicorn backend.app.main:app --reload
```

## API Documentation

Once the application is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database

The application uses PostgreSQL. When using Docker, the database will be automatically set up and migrations will run on startup.
