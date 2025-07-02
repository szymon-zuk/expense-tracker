# expense-tracker
Personal expense tracking application built with FastAPI, featuring JWT authentication and Google OAuth integration.

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

## Features

- **Authentication & Authorization**
  - JWT token-based authentication
  - Google OAuth2 integration
  - User registration and login
  - Password hashing with bcrypt
  - Token refresh mechanism

- **Expense Management**
  - CRUD operations for expenses
  - Category-based organization
  - Multi-currency support (USD, EUR, PLN, GBP)
  - User-specific expense isolation

- **Analytics & Statistics**
  - Expense statistics by date range
  - Currency breakdown
  - Category-wise analysis
  - Financial reporting

## Authentication Setup

### Google OAuth Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (or Google OAuth2 API)
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
5. Copy your Client ID and Client Secret

### Environment Variables

Copy the `env.template` file to `.env` and fill in your configuration:

```bash
cp env.template .env
```

Required OAuth variables:
- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret
- `JWT_SECRET_KEY`: A secure random string for JWT signing

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with email/password
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `GET /auth/google` - Initiate Google OAuth
- `GET /auth/google/callback` - Google OAuth callback
- `POST /auth/logout` - Logout user

### Categories
- `GET /categories` - List all categories (with optional usage statistics)
- `GET /categories/{id}` - Get specific category with stats
- `POST /categories` - Create new category
- `PUT /categories/{id}` - Update category
- `DELETE /categories/{id}` - Delete category (with force option)
- `GET /categories/{id}/expenses` - Get user's expenses in a category

### Expenses
- `GET /expenses` - List user's expenses (with pagination and filtering)
- `GET /expenses/{id}` - Get specific expense
- `POST /expenses` - Create new expense
- `PUT /expenses/{id}` - Update expense
- `DELETE /expenses/{id}` - Delete expense
- `GET /expenses/statistics` - Get expense analytics

All category and expense endpoints require authentication (Bearer token).

## API Documentation

Once the application is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database

The application uses PostgreSQL. When using Docker, the database will be automatically set up and migrations will run on startup.

### Manual Migration

If setting up manually:
```bash
# Run migrations
uv run alembic upgrade head
```

## Usage Examples

### Authentication Flow

1. **Register a new user:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
  }'
```

2. **Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'
```

3. **Use the returned token for authenticated requests:**
```bash
# IMPORTANT: Include "Bearer " before your token!
curl -X GET "http://localhost:8000/expenses" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Common mistake (missing "Bearer "):
# curl -H "Authorization: YOUR_ACCESS_TOKEN"  ← This is WRONG!
```

### Google OAuth Flow

1. Get authorization URL:
```bash
curl -X GET "http://localhost:8000/auth/google"
```

2. Visit the returned `auth_url` in your browser
3. After authorization, you'll be redirected with tokens

### Managing Categories

```bash
# Create a new category
curl -X POST "http://localhost:8000/categories" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Coffee & Drinks",
    "description": "Daily coffee and beverages"
  }'

# List all categories with usage statistics
curl -X GET "http://localhost:8000/categories?include_stats=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get specific category with stats
curl -X GET "http://localhost:8000/categories/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Creating Expenses

```bash
curl -X POST "http://localhost:8000/expenses" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Grocery Shopping",
    "description": "Weekly groceries",
    "currency": "USD",
    "amount": 85.50,
    "category_id": 1
  }'
```

### Seeding Default Categories

Run this command to populate your database with common expense categories:

```bash
# Using Docker
docker-compose -f docker-compose.dev.yml run --rm app python scripts/seed_categories.py

# Or locally (if you have Python environment set up)
python scripts/seed_categories.py
```

## Troubleshooting Authentication

### Common Authentication Issues

**1. "Could not validate credentials" Error**
```bash
# ❌ WRONG - Missing "Bearer " prefix
curl -H "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ✅ CORRECT - Include "Bearer " prefix
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**2. Token Expired**
- Tokens expire after 30 minutes
- Login again to get a fresh token
- Use refresh token endpoint: `POST /auth/refresh`

**3. Getting Help**
```bash
# Get authentication help and examples
curl http://localhost:8000/auth/help

# Test if your token is working
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/auth/token-info
```

### Using Swagger UI (Recommended)

1. **Open**: `http://localhost:8000/docs`
2. **Login**: Use `POST /auth/login` to get your token
3. **Authorize**: Click the 🔒 "Authorize" button at the top
4. **Enter**: `Bearer YOUR_ACCESS_TOKEN` (include "Bearer ")
5. **Test**: Try any protected endpoint like `GET /auth/me`

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens, Google OAuth2
- **Migration**: Alembic
- **Container**: Docker & Docker Compose
- **Package Management**: UV
