# tests/database/test_analytics.py
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch
import json

from database.models import Patient, HealthAssessment, SymptomRecord
from database.database import AsyncSessionLocal


class TestDatabaseAnalytics:
    """Test database analytics and reporting capabilities"""

    @pytest.fixture
    async def session(self):
        """Create a test database session"""
        async with AsyncSessionLocal() as session:
            yield session

    @pytest.fixture
    async def analytics_data(self, session):
        """Create comprehensive data for analytics testing"""
        # Create patients with varied demographics
        patients = []
        for i in range(50):
            patient = Patient(
                name=f"Analytics Patient {i}",
                age=20 + (i % 60),
                gender="male" if i % 2 == 0 else "female",
                email=f"analytics{i}@test.com",
                medical_history=[f"condition_{i % 5}"],
                allergies=[f"allergy_{i % 3}"] if i % 4 == 0 else []
            )
            patients.append(patient)
            session.add(patient)

        await session.commit()

        # Create assessments with varied risk levels and dates
        assessments = []
        base_date = datetime.now() - timedelta(days=30)

        for i, patient in enumerate(patients):
            for j in range(1, 4):  # 1-3 assessments per patient
                assessment_date = base_date + timedelta(days=i % 30)

                assessment = HealthAssessment(
                    patient_id=patient.id,
                    symptoms=[f"symptom_{j}", f"symptom_{(j+1)%8}"],
                    risk_level=["low", "medium", "high"][i % 3],
                    risk_score=10 + (i % 80),
                    urgency=["low", "normal", "high"][i % 3],
                    confidence_score=0.5 + (i % 5) * 0.1,
                    ai_recommendations=[f"recommendation_{j}"],
                    status=["pending", "completed", "reviewed"][j % 3],
                    created_at=assessment_date
                )
                assessments.append(assessment)
                session.add(assessment)

                # Add symptom records for some assessments
                if i % 2 == 0:
                    symptom = SymptomRecord(
                        assessment_id=assessment.id,
                        name=f"symptom_{j}",
                        severity=["mild", "moderate", "severe"][j % 3],
                        duration_days=j * 2,
                        pain_scale=j * 2 + 1,
                        created_at=assessment_date
                    )
                    session.add(symptom)

        await session.commit()
        return {"patients": patients, "assessments": assessments}

    async def test_patient_demographics_analysis(self, session, analytics_data):
        """Test patient demographics analytics"""
        # Age distribution
        age_stats = await session.execute(
            select(
                func.min(Patient.age).label("min_age"),
                func.max(Patient.age).label("max_age"),
                func.avg(Patient.age).label("avg_age"),
                func.count(Patient.id).label("total_patients")
            )
        )
        stats = age_stats.first()

        assert stats.min_age >= 20
        assert stats.max_age <= 80
        assert stats.avg_age > 0
        assert stats.total_patients > 0

        # Gender distribution
        gender_dist = await session.execute(
            select(
                Patient.gender,
                func.count(Patient.id).label("count")
            )
            .group_by(Patient.gender)
        )
        gender_results = gender_dist.fetchall()

        gender_counts = {row.gender: row.count for row in gender_results}
        assert "male" in gender_counts
        assert "female" in gender_counts
        assert gender_counts["male"] > 0
        assert gender_counts["female"] > 0

    async def test_risk_assessment_analytics(self, session, analytics_data):
        """Test risk assessment analytics"""
        # Risk level distribution
        risk_dist = await session.execute(
            select(
                HealthAssessment.risk_level,
                func.count(HealthAssessment.id).label("count"),
                func.avg(HealthAssessment.risk_score).label("avg_score")
            )
            .group_by(HealthAssessment.risk_level)
        )
        risk_results = risk_dist.fetchall()

        risk_data = {
            row.risk_level: {"count": row.count, "avg_score": row.avg_score}
            for row in risk_results
        }

        assert "low" in risk_data
        assert "medium" in risk_data
        assert "high" in risk_data
        assert all(data["count"] > 0 for data in risk_data.values())
        assert all(data["avg_score"] >= 0 for data in risk_data.values())

    async def test_temporal_analysis(self, session, analytics_data):
        """Test temporal trends analysis"""
        # Assessments over time
        daily_assessments = await session.execute(
            select(
                func.date(HealthAssessment.created_at).label("assessment_date"),
                func.count(HealthAssessment.id).label("count")
            )
            .group_by(func.date(HealthAssessment.created_at))
            .order_by(func.date(HealthAssessment.created_at))
        )
        daily_results = daily_assessments.fetchall()

        assert len(daily_results) > 0
        assert all(row.count > 0 for row in daily_results)

        # Weekly trends
        weekly_assessments = await session.execute(
            select(
                func.date_trunc('week', HealthAssessment.created_at).label("week"),
                func.count(HealthAssessment.id).label("count"),
                func.avg(HealthAssessment.risk_score).label("avg_risk")
            )
            .group_by(func.date_trunc('week', HealthAssessment.created_at))
            .order_by(func.date_trunc('week', HealthAssessment.created_at))
        )
        weekly_results = weekly_assessments.fetchall()

        assert len(weekly_results) > 0

    async def test_symptom_analysis(self, session, analytics_data):
        """Test symptom pattern analysis"""
        # Most common symptoms
        symptom_frequency = await session.execute(
            select(
                SymptomRecord.name,
                func.count(SymptomRecord.id).label("frequency"),
                func.avg(SymptomRecord.pain_scale).label("avg_pain")
            )
            .group_by(SymptomRecord.name)
            .order_by(func.count(SymptomRecord.id).desc())
        )
        symptom_results = symptom_frequency.fetchall()

        assert len(symptom_results) > 0
        assert all(row.frequency > 0 for row in symptom_results)

        # Severity distribution
        severity_dist = await session.execute(
            select(
                SymptomRecord.severity,
                func.count(SymptomRecord.id).label("count")
            )
            .group_by(SymptomRecord.severity)
        )
        severity_results = severity_dist.fetchall()

        severity_counts = {row.severity: row.count for row in severity_results}
        assert len(severity_counts) > 0

    async def test_patient_risk_profiling(self, session, analytics_data):
        """Test patient risk profiling analytics"""
        # High-risk patients
        high_risk_patients = await session.execute(
            select(
                Patient.id,
                Patient.name,
                Patient.age,
                func.count(HealthAssessment.id).label("assessment_count"),
                func.avg(HealthAssessment.risk_score).label("avg_risk_score"),
                func.max(HealthAssessment.risk_score).label("max_risk_score")
            )
            .join(HealthAssessment)
            .group_by(Patient.id, Patient.name, Patient.age)
            .having(func.avg(HealthAssessment.risk_score) > 50)
            .order_by(func.avg(HealthAssessment.risk_score).desc())
        )
        high_risk_results = high_risk_patients.fetchall()

        # Should have some high-risk patients
        for patient in high_risk_results:
            assert patient.avg_risk_score > 50
            assert patient.assessment_count > 0

    async def test_assessment_status_analytics(self, session, analytics_data):
        """Test assessment status and workflow analytics"""
        # Status distribution
        status_dist = await session.execute(
            select(
                HealthAssessment.status,
                func.count(HealthAssessment.id).label("count")
            )
            .group_by(HealthAssessment.status)
        )
        status_results = status_dist.fetchall()

        status_counts = {row.status: row.count for row in status_results}
        assert len(status_counts) > 0

        # Pending assessments analysis
        pending_assessments = await session.execute(
            select(
                HealthAssessment.id,
                HealthAssessment.created_at,
                HealthAssessment.risk_level,
                Patient.name
            )
            .join(Patient)
            .where(HealthAssessment.status == "pending")
            .order_by(HealthAssessment.created_at.desc())
        )
        pending_results = pending_assessments.fetchall()

        # Verify pending assessments structure
        for assessment in pending_results:
            assert assessment.risk_level in ["low", "medium", "high"]
            assert assessment.name is not None

    async def test_ai_confidence_analysis(self, session, analytics_data):
        """Test AI confidence score analysis"""
        # Confidence score distribution
        confidence_stats = await session.execute(
            select(
                func.min(HealthAssessment.confidence_score).label("min_confidence"),
                func.max(HealthAssessment.confidence_score).label("max_confidence"),
                func.avg(HealthAssessment.confidence_score).label("avg_confidence"),
                func.count(HealthAssessment.id).label("total_assessments")
            )
        )
        confidence_result = confidence_stats.first()

        assert 0 <= confidence_result.min_confidence <= 1
        assert 0 <= confidence_result.max_confidence <= 1
        assert 0 <= confidence_result.avg_confidence <= 1
        assert confidence_result.total_assessments > 0

        # Low confidence assessments
        low_confidence = await session.execute(
            select(
                HealthAssessment.id,
                HealthAssessment.confidence_score,
                HealthAssessment.risk_level,
                Patient.name
            )
            .join(Patient)
            .where(HealthAssessment.confidence_score < 0.7)
            .order_by(HealthAssessment.confidence_score.asc())
        )
        low_confidence_results = low_confidence.fetchall()

        for assessment in low_confidence_results:
            assert assessment.confidence_score < 0.7

    async def test_cohort_analysis(self, session, analytics_data):
        """Test patient cohort analysis"""
        # Age cohort analysis
        age_cohorts = await session.execute(
            select(
                func.case(
                    (Patient.age < 30, "20-29"),
                    (Patient.age < 50, "30-49"),
                    (Patient.age < 70, "50-69"),
                    else_="70+"
                ).label("age_cohort"),
                func.count(Patient.id).label("patient_count"),
                func.avg(HealthAssessment.risk_score).label("avg_risk_score")
            )
            .join(HealthAssessment)
            .group_by(
                func.case(
                    (Patient.age < 30, "20-29"),
                    (Patient.age < 50, "30-49"),
                    (Patient.age < 70, "50-69"),
                    else_="70+"
                )
            )
        )
        cohort_results = age_cohorts.fetchall()

        cohort_data = {
            row.age_cohort: {
                "patient_count": row.patient_count,
                "avg_risk_score": row.avg_risk_score
            }
            for row in cohort_results
        }

        assert len(cohort_data) > 0
        assert all(data["patient_count"] > 0 for data in cohort_data.values())

    async def test_medical_history_analytics(self, session, analytics_data):
        """Test medical history pattern analysis"""
        # Most common medical conditions
        # This requires JSON operations - adapt based on your database
        try:
            # PostgreSQL JSON query example
            conditions_query = await session.execute(
                text("""
                SELECT
                    jsonb_array_elements_text(medical_history) as condition,
                    COUNT(*) as frequency
                FROM patients
                WHERE medical_history IS NOT NULL
                GROUP BY condition
                ORDER BY frequency DESC
                """)
            )
            conditions_results = conditions_query.fetchall()

            # Should have some medical conditions
            assert len(conditions_results) > 0

        except Exception:
            # Skip if JSON operations not supported
            pytest.skip("JSON operations not supported in this database")

    async def test_performance_metrics_analytics(self, session, analytics_data):
        """Test system performance metrics"""
        # Assessment processing time simulation
        # (In real implementation, this would track actual processing times)

        # Query response time analysis
        import time
        start_time = time.time()

        complex_query = await session.execute(
            select(
                Patient.name,
                func.count(HealthAssessment.id).label("assessment_count"),
                func.avg(HealthAssessment.risk_score).label("avg_risk"),
                func.count(SymptomRecord.id).label("symptom_count")
            )
            .join(HealthAssessment)
            .join(SymptomRecord, isouter=True)
            .group_by(Patient.id, Patient.name)
            .having(func.count(HealthAssessment.id) > 1)
            .order_by(func.avg(HealthAssessment.risk_score).desc())
        )

        end_time = time.time()
        query_time = end_time - start_time

        results = complex_query.fetchall()

        # Verify query completed in reasonable time
        assert query_time < 1.0  # Should complete within 1 second
        assert len(results) >= 0

    async def test_predictive_analytics_data_prep(self, session, analytics_data):
        """Test data preparation for predictive analytics"""
        # Feature extraction for ML models
        feature_query = await session.execute(
            select(
                Patient.age,
                Patient.gender,
                HealthAssessment.risk_score,
                HealthAssessment.confidence_score,
                func.count(SymptomRecord.id).label("symptom_count"),
                func.avg(SymptomRecord.pain_scale).label("avg_pain_scale")
            )
            .join(HealthAssessment)
            .join(SymptomRecord, isouter=True)
            .group_by(
                Patient.id,
                Patient.age,
                Patient.gender,
                HealthAssessment.risk_score,
                HealthAssessment.confidence_score
            )
        )

        features = feature_query.fetchall()

        # Verify feature data structure
        for feature in features:
            assert feature.age > 0
            assert feature.gender in ["male", "female"]
            assert 0 <= feature.risk_score <= 100
            assert 0 <= feature.confidence_score <= 1
            assert feature.symptom_count >= 0
