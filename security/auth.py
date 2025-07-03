"""
Authentication and Authorization Module
Provides JWT-based authentication, RBAC, and session management
"""

import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import os
import secrets
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
MFA_TOKEN_EXPIRE_MINUTES = 5

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
security = HTTPBearer()

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(str, Enum):
    """System permissions"""
    READ_ASSESSMENTS = "read:assessments"
    WRITE_ASSESSMENTS = "write:assessments"
    DELETE_ASSESSMENTS = "delete:assessments"
    READ_ANALYTICS = "read:analytics"
    WRITE_ANALYTICS = "write:analytics"
    ADMIN_ACCESS = "admin:access"
    PATIENT_DATA = "access:patient_data"
    EXPORT_DATA = "export:data"

# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [p.value for p in Permission],
    UserRole.DOCTOR: [
        Permission.READ_ASSESSMENTS.value,
        Permission.WRITE_ASSESSMENTS.value,
        Permission.READ_ANALYTICS.value,
        Permission.PATIENT_DATA.value,
    ],
    UserRole.NURSE: [
        Permission.READ_ASSESSMENTS.value,
        Permission.WRITE_ASSESSMENTS.value,
        Permission.PATIENT_DATA.value,
    ],
    UserRole.ANALYST: [
        Permission.READ_ASSESSMENTS.value,
        Permission.READ_ANALYTICS.value,
        Permission.WRITE_ANALYTICS.value,
        Permission.EXPORT_DATA.value,
    ],
    UserRole.PATIENT: [
        Permission.READ_ASSESSMENTS.value,
    ],
    UserRole.VIEWER: [
        Permission.READ_ASSESSMENTS.value,
        Permission.READ_ANALYTICS.value,
    ],
}

@dataclass
class User:
    """User data model"""
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    password_hash: str = ""

class TokenData(BaseModel):
    """JWT token data"""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: List[str]
    exp: datetime
    iat: datetime
    token_type: str = "access"

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str
    mfa_code: Optional[str] = None

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class SecurityAuditLog(BaseModel):
    """Security audit log entry"""
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: Optional[str]
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any]

class AuthenticationService:
    """Authentication and authorization service"""

    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.audit_logs: List[SecurityAuditLog] = []

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        permissions = ROLE_PERMISSIONS.get(user.role, [])
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        token_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "access"
        }

        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        token_data = {
            "user_id": user.id,
            "username": user.username,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "refresh"
        }

        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Check if token is expired
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )

            # Create TokenData object
            token_data = TokenData(
                user_id=payload["user_id"],
                username=payload["username"],
                email=payload.get("email", ""),
                role=UserRole(payload["role"]),
                permissions=payload.get("permissions", []),
                exp=exp,
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                token_type=payload.get("token_type", "access")
            )

            return token_data

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        # In production, this would query the database
        # For demo purposes, creating a mock user
        if username == "admin" and password == "admin123":
            return User(
                id="admin-001",
                email="admin@healthassess.com",
                username="admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                password_hash=self.hash_password(password)
            )
        elif username == "doctor" and password == "doctor123":
            return User(
                id="doctor-001",
                email="doctor@healthassess.com",
                username="doctor",
                role=UserRole.DOCTOR,
                is_active=True,
                is_verified=True,
                password_hash=self.hash_password(password)
            )
        return None

    def check_permission(self, user_role: UserRole, required_permission: Permission) -> bool:
        """Check if user role has required permission"""
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return required_permission.value in user_permissions

    def log_security_event(self, event: SecurityAuditLog):
        """Log security audit event"""
        self.audit_logs.append(event)
        logger.info(f"Security event: {event.action} by user {event.user_id} - Success: {event.success}")

    def generate_mfa_token(self, user_id: str) -> str:
        """Generate MFA token (simplified - in production use TOTP)"""
        return secrets.token_hex(3)  # 6-character hex code

    def verify_mfa_token(self, user_id: str, token: str) -> bool:
        """Verify MFA token (simplified implementation)"""
        # In production, this would verify against TOTP or SMS
        return len(token) == 6 and token.isalnum()

# Global authentication service instance
auth_service = AuthenticationService()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    token_data = auth_service.verify_token(token)

    # In production, fetch user from database
    user = User(
        id=token_data.user_id,
        email=token_data.email,
        username=token_data.username,
        role=token_data.role,
        is_active=True,
        is_verified=True
    )

    return user

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not auth_service.check_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    return permission_checker

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role.value}"
            )
        return current_user
    return role_checker

# Example usage decorators
require_admin = require_role(UserRole.ADMIN)
require_doctor = require_role(UserRole.DOCTOR)
require_read_assessments = require_permission(Permission.READ_ASSESSMENTS)
require_write_assessments = require_permission(Permission.WRITE_ASSESSMENTS)
require_analytics = require_permission(Permission.READ_ANALYTICS)
