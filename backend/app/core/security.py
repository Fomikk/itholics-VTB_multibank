"""Security utilities and middleware."""
import re
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        """Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._request_counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request."""
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests (older than 1 minute)
        current_time = request.scope.get("time", 0)
        if client_ip in self._request_counts:
            self._request_counts[client_ip] = [
                req_time
                for req_time in self._request_counts[client_ip]
                if current_time - req_time < 60
            ]
        
        # Check rate limit
        if client_ip in self._request_counts:
            if len(self._request_counts[client_ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )
            self._request_counts[client_ip].append(current_time)
        else:
            self._request_counts[client_ip] = [current_time]
        
        response = await call_next(request)
        return response


def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize user input to prevent injection attacks.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        HTTPException: If input is invalid
    """
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail="Invalid input type")
    
    # Remove null bytes
    value = value.replace("\x00", "")
    
    # Check length
    if max_length and len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Input too long. Maximum length: {max_length}"
        )
    
    # Remove potentially dangerous characters
    # Allow alphanumeric, spaces, and common punctuation
    sanitized = re.sub(r'[^\w\s\-_.,@]', '', value)
    
    return sanitized.strip()


def validate_client_id(client_id: str) -> str:
    """Validate client ID format.

    Args:
        client_id: Client ID to validate

    Returns:
        Validated client ID

    Raises:
        HTTPException: If client ID is invalid
    """
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID is required")
    
    # Client ID should be alphanumeric with dashes/underscores
    if not re.match(r'^[a-zA-Z0-9\-_]+$', client_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid client ID format. Only alphanumeric characters, dashes and underscores are allowed"
        )
    
    if len(client_id) > 100:
        raise HTTPException(status_code=400, detail="Client ID too long")
    
    return client_id


def validate_bank_code(bank_code: str) -> str:
    """Validate bank code.

    Args:
        bank_code: Bank code to validate

    Returns:
        Validated bank code

    Raises:
        HTTPException: If bank code is invalid
    """
    bank_code_lower = bank_code.lower()
    if bank_code_lower not in ["vbank", "abank", "sbank"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bank code: {bank_code}. Must be vbank, abank, or sbank"
        )
    return bank_code_lower


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging.

    Args:
        data: Sensitive string to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return "***"
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]

