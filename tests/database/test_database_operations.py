"""
Database operations tests - testing CRUD operations and business logic
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import Base, Patient, HealthAssessment, SymptomRecord
from database.database import get_db
from services.ai_health_service import AIHealthService
import uuid


class TestDatabaseOperations:
    """Test database CRUD operations"""

    def test_create_patient_with_assessment(self, db_session):
        """Test creating patient with associated assessment"""
        # Create patient
        patient_data = {
            "name": "Alice Johnson",
            "age": 32,
            "gender": "female",
            "email": "alice@example.com",
            "medical_history": [{"condition": "asthma", "diagnosed": "2018-03-15"}],
            "allergies": ["cats", "pollen"]
        }

        patient = Patient(**patient_data)
        db_session.add(patient)
        db_session.commit()

        # Create assessment
        assessment_data = {
            "patient_id": patient.id,
            "symptoms": ["shortness of breath", "wheezing"],
            "risk_level": "medium",
            "risk_score": 65,
            "urgency": "moderate",
            "confidence_score": 0.85,
            "ai_analysis": "Possible asthma exacerbation",
            "vital_signs": {"heart_rate": 95, "respiratory_rate": 22}
        }

        assessment = HealthAssessment(**assessment_data)
        db_session.add(assessment)
        db_session.commit()

        # Verify creation
        retrieved_patient = db_session.query(Patient).filter_by(email="alice@example.com").first()
        assert retrieved_patient is not None
        assert len(retrieved_patient.assessments) == 1
        assert retrieved_patient.assessments[0].risk_score == 65

    def test_update_patient_information(self, db_session):
        """Test updating patient information"""
        # Create patient
        patient = Patient(name="Bob Smith", age=28, email="bob@example.com")
        db_session.add(patient)
        db_session.commit()

        original_id = patient.id
        original_created = patient.created_at

        # Update patient
        patient.age = 29
        patient.phone = "+1-555-0123"
        patient.allergies = ["shellfish"]
        db_session.commit()

        # Verify update
        updated_patient = db_session.query(Patient).filter_by(id=original_id).first()
        assert updated_patient.age == 29
        assert updated_patient.phone == "+1-555-0123"
        assert "shellfish" in updated_patient.allergies
        assert updated_patient.created_at == original_created
        assert updated_patient.updated_at is not None

    def test_delete_patient_cascade(self, db_session):
        """Test that deleting patient removes all associated data"""
        # Create patient with assessment and symptoms
        patient = Patient(name="Test Delete", age=30)
        db_session.add(patient)
        db_session.commit()

        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["fever"],
            risk_level="low",
            risk_score=30,
            urgency="routine",
            confidence_score=0.6
        )
        db_session.add(assessment)
        db_session.commit()

        symptom = SymptomRecord(
            assessment_id=assessment.id,
            name="fever",
            severity="mild",
            duration_days=2
        )
        db_session.add(symptom)
        db_session.commit()

        patient_id = patient.id
        assessment_id = assessment.id
        symptom_id = symptom.id

        # Delete patient
        db_session.delete(patient)
        db_session.commit()

        # Verify cascade deletion
        assert db_session.query(Patient).filter_by(id=patient_id).first() is None
        assert db_session.query(HealthAssessment).filter_by(id=assessment_id).first() is None
        assert db_session.query(SymptomRecord).filter_by(id=symptom_id).first() is None


class TestDatabaseQueries:
    """Test complex database queries and analytics"""

    def test_patient_search(self, db_session):
        """Test patient search functionality"""
        # Create test patients
        patients = [
            Patient(name="John Smith", age=35, email="john.smith@email.com"),
            Patient(name="Jane Smith", age=42, email="jane.smith@email.com"),
            Patient(name="Bob Johnson", age=28, email="bob.johnson@email.com")
        ]

        for patient in patients:
            db_session.add(patient)
        db_session.commit()

        # Test name search
        smith_patients = db_session.query(Patient)\
            .filter(Patient.name.contains("Smith"))\
            .all()
        assert len(smith_patients) == 2

        # Test email search
        john_patient = db_session.query(Patient)\
            .filter(Patient.email.contains("john.smith"))\
            .first()
        assert john_patient.name == "John Smith"

    def test_assessment_analytics(self, db_session):
        """Test assessment analytics queries"""
        # Create patient
        patient = Patient(name="Analytics Test", age=40)
        db_session.add(patient)
        db_session.commit()

        # Create assessments with different risk levels
        risk_data = [
            {"risk_level": "low", "risk_score": 25},
            {"risk_level": "medium", "risk_score": 55},
            {"risk_level": "high", "risk_score": 85},
            {"risk_level": "medium", "risk_score": 60}
        ]

        for data in risk_data:
            assessment = HealthAssessment(
                patient_id=patient.id,
                symptoms=["test"],
                risk_level=data["risk_level"],
                risk_score=data["risk_score"],
                urgency="moderate",
                confidence_score=0.7
            )
            db_session.add(assessment)
        db_session.commit()

        # Test analytics queries
        total_assessments = db_session.query(HealthAssessment).count()
        assert total_assessments == 4

        high_risk_count = db_session.query(HealthAssessment)\
            .filter(HealthAssessment.risk_level == "high")\
            .count()
        assert high_risk_count == 1

        avg_risk_score = db_session.query(func.avg(HealthAssessment.risk_score)).scalar()
        assert abs(avg_risk_score - 56.25) < 0.01  # (25+55+85+60)/4 = 56.25

    def test_recent_assessments_query(self, db_session):
        """Test querying recent assessments"""
        # Create patient
        patient = Patient(name="Recent Test", age=30)
        db_session.add(patient)
        db_session.commit()

        # Create assessments with different timestamps
        now = datetime.utcnow()
        old_assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["old symptom"],
            risk_level="low",
            risk_score=20,
            urgency="routine",
            confidence_score=0.5
        )
        # Manually set old timestamp
        old_assessment.created_at = now - timedelta(days=10)

        recent_assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["recent symptom"],
            risk_level="medium",
            risk_score=50,
            urgency="moderate",
            confidence_score=0.7
        )

        db_session.add(old_assessment)
        db_session.add(recent_assessment)
        db_session.commit()

        # Query assessments from last 7 days
        cutoff_date = now - timedelta(days=7)
        recent_assessments = db_session.query(HealthAssessment)\
            .filter(HealthAssessment.created_at >= cutoff_date)\
            .all()

        assert len(recent_assessments) == 1
        assert recent_assessments[0].symptoms == ["recent symptom"]


class TestDatabasePerformance:
    """Test database performance and optimization"""

    def test_bulk_patient_creation(self, db_session):
        """Test bulk creation performance"""
        import time

        # Create 100 patients
        patients = []
        for i in range(100):
            patient = Patient(
                name=f"Patient {i}",
                age=20 + (i % 60),
                email=f"patient{i}@example.com"
            )
            patients.append(patient)

        start_time = time.time()
        db_session.add_all(patients)
        db_session.commit()
        end_time = time.time()

        # Should complete in reasonable time (under 1 second)
        assert end_time - start_time < 1.0

        # Verify all created
        patient_count = db_session.query(Patient).count()
        assert patient_count >= 100

    def test_indexed_queries(self, db_session):
        """Test that indexed fields perform well"""
        import time

        # Create patients with indexed fields
        for i in range(50):
            patient = Patient(
                name=f"Indexed Test {i}",
                age=25 + i,
                email=f"indexed{i}@example.com"
            )
            db_session.add(patient)
        db_session.commit()

        # Test email index performance
        start_time = time.time()
        patient = db_session.query(Patient)\
            .filter(Patient.email == "indexed25@example.com")\
            .first()
        end_time = time.time()

        assert patient is not None
        assert patient.name == "Indexed Test 25"
        # Should be very fast with index
        assert end_time - start_time < 0.1

    def test_complex_join_performance(self, db_session):
        """Test performance of complex joins"""
        import time

        # Create test data
        patient = Patient(name="Join Test", age=35)
        db_session.add(patient)
        db_session.commit()

        # Create multiple assessments with symptoms
        for i in range(20):
            assessment = HealthAssessment(
                patient_id=patient.id,
                symptoms=[f"symptom{i}"],
                risk_level="medium",
                risk_score=50 + i,
                urgency="moderate",
                confidence_score=0.7
            )
            db_session.add(assessment)
            db_session.commit()

            symptom = SymptomRecord(
                assessment_id=assessment.id,
                name=f"symptom{i}",
                severity="moderate",
                duration_days=i + 1
            )
            db_session.add(symptom)

        db_session.commit()

        # Test complex join query
        start_time = time.time()
        results = db_session.query(Patient)\
            .join(HealthAssessment)\
            .join(SymptomRecord)\
            .filter(SymptomRecord.severity == "moderate")\
            .all()
        end_time = time.time()

        assert len(results) == 20  # Should find all records
        # Should complete reasonably fast
        assert end_time - start_time < 0.5


class TestDatabaseConstraints:
    """Test database constraints and data integrity"""

    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraint enforcement"""
        # Try to create assessment with invalid patient_id
        assessment = HealthAssessment(
            patient_id="invalid-uuid",
            symptoms=["test"],
            risk_level="low",
            risk_score=30,
            urgency="routine",
            confidence_score=0.5
        )

        db_session.add(assessment)
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            db_session.commit()

    def test_required_field_constraints(self, db_session):
        """Test required field constraints"""
        # Try to create patient without required name
        patient = Patient(age=30)  # Missing required name

        db_session.add(patient)
        with pytest.raises(Exception):  # Should raise not null constraint error
            db_session.commit()

    def test_data_type_constraints(self, db_session):
        """Test data type constraints"""
        # Create patient with valid data
        patient = Patient(name="Type Test", age=30)
        db_session.add(patient)
        db_session.commit()

        # Try to create assessment with invalid risk_score type
        assessment = HealthAssessment(
            patient_id=patient.id,
            symptoms=["test"],
            risk_level="low",
            risk_score="invalid",  # Should be integer
            urgency="routine",
            confidence_score=0.5
        )

        db_session.add(assessment)
        with pytest.raises(Exception):  # Should raise data type error
            db_session.commit()


# Import the func from SQLAlchemy for analytics tests
from sqlalchemy.sql import func
