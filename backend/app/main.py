from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from backend.app.config.logging import get_logger, setup_logging
from backend.app.config.settings import get_settings
from backend.app.routers import auth, categories, expenses

# Initialize logging first
setup_logging()
logger = get_logger("main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Expense Tracker API startup complete")
    logger.info(f"📊 Running in {settings.MODE.value} mode")
    logger.info(f"🔑 JWT configured with {settings.JWT_ALGORITHM} algorithm")

    yield

    # Shutdown
    logger.info("🛑 Expense Tracker API shutting down")


app = FastAPI(
    title="Expense Tracker API",
    description="A personal expense tracking application with JWT authentication and Google OAuth",
    version="1.0.0",
    lifespan=lifespan,
)

# Add session middleware for OAuth state management
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

logger.info("🔧 Session middleware configured")


@app.get("/")
async def root():
    logger.info("📋 Root endpoint accessed")
    return {
        "message": "Welcome to Expense Tracker API",
        "version": "1.0.0",
        "documentation": {"swagger_ui": "/docs", "redoc": "/redoc"},
        "authentication": {
            "help": "/auth/help",
            "register": "/auth/register",
            "login": "/auth/login",
            "user_info": "/auth/me",
            "token_test": "/auth/token-info",
        },
        "endpoints": {"categories": "/categories", "expenses": "/expenses"},
        "quick_start": {
            "1": "Visit /docs for interactive API documentation",
            "2": "Register at /auth/register",
            "3": "Login at /auth/login to get your token",
            "4": "Use 'Authorize' button in /docs with format: Bearer <token>",
            "5": "Need help? Visit /auth/help",
        },
    }


# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(categories.router, tags=["categories"])
app.include_router(expenses.router, tags=["expenses"])

logger.info("🔗 All routers included: auth, categories, expenses")
