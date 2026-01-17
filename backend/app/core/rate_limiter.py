"""
Rate limiting configuration for API endpoints
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiter(app: FastAPI):
    """Setup rate limiter for the FastAPI application"""
    
    # Enable rate limiter
    app.state.limiter_enabled = True
    
    # Custom error handler for rate limit exceeded
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )


# Rate limit configurations by endpoint type
RATE_LIMITS = {
    "auth_register": "5/minute",      # 5 registration attempts per minute per IP
    "auth_login": "10/minute",        # 10 login attempts per minute per IP
    "auth_google": "10/minute",       # 10 Google auth attempts per minute per IP
    "analysis": "3/minute",           # 3 analysis requests per minute per IP (heavy operation)
    "analysis_history": "30/minute",  # 30 history requests per minute per IP
    "analysis_detail": "30/minute",   # 30 detail requests per minute per IP
    "analysis_comments": "30/minute", # 30 comment requests per minute per IP
    "general": "100/minute",          # Default rate limit
}


def get_rate_limit(endpoint_type: str = "general") -> str:
    """Get rate limit for specific endpoint type"""
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS["general"])
