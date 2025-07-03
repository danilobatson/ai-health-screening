"""
Simplified database operations tests
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_, or_
from database.models import Base, Patient, HealthAssessment, SymptomRecord
import uuid


@pytest.fixture(scope="function")
async def test_session():
    """Create a test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///test_operations.db", echo=False)

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


class TestDatabaseOperations:
    """Test database CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_patient(self, test_session):
        """Test creating a patient"""
        patient = Patient(
            name="John Doe",
            age=30,
            gender="male",
            email="john@example.com"
        )

        test_session.add(patient)
        await test_session.commit()

        # Verify patient was created
        assert patient.id is not None
        assert patient.name == "John Doe"

    @pytest.mark.asyncio
    async def test_read_patient(self, test_session):
        """Test reading a patient"""
        # Create patient
        patient = Patient(name="Jane Doe", age=25, email="jane@example.com")
        test_session.add(patient)
        await test_session.commit()

        # Read patient back
        result = await test_session.execute(
            select(Patient).where(Patient.email == "jane@example.com")
        )
        retrieved_patient = result.scalar_one()

        assert retrieved_patient.name == "Jane Doe"
        assert retrieved_patient.age == 25

    @pytest.mark.asyncio
    async def test_update_patient(self, test_session):
        """Test updating a patient"""
        # Create patient
        patient = Patient(name="Bob Smith", age=35, email="bob@example.com")
        test_session.add(patient)
        await test_session.commit()

        # Update patient
        patient.age = 36
        await test_session.commit()

        # Verify update
        result = await test_session.execute(
            select(Patient).where(Patient.email == "bob@example.com")
        )
        updated_patient = result.scalar_one()

        assert updated_patient.age == 36

    @pytest.mark.asyncio
    async def test_delete_patient(self, test_session):
        """Test deleting a patient"""
        # Create patient
        patient = Patient(name="Delete Me", age=40, email="delete@example.com")
        test_session.add(patient)
        await test_session.commit()

        # Delete patient
        await test_session.delete(patient)
        await test_session.commit()

        # Verify deletion
        result = await test_session.execute(
            select(Patient).where(Patient.email == "delete@example.com")
        )
        deleted_patient = result.scalar_one_or_none()

        assert deleted_patient is None

    @pytest.mark.asyncio
    async def test_create_health_assessment(self, test_session):
        """Test creating a health assessment"""
        # Create patient first
        patient = Patient(name="Assessment Patient", age=30)
        test_session.add(patient)
        await test_session.commit()

        # Create assessment
        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["headache", "fever"],
            risk_level="medium",
            risk_score=60,
            urgency="normal",
            confidence_score=0.8
        )

        test_session.add(assessment)
        await test_session.commit()

        # Verify assessment was created
        assert assessment.id is not None
        assert assessment.patient_id == patient.id
        assert assessment.risk_level == "medium"

    @pytest.mark.asyncio
    async def test_query_assessments_by_risk_level(self, test_session):
        """Test querying assessments by risk level"""
        # Create patient
        patient = Patient(name="Risk Patient", age=30)
        test_session.add(patient)
        await test_session.commit()

        # Create assessments with different risk levels
        high_risk = HealthAssessment(
            patient_id=patient.id,
            symptoms=["chest pain"],
            risk_level="high",
            risk_score=90,
            urgency="urgent",
            confidence_score=0.9
        )

        low_risk = HealthAssessment(
            patient_id=patient.id,
            symptoms=["mild cough"],
            risk_level="low",
            risk_score=20,
            urgency="low",
            confidence_score=0.7
        )

        test_session.add_all([high_risk, low_risk])
        await test_session.commit()

        # Query high-risk assessments
        result = await test_session.execute(
            select(HealthAssessment).where(HealthAssessment.risk_level == "high")
        )
        high_risk_assessments = result.scalars().all()

        assert len(high_risk_assessments) == 1
        assert high_risk_assessments[0].risk_score == 90

    @pytest.mark.asyncio
    async def test_count_patients(self, test_session):
        """Test counting patients"""
        # Create multiple patients
        patients = [
            Patient(name=f"Patient {i}", age=20 + i, email=f"patient{i}@example.com")
            for i in range(5)
        ]

        test_session.add_all(patients)
        await test_session.commit()

        # Count patients
        result = await test_session.execute(select(func.count(Patient.id)))
        count = result.scalar()

        assert count == 5

    @pytest.mark.asyncio
    async def test_filter_patients_by_age(self, test_session):
        """Test filtering patients by age"""
        # Create patients with different ages
        patients = [
            Patient(name="Young Patient", age=20, email="young@example.com"),
            Patient(name="Middle Patient", age=40, email="middle@example.com"),
            Patient(name="Old Patient", age=60, email="old@example.com")
        ]

        test_session.add_all(patients)
        await test_session.commit()

        # Filter patients over 30
        result = await test_session.execute(
            select(Patient).where(Patient.age > 30)
        )
        older_patients = result.scalars().all()

        assert len(older_patients) == 2
        assert all(p.age > 30 for p in older_patients)

    @pytest.mark.asyncio
    async def test_join_query_patient_assessments(self, test_session):
        """Test joining patients with their assessments"""
        # Create patient
        patient = Patient(name="Join Patient", age=35, email="join@example.com")
        test_session.add(patient)
        await test_session.commit()

        # Create assessments
        assessments = [
            HealthAssessment(
                patient_id=patient.id,
                symptoms=[f"symptom{i}"],
                risk_level="medium",
                risk_score=50 + i,
                urgency="normal",
                confidence_score=0.8
            )
            for i in range(3)
        ]

        test_session.add_all(assessments)
        await test_session.commit()

        # Join query
        result = await test_session.execute(
            select(Patient.name, HealthAssessment.risk_score)
            .join(HealthAssessment)
            .where(Patient.email == "join@example.com")
        )

        join_results = result.fetchall()

        assert len(join_results) == 3
        assert all(row[0] == "Join Patient" for row in join_results)

    @pytest.mark.asyncio
    async def test_aggregate_functions(self, test_session):
        """Test aggregate functions"""
        # Create patient
        patient = Patient(name="Aggregate Patient", age=30)
        test_session.add(patient)
        await test_session.commit()

        # Create assessments with different risk scores
        risk_scores = [20, 40, 60, 80]
        assessments = [
            HealthAssessment(
                patient_id=patient.id,
                symptoms=["test"],
                risk_level="medium",
                risk_score=score,
                urgency="normal",
                confidence_score=0.8
            )
            for score in risk_scores
        ]

        test_session.add_all(assessments)
        await test_session.commit()

        # Test aggregations
        result = await test_session.execute(
            select(
                func.count(HealthAssessment.id),
                func.avg(HealthAssessment.risk_score),
                func.min(HealthAssessment.risk_score),
                func.max(HealthAssessment.risk_score)
            )
            .where(HealthAssessment.patient_id == patient.id)
        )

        count, avg_score, min_score, max_score = result.first()

        assert count == 4
        assert avg_score == 50.0  # (20+40+60+80)/4
        assert min_score == 20
        assert max_score == 80

    @pytest.mark.asyncio
    async def test_bulk_operations(self, test_session):
        """Test bulk insert operations"""
        # Create multiple patients in bulk
        patients = [
            Patient(name=f"Bulk Patient {i}", age=20 + i, email=f"bulk{i}@example.com")
            for i in range(10)
        ]

        test_session.add_all(patients)
        await test_session.commit()

        # Verify all patients were created
        result = await test_session.execute(
            select(func.count(Patient.id))
            .where(Patient.name.like("Bulk Patient%"))
        )
        count = result.scalar()

        assert count == 10

    @pytest.mark.asyncio
    async def test_complex_query_conditions(self, test_session):
        """Test complex query conditions with AND/OR"""
        # Create patients
        patients = [
            Patient(name="John", age=25, gender="male", email="john@test.com"),
            Patient(name="Jane", age=30, gender="female", email="jane@test.com"),
            Patient(name="Bob", age=35, gender="male", email="bob@test.com"),
            Patient(name="Alice", age=40, gender="female", email="alice@test.com")
        ]

        test_session.add_all(patients)
        await test_session.commit()

        # Complex query: males over 30 OR females under 35
        result = await test_session.execute(
            select(Patient).where(
                or_(
                    and_(Patient.gender == "male", Patient.age > 30),
                    and_(Patient.gender == "female", Patient.age < 35)
                )
            )
        )

        matching_patients = result.scalars().all()

        # Should match Bob (male, 35) and Jane (female, 30)
        assert len(matching_patients) == 2
        names = [p.name for p in matching_patients]
        assert "Bob" in names
        assert "Jane" in names
