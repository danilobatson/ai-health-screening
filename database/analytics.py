# database/analytics.py
"""
Advanced database analytics and reporting capabilities
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import text, func, select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from .models import Patient, HealthAssessment, SymptomRecord
from .connection_pool import get_pool_manager

logger = logging.getLogger(__name__)


class HealthAnalytics:
    """Advanced health analytics and reporting"""

    def __init__(self):
        self.pool_manager = None

    async def _get_session(self):
        """Get database session"""
        if not self.pool_manager:
            self.pool_manager = await get_pool_manager()
        return self.pool_manager.get_session()

    async def get_patient_demographics(self) -> Dict[str, Any]:
        """Get comprehensive patient demographics analysis"""
        async with await self._get_session() as session:
            # Age statistics
            age_stats = await session.execute(
                select(
                    func.min(Patient.age).label("min_age"),
                    func.max(Patient.age).label("max_age"),
                    func.avg(Patient.age).label("avg_age"),
                    func.count(Patient.id).label("total_patients")
                )
            )
            age_result = age_stats.first()

            # Gender distribution
            gender_dist = await session.execute(
                select(
                    Patient.gender,
                    func.count(Patient.id).label("count")
                )
                .group_by(Patient.gender)
            )
            gender_results = gender_dist.fetchall()

            # Age cohorts
            age_cohorts = await session.execute(
                select(
                    func.case(
                        (Patient.age < 18, "0-17"),
                        (Patient.age < 30, "18-29"),
                        (Patient.age < 50, "30-49"),
                        (Patient.age < 65, "50-64"),
                        else_="65+"
                    ).label("age_cohort"),
                    func.count(Patient.id).label("count")
                )
                .group_by(
                    func.case(
                        (Patient.age < 18, "0-17"),
                        (Patient.age < 30, "18-29"),
                        (Patient.age < 50, "30-49"),
                        (Patient.age < 65, "50-64"),
                        else_="65+"
                    )
                )
            )
            cohort_results = age_cohorts.fetchall()

            return {
                "age_statistics": {
                    "min": age_result.min_age,
                    "max": age_result.max_age,
                    "average": float(age_result.avg_age) if age_result.avg_age else 0,
                    "total_patients": age_result.total_patients
                },
                "gender_distribution": {
                    row.gender or "unknown": row.count for row in gender_results
                },
                "age_cohorts": {
                    row.age_cohort: row.count for row in cohort_results
                }
            }

    async def get_risk_assessment_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get risk assessment analytics for specified period"""
        async with await self._get_session() as session:
            start_date = datetime.now() - timedelta(days=days)

            # Risk level distribution
            risk_dist = await session.execute(
                select(
                    HealthAssessment.risk_level,
                    func.count(HealthAssessment.id).label("count"),
                    func.avg(HealthAssessment.risk_score).label("avg_score")
                )
                .where(HealthAssessment.created_at >= start_date)
                .group_by(HealthAssessment.risk_level)
            )
            risk_results = risk_dist.fetchall()

            # Urgency distribution
            urgency_dist = await session.execute(
                select(
                    HealthAssessment.urgency,
                    func.count(HealthAssessment.id).label("count")
                )
                .where(HealthAssessment.created_at >= start_date)
                .group_by(HealthAssessment.urgency)
            )
            urgency_results = urgency_dist.fetchall()

            # Daily assessment trends
            daily_trends = await session.execute(
                select(
                    func.date(HealthAssessment.created_at).label("date"),
                    func.count(HealthAssessment.id).label("count"),
                    func.avg(HealthAssessment.risk_score).label("avg_risk_score")
                )
                .where(HealthAssessment.created_at >= start_date)
                .group_by(func.date(HealthAssessment.created_at))
                .order_by(func.date(HealthAssessment.created_at))
            )
            trend_results = daily_trends.fetchall()

            # AI confidence analysis
            confidence_stats = await session.execute(
                select(
                    func.min(HealthAssessment.confidence_score).label("min_confidence"),
                    func.max(HealthAssessment.confidence_score).label("max_confidence"),
                    func.avg(HealthAssessment.confidence_score).label("avg_confidence")
                )
                .where(HealthAssessment.created_at >= start_date)
            )
            confidence_result = confidence_stats.first()

            return {
                "period_days": days,
                "risk_distribution": {
                    row.risk_level: {
                        "count": row.count,
                        "avg_score": float(row.avg_score) if row.avg_score else 0
                    } for row in risk_results
                },
                "urgency_distribution": {
                    row.urgency: row.count for row in urgency_results
                },
                "daily_trends": [
                    {
                        "date": row.date.isoformat(),
                        "count": row.count,
                        "avg_risk_score": float(row.avg_risk_score) if row.avg_risk_score else 0
                    } for row in trend_results
                ],
                "ai_confidence": {
                    "min": float(confidence_result.min_confidence) if confidence_result.min_confidence else 0,
                    "max": float(confidence_result.max_confidence) if confidence_result.max_confidence else 0,
                    "average": float(confidence_result.avg_confidence) if confidence_result.avg_confidence else 0
                }
            }

    async def get_symptom_analytics(self, limit: int = 20) -> Dict[str, Any]:
        """Get symptom pattern analytics"""
        async with await self._get_session() as session:
            # Most common symptoms
            symptom_frequency = await session.execute(
                select(
                    SymptomRecord.name,
                    func.count(SymptomRecord.id).label("frequency"),
                    func.avg(SymptomRecord.pain_scale).label("avg_pain_scale")
                )
                .group_by(SymptomRecord.name)
                .order_by(func.count(SymptomRecord.id).desc())
                .limit(limit)
            )
            symptom_results = symptom_frequency.fetchall()

            # Severity distribution
            severity_dist = await session.execute(
                select(
                    SymptomRecord.severity,
                    func.count(SymptomRecord.id).label("count")
                )
                .group_by(SymptomRecord.severity)
            )
            severity_results = severity_dist.fetchall()

            # Duration analysis
            duration_stats = await session.execute(
                select(
                    func.min(SymptomRecord.duration_days).label("min_duration"),
                    func.max(SymptomRecord.duration_days).label("max_duration"),
                    func.avg(SymptomRecord.duration_days).label("avg_duration")
                )
                .where(SymptomRecord.duration_days.isnot(None))
            )
            duration_result = duration_stats.first()

            # Pain scale analysis
            pain_stats = await session.execute(
                select(
                    func.min(SymptomRecord.pain_scale).label("min_pain"),
                    func.max(SymptomRecord.pain_scale).label("max_pain"),
                    func.avg(SymptomRecord.pain_scale).label("avg_pain")
                )
                .where(SymptomRecord.pain_scale.isnot(None))
            )
            pain_result = pain_stats.first()

            return {
                "most_common_symptoms": [
                    {
                        "name": row.name,
                        "frequency": row.frequency,
                        "avg_pain_scale": float(row.avg_pain_scale) if row.avg_pain_scale else None
                    } for row in symptom_results
                ],
                "severity_distribution": {
                    row.severity: row.count for row in severity_results
                },
                "duration_statistics": {
                    "min": duration_result.min_duration,
                    "max": duration_result.max_duration,
                    "average": float(duration_result.avg_duration) if duration_result.avg_duration else None
                },
                "pain_scale_statistics": {
                    "min": pain_result.min_pain,
                    "max": pain_result.max_pain,
                    "average": float(pain_result.avg_pain) if pain_result.avg_pain else None
                }
            }

    async def get_high_risk_patients(self, risk_threshold: int = 70, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of high-risk patients requiring attention"""
        async with await self._get_session() as session:
            high_risk_query = await session.execute(
                select(
                    Patient.id,
                    Patient.name,
                    Patient.age,
                    Patient.gender,
                    func.count(HealthAssessment.id).label("assessment_count"),
                    func.max(HealthAssessment.risk_score).label("max_risk_score"),
                    func.avg(HealthAssessment.risk_score).label("avg_risk_score"),
                    func.max(HealthAssessment.created_at).label("last_assessment")
                )
                .join(HealthAssessment)
                .group_by(Patient.id, Patient.name, Patient.age, Patient.gender)
                .having(func.max(HealthAssessment.risk_score) >= risk_threshold)
                .order_by(func.max(HealthAssessment.risk_score).desc())
                .limit(limit)
            )

            results = high_risk_query.fetchall()

            return [
                {
                    "patient_id": row.id,
                    "name": row.name,
                    "age": row.age,
                    "gender": row.gender,
                    "assessment_count": row.assessment_count,
                    "max_risk_score": row.max_risk_score,
                    "avg_risk_score": float(row.avg_risk_score),
                    "last_assessment": row.last_assessment.isoformat() if row.last_assessment else None
                } for row in results
            ]

    async def get_assessment_workflow_analytics(self) -> Dict[str, Any]:
        """Get assessment workflow and status analytics"""
        async with await self._get_session() as session:
            # Status distribution
            status_dist = await session.execute(
                select(
                    HealthAssessment.status,
                    func.count(HealthAssessment.id).label("count")
                )
                .group_by(HealthAssessment.status)
            )
            status_results = status_dist.fetchall()

            # Pending assessments by age
            pending_by_age = await session.execute(
                select(
                    func.case(
                        (func.age(HealthAssessment.created_at) < text("interval '1 hour'"), "< 1 hour"),
                        (func.age(HealthAssessment.created_at) < text("interval '1 day'"), "1-24 hours"),
                        (func.age(HealthAssessment.created_at) < text("interval '1 week'"), "1-7 days"),
                        else_="> 1 week"
                    ).label("age_category"),
                    func.count(HealthAssessment.id).label("count")
                )
                .where(HealthAssessment.status == "pending")
                .group_by(
                    func.case(
                        (func.age(HealthAssessment.created_at) < text("interval '1 hour'"), "< 1 hour"),
                        (func.age(HealthAssessment.created_at) < text("interval '1 day'"), "1-24 hours"),
                        (func.age(HealthAssessment.created_at) < text("interval '1 week'"), "1-7 days"),
                        else_="> 1 week"
                    )
                )
            )
            pending_results = pending_by_age.fetchall()

            # Follow-up requirements
            followup_stats = await session.execute(
                select(
                    func.count(HealthAssessment.id).label("total_with_followup"),
                    func.count(
                        func.case(
                            (HealthAssessment.follow_up_date < func.now(), 1),
                            else_=None
                        )
                    ).label("overdue_followups")
                )
                .where(HealthAssessment.follow_up_required == True)
            )
            followup_result = followup_stats.first()

            return {
                "status_distribution": {
                    row.status: row.count for row in status_results
                },
                "pending_by_age": {
                    row.age_category: row.count for row in pending_results
                },
                "follow_up_analytics": {
                    "total_requiring_followup": followup_result.total_with_followup,
                    "overdue_followups": followup_result.overdue_followups
                }
            }

    async def generate_executive_summary(self, days: int = 30) -> Dict[str, Any]:
        """Generate executive summary report"""
        start_date = datetime.now() - timedelta(days=days)

        async with await self._get_session() as session:
            # Key metrics
            metrics = await session.execute(
                select(
                    func.count(Patient.id).label("total_patients"),
                    func.count(HealthAssessment.id).label("total_assessments"),
                    func.count(
                        func.case(
                            (HealthAssessment.created_at >= start_date, 1),
                            else_=None
                        )
                    ).label("recent_assessments"),
                    func.count(
                        func.case(
                            (HealthAssessment.risk_level == "high", 1),
                            else_=None
                        )
                    ).label("high_risk_assessments"),
                    func.avg(HealthAssessment.risk_score).label("avg_risk_score"),
                    func.avg(HealthAssessment.confidence_score).label("avg_confidence")
                )
                .select_from(Patient)
                .join(HealthAssessment, isouter=True)
            )
            metrics_result = metrics.first()

            # System performance
            performance = await session.execute(
                select(
                    func.count(
                        func.case(
                            (HealthAssessment.status == "pending", 1),
                            else_=None
                        )
                    ).label("pending_assessments"),
                    func.count(
                        func.case(
                            (and_(
                                HealthAssessment.follow_up_required == True,
                                HealthAssessment.follow_up_date < func.now()
                            ), 1),
                            else_=None
                        )
                    ).label("overdue_followups")
                )
                .select_from(HealthAssessment)
            )
            performance_result = performance.first()

            return {
                "report_period_days": days,
                "generated_at": datetime.now().isoformat(),
                "key_metrics": {
                    "total_patients": metrics_result.total_patients,
                    "total_assessments": metrics_result.total_assessments,
                    "recent_assessments": metrics_result.recent_assessments,
                    "high_risk_assessments": metrics_result.high_risk_assessments,
                    "avg_risk_score": float(metrics_result.avg_risk_score) if metrics_result.avg_risk_score else 0,
                    "avg_ai_confidence": float(metrics_result.avg_confidence) if metrics_result.avg_confidence else 0
                },
                "system_performance": {
                    "pending_assessments": performance_result.pending_assessments,
                    "overdue_followups": performance_result.overdue_followups,
                    "assessment_processing_rate": (
                        metrics_result.recent_assessments / days if days > 0 else 0
                    )
                },
                "recommendations": await self._generate_recommendations(
                    metrics_result, performance_result
                )
            }

    async def _generate_recommendations(self, metrics, performance) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []

        if performance.pending_assessments > 10:
            recommendations.append(
                f"High number of pending assessments ({performance.pending_assessments}). "
                "Consider reviewing workflow efficiency."
            )

        if performance.overdue_followups > 5:
            recommendations.append(
                f"Multiple overdue follow-ups ({performance.overdue_followups}). "
                "Priority should be given to patient follow-up care."
            )

        if metrics.avg_risk_score and metrics.avg_risk_score > 60:
            recommendations.append(
                f"Average risk score is elevated ({metrics.avg_risk_score:.1f}). "
                "Monitor patient population health trends."
            )

        if metrics.avg_confidence and metrics.avg_confidence < 0.7:
            recommendations.append(
                f"AI confidence is below optimal ({metrics.avg_confidence:.2f}). "
                "Consider model retraining or additional data collection."
            )

        if not recommendations:
            recommendations.append("System performance is within normal parameters.")

        return recommendations


class PerformanceAnalytics:
    """Database and system performance analytics"""

    def __init__(self):
        self.pool_manager = None

    async def _get_session(self):
        """Get database session"""
        if not self.pool_manager:
            self.pool_manager = await get_pool_manager()
        return self.pool_manager.get_session()

    async def get_database_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        async with await self._get_session() as session:
            try:
                # PostgreSQL specific queries
                # Active connections
                connections = await session.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                )
                active_connections = connections.scalar()

                # Database size
                db_size = await session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                database_size = db_size.scalar()

                # Table sizes
                table_sizes = await session.execute(
                    text("""
                    SELECT
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    """)
                )
                table_results = table_sizes.fetchall()

                # Query performance stats (if available)
                slow_queries = await session.execute(
                    text("""
                    SELECT query, calls, total_time, mean_time
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT 10
                    """)
                )
                slow_query_results = slow_queries.fetchall()

                return {
                    "active_connections": active_connections,
                    "database_size": database_size,
                    "table_sizes": [
                        {"table": row.tablename, "size": row.size}
                        for row in table_results
                    ],
                    "slow_queries": [
                        {
                            "query": row.query[:100] + "..." if len(row.query) > 100 else row.query,
                            "calls": row.calls,
                            "total_time": float(row.total_time),
                            "mean_time": float(row.mean_time)
                        } for row in slow_query_results
                    ] if slow_query_results else []
                }

            except Exception as e:
                logger.warning(f"Could not get detailed performance metrics: {e}")
                # Fallback to basic metrics
                return {
                    "active_connections": "unavailable",
                    "database_size": "unavailable",
                    "table_sizes": [],
                    "slow_queries": []
                }

    async def get_connection_pool_metrics(self) -> Dict[str, Any]:
        """Get connection pool performance metrics"""
        if not self.pool_manager:
            self.pool_manager = await get_pool_manager()

        return await self.pool_manager.get_pool_status()

    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run basic performance benchmark"""
        import time

        async with await self._get_session() as session:
            # Simple query benchmark
            start_time = time.time()
            await session.execute(text("SELECT 1"))
            simple_query_time = time.time() - start_time

            # Count query benchmark
            start_time = time.time()
            result = await session.execute(select(func.count(Patient.id)))
            count_query_time = time.time() - start_time
            patient_count = result.scalar()

            # Join query benchmark
            start_time = time.time()
            await session.execute(
                select(Patient.name, HealthAssessment.risk_level)
                .join(HealthAssessment)
                .limit(100)
            )
            join_query_time = time.time() - start_time

            return {
                "simple_query_time_ms": simple_query_time * 1000,
                "count_query_time_ms": count_query_time * 1000,
                "join_query_time_ms": join_query_time * 1000,
                "patient_count": patient_count,
                "benchmark_timestamp": datetime.now().isoformat()
            }
