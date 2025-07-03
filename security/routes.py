"""
Secure API Routes for Health Assessment
Integrates authentication, authorization, and security monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from security.auth import (
    User, UserRole, Permission, LoginRequest, TokenResponse,
    auth_service, get_current_user, require_permission, require_role
)
from security.privacy import secure_processor, hipaa_compliance
from security.api_security import security_monitor, api_key_manager
from security.middleware import require_secure_headers, validate_content_type, log_security_event

logger = logging.getLogger(__name__)

# Security router
security_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
assessment_router = APIRouter(prefix="/api/v1/assessment", tags=["Health Assessment"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])

# Request/Response models
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class HealthAssessmentRequest(BaseModel):
    symptoms: List[str]
    severity: Dict[str, int]
    duration: Dict[str, str]
    medical_history: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    age: int
    gender: str

class HealthAssessmentResponse(BaseModel):
    assessment_id: str
    risk_score: float
    recommendations: List[str]
    severity_level: str
    timestamp: datetime
    encrypted: bool = True

class SecuritySummaryResponse(BaseModel):
    period_hours: int
    total_events: int
    event_types: Dict[str, int]
    threat_levels: Dict[str, int]
    blocked_requests: int

# Authentication endpoints
@security_router.post("/login", response_model=LoginResponse)
@require_secure_headers()
@validate_content_type()
async def login(request: Request, login_data: LoginRequest) -> LoginResponse:
    """Authenticate user and return JWT tokens"""

    # Log login attempt
    await log_security_event(
        event_type="login_attempt",
        details={"username": login_data.username},
        request=request
    )

    # Authenticate user
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        await log_security_event(
            event_type="login_failed",
            details={"username": login_data.username, "reason": "invalid_credentials"},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check MFA if enabled
    if user.mfa_enabled:
        if not login_data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA code required"
            )

        if not auth_service.verify_mfa_token(user.id, login_data.mfa_code):
            await log_security_event(
                event_type="mfa_failed",
                details={"user_id": user.id},
                request=request,
                user=user
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )

    # Generate tokens
    access_token = auth_service.create_access_token(user)
    refresh_token = auth_service.create_refresh_token(user)

    # Log successful login
    await log_security_event(
        event_type="login_success",
        details={"user_id": user.id, "role": user.role.value},
        request=request,
        user=user
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,  # 30 minutes
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value
        }
    )

@security_router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    """Logout user and invalidate tokens"""

    await log_security_event(
        event_type="logout",
        details={"user_id": current_user.id},
        request=request,
        user=current_user
    )

    # In production, add token to blacklist
    return {"message": "Successfully logged out"}

@security_router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified
    }

# Health Assessment endpoints
@assessment_router.post("/", response_model=HealthAssessmentResponse)
@require_secure_headers()
@validate_content_type()
async def create_assessment(
    request: Request,
    assessment_data: HealthAssessmentRequest,
    current_user: User = Depends(require_permission(Permission.WRITE_ASSESSMENTS))
) -> HealthAssessmentResponse:
    """Create new health assessment with security processing"""

    # Log assessment creation
    await log_security_event(
        event_type="assessment_created",
        details={"user_id": current_user.id, "symptoms_count": len(assessment_data.symptoms)},
        request=request,
        user=current_user
    )

    # Process data with security measures
    assessment_dict = assessment_data.dict()
    secured_data = secure_processor.process_assessment_data(
        assessment_dict,
        current_user.id,
        "health_assessment"
    )

    # Simulate AI processing (in production, call actual ML service)
    risk_score = min(75.0, sum(assessment_data.severity.values()) / len(assessment_data.severity) * 10)

    # Generate recommendations based on risk
    recommendations = []
    if risk_score > 70:
        recommendations.extend([
            "Seek immediate medical attention",
            "Monitor symptoms closely",
            "Follow up with healthcare provider"
        ])
    elif risk_score > 40:
        recommendations.extend([
            "Schedule appointment with healthcare provider",
            "Monitor symptoms",
            "Maintain healthy lifestyle"
        ])
    else:
        recommendations.extend([
            "Continue monitoring symptoms",
            "Maintain healthy lifestyle",
            "Schedule routine checkup"
        ])

    # Determine severity level
    if risk_score > 70:
        severity_level = "high"
    elif risk_score > 40:
        severity_level = "medium"
    else:
        severity_level = "low"

    # Log HIPAA-compliant data access
    hipaa_compliance.log_data_access(
        user_id=current_user.id,
        action="create_assessment",
        data_type="assessment_data",
        purpose="health_assessment"
    )

    import secrets
    assessment_id = secrets.token_hex(16)

    return HealthAssessmentResponse(
        assessment_id=assessment_id,
        risk_score=risk_score,
        recommendations=recommendations,
        severity_level=severity_level,
        timestamp=datetime.now(timezone.utc),
        encrypted=True
    )

@assessment_router.get("/history")
async def get_assessment_history(
    current_user: User = Depends(require_permission(Permission.READ_ASSESSMENTS))
) -> List[Dict[str, Any]]:
    """Get user's assessment history"""

    # Log data access
    hipaa_compliance.log_data_access(
        user_id=current_user.id,
        action="view_assessment_history",
        data_type="assessment_data",
        purpose="patient_care"
    )

    # In production, fetch from database
    return [
        {
            "assessment_id": "sample-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_score": 45.0,
            "severity_level": "medium"
        }
    ]

@assessment_router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    current_user: User = Depends(require_permission(Permission.READ_ASSESSMENTS))
) -> Dict[str, Any]:
    """Get specific assessment by ID"""

    # Log data access
    hipaa_compliance.log_data_access(
        user_id=current_user.id,
        action="view_assessment",
        data_type="assessment_data",
        record_id=assessment_id,
        purpose="patient_care"
    )

    # In production, fetch from database and decrypt
    return {
        "assessment_id": assessment_id,
        "risk_score": 45.0,
        "recommendations": ["Monitor symptoms", "Follow up if needed"],
        "severity_level": "medium",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Administrative endpoints
@admin_router.get("/security/summary", response_model=SecuritySummaryResponse)
async def get_security_summary(
    hours: int = 24,
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> SecuritySummaryResponse:
    """Get security summary for administrators"""

    summary = security_monitor.get_security_summary(hours=hours)
    return SecuritySummaryResponse(**summary)

@admin_router.get("/security/events")
async def get_security_events(
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> List[Dict[str, Any]]:
    """Get recent security events"""

    events = security_monitor.security_events[-limit:]
    return [
        {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "threat_level": event.threat_level.value,
            "source_ip": event.source_ip,
            "endpoint": event.endpoint,
            "blocked": event.blocked,
            "details": event.details
        }
        for event in events
    ]

@admin_router.get("/hipaa/audit")
async def get_hipaa_audit_trail(
    days: int = 30,
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> List[Dict[str, Any]]:
    """Get HIPAA audit trail"""

    from datetime import timedelta
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    audit_logs = hipaa_compliance.get_audit_trail(start_date=start_date)

    return [
        {
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "action": log.action,
            "data_type": log.data_type,
            "record_id": log.record_id,
            "purpose": log.purpose,
            "ip_address": log.ip_address,
            "success": log.success
        }
        for log in audit_logs
    ]

@admin_router.post("/api-keys")
async def create_api_key(
    name: str,
    permissions: List[str],
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Dict[str, str]:
    """Create new API key"""

    api_key = api_key_manager.create_api_key(name, permissions)

    await log_security_event(
        event_type="api_key_created",
        details={"name": name, "permissions": permissions, "created_by": current_user.id},
        request=None,
        user=current_user
    )

    return {
        "api_key": api_key,
        "name": name,
        "permissions": permissions,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

@admin_router.delete("/api-keys/{key}")
async def revoke_api_key(
    key: str,
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Dict[str, str]:
    """Revoke API key"""

    success = api_key_manager.revoke_api_key(key)

    if success:
        await log_security_event(
            event_type="api_key_revoked",
            details={"key_prefix": key[:8], "revoked_by": current_user.id},
            request=None,
            user=current_user
        )
        return {"message": "API key revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

# Health check endpoint (no authentication required)
@security_router.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# Include all routers
def get_security_routers():
    """Get all security-enabled routers"""
    return [security_router, assessment_router, admin_router]
