"""
Security module tests - Authentication, Authorization, and Security Features
"""
import pytest
import jwt
import time
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from unittest.mock import Mock, patch

from security.auth import (
    AuthenticationService, User, UserRole, Permission,
    auth_service, ROLE_PERMISSIONS
)
from security.privacy import (
    EncryptionService, DataAnonymizer, HIPAACompliance,
    EncryptionLevel, PIIType
)
from security.api_security import (
    InputValidator, RateLimiter, SecurityMonitor, APIKeyManager,
    ThreatLevel, AttackType
)


class TestAuthenticationService:
    """Test authentication and authorization"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        auth = AuthenticationService()
        password = "test_password_123"

        # Hash password
        hashed = auth.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long

        # Verify correct password
        assert auth.verify_password(password, hashed)

        # Verify incorrect password
        assert not auth.verify_password("wrong_password", hashed)

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        auth = AuthenticationService()

        # Create test user
        user = User(
            id="test-user-001",
            email="test@example.com",
            username="testuser",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True
        )

        # Create access token
        token = auth.create_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long

        # Verify token
        token_data = auth.verify_token(token)
        assert token_data.user_id == user.id
        assert token_data.username == user.username
        assert token_data.role == user.role
        assert Permission.READ_ASSESSMENTS.value in token_data.permissions

    def test_token_expiration(self):
        """Test token expiration handling"""
        auth = AuthenticationService()
        user = User(
            id="test-user-002",
            email="test2@example.com",
            username="testuser2",
            role=UserRole.PATIENT
        )

        # Create token with short expiration
        with patch('security.auth.ACCESS_TOKEN_EXPIRE_MINUTES', -1):
            token = auth.create_access_token(user)

            # Token should be expired and raise exception
            with pytest.raises(HTTPException) as exc_info:
                auth.verify_token(token)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_role_permissions(self):
        """Test role-based permission system"""
        auth = AuthenticationService()

        # Test admin has all permissions
        assert auth.check_permission(UserRole.ADMIN, Permission.ADMIN_ACCESS)
        assert auth.check_permission(UserRole.ADMIN, Permission.READ_ASSESSMENTS)
        assert auth.check_permission(UserRole.ADMIN, Permission.WRITE_ASSESSMENTS)

        # Test doctor has appropriate permissions
        assert auth.check_permission(UserRole.DOCTOR, Permission.READ_ASSESSMENTS)
        assert auth.check_permission(UserRole.DOCTOR, Permission.WRITE_ASSESSMENTS)
        assert not auth.check_permission(UserRole.DOCTOR, Permission.ADMIN_ACCESS)

        # Test patient has limited permissions
        assert auth.check_permission(UserRole.PATIENT, Permission.READ_ASSESSMENTS)
        assert not auth.check_permission(UserRole.PATIENT, Permission.WRITE_ASSESSMENTS)
        assert not auth.check_permission(UserRole.PATIENT, Permission.ADMIN_ACCESS)

    def test_user_authentication(self):
        """Test user authentication"""
        auth = AuthenticationService()

        # Test valid credentials
        user = auth.authenticate_user("admin", "admin123")
        assert user is not None
        assert user.username == "admin"
        assert user.role == UserRole.ADMIN

        user = auth.authenticate_user("doctor", "doctor123")
        assert user is not None
        assert user.username == "doctor"
        assert user.role == UserRole.DOCTOR

        # Test invalid credentials
        user = auth.authenticate_user("admin", "wrong_password")
        assert user is None

        user = auth.authenticate_user("nonexistent", "password")
        assert user is None

    def test_mfa_token_generation_and_verification(self):
        """Test MFA token functionality"""
        auth = AuthenticationService()

        # Generate MFA token
        token = auth.generate_mfa_token("user-123")
        assert isinstance(token, str)
        assert len(token) == 6  # 6-character hex code

        # Verify valid MFA token format
        assert auth.verify_mfa_token("user-123", "abc123")
        assert auth.verify_mfa_token("user-123", "123456")

        # Verify invalid MFA token format
        assert not auth.verify_mfa_token("user-123", "12345")  # Too short
        assert not auth.verify_mfa_token("user-123", "1234567")  # Too long
        assert not auth.verify_mfa_token("user-123", "12345!")  # Invalid character


class TestEncryptionService:
    """Test data encryption and privacy features"""

    def test_data_encryption_and_decryption(self):
        """Test data encryption and decryption"""
        encryption = EncryptionService()

        # Test string encryption
        original_data = "sensitive patient data"
        encrypted = encryption.encrypt_data(original_data)

        assert encrypted != original_data
        assert len(encrypted) > len(original_data)

        # Test decryption
        decrypted = encryption.decrypt_data(encrypted)
        assert decrypted == original_data

    def test_pii_hashing(self):
        """Test PII data hashing"""
        encryption = EncryptionService()

        # Test PII hashing with auto-generated salt
        pii_data = "john.doe@email.com"
        hashed1, salt1 = encryption.hash_pii(pii_data)

        assert hashed1 != pii_data
        assert len(hashed1) > 40  # Base64 encoded hash is long
        assert len(salt1) == 32  # Hex salt is 32 characters

        # Test PII hashing with provided salt
        hashed2, salt2 = encryption.hash_pii(pii_data, salt1)

        assert hashed1 == hashed2  # Same data + salt = same hash
        assert salt1 == salt2

        # Test different salt produces different hash
        hashed3, salt3 = encryption.hash_pii(pii_data)
        assert hashed1 != hashed3
        assert salt1 != salt3


class TestDataAnonymizer:
    """Test data anonymization for analytics"""

    def test_assessment_data_anonymization(self):
        """Test anonymization of assessment data"""
        anonymizer = DataAnonymizer()

        original_data = {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "555-123-4567",
            "age": 35,
            "location": "San Francisco, CA",
            "symptoms": ["headache", "fever"],
            "risk_score": 65
        }

        anonymized = anonymizer.anonymize_assessment_data(original_data)

        # Check that PII is anonymized
        assert anonymized["name"] != original_data["name"]
        assert anonymized["name"].startswith("Patient_")
        assert anonymized["email"] != original_data["email"]
        assert anonymized["email"].endswith("@example.com")

        # Check that age is generalized
        assert "age_range" in anonymized
        assert anonymized["age_range"] == "30-44"
        assert "age" not in anonymized

        # Check that location is generalized
        assert "region" in anonymized
        assert anonymized["region"] == "West Coast"
        assert "location" not in anonymized

        # Check that non-PII data is preserved
        assert anonymized["symptoms"] == original_data["symptoms"]
        assert anonymized["risk_score"] == original_data["risk_score"]

        # Check anonymization metadata
        assert "anonymized_at" in anonymized
        assert "anonymization_id" in anonymized

    def test_age_generalization(self):
        """Test age generalization ranges"""
        anonymizer = DataAnonymizer()

        # Test different age ranges
        assert anonymizer._generalize_age(15) == "0-17"
        assert anonymizer._generalize_age(25) == "18-29"
        assert anonymizer._generalize_age(35) == "30-44"
        assert anonymizer._generalize_age(55) == "45-59"
        assert anonymizer._generalize_age(65) == "60-74"
        assert anonymizer._generalize_age(80) == "75+"

    def test_location_generalization(self):
        """Test location generalization"""
        anonymizer = DataAnonymizer()

        # Test different regions
        assert anonymizer._generalize_location("San Francisco, CA") == "West Coast"
        assert anonymizer._generalize_location("New York, NY") == "Northeast"
        assert anonymizer._generalize_location("Austin, TX") == "Southeast"
        assert anonymizer._generalize_location("Denver, CO") == "Other US"


class TestHIPAACompliance:
    """Test HIPAA compliance features"""

    def test_data_access_logging(self):
        """Test data access audit logging"""
        hipaa = HIPAACompliance()

        # Log data access
        hipaa.log_data_access(
            user_id="doctor-001",
            action="view_patient_record",
            data_type="assessment_data",
            record_id="patient-123",
            purpose="patient_care"
        )

        assert len(hipaa.audit_logs) == 1
        log = hipaa.audit_logs[0]

        assert log.user_id == "doctor-001"
        assert log.action == "view_patient_record"
        assert log.data_type == "assessment_data"
        assert log.record_id == "patient-123"
        assert log.purpose == "patient_care"
        assert log.success is True

    def test_audit_trail_filtering(self):
        """Test audit trail filtering"""
        hipaa = HIPAACompliance()

        # Add multiple log entries
        users = ["user1", "user2", "user1"]
        for i, user in enumerate(users):
            hipaa.log_data_access(
                user_id=user,
                action=f"action_{i}",
                data_type="test_data"
            )

        # Test filtering by user
        user1_logs = hipaa.get_audit_trail(user_id="user1")
        assert len(user1_logs) == 2

        user2_logs = hipaa.get_audit_trail(user_id="user2")
        assert len(user2_logs) == 1

        # Test date filtering
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        future_logs = hipaa.get_audit_trail(start_date=future_date)
        assert len(future_logs) == 0

    def test_data_retention_checking(self):
        """Test data retention policy checking"""
        hipaa = HIPAACompliance()

        # Add old log entry (simulate by manipulating timestamp)
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=400)

        # Create a test audit log entry directly
        from security.privacy import AuditLog
        old_log = AuditLog(
            timestamp=old_timestamp,
            user_id="test",
            action="old_action",
            data_type="system_logs",
            record_id=None,
            classification=EncryptionLevel.CONFIDENTIAL,
            purpose="test",
            ip_address="test",
            success=True
        )
        hipaa.audit_logs.append(old_log)

        # Check retention
        expired_data = hipaa.check_data_retention()

        # Should find expired system logs (365 day retention vs 400 day old data)
        logs_expired = next(
            (item for item in expired_data if item["data_type"] == "system_logs"),
            None
        )
        assert logs_expired is not None
        assert logs_expired["expired_count"] > 0

    def test_privacy_notice_generation(self):
        """Test privacy notice generation"""
        hipaa = HIPAACompliance()

        notice = hipaa.generate_privacy_notice()

        # Check that notice contains required elements
        assert "NOTICE OF PRIVACY PRACTICES" in notice
        assert "YOUR RIGHTS" in notice
        assert "OUR USES AND DISCLOSURES" in notice
        assert "SECURITY MEASURES" in notice
        assert "encrypted" in notice.lower()
        assert "audit" in notice.lower()


class TestInputValidator:
    """Test input validation and sanitization"""

    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        validator = InputValidator()

        # Test safe input
        safe_input = "normal user input"
        result = validator.validate_input(safe_input)
        assert result["valid"] is True
        assert len(result["violations"]) == 0

        # Test SQL injection attempts
        sql_injections = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "1; DELETE FROM data; --"
        ]

        for injection in sql_injections:
            result = validator.validate_input(injection)
            assert result["valid"] is False
            assert len(result["violations"]) > 0
            assert any(v["type"] == "sql_injection" for v in result["violations"])

    def test_xss_detection(self):
        """Test XSS pattern detection"""
        validator = InputValidator()

        # Test XSS attempts
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='malicious.com'></iframe>"
        ]

        for xss in xss_attempts:
            result = validator.validate_input(xss)
            assert result["valid"] is False
            assert len(result["violations"]) > 0
            assert any(v["type"] == "xss" for v in result["violations"])

    def test_path_traversal_detection(self):
        """Test path traversal pattern detection"""
        validator = InputValidator()

        # Test path traversal attempts
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]

        for traversal in traversal_attempts:
            result = validator.validate_input(traversal)
            assert result["valid"] is False
            assert len(result["violations"]) > 0
            assert any(v["type"] == "path_traversal" for v in result["violations"])

    def test_nested_data_validation(self):
        """Test validation of nested data structures"""
        validator = InputValidator()

        # Test nested dict with malicious content
        nested_data = {
            "user": {
                "name": "John",
                "email": "<script>alert('xss')</script>",
                "preferences": {
                    "theme": "'; DROP TABLE themes; --"
                }
            },
            "comments": [
                "Normal comment",
                "javascript:alert('xss')"
            ]
        }

        result = validator.validate_input(nested_data)
        assert result["valid"] is False
        assert len(result["violations"]) >= 3  # XSS in email, SQL in theme, XSS in comment


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_rate_limit_enforcement(self):
        """Test rate limit enforcement"""
        limiter = RateLimiter()

        # Test within limits
        for i in range(10):
            result = limiter.check_rate_limit("test_user")
            assert result["allowed"] is True

        # Test exceeding minute limit
        for i in range(60):  # Default minute limit is 60
            limiter.check_rate_limit("test_user_heavy")

        # Next request should be blocked
        result = limiter.check_rate_limit("test_user_heavy")
        assert result["allowed"] is False
        assert result["reason"] == "rate_limit_minute"

    def test_different_identifiers(self):
        """Test rate limiting for different identifiers"""
        limiter = RateLimiter()

        # Test that different users have separate limits
        for i in range(30):
            result1 = limiter.check_rate_limit("user1")
            result2 = limiter.check_rate_limit("user2")
            assert result1["allowed"] is True
            assert result2["allowed"] is True


class TestSecurityMonitor:
    """Test security monitoring functionality"""

    def test_suspicious_user_agent_detection(self):
        """Test suspicious user agent detection"""
        monitor = SecurityMonitor()

        # Test legitimate user agents
        legitimate_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]

        for agent in legitimate_agents:
            assert not monitor._is_suspicious_user_agent(agent)

        # Test suspicious user agents
        suspicious_agents = [
            "python-requests/2.25.1",
            "curl/7.68.0",
            "sqlmap/1.4.6",
            "Mozilla/5.0 bot crawler"
        ]

        for agent in suspicious_agents:
            assert monitor._is_suspicious_user_agent(agent)

    def test_security_event_logging(self):
        """Test security event logging"""
        monitor = SecurityMonitor()

        # Create mock request
        mock_request = Mock()
        mock_request.url.path = "/api/test"
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "test-agent"}

        # Analyze request
        result = monitor.analyze_request(mock_request)

        assert "threats" in result
        assert "blocked" in result
        assert "client_ip" in result
        assert result["client_ip"] == "192.168.1.100"

    def test_security_summary_generation(self):
        """Test security summary generation"""
        monitor = SecurityMonitor()

        # Add some test events
        from security.api_security import SecurityEvent

        test_events = [
            SecurityEvent(
                timestamp=datetime.now(timezone.utc),
                event_type=AttackType.RATE_LIMIT_EXCEEDED,
                threat_level=ThreatLevel.MEDIUM,
                source_ip="192.168.1.1",
                user_agent="test",
                endpoint="/api/test",
                blocked=True
            )
        ]

        monitor.security_events.extend(test_events)

        # Generate summary
        summary = monitor.get_security_summary(hours=24)

        assert "total_events" in summary
        assert "event_types" in summary
        assert "threat_levels" in summary
        assert "blocked_requests" in summary
        assert summary["total_events"] >= len(test_events)


class TestAPIKeyManager:
    """Test API key management"""

    def test_api_key_creation(self):
        """Test API key creation"""
        manager = APIKeyManager()

        permissions = ["read:assessments", "write:assessments"]
        api_key = manager.create_api_key("test_app", permissions)

        assert isinstance(api_key, str)
        assert len(api_key) > 40  # Should be long and secure

        # Validate the created key
        key_data = manager.validate_api_key(api_key)
        assert key_data is not None
        assert key_data.name == "test_app"
        assert key_data.permissions == permissions
        assert key_data.is_active is True

    def test_api_key_validation(self):
        """Test API key validation"""
        manager = APIKeyManager()

        # Test invalid key
        invalid_key = "invalid_key_12345"
        result = manager.validate_api_key(invalid_key)
        assert result is None

        # Test valid key
        permissions = ["read:data"]
        valid_key = manager.create_api_key("valid_app", permissions)
        result = manager.validate_api_key(valid_key)
        assert result is not None
        assert result.name == "valid_app"

    def test_api_key_revocation(self):
        """Test API key revocation"""
        manager = APIKeyManager()

        # Create and revoke key
        permissions = ["read:assessments"]
        api_key = manager.create_api_key("revoke_test", permissions)

        # Key should be valid initially
        assert manager.validate_api_key(api_key) is not None

        # Revoke key
        success = manager.revoke_api_key(api_key)
        assert success is True

        # Key should no longer be valid
        assert manager.validate_api_key(api_key) is None

        # Revoking non-existent key should fail
        fake_key = "fake_key_123"
        success = manager.revoke_api_key(fake_key)
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
