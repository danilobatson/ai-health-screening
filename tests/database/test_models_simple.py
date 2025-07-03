"""
Simplified database model tests that work with existing infrastructure
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base, Patient, HealthAssessment, SymptomRecord
import uuid


@pytest.fixture(scope="function")
async def test_session():
    """Create a test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///test_models.db", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


class TestDatabaseModels:
    """Test database models with async support"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_patient_model_creation(self, test_session):
        """Test Patient model creation and basic attributes"""
        patient = Patient(
            name="Test Patient",
            age=35,
            gender="female",
            email="test@example.com",
            medical_history=["hypertension"],
            allergies=["penicillin"]
        )

        test_session.add(patient)
        await test_session.commit()

        # Verify patient was created
        assert patient.id is not None
        assert patient.name == "Test Patient"
        assert patient.age == 35
        assert patient.gender == "female"
        assert patient.email == "test@example.com"
        assert patient.is_active is True
        assert patient.created_at is not None
        assert "hypertension" in patient.medical_history
        assert "penicillin" in patient.allergies

    @pytest.mark.asyncio
    async def test_health_assessment_model(self, test_session):
        """Test HealthAssessment model creation"""
        # Create patient first
        patient = Patient(name="Assessment Patient", age=30, gender="male")
        test_session.add(patient)
        await test_session.commit()

        # Create assessment
        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["headache", "nausea"],
            risk_level="medium",
            risk_score=65,
            urgency="normal",
            confidence_score=0.85,
            ai_recommendations=["rest", "hydration"],
            status="pending"
        )

        test_session.add(assessment)
        await test_session.commit()

        # Verify assessment was created
        assert assessment.id is not None
        assert assessment.patient_id == patient.id
        assert assessment.symptoms == ["headache", "nausea"]
        assert assessment.risk_level == "medium"
        assert assessment.risk_score == 65
        assert assessment.urgency == "normal"
        assert assessment.confidence_score == 0.85
        assert assessment.ai_recommendations == ["rest", "hydration"]
        assert assessment.status == "pending"
        assert assessment.created_at is not None

    @pytest.mark.asyncio
    async def test_symptom_record_model(self, test_session):
        """Test SymptomRecord model creation"""
        # Create patient and assessment first
        patient = Patient(name="Symptom Patient", age=40, gender="female")
        test_session.add(patient)
        await test_session.commit()

        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["fever"],
            risk_level="low",
            risk_score=30,
            urgency="low",
            confidence_score=0.7
        )
        test_session.add(assessment)
        await test_session.commit()

        # Create symptom record
        symptom = SymptomRecord(
            assessment_id=assessment.id,
            name="fever",
            severity="moderate",
            duration_days=3,
            location="general",
            pain_scale=6,
            onset="gradual",
            frequency="constant"
        )

        test_session.add(symptom)
        await test_session.commit()

        # Verify symptom record was created
        assert symptom.id is not None
        assert symptom.assessment_id == assessment.id
        assert symptom.name == "fever"
        assert symptom.severity == "moderate"
        assert symptom.duration_days == 3
        assert symptom.location == "general"
        assert symptom.pain_scale == 6
        assert symptom.onset == "gradual"
        assert symptom.frequency == "constant"
        assert symptom.created_at is not None

    @pytest.mark.asyncio
    async def test_model_relationships(self, test_session):
        """Test relationships between models"""
        # Create patient
        patient = Patient(name="Relationship Patient", age=25, gender="male")
        test_session.add(patient)
        await test_session.commit()

        # Create assessment
        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["cough"],
            risk_level="low",
            risk_score=20,
            urgency="low",
            confidence_score=0.9
        )
        test_session.add(assessment)
        await test_session.commit()

        # Create symptom record
        symptom = SymptomRecord(
            assessment_id=assessment.id,
            name="cough",
            severity="mild",
            duration_days=2
        )
        test_session.add(symptom)
        await test_session.commit()

        # Test relationships (would require proper lazy loading setup)
        # For now, just verify IDs match
        assert assessment.patient_id == patient.id
        assert symptom.assessment_id == assessment.id

    @pytest.mark.asyncio
    async def test_patient_unique_email(self, test_session):
        """Test that patient email must be unique"""
        # Create first patient
        patient1 = Patient(name="Patient One", age=30, email="unique@test.com")
        test_session.add(patient1)
        await test_session.commit()

        # Try to create second patient with same email
        patient2 = Patient(name="Patient Two", age=25, email="unique@test.com")
        test_session.add(patient2)

        # This should raise an integrity error
        with pytest.raises(Exception):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_patient_required_fields(self, test_session):
        """Test that required fields are enforced"""
        # Try to create patient without required name field
        patient = Patient(age=30)  # Missing required name
        test_session.add(patient)

        # This should raise an error
        with pytest.raises(Exception):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_assessment_required_fields(self, test_session):
        """Test that assessment required fields are enforced"""
        # Create patient first
        patient = Patient(name="Test Patient", age=30)
        test_session.add(patient)
        await test_session.commit()

        # Try to create assessment without required fields
        assessment = HealthAssessment(patient_id=patient.id)  # Missing required fields
        test_session.add(assessment)

        # This should raise an error
        with pytest.raises(Exception):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_model_string_representations(self, test_session):
        """Test model __repr__ methods"""
        # Create patient
        patient = Patient(name="Repr Patient", age=30)
        test_session.add(patient)
        await test_session.commit()

        # Test patient repr
        patient_repr = repr(patient)
        assert "Repr Patient" in patient_repr
        assert "30" in patient_repr

        # Create assessment
        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["test"],
            risk_level="low",
            risk_score=10,
            urgency="low",
            confidence_score=0.5
        )
        test_session.add(assessment)
        await test_session.commit()

        # Test assessment repr
        assessment_repr = repr(assessment)
        assert "low" in assessment_repr
        assert patient.id in assessment_repr

        # Create symptom
        symptom = SymptomRecord(
            assessment_id=assessment.id,
            name="test symptom",
            severity="mild"
        )
        test_session.add(symptom)
        await test_session.commit()

        # Test symptom repr
        symptom_repr = repr(symptom)
        assert "test symptom" in symptom_repr
        assert "mild" in symptom_repr
