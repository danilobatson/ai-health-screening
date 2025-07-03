"""
Security Module for AI Health Assessment System
Provides authentication, authorization, encryption, and audit capabilities
"""

from .auth import (
    AuthenticationService,
    User,
    UserRole,
    Permission,
    TokenData,
    LoginRequest,
    TokenResponse,
    SecurityAuditLog,
    auth_service,
    get_current_user,
    require_permission,
    require_role,
    require_admin,
    require_doctor,
    require_read_assessments,
    require_write_assessments,
    require_analytics,
)

from .privacy import (
    EncryptionLevel,
    PIIType,
    EncryptionService,
    DataAnonymizer,
    HIPAACompliance,
    SecureDataProcessor,
    encryption_service,
    data_anonymizer,
    hipaa_compliance,
    secure_processor,
)

from .api_security import (
    ThreatLevel,
    AttackType,
    SecurityEvent,
    InputValidator,
    RateLimiter,
    SecurityMonitor,
    APIKeyManager,
    security_monitor,
    api_key_manager,
    input_validator,
    rate_limiter,
)

from .middleware import (
    SecurityMiddleware,
    HIPAAMiddleware,
    create_secure_app,
    require_secure_headers,
    validate_content_type,
    get_request_fingerprint,
    check_request_integrity,
    log_security_event,
)

from .routes import (
    get_security_routers,
    security_router,
    assessment_router,
    admin_router,
)

__all__ = [
    # Authentication
    "AuthenticationService", "User", "UserRole", "Permission", "TokenData",
    "LoginRequest", "TokenResponse", "SecurityAuditLog", "auth_service",
    "get_current_user", "require_permission", "require_role", "require_admin",
    "require_doctor", "require_read_assessments", "require_write_assessments",
    "require_analytics",

    # Privacy & Encryption
    "EncryptionLevel", "PIIType", "EncryptionService", "DataAnonymizer",
    "HIPAACompliance", "SecureDataProcessor", "encryption_service",
    "data_anonymizer", "hipaa_compliance", "secure_processor",

    # API Security
    "ThreatLevel", "AttackType", "SecurityEvent", "InputValidator",
    "RateLimiter", "SecurityMonitor", "APIKeyManager", "security_monitor",
    "api_key_manager", "input_validator", "rate_limiter",

    # Middleware
    "SecurityMiddleware", "HIPAAMiddleware", "create_secure_app",
    "require_secure_headers", "validate_content_type", "get_request_fingerprint",
    "check_request_integrity", "log_security_event",

    # Routes
    "get_security_routers", "security_router", "assessment_router", "admin_router",
]
