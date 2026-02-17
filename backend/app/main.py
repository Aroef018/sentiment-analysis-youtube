from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.analysis import router as analysis_router
from app.api import auth
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.rate_limiter import limiter, setup_rate_limiter
import logging

# Setup logging first
setup_logging("sentiment-analysis")
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Sentiment Analysis API")

# Setup rate limiter
app.state.limiter = limiter
setup_rate_limiter(app)


class SizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size"""
    MAX_UPLOAD_SIZE = 1_000_000  # 1 MB limit

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            if "content-length" in request.headers:
                content_length = int(request.headers["content-length"])
                if content_length > self.MAX_UPLOAD_SIZE:
                    logger.warning(
                        f"Request rejected - size exceeded",
                        extra={
                            "ip": request.client.host if request.client else "unknown",
                            "content_length": content_length,
                            "max_allowed": self.MAX_UPLOAD_SIZE
                        }
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large. Maximum size is 1 MB."}
                    )
        return await call_next(request)


# Add size limit middleware BEFORE CORS
app.add_middleware(SizeLimitMiddleware)

# CORS configuration - dynamically set origins
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add production frontend URL from env if set
import os
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],  # Restrict to needed methods only
    allow_headers=["Content-Type", "Authorization"],  # Restrict to needed headers only
    max_age=600,  # Cache preflight requests for 10 minutes
    expose_headers=["Content-Type"],
)

from app.api.analysis_debug import router as analysis_debug_router

app.include_router(analysis_router)
app.include_router(auth.router)
app.include_router(analysis_debug_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup", extra={"event": "startup"})
    
    # Warm up database connection to prevent Neon cold start
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection warmed up successfully")
    except Exception as e:
        logger.warning(f"Failed to warm up database connection: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown", extra={"event": "shutdown"})


@app.get("/health")
async def health_check():
    """Health check endpoint with concurrent analysis status and DB health"""
    from app.services.analysis_service import _get_analysis_semaphore
    from app.db.session import engine
    from sqlalchemy import text
    
    semaphore = _get_analysis_semaphore()
    available_slots = semaphore._value
    max_concurrent = settings.MAX_CONCURRENT_ANALYSIS
    active_analysis = max_concurrent - available_slots
    
    # Check DB connection pool status
    pool = engine.pool
    pool_status = {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
    
    # Try to ping database
    db_healthy = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False
    
    return {
        "status": "ok" if db_healthy else "degraded",
        "database": {
            "healthy": db_healthy,
            "pool": pool_status,
        },
        "concurrent_analysis": {
            "active": active_analysis,
            "max": max_concurrent,
            "available": available_slots
        }
    }


