"""
Rate Limiting Middleware
"""
import time
import logging
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from collections import defaultdict, deque
from threading import Lock
import asyncio

from app.schemas.errors import create_error_response, NetworkErrorCodes

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = Lock()
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed.
        Returns (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        
        with self.lock:
            # Clean old requests outside the window
            request_times = self.requests[key]
            while request_times and request_times[0] <= current_time - window_seconds:
                request_times.popleft()
            
            # Check if limit exceeded
            if len(request_times) >= limit:
                # Calculate retry after time
                oldest_request = request_times[0]
                retry_after = int(oldest_request + window_seconds - current_time) + 1
                return False, retry_after
            
            # Add current request
            request_times.append(current_time)
            return True, None


class RateLimitConfig:
    """Rate limit configuration"""
    
    # Auth endpoints - stricter limits
    AUTH_LIMIT = 10  # requests per minute
    AUTH_WINDOW = 60  # seconds
    
    # API endpoints - more generous limits
    API_LIMIT = 100  # requests per minute
    API_WINDOW = 60  # seconds
    
    # File upload endpoints - very strict
    UPLOAD_LIMIT = 5  # requests per minute
    UPLOAD_WINDOW = 60  # seconds


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP address"""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


def get_rate_limit_key(request: Request, user_id: Optional[int] = None) -> str:
    """Generate rate limit key"""
    client_ip = get_client_ip(request)
    
    if user_id:
        # For authenticated requests, use user ID + IP
        return f"user:{user_id}:{client_ip}"
    else:
        # For unauthenticated requests, use IP only
        return f"ip:{client_ip}"


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    path = request.url.path
    method = request.method
    
    # Skip rate limiting for health checks
    if path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Determine rate limit based on endpoint
    limit = RateLimitConfig.API_LIMIT
    window = RateLimitConfig.API_WINDOW
    
    if path.startswith("/api/v1/auth/"):
        limit = RateLimitConfig.AUTH_LIMIT
        window = RateLimitConfig.AUTH_WINDOW
    elif "upload" in path.lower() or method == "POST" and any(
        endpoint in path for endpoint in ["/bookings", "/reviews", "/complaints"]
    ):
        limit = RateLimitConfig.UPLOAD_LIMIT
        window = RateLimitConfig.UPLOAD_WINDOW
    
    # Get rate limit key
    client_ip = get_client_ip(request)
    
    # For authenticated endpoints, try to get user ID from token
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from app.core.security import decode_token
            token = auth_header.split(" ")[1]
            user_id = decode_token(token)
        except Exception:
            pass  # Continue with IP-based rate limiting
    
    rate_limit_key = get_rate_limit_key(request, user_id)
    
    # Check rate limit
    is_allowed, retry_after = rate_limiter.is_allowed(rate_limit_key, limit, window)
    
    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for {rate_limit_key} on {method} {path}. "
            f"Limit: {limit}/{window}s, Retry after: {retry_after}s"
        )
        
        error_response = create_error_response(
            error_code=NetworkErrorCodes.RATE_LIMIT_EXCEEDED,
            message=f"Too many requests. Please try again in {retry_after} seconds.",
            details={
                "limit": limit,
                "window_seconds": window,
                "retry_after": retry_after,
                "endpoint": path
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response.dict(),
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": str(window),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    
    # Calculate remaining requests
    with rate_limiter.lock:
        current_requests = len(rate_limiter.requests[rate_limit_key])
        remaining = max(0, limit - current_requests)
    
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Window"] = str(window)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response


def create_rate_limit_dependency(limit: int, window: int = 60):
    """Create a dependency for specific rate limits"""
    async def rate_limit_dependency(request: Request):
        client_ip = get_client_ip(request)
        
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        rate_limit_key = get_rate_limit_key(request, user_id)
        
        is_allowed, retry_after = rate_limiter.is_allowed(rate_limit_key, limit, window)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {rate_limit_key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=create_error_response(
                    error_code=NetworkErrorCodes.RATE_LIMIT_EXCEEDED,
                    message=f"Too many requests. Please try again in {retry_after} seconds.",
                    details={
                        "limit": limit,
                        "window_seconds": window,
                        "retry_after": retry_after
                    }
                ).dict(),
                headers={"Retry-After": str(retry_after)}
            )
    
    return rate_limit_dependency


# Pre-defined rate limit dependencies
strict_rate_limit = create_rate_limit_dependency(5, 60)  # 5 per minute
auth_rate_limit = create_rate_limit_dependency(10, 60)  # 10 per minute
api_rate_limit = create_rate_limit_dependency(100, 60)  # 100 per minute