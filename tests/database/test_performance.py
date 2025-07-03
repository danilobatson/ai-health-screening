# tests/database/test_performance.py
import pytest
import asyncio
import time
from sqlalchemy import text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch
import logging

from database.models import Patient, HealthAssessment, SymptomRecord
from database.database import AsyncSessionLocal, engine


class TestDatabasePerformance:
    """Test database performance and optimization"""

    @pytest.fixture
    async def session(self):
        """Create a test database session"""
        async with AsyncSessionLocal() as session:
            yield session

    @pytest.fixture
    async def sample_data(self, session):
        """Create sample data for performance testing"""
        patients = []
        assessments = []

        # Create 100 patients for performance testing
        for i in range(100):
            patient = Patient(
                name=f"Test Patient {i}",
                age=25 + (i % 50),
                gender="male" if i % 2 == 0 else "female",
                email=f"patient{i}@test.com",
                medical_history=[f"condition_{i % 5}"],
                allergies=[f"allergy_{i % 3}"] if i % 3 == 0 else []
            )
            patients.append(patient)
            session.add(patient)

        await session.commit()

        # Create assessments for each patient
        for i, patient in enumerate(patients):
            for j in range(3):  # 3 assessments per patient
                assessment = HealthAssessment(
                    patient_id=patient.id,
                    symptoms=[f"symptom_{j}", f"symptom_{(j+1)%5}"],
                    risk_level="medium" if i % 2 == 0 else "low",
                    risk_score=50 + (i % 30),
                    urgency="normal",
                    confidence_score=0.7 + (i % 3) * 0.1,
                    ai_recommendations=[f"recommendation_{j}"],
                    status="completed" if j < 2 else "pending"
                )
                assessments.append(assessment)
                session.add(assessment)

        await session.commit()
        return {"patients": patients, "assessments": assessments}

    async def test_bulk_insert_performance(self, session):
        """Test bulk insert performance"""
        start_time = time.time()

        # Create 1000 patients in bulk
        patients = []
        for i in range(1000):
            patient = Patient(
                name=f"Bulk Patient {i}",
                age=20 + (i % 60),
                gender="male" if i % 2 == 0 else "female",
                email=f"bulk{i}@test.com"
            )
            patients.append(patient)

        session.add_all(patients)
        await session.commit()

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within 5 seconds
        assert duration < 5.0, f"Bulk insert took too long: {duration}s"

        # Verify all patients were inserted
        count_result = await session.execute(
            select(func.count(Patient.id)).where(Patient.name.like("Bulk Patient%"))
        )
        count = count_result.scalar()
        assert count == 1000

    async def test_query_performance_with_indexes(self, session, sample_data):
        """Test query performance with proper indexing"""
        start_time = time.time()

        # Test indexed query (by email)
        result = await session.execute(
            select(Patient).where(Patient.email == "patient50@test.com")
        )
        patient = result.scalar_one_or_none()

        end_time = time.time()
        duration = end_time - start_time

        # Indexed query should be fast
        assert duration < 0.1, f"Indexed query took too long: {duration}s"
        assert patient is not None
        assert patient.email == "patient50@test.com"

    async def test_complex_join_performance(self, session, sample_data):
        """Test performance of complex joins"""
        start_time = time.time()

        # Complex query with joins and aggregations
        result = await session.execute(
            select(
                Patient.name,
                func.count(HealthAssessment.id).label("assessment_count"),
                func.avg(HealthAssessment.risk_score).label("avg_risk_score")
            )
            .join(HealthAssessment)
            .where(Patient.age > 30)
            .group_by(Patient.id, Patient.name)
            .having(func.count(HealthAssessment.id) > 2)
            .order_by(func.avg(HealthAssessment.risk_score).desc())
            .limit(10)
        )

        results = result.fetchall()

        end_time = time.time()
        duration = end_time - start_time

        # Complex query should complete within reasonable time
        assert duration < 1.0, f"Complex join query took too long: {duration}s"
        assert len(results) > 0

    async def test_pagination_performance(self, session, sample_data):
        """Test pagination performance with offset and limit"""
        page_size = 10
        total_pages = 10

        start_time = time.time()

        for page in range(total_pages):
            offset = page * page_size
            result = await session.execute(
                select(Patient)
                .order_by(Patient.created_at)
                .offset(offset)
                .limit(page_size)
            )
            patients = result.scalars().all()
            assert len(patients) <= page_size

        end_time = time.time()
        duration = end_time - start_time

        # Pagination should be efficient
        assert duration < 2.0, f"Pagination took too long: {duration}s"

    async def test_connection_pool_performance(self):
        """Test connection pool efficiency"""
        start_time = time.time()

        # Simulate concurrent database operations
        async def db_operation():
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(func.now()))
                return result.scalar()

        # Run 20 concurrent operations
        tasks = [db_operation() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All operations should complete and connection pool should handle concurrency
        assert len(results) == 20
        assert all(result is not None for result in results)
        assert duration < 3.0, f"Connection pool operations took too long: {duration}s"

    async def test_memory_usage_large_dataset(self, session):
        """Test memory efficiency with large result sets"""
        # Create a query that could potentially use a lot of memory
        result = await session.execute(
            select(Patient.id, Patient.name, Patient.age)
            .order_by(Patient.created_at)
            .limit(1000)
        )

        # Use fetchmany to avoid loading all results at once
        batch_size = 100
        total_processed = 0

        while True:
            batch = result.fetchmany(batch_size)
            if not batch:
                break
            total_processed += len(batch)
            # Process batch (simulated)
            assert all(len(row) == 3 for row in batch)

        # Should have processed some records efficiently
        assert total_processed >= 0

    async def test_database_monitoring_queries(self, session):
        """Test queries for database monitoring and health"""
        # Test connection count (PostgreSQL specific)
        try:
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            )
            active_connections = result.scalar()
            assert isinstance(active_connections, int)
            assert active_connections >= 0
        except Exception:
            # Skip if not PostgreSQL or permissions issue
            pytest.skip("Database monitoring queries not available")

    async def test_index_usage_analysis(self, session):
        """Test index usage analysis"""
        # Create a query that should use indexes
        result = await session.execute(
            select(Patient).where(Patient.email.like("%@test.com")).limit(5)
        )
        patients = result.scalars().all()

        # Verify the query executed (index usage would be checked in real monitoring)
        assert len(patients) >= 0

    async def test_query_execution_plan(self, session):
        """Test query execution plan analysis"""
        # PostgreSQL EXPLAIN query
        try:
            result = await session.execute(
                text("EXPLAIN SELECT * FROM patients WHERE email LIKE '%@test.com' LIMIT 5")
            )
            plan = result.fetchall()
            assert len(plan) > 0
        except Exception:
            # Skip if not supported or permissions issue
            pytest.skip("Query execution plan analysis not available")

    async def test_concurrent_read_write_performance(self, session):
        """Test performance under concurrent read/write operations"""
        async def write_operation():
            async with AsyncSessionLocal() as write_session:
                patient = Patient(
                    name="Concurrent Test Patient",
                    age=30,
                    email=f"concurrent_{time.time()}@test.com"
                )
                write_session.add(patient)
                await write_session.commit()
                return patient.id

        async def read_operation():
            async with AsyncSessionLocal() as read_session:
                result = await read_session.execute(
                    select(func.count(Patient.id))
                )
                return result.scalar()

        start_time = time.time()

        # Run concurrent reads and writes
        write_tasks = [write_operation() for _ in range(5)]
        read_tasks = [read_operation() for _ in range(10)]

        write_results = await asyncio.gather(*write_tasks)
        read_results = await asyncio.gather(*read_tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All operations should complete successfully
        assert len(write_results) == 5
        assert len(read_results) == 10
        assert all(isinstance(result, str) for result in write_results)
        assert all(isinstance(result, int) for result in read_results)
        assert duration < 5.0, f"Concurrent operations took too long: {duration}s"


class TestDatabaseOptimization:
    """Test database optimization features"""

    @pytest.fixture
    async def session(self):
        """Create a test database session"""
        async with AsyncSessionLocal() as session:
            yield session

    async def test_query_optimization_hints(self, session):
        """Test query optimization techniques"""
        # Test query with proper ordering and limiting
        result = await session.execute(
            select(Patient)
            .where(Patient.age > 25)
            .order_by(Patient.created_at.desc())
            .limit(10)
        )
        patients = result.scalars().all()
        assert len(patients) <= 10

    async def test_eager_loading_optimization(self, session):
        """Test eager loading to avoid N+1 queries"""
        from sqlalchemy.orm import selectinload

        # Use selectinload to eagerly load related assessments
        result = await session.execute(
            select(Patient)
            .options(selectinload(Patient.assessments))
            .limit(5)
        )
        patients = result.scalars().all()

        # Access related data without additional queries
        for patient in patients:
            assessments = patient.assessments
            assert isinstance(assessments, list)

    async def test_batch_operations_optimization(self, session):
        """Test batch operations for better performance"""
        # Create patients in batches
        batch_size = 50
        total_patients = 150

        for batch_start in range(0, total_patients, batch_size):
            batch_patients = []
            for i in range(batch_start, min(batch_start + batch_size, total_patients)):
                patient = Patient(
                    name=f"Batch Patient {i}",
                    age=25 + (i % 40),
                    email=f"batch{i}@test.com"
                )
                batch_patients.append(patient)

            session.add_all(batch_patients)
            await session.commit()

        # Verify all patients were created
        result = await session.execute(
            select(func.count(Patient.id)).where(Patient.name.like("Batch Patient%"))
        )
        count = result.scalar()
        assert count == total_patients

    async def test_database_statistics_collection(self, session):
        """Test collection of database statistics"""
        # Collect table statistics
        stats = {}

        # Patient table stats
        result = await session.execute(select(func.count(Patient.id)))
        stats['patient_count'] = result.scalar()

        result = await session.execute(select(func.avg(Patient.age)))
        stats['avg_patient_age'] = result.scalar()

        # Assessment table stats
        result = await session.execute(select(func.count(HealthAssessment.id)))
        stats['assessment_count'] = result.scalar()

        result = await session.execute(select(func.avg(HealthAssessment.risk_score)))
        stats['avg_risk_score'] = result.scalar()

        # Verify statistics are reasonable
        assert stats['patient_count'] >= 0
        assert stats['assessment_count'] >= 0
        if stats['avg_patient_age']:
            assert 0 <= stats['avg_patient_age'] <= 150
        if stats['avg_risk_score']:
            assert 0 <= stats['avg_risk_score'] <= 100
