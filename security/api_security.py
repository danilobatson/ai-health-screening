"""
API Security and Monitoring Module
Provides rate limiting, input validation, and security monitoring
"""

import time
import re
import hashlib
import ipaddress
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, validator
import structlog
import secrets
import json
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = structlog.get_logger()

class ThreatLevel(str, Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AttackType(str, Enum):
    """Types of security attacks"""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

@dataclass
class SecurityEvent:
    """Security event data"""
    timestamp: datetime
    event_type: AttackType
    threat_level: ThreatLevel
    source_ip: str
    user_agent: str
    endpoint: str
    user_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False

@dataclass
class RateLimitRule:
    """Rate limiting rule definition"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10
    window_size: int = 60  # seconds

class APIKey(BaseModel):
    """API key model"""
    key_id: str
    key_hash: str
    name: str
    permissions: List[str]
    rate_limit: RateLimitRule
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used: Optional[datetime] = None

class SecurityAudit(BaseModel):
    """Security audit entry"""
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    method: str
    status_code: int
    response_time: float
    user_agent: str
    payload_size: int
    security_events: List[SecurityEvent] = []

class InputValidator:
    """Input validation and sanitization"""

    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"][^'\"]*['\"])",
            r"(;|\||\&)",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]

        # File path traversal
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e/",
            r"..%2f",
            r"%2e%2e%5c",
        ]

    def validate_input(self, data: Any, field_name: str = "input") -> Dict[str, Any]:
        """Validate and sanitize input data"""
        violations = []

        if isinstance(data, str):
            violations.extend(self._check_sql_injection(data, field_name))
            violations.extend(self._check_xss(data, field_name))
            violations.extend(self._check_path_traversal(data, field_name))
        elif isinstance(data, dict):
            for key, value in data.items():
                sub_violations = self.validate_input(value, f"{field_name}.{key}")
                violations.extend(sub_violations["violations"])
        elif isinstance(data, list):
            for i, item in enumerate(data):
                sub_violations = self.validate_input(item, f"{field_name}[{i}]")
                violations.extend(sub_violations["violations"])

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "sanitized_data": self._sanitize_data(data) if violations else data
        }

    def _check_sql_injection(self, text: str, field_name: str) -> List[Dict[str, Any]]:
        """Check for SQL injection patterns"""
        violations = []
        for pattern in self.sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append({
                    "type": "sql_injection",
                    "field": field_name,
                    "pattern": pattern,
                    "threat_level": ThreatLevel.HIGH
                })
        return violations

    def _check_xss(self, text: str, field_name: str) -> List[Dict[str, Any]]:
        """Check for XSS patterns"""
        violations = []
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append({
                    "type": "xss",
                    "field": field_name,
                    "pattern": pattern,
                    "threat_level": ThreatLevel.HIGH
                })
        return violations

    def _check_path_traversal(self, text: str, field_name: str) -> List[Dict[str, Any]]:
        """Check for path traversal patterns"""
        violations = []
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append({
                    "type": "path_traversal",
                    "field": field_name,
                    "pattern": pattern,
                    "threat_level": ThreatLevel.MEDIUM
                })
        return violations

    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data by removing dangerous patterns"""
        if isinstance(data, str):
            # Remove SQL injection patterns
            for pattern in self.sql_patterns:
                data = re.sub(pattern, "", data, flags=re.IGNORECASE)

            # Remove XSS patterns
            for pattern in self.xss_patterns:
                data = re.sub(pattern, "", data, flags=re.IGNORECASE)

            # Remove path traversal patterns
            for pattern in self.path_traversal_patterns:
                data = re.sub(pattern, "", data, flags=re.IGNORECASE)

            return data.strip()

        return data

class RateLimiter:
    """Rate limiting implementation"""

    def __init__(self):
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.default_rule = RateLimitRule(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000
        )

    def check_rate_limit(self, identifier: str, rule: Optional[RateLimitRule] = None) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        if rule is None:
            rule = self.default_rule

        current_time = time.time()

        # Check if IP is currently blocked
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier].timestamp():
                return {
                    "allowed": False,
                    "reason": "ip_blocked",
                    "retry_after": int(self.blocked_ips[identifier].timestamp() - current_time)
                }
            else:
                del self.blocked_ips[identifier]

        # Get request history
        requests = self.request_counts[identifier]

        # Clean old requests (older than 24 hours)
        cutoff_time = current_time - 86400  # 24 hours
        while requests and requests[0] < cutoff_time:
            requests.popleft()

        # Count requests in different time windows
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        day_ago = current_time - 86400

        requests_last_minute = sum(1 for req_time in requests if req_time > minute_ago)
        requests_last_hour = sum(1 for req_time in requests if req_time > hour_ago)
        requests_last_day = sum(1 for req_time in requests if req_time > day_ago)

        # Check limits
        if requests_last_minute >= rule.requests_per_minute:
            self._block_temporarily(identifier, 60)  # Block for 1 minute
            return {
                "allowed": False,
                "reason": "rate_limit_minute",
                "limit": rule.requests_per_minute,
                "current": requests_last_minute,
                "retry_after": 60
            }

        if requests_last_hour >= rule.requests_per_hour:
            self._block_temporarily(identifier, 3600)  # Block for 1 hour
            return {
                "allowed": False,
                "reason": "rate_limit_hour",
                "limit": rule.requests_per_hour,
                "current": requests_last_hour,
                "retry_after": 3600
            }

        if requests_last_day >= rule.requests_per_day:
            self._block_temporarily(identifier, 86400)  # Block for 24 hours
            return {
                "allowed": False,
                "reason": "rate_limit_day",
                "limit": rule.requests_per_day,
                "current": requests_last_day,
                "retry_after": 86400
            }

        # Record this request
        requests.append(current_time)

        return {
            "allowed": True,
            "remaining": {
                "minute": rule.requests_per_minute - requests_last_minute - 1,
                "hour": rule.requests_per_hour - requests_last_hour - 1,
                "day": rule.requests_per_day - requests_last_day - 1
            }
        }

    def _block_temporarily(self, identifier: str, duration: int):
        """Block identifier temporarily"""
        self.blocked_ips[identifier] = datetime.now(timezone.utc) + timedelta(seconds=duration)

class SecurityMonitor:
    """Security monitoring and threat detection"""

    def __init__(self):
        self.security_events: List[SecurityEvent] = []
        self.suspicious_ips: Dict[str, List[datetime]] = defaultdict(list)
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()

    def analyze_request(self, request: Request, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze incoming request for security threats"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        threats = []

        # Check for suspicious patterns
        if self._is_suspicious_user_agent(user_agent):
            threats.append({
                "type": AttackType.SUSPICIOUS_PATTERN,
                "level": ThreatLevel.MEDIUM,
                "details": {"user_agent": user_agent}
            })

        # Check rate limits
        rate_limit_result = self.rate_limiter.check_rate_limit(client_ip)
        if not rate_limit_result["allowed"]:
            threats.append({
                "type": AttackType.RATE_LIMIT_EXCEEDED,
                "level": ThreatLevel.HIGH,
                "details": rate_limit_result
            })

        # Check IP reputation
        if self._is_suspicious_ip(client_ip):
            threats.append({
                "type": AttackType.SUSPICIOUS_PATTERN,
                "level": ThreatLevel.HIGH,
                "details": {"suspicious_ip": client_ip}
            })

        # Log security events
        for threat in threats:
            event = SecurityEvent(
                timestamp=datetime.now(timezone.utc),
                event_type=threat["type"],
                threat_level=threat["level"],
                source_ip=client_ip,
                user_agent=user_agent,
                endpoint=str(request.url.path),
                user_id=user_id,
                details=threat["details"],
                blocked=threat["level"] in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
            )
            self.security_events.append(event)

            if event.blocked:
                logger.warning(
                    "Security threat blocked",
                    event_type=threat["type"],
                    threat_level=threat["level"],
                    source_ip=client_ip,
                    endpoint=str(request.url.path)
                )

        return {
            "threats": threats,
            "blocked": any(t["level"] in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] for t in threats),
            "client_ip": client_ip
        }

    def validate_request_data(self, data: Any) -> Dict[str, Any]:
        """Validate request data for security issues"""
        return self.input_validator.validate_input(data)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        suspicious_patterns = [
            r"bot",
            r"crawler",
            r"spider",
            r"scraper",
            r"python-requests",
            r"curl",
            r"wget",
            r"sqlmap",
            r"nikto",
            r"nmap",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True

        return False

    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP is suspicious"""
        try:
            ip_obj = ipaddress.ip_address(ip)

            # Check for private/internal IPs (may be suspicious in production)
            if ip_obj.is_private and not ip_obj.is_loopback:
                return False  # Internal IPs are generally OK

            # Check for known malicious IP ranges (simplified)
            # In production, this would check against threat intelligence feeds
            suspicious_ranges = [
                "10.0.0.0/8",     # Private range (example)
                "192.168.0.0/16", # Private range (example)
            ]

            for range_str in suspicious_ranges:
                if ip_obj in ipaddress.ip_network(range_str):
                    return False  # Actually not suspicious for demo

        except ValueError:
            return True  # Invalid IP format is suspicious

        return False

    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security summary for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_events = [e for e in self.security_events if e.timestamp > cutoff_time]

        # Group by event type
        event_counts = defaultdict(int)
        threat_levels = defaultdict(int)
        top_ips = defaultdict(int)

        for event in recent_events:
            event_counts[event.event_type.value] += 1
            threat_levels[event.threat_level.value] += 1
            top_ips[event.source_ip] += 1

        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "event_types": dict(event_counts),
            "threat_levels": dict(threat_levels),
            "top_source_ips": dict(sorted(top_ips.items(), key=lambda x: x[1], reverse=True)[:10]),
            "blocked_requests": len([e for e in recent_events if e.blocked])
        }

class APIKeyManager:
    """Manages API keys for external access"""

    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.key_header = APIKeyHeader(name="X-API-Key")

    def create_api_key(self, name: str, permissions: List[str],
                      rate_limit: Optional[RateLimitRule] = None) -> str:
        """Create new API key"""
        if rate_limit is None:
            rate_limit = RateLimitRule(
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=5000
            )

        # Generate secure API key
        key = secrets.token_urlsafe(32)
        key_id = secrets.token_hex(8)
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            rate_limit=rate_limit,
            created_at=datetime.now(timezone.utc)
        )

        self.api_keys[key] = api_key
        return key

    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate API key and return associated data"""
        api_key = self.api_keys.get(key)
        if not api_key:
            return None

        if not api_key.is_active:
            return None

        if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
            return None

        # Update last used
        api_key.last_used = datetime.now(timezone.utc)
        return api_key

    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key"""
        if key in self.api_keys:
            self.api_keys[key].is_active = False
            return True
        return False

# Global instances
security_monitor = SecurityMonitor()
api_key_manager = APIKeyManager()
input_validator = InputValidator()
rate_limiter = RateLimiter()
