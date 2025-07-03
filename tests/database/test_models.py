"""
Database model tests - comprehensive testing of SQLAlchemy models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from database.models import Base, Patient, HealthAssessment, SymptomRecord
import uuid
import asyncio


class TestPatientModel:
    """Test Patient model functionality"""

    def test_patient_creation(self, db_session):
        """Test basic patient creation"""
        patient = Patient(
            name="John Doe",
            age=30,
            gender="male",
            email="john.doe@example.com"
        )
        db_session.add(patient)
        db_session.commit()

        assert patient.id is not None
        assert patient.name == "John Doe"
        assert patient.age == 30
"""
Database model tests - comprehensive testing of SQLAlchemy models
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base, Patient, HealthAssessment, SymptomRecord
import uuid
import os


@pytest.fixture
async def async_session():
    """Create async test database session"""
    # Use SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///test.db", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


class TestPatientModel:
    """Test Patient model functionality"""

    async def test_patient_creation(self, async_session):
        """Test basic patient creation"""
        patient = Patient(
            name="John Doe",
            age=30,
            gender="male",
            email="john.doe@example.com"
        )
        async_session.add(patient)
        await async_session.commit()

        assert patient.id is not None
        assert patient.name == "John Doe"
        assert patient.age == 30
        assert patient.is_active is True
        assert patient.created_at is not None

    async def test_patient_relationships(self, async_session):
        """Test patient-assessment relationships"""
        # Create patient
        patient = Patient(name="Jane Doe", age=25, gender="female")
        async_session.add(patient)
        await async_session.commit()

        # Create assessment
        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["headache", "fever"],
            risk_level="medium",
            risk_score=60,
            urgency="moderate",
            confidence_score=0.8
        )
        async_session.add(assessment)
        await async_session.commit()

        # Test relationship
        await async_session.refresh(patient)
        await async_session.refresh(assessment)

        assert len(patient.assessments) == 1
        assert patient.assessments[0].id == assessment.id
        assert assessment.patient.id == patient.id
        db_session.commit()

        # Test relationship
        assert len(patient.assessments) == 1
        assert patient.assessments[0].risk_level == "medium"
        assert assessment.patient.name == "Jane Doe"

    def test_patient_medical_history_json(self, db_session):
        """Test JSON field functionality"""
        medical_history = [
            {"condition": "diabetes", "diagnosed": "2020-01-01"},
            {"condition": "hypertension", "diagnosed": "2019-06-15"}
        ]

        patient = Patient(
            name="Medical Test",
            age=45,
            medical_history=medical_history,
            allergies=["penicillin", "shellfish"]
        )
        db_session.add(patient)
        db_session.commit()

        # Refresh from database
        db_session.refresh(patient)

        assert len(patient.medical_history) == 2
        assert patient.medical_history[0]["condition"] == "diabetes"
        assert "penicillin" in patient.allergies

    def test_patient_unique_email(self, db_session):
        """Test email uniqueness constraint"""
        patient1 = Patient(name="Test 1", age=30, email="test@example.com")
        patient2 = Patient(name="Test 2", age=25, email="test@example.com")

        db_session.add(patient1)
        db_session.commit()

        db_session.add(patient2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestHealthAssessmentModel:
    """Test HealthAssessment model functionality"""

    def test_assessment_creation(self, db_session, sample_patient):
        """Test health assessment creation"""
        assessment = HealthAssessment(
            patient_id=sample_patient.id,
            symptoms=["headache", "nausea", "dizziness"],
            risk_level="high",
            risk_score=85,
            urgency="immediate",
            confidence_score=0.9,
            ai_analysis="Potential migraine or neurological issue",
            ai_model_used="gemini-pro"
        )
        db_session.add(assessment)
        db_session.commit()

        assert assessment.id is not None
        assert assessment.risk_score == 85
        assert assessment.status == "pending"
        assert assessment.follow_up_required is False
        assert assessment.created_at is not None

    def test_assessment_with_symptoms_detail(self, db_session, sample_patient):
        """Test assessment with detailed symptom records"""
        assessment = HealthAssessment(
            patient_id=sample_patient.id,
            symptoms=["headache"],
            risk_level="medium",
            risk_score=60,
            urgency="moderate",
            confidence_score=0.7
        )
        db_session.add(assessment)
        db_session.commit()

        # Add detailed symptom
        symptom = SymptomRecord(
            assessment_id=assessment.id,
            name="headache",
            severity="severe",
            duration_days=3,
            location="frontal",
            pain_scale=8,
            triggers=["stress", "lack of sleep"]
        )
        db_session.add(symptom)
        db_session.commit()

        # Test relationships
        assert len(assessment.symptoms_detail) == 1
        assert assessment.symptoms_detail[0].name == "headache"
        assert symptom.assessment.patient_id == sample_patient.id

    def test_assessment_status_updates(self, db_session, sample_patient):
        """Test assessment status tracking"""
        assessment = HealthAssessment(
            patient_id=sample_patient.id,
            symptoms=["fever"],
            risk_level="low",
            risk_score=30,
            urgency="routine",
            confidence_score=0.6
        )
        db_session.add(assessment)
        db_session.commit()

        # Update status
        assessment.status = "reviewed"
        assessment.reviewed_by = "Dr. Smith"
        assessment.reviewed_at = datetime.utcnow()
        assessment.follow_up_required = True
        assessment.follow_up_date = datetime.utcnow() + timedelta(days=7)

        db_session.commit()
        db_session.refresh(assessment)

        assert assessment.status == "reviewed"
        assert assessment.reviewed_by == "Dr. Smith"
        assert assessment.follow_up_required is True
        assert assessment.follow_up_date is not None


class TestSymptomRecordModel:
    """Test SymptomRecord model functionality"""

    def test_symptom_record_creation(self, db_session, sample_assessment):
        """Test symptom record creation"""
        symptom = SymptomRecord(
            assessment_id=sample_assessment.id,
            name="chest pain",
            severity="moderate",
            duration_days=2,
            location="center chest",
            description="Sharp pain when breathing",
            onset="sudden",
            frequency="intermittent",
            pain_scale=6,
            triggers=["deep breathing", "movement"]
        )
        db_session.add(symptom)
        db_session.commit()

        assert symptom.id is not None
        assert symptom.name == "chest pain"
        assert symptom.pain_scale == 6
        assert "deep breathing" in symptom.triggers
        assert symptom.created_at is not None

    def test_symptom_cascade_delete(self, db_session, sample_patient):
        """Test that symptoms are deleted when assessment is deleted"""
        assessment = HealthAssessment(
            patient_id=sample_patient.id,
            symptoms=["cough"],
            risk_level="low",
            risk_score=25,
            urgency="routine",
            confidence_score=0.5
        )
        db_session.add(assessment)
        db_session.commit()

        symptom = SymptomRecord(
            assessment_id=assessment.id,
            name="cough",
            severity="mild",
            duration_days=5
        )
        db_session.add(symptom)
        db_session.commit()

        symptom_id = symptom.id

        # Delete assessment
        db_session.delete(assessment)
        db_session.commit()

        # Verify symptom was deleted
        deleted_symptom = db_session.query(SymptomRecord).filter_by(id=symptom_id).first()
        assert deleted_symptom is None


class TestModelIntegration:
    """Test model integration and complex queries"""

    def test_patient_assessment_history(self, db_session):
        """Test querying patient assessment history"""
        # Create patient with multiple assessments
        patient = Patient(name="History Test", age=40, gender="female")
        db_session.add(patient)
        db_session.commit()

        # Create assessments over time
        assessments_data = [
            {"symptoms": ["headache"], "risk_level": "low", "risk_score": 20},
            {"symptoms": ["fever", "cough"], "risk_level": "medium", "risk_score": 50},
            {"symptoms": ["chest pain"], "risk_level": "high", "risk_score": 80}
        ]

        for data in assessments_data:
            assessment = HealthAssessment(
                patient_id=patient.id,
                symptoms=data["symptoms"],
                risk_level=data["risk_level"],
                risk_score=data["risk_score"],
                urgency="moderate",
                confidence_score=0.7
            )
            db_session.add(assessment)

        db_session.commit()

        # Query assessment history
        history = db_session.query(HealthAssessment)\
            .filter_by(patient_id=patient.id)\
            .order_by(HealthAssessment.created_at.desc())\
            .all()

        assert len(history) == 3
        assert history[0].risk_score == 80  # Most recent (highest risk)
        assert history[-1].risk_score == 20  # Oldest (lowest risk)

    def test_high_risk_patients_query(self, db_session):
        """Test querying high-risk patients"""
        # Create patients with different risk levels
        patients_data = [
            {"name": "Low Risk", "age": 25, "risk_score": 20},
            {"name": "Medium Risk", "age": 35, "risk_score": 60},
            {"name": "High Risk", "age": 45, "risk_score": 90}
        ]

        for data in patients_data:
            patient = Patient(name=data["name"], age=data["age"])
            db_session.add(patient)
            db_session.commit()

            assessment = HealthAssessment(
                patient_id=patient.id,
                symptoms=["test"],
                risk_level="high" if data["risk_score"] > 70 else "medium" if data["risk_score"] > 40 else "low",
                risk_score=data["risk_score"],
                urgency="immediate" if data["risk_score"] > 70 else "moderate",
                confidence_score=0.8
            )
            db_session.add(assessment)

        db_session.commit()

        # Query high-risk patients
        high_risk_patients = db_session.query(Patient)\
            .join(HealthAssessment)\
            .filter(HealthAssessment.risk_score > 70)\
            .all()

        assert len(high_risk_patients) == 1
        assert high_risk_patients[0].name == "High Risk"
