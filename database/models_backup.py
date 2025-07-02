# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()

class Patient(Base):
    """Modern Patient model with comprehensive health data"""
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    # Medical information
    medical_history = Column(JSON, default=list)  # List of conditions
    allergies = Column(JSON, default=list)        # List of allergies
    medications = Column(JSON, default=list)      # Current medications
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
    symptoms = Column(JSON, nullable=False)  # List of symptom objects
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High
    risk_score = Column(Integer, nullable=False)
    urgency = Column(String(20), nullable=False)  # Routine, Monitor, Urgent, Emergency
    confidence_score = Column(Float, nullable=False, default=0.5)

    # AI Analysis
    ai_recommendations = Column(JSON, default=list)
    ai_analysis = Column(Text, nullable=True)  # Detailed AI analysis
    ai_model_used = Column(String(50), nullable=True)  # "gemini-pro", "gpt-4", etc.

    # Clinical data
    vital_signs = Column(JSON, nullable=True)  # Blood pressure, heart rate, etc.
    assessment_notes = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(String(20), default="pending")  # pending, reviewed, completed
    reviewed_by = Column(String(100), nullable=True)  # Healthcare provider name
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
    severity = Column(String(20), nullable=False)  # mild, moderate, severe
    duration_days = Column(Integer, nullable=True)
    location = Column(String(100), nullable=True)  # Body location
    description = Column(Text, nullable=True)

    # Symptom characteristics
    onset = Column(String(50), nullable=True)  # sudden, gradual
    frequency = Column(String(50), nullable=True)  # constant, intermittent
    triggers = Column(JSON, default=list)  # What makes it worse/better

    # Pain scale (1-10)
    pain_scale = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assessment = relationship("HealthAssessment", back_populates="symptoms_detail")

    def __repr__(self):
        return f"<SymptomRecord(id={self.id}, name={self.name}, severity={self.severity})>"

class HealthProvider(Base):
    """Healthcare providers who review assessments"""
    __tablename__ = "health_providers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)  # MD, NP, PA, etc.
    specialization = Column(String(100), nullable=True)
    license_number = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)

    # Professional info
    years_experience = Column(Integer, nullable=True)
    institution = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)

    # System access
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default="provider")  # provider, admin, specialist

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<HealthProvider(id={self.id}, name={self.name}, title={self.title})>"

class AssessmentAnalytics(Base):
    """Analytics and reporting data"""
    __tablename__ = "assessment_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    week_of_year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    # Metrics
    total_assessments = Column(Integer, default=0)
    high_risk_assessments = Column(Integer, default=0)
    medium_risk_assessments = Column(Integer, default=0)
    low_risk_assessments = Column(Integer, default=0)

    # Response times
    avg_assessment_time_seconds = Column(Float, nullable=True)
    avg_ai_processing_time_seconds = Column(Float, nullable=True)

    # Common symptoms
    top_symptoms = Column(JSON, default=list)  # Most common symptoms

    # Age demographics
    avg_patient_age = Column(Float, nullable=True)
    pediatric_assessments = Column(Integer, default=0)  # <18
    adult_assessments = Column(Integer, default=0)      # 18-64
    elderly_assessments = Column(Integer, default=0)    # 65+

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AssessmentAnalytics(date={self.date}, total_assessments={self.total_assessments})>"
