from contextlib import asynccontextmanager
from pathlib import Path
import sys
from typing import AsyncGenerator

# Ensure backend directory is on sys.path so 'app' is always importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import check_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions: ensure all tables (including taxpayer_profiles) exist
    try:
        from sqlmodel import SQLModel
        from app.database import sync_engine
        import app.models  # load all SQLModel tables
        SQLModel.metadata.create_all(sync_engine)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database initialization check notice: {e}")
    yield
    # Shutdown actions


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://taxplan.tyes.dev",
]
if settings.APP_URL and settings.APP_URL not in allowed_origins:
    allowed_origins.append(settings.APP_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://([a-zA-Z0-9-]+\.)*(tyes\.dev|pages\.dev|onrender\.com|hf\.space)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.responses import JSONResponse

# Simple in-memory rate limiter: max 60 requests per minute per IP
_rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW_SECONDS = 60

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("testclient", "unknown") or settings.ENVIRONMENT == "test":
        return await call_next(request)
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if t > window_start
    ]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please wait before retrying."},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
        )
    _rate_limit_store[client_ip].append(now)
    return await call_next(request)

# Include v1 REST API routes
from app.api import api_router
app.include_router(api_router)



@app.api_route("/", methods=["GET", "HEAD"])
async def root() -> dict[str, str]:
    return {
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


@app.api_route("/health", methods=["GET", "HEAD"], summary="Health check with DB connectivity")
async def health_check() -> JSONResponse:
    db_ok, err = await check_database_connection()
    if db_ok:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "connected",
                "environment": settings.ENVIRONMENT,
            },
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "unhealthy",
            "database": "disconnected",
            "detail": err,
            "environment": settings.ENVIRONMENT,
        },
    )
