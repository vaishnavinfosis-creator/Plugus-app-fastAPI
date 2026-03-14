"""
Plugus Platform - Main Application
"""
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.core.security_config import validate_startup_security
from app.middleware.rate_limit import rate_limit_middleware
from app.middleware.error_handler import error_handler_middleware
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Validate security configuration
    logger.info("Starting Plugus Platform...")
    
    if not validate_startup_security(settings):
        logger.critical("Security validation failed - shutting down")
        sys.exit(1)
    
    # Create tables if they don't exist (for development)
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown: cleanup if needed
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.middleware("http")(rate_limit_middleware)

# Error handling
app.middleware("http")(error_handler_middleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}
