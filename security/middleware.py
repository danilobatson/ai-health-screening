"""
Security Middleware for FastAPI Integration
Provides security middleware for authentication, rate limiting, and monitoring
"""

from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import json
from typing import Callable, Dict, Any, Optional
import logging
from datetime import datetime, timezone

from .auth import auth_service, get_current_user, User
from .api_security import security_monitor, rate_limiter, input_validator
from .privacy import hipaa_compliance

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request processing"""

    def __init__(self, app: FastAPI, enable_rate_limiting: bool = True,
                 enable_input_validation: bool = True, enable_monitoring: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_input_validation = enable_input_validation
        self.enable_monitoring = enable_monitoring

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security filters"""
        start_time = time.time()

        try:
            # Security analysis
            if self.enable_monitoring:
                security_analysis = security_monitor.analyze_request(request)

                # Block if high threat detected
                if security_analysis["blocked"]:
                    logger.warning(f"Blocked request from {security_analysis['client_ip']}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Request blocked due to security policy"}
                    )

            # Rate limiting
            if self.enable_rate_limiting:
                client_ip = request.client.host if request.client else "unknown"
                rate_limit_result = rate_limiter.check_rate_limit(client_ip)

                if not rate_limit_result["allowed"]:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Rate limit exceeded",
                            "retry_after": rate_limit_result.get("retry_after", 60)
                        },
                        headers={"Retry-After": str(rate_limit_result.get("retry_after", 60))}
                    )

            # Input validation for POST/PUT requests
            if self.enable_input_validation and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    # Read and validate request body
                    body = await request.body()
                    if body:
                        try:
                            json_data = json.loads(body)
                            validation_result = input_validator.validate_input(json_data)

                            if not validation_result["valid"]:
                                logger.warning(f"Invalid input detected: {validation_result['violations']}")
                                return JSONResponse(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    content={
                                        "detail": "Invalid input detected",
                                        "violations": validation_result["violations"]
                                    }
                                )
                        except json.JSONDecodeError:
                            pass  # Not JSON data, skip validation

                        # Recreate request with original body
                        request._body = body
                except Exception as e:
                    logger.error(f"Error validating input: {e}")

            # Process request
            response = await call_next(request)

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Log successful request
            processing_time = time.time() - start_time
            self._log_request(request, response, processing_time)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal security error"}
            )

    def _log_request(self, request: Request, response: Response, processing_time: float):
        """Log request for audit purposes"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "processing_time": processing_time,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_length": response.headers.get("content-length", 0)
        }

        logger.info(f"Request processed: {log_data}")

class HIPAAMiddleware(BaseHTTPMiddleware):
    """HIPAA compliance middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with HIPAA compliance logging"""

        # Extract user information if available
        user_id = None
        try:
            # Try to get user from authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                token_data = auth_service.verify_token(token)
                user_id = token_data.user_id
        except:
            pass  # No valid token, continue without user

        # Log data access for HIPAA compliance
        if request.url.path.startswith("/api/") and user_id:
            hipaa_compliance.log_data_access(
                user_id=user_id,
                action=f"{request.method}_{request.url.path}",
                data_type="health_data",
                ip_address=request.client.host if request.client else "unknown"
            )

        response = await call_next(request)
        return response

def create_secure_app() -> FastAPI:
    """Create FastAPI app with security middleware"""
    app = FastAPI(
        title="AI Health Assessment API",
        description="Secure AI-powered health assessment system",
        version="1.0.0",
        docs_url="/docs" if logger.level <= logging.DEBUG else None,  # Hide docs in production
        redoc_url=None  # Disable redoc
    )

    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(HIPAAMiddleware)

    return app

# Security route decorators
def require_secure_headers():
    """Decorator to require secure headers"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0] if args else None
            if request and isinstance(request, Request):
                # Check for required security headers
                required_headers = ["user-agent", "accept"]
                for header in required_headers:
                    if not request.headers.get(header):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Missing required header: {header}"
                        )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_content_type(allowed_types: list = ["application/json"]):
    """Decorator to validate content type"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0] if args else None
            if request and isinstance(request, Request):
                content_type = request.headers.get("content-type", "")
                if not any(allowed_type in content_type for allowed_type in allowed_types):
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported content type. Allowed: {allowed_types}"
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Security utility functions
def get_request_fingerprint(request: Request) -> str:
    """Generate unique fingerprint for request"""
    import hashlib

    fingerprint_data = {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "accept": request.headers.get("accept", ""),
        "accept_language": request.headers.get("accept-language", ""),
        "accept_encoding": request.headers.get("accept-encoding", "")
    }

    fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def check_request_integrity(request: Request) -> bool:
    """Check request integrity"""
    # Basic integrity checks
    user_agent = request.headers.get("user-agent", "")

    # Check for empty or suspicious user agent
    if not user_agent or len(user_agent) < 10:
        return False

    # Check for valid HTTP version
    if not hasattr(request, 'scope') or request.scope.get('http_version') not in ['1.1', '2']:
        return False

    return True

async def log_security_event(event_type: str, details: Dict[str, Any],
                           request: Request, user: Optional[User] = None):
    """Log security event"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": user.id if user else None,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "endpoint": str(request.url.path),
        "details": details
    }

    logger.warning(f"Security event: {event_type}", extra=log_entry)
