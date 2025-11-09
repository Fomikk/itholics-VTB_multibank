"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.security import SecurityHeadersMiddleware, RateLimitMiddleware
from app.core.logging_config import setup_logging
from app.settings import settings
from app.routers import banks, health

# Setup secure logging
setup_logging()

app = FastAPI(
    title="FinGuru API",
    description="Мультибанковский агрегатор с кешбек-игрой",
    version="0.1.0",
    docs_url="/docs",  # Always enable docs for development
    redoc_url="/redoc",
)

# Security headers middleware (must be first)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# CORS middleware - restrict in production
allowed_origins = (
    ["http://localhost:5173", "http://localhost:3000"]
    if settings.app_env == "dev"
    else []  # Configure production origins
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=[],
    max_age=3600,
)

# Include routers
app.include_router(health.router)
app.include_router(banks.router)


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

