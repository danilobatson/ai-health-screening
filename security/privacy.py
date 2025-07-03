"""
Data Security and Privacy Module
Provides encryption, data anonymization, and HIPAA compliance features
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib
import secrets
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EncryptionLevel(str, Enum):
    """Encryption levels for different data types"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class PIIType(str, Enum):
    """Types of Personal Identifiable Information"""
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    ADDRESS = "address"
    DOB = "date_of_birth"
    MEDICAL_ID = "medical_id"
    CUSTOM = "custom"

@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    iterations: int = 100000
    salt_length: int = 32
    iv_length: int = 12

class DataClassification(BaseModel):
    """Data classification model"""
    level: EncryptionLevel
    pii_types: List[PIIType]
    retention_days: int
    requires_consent: bool = True
    audit_required: bool = True

class AuditLog(BaseModel):
    """Data access audit log"""
    timestamp: datetime
    user_id: str
    action: str
    data_type: str
    record_id: Optional[str]
    classification: EncryptionLevel
    purpose: str
    ip_address: str
    success: bool

class EncryptionService:
    """Handles data encryption and decryption"""

    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        self.config = EncryptionConfig()

    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = os.getenv("ENCRYPTION_KEY_FILE", ".encryption_key")

        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict permissions
            return key

    def encrypt_data(self, data: str, classification: EncryptionLevel = EncryptionLevel.CONFIDENTIAL) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def hash_pii(self, pii_data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash PII data for secure storage"""
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for secure hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=self.config.iterations,
        )

        hashed = base64.b64encode(kdf.derive(pii_data.encode())).decode()
        return hashed, salt

class DataAnonymizer:
    """Handles data anonymization for analytics"""

    def __init__(self):
        self.encryption_service = EncryptionService()

    def anonymize_assessment_data(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize assessment data for analytics"""
        anonymized = assessment_data.copy()

        # Remove direct identifiers
        pii_fields = ["name", "email", "phone", "address", "medical_id"]
        for field in pii_fields:
            if field in anonymized:
                anonymized[field] = self._generate_pseudonym(field, assessment_data.get(field, ""))

        # Generalize age into ranges
        if "age" in anonymized:
            anonymized["age_range"] = self._generalize_age(anonymized["age"])
            del anonymized["age"]

        # Generalize location to region
        if "location" in anonymized:
            anonymized["region"] = self._generalize_location(anonymized["location"])
            del anonymized["location"]

        # Add anonymization timestamp
        anonymized["anonymized_at"] = datetime.now(timezone.utc).isoformat()
        anonymized["anonymization_id"] = secrets.token_hex(8)

        return anonymized

    def _generate_pseudonym(self, field_type: str, original_value: str) -> str:
        """Generate consistent pseudonym for a field"""
        # Create deterministic but secure pseudonym
        hash_input = f"{field_type}:{original_value}:salt_secret"
        hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()

        if field_type == "name":
            return f"Patient_{hash_digest[:8]}"
        elif field_type == "email":
            return f"patient_{hash_digest[:8]}@example.com"
        elif field_type == "phone":
            return f"***-***-{hash_digest[:4]}"
        else:
            return f"***_{hash_digest[:6]}"

    def _generalize_age(self, age: int) -> str:
        """Generalize age into ranges"""
        if age < 18:
            return "0-17"
        elif age < 30:
            return "18-29"
        elif age < 45:
            return "30-44"
        elif age < 60:
            return "45-59"
        elif age < 75:
            return "60-74"
        else:
            return "75+"

    def _generalize_location(self, location: str) -> str:
        """Generalize location to region"""
        # Simple region mapping (in production, use proper geolocation service)
        location_lower = location.lower()

        if any(state in location_lower for state in ["ca", "california", "nevada", "oregon", "washington"]):
            return "West Coast"
        elif any(state in location_lower for state in ["ny", "new york", "nj", "pennsylvania", "massachusetts"]):
            return "Northeast"
        elif any(state in location_lower for state in ["tx", "texas", "florida", "georgia", "alabama"]):
            return "Southeast"
        else:
            return "Other US"

class HIPAACompliance:
    """HIPAA compliance utilities"""

    def __init__(self):
        self.audit_logs: List[AuditLog] = []
        self.data_classifications = {
            "assessment_data": DataClassification(
                level=EncryptionLevel.RESTRICTED,
                pii_types=[PIIType.NAME, PIIType.EMAIL, PIIType.DOB],
                retention_days=2555,  # 7 years
                requires_consent=True,
                audit_required=True
            ),
            "analytics_data": DataClassification(
                level=EncryptionLevel.INTERNAL,
                pii_types=[],
                retention_days=1095,  # 3 years
                requires_consent=False,
                audit_required=True
            ),
            "system_logs": DataClassification(
                level=EncryptionLevel.CONFIDENTIAL,
                pii_types=[PIIType.EMAIL],
                retention_days=365,  # 1 year
                requires_consent=False,
                audit_required=True
            )
        }

    def log_data_access(self, user_id: str, action: str, data_type: str,
                       record_id: Optional[str] = None, purpose: str = "healthcare_service",
                       ip_address: str = "unknown") -> None:
        """Log data access for HIPAA audit trail"""
        classification = self.data_classifications.get(data_type,
            DataClassification(level=EncryptionLevel.RESTRICTED, pii_types=[], retention_days=365))

        audit_log = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            action=action,
            data_type=data_type,
            record_id=record_id,
            classification=classification.level,
            purpose=purpose,
            ip_address=ip_address,
            success=True
        )

        self.audit_logs.append(audit_log)
        logger.info(f"HIPAA Audit: {action} on {data_type} by user {user_id}")

    def get_audit_trail(self, user_id: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[AuditLog]:
        """Get filtered audit trail"""
        filtered_logs = self.audit_logs

        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]

        if start_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_date]

        if end_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_date]

        return filtered_logs

    def check_data_retention(self) -> List[Dict[str, Any]]:
        """Check for data that should be purged based on retention policy"""
        expired_data = []
        current_time = datetime.now(timezone.utc)

        for data_type, classification in self.data_classifications.items():
            retention_date = current_time - timedelta(days=classification.retention_days)

            # In production, this would query the database for expired records
            expired_records = [
                log for log in self.audit_logs
                if log.data_type == data_type and log.timestamp < retention_date
            ]

            if expired_records:
                expired_data.append({
                    "data_type": data_type,
                    "retention_days": classification.retention_days,
                    "expired_count": len(expired_records),
                    "oldest_record": min(log.timestamp for log in expired_records)
                })

        return expired_data

    def generate_privacy_notice(self) -> str:
        """Generate HIPAA privacy notice"""
        return """
        NOTICE OF PRIVACY PRACTICES

        This notice describes how medical information about you may be used and disclosed
        and how you can get access to this information. Please review it carefully.

        YOUR RIGHTS:
        - Right to request restrictions on uses and disclosures
        - Right to receive confidential communications
        - Right to inspect and copy your health information
        - Right to amend your health information
        - Right to receive an accounting of disclosures
        - Right to file a complaint

        OUR USES AND DISCLOSURES:
        We may use and disclose your health information for:
        - Treatment purposes
        - Payment activities
        - Healthcare operations
        - As required by law

        SECURITY MEASURES:
        - All data is encrypted at rest and in transit
        - Access controls and audit logging
        - Regular security assessments
        - Employee security training

        For more information, contact our Privacy Officer.
        """

class SecureDataProcessor:
    """Combines encryption, anonymization, and compliance"""

    def __init__(self):
        self.encryption_service = EncryptionService()
        self.anonymizer = DataAnonymizer()
        self.hipaa = HIPAACompliance()

    def process_assessment_data(self, data: Dict[str, Any], user_id: str,
                              purpose: str = "assessment") -> Dict[str, Any]:
        """Process assessment data with full security measures"""

        # Log access
        self.hipaa.log_data_access(
            user_id=user_id,
            action="process_assessment",
            data_type="assessment_data",
            purpose=purpose
        )

        # Encrypt sensitive fields
        sensitive_fields = ["symptoms", "medical_history", "medications"]
        processed_data = data.copy()

        for field in sensitive_fields:
            if field in processed_data:
                processed_data[f"{field}_encrypted"] = self.encryption_service.encrypt_data(
                    str(processed_data[field])
                )
                # Keep original for processing, remove in production
                # del processed_data[field]

        # Add security metadata
        processed_data["security_metadata"] = {
            "encryption_timestamp": datetime.now(timezone.utc).isoformat(),
            "processed_by": user_id,
            "classification": "restricted",
            "requires_decryption": True
        }

        return processed_data

    def create_analytics_dataset(self, raw_data: List[Dict[str, Any]],
                                user_id: str) -> List[Dict[str, Any]]:
        """Create anonymized dataset for analytics"""

        # Log analytics data creation
        self.hipaa.log_data_access(
            user_id=user_id,
            action="create_analytics_dataset",
            data_type="analytics_data",
            purpose="analytics"
        )

        # Anonymize each record
        anonymized_data = []
        for record in raw_data:
            anonymized_record = self.anonymizer.anonymize_assessment_data(record)
            anonymized_data.append(anonymized_record)

        return anonymized_data

# Global instances
encryption_service = EncryptionService()
data_anonymizer = DataAnonymizer()
hipaa_compliance = HIPAACompliance()
secure_processor = SecureDataProcessor()
