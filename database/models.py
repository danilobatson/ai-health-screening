# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class Patient(Base):
    """Patient model with comprehensive health data"""
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    # Medical information
    medical_history = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    medications = Column(JSON, default=list)
    emergency_contact = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    assessments = relationship("HealthAssessment", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.id}, name={self.name}, age={self.age})>"

class HealthAssessment(Base):
    """Health assessment records with AI analysis"""
    __tablename__ = "health_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)

    # Assessment data
    symptoms = Column(JSON, nullable=False)
    risk_level = Column(String(20), nullable=False)
    risk_score = Column(Integer, nullable=False)
    urgency = Column(String(20), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.5)

    # AI Analysis
    ai_recommendations = Column(JSON, default=list)
    ai_analysis = Column(Text, nullable=True)
    ai_model_used = Column(String(50), nullable=True)

    # Clinical data
    vital_signs = Column(JSON, nullable=True)
    assessment_notes = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(String(20), default="pending")
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="assessments")
    symptoms_detail = relationship("SymptomRecord", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<HealthAssessment(id={self.id}, patient_id={self.patient_id}, risk_level={self.risk_level})>"

class SymptomRecord(Base):
    """Detailed symptom tracking"""
    __tablename__ = "symptom_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String, ForeignKey("health_assessments.id"), nullable=False, index=True)

    # Symptom details
    name = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    duration_days = Column(Integer, nullable=True)
    location = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Symptom characteristics
    onset = Column(String(50), nullable=True)
    frequency = Column(String(50), nullable=True)
    triggers = Column(JSON, default=list)
    pain_scale = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assessment = relationship("HealthAssessment", back_populates="symptoms_detail")

    def __repr__(self):
        return f"<SymptomRecord(id={self.id}, name={self.name}, severity={self.severity})>"
