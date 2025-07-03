#!/usr/bin/env python3
"""
Database Management CLI Tool
Advanced database operations, monitoring, and maintenance
"""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Optional
import argparse

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection_pool import get_pool_manager, ConnectionPoolMonitor
from database.analytics import HealthAnalytics, PerformanceAnalytics
from database.caching import get_cache_manager, CacheWarmer, get_query_cache
from database.database import init_db, check_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseCLI:
    """Database management CLI commands"""

    def __init__(self):
        self.health_analytics = HealthAnalytics()
        self.performance_analytics = PerformanceAnalytics()

    async def init_database(self):
        """Initialize database schema"""
        print("🗄️ Initializing database...")
        success = await init_db()
        if success:
            print("✅ Database initialized successfully")
        else:
            print("❌ Database initialization failed")
            sys.exit(1)

    async def check_connection(self):
        """Check database connection"""
        print("🔗 Checking database connection...")
        success = await check_db_connection()
        if success:
            print("✅ Database connection is healthy")
        else:
            print("❌ Database connection failed")
            sys.exit(1)

    async def show_pool_status(self):
        """Show connection pool status"""
        print("🏊 Connection Pool Status:")
        pool_manager = await get_pool_manager()
        status = await pool_manager.get_pool_status()

        print(json.dumps(status, indent=2, default=str))

    async def warm_up_pool(self, connections: int = 5):
        """Warm up connection pool"""
        print(f"🔥 Warming up connection pool with {connections} connections...")
        pool_manager = await get_pool_manager()
        await pool_manager.warm_up_pool(target_connections=connections)
        print("✅ Connection pool warmed up")

    async def show_analytics(self, days: int = 30):
        """Show comprehensive analytics"""
        print(f"📊 Health Analytics (Last {days} days):")

        # Patient demographics
        demographics = await self.health_analytics.get_patient_demographics()
        print("\n👥 Patient Demographics:")
        print(json.dumps(demographics, indent=2, default=str))

        # Risk assessment analytics
        risk_analytics = await self.health_analytics.get_risk_assessment_analytics(days)
        print(f"\n⚠️ Risk Assessment Analytics:")
        print(json.dumps(risk_analytics, indent=2, default=str))

        # Symptom analytics
        symptom_analytics = await self.health_analytics.get_symptom_analytics()
        print("\n🩺 Symptom Analytics:")
        print(json.dumps(symptom_analytics, indent=2, default=str))

    async def show_high_risk_patients(self, threshold: int = 70, limit: int = 10):
        """Show high-risk patients"""
        print(f"🚨 High-Risk Patients (Risk Score ≥ {threshold}):")
        patients = await self.health_analytics.get_high_risk_patients(threshold, limit)

        if not patients:
            print("No high-risk patients found.")
            return

        for patient in patients:
            print(f"\n• {patient['name']} (ID: {patient['patient_id'][:8]}...)")
            print(f"  Age: {patient['age']}, Gender: {patient['gender']}")
            print(f"  Max Risk Score: {patient['max_risk_score']}")
            print(f"  Avg Risk Score: {patient['avg_risk_score']:.1f}")
            print(f"  Assessment Count: {patient['assessment_count']}")
            print(f"  Last Assessment: {patient['last_assessment']}")

    async def generate_executive_report(self, days: int = 30):
        """Generate executive summary report"""
        print(f"📈 Executive Summary Report (Last {days} days):")
        summary = await self.health_analytics.generate_executive_summary(days)

        print("\n📋 Key Metrics:")
        metrics = summary['key_metrics']
        print(f"  Total Patients: {metrics['total_patients']}")
        print(f"  Total Assessments: {metrics['total_assessments']}")
        print(f"  Recent Assessments: {metrics['recent_assessments']}")
        print(f"  High-Risk Assessments: {metrics['high_risk_assessments']}")
        print(f"  Average Risk Score: {metrics['avg_risk_score']:.1f}")
        print(f"  Average AI Confidence: {metrics['avg_ai_confidence']:.2f}")

        print("\n⚡ System Performance:")
        performance = summary['system_performance']
        print(f"  Pending Assessments: {performance['pending_assessments']}")
        print(f"  Overdue Follow-ups: {performance['overdue_followups']}")
        print(f"  Assessment Processing Rate: {performance['assessment_processing_rate']:.1f}/day")

        print("\n💡 Recommendations:")
        for i, recommendation in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {recommendation}")

    async def show_performance_metrics(self):
        """Show database performance metrics"""
        print("⚡ Database Performance Metrics:")

        # Database performance
        db_metrics = await self.performance_analytics.get_database_performance_metrics()
        print("\n🗄️ Database Metrics:")
        print(json.dumps(db_metrics, indent=2, default=str))

        # Connection pool metrics
        pool_metrics = await self.performance_analytics.get_connection_pool_metrics()
        print("\n🏊 Connection Pool Metrics:")
        print(json.dumps(pool_metrics, indent=2, default=str))

        # Performance benchmark
        benchmark = await self.performance_analytics.run_performance_benchmark()
        print("\n🏃 Performance Benchmark:")
        print(json.dumps(benchmark, indent=2, default=str))

    async def show_cache_status(self):
        """Show cache status"""
        print("🗃️ Cache Status:")
        cache_manager = get_cache_manager()

        # Cache statistics
        stats = cache_manager.get_stats()
        print("\n📊 Cache Statistics:")
        print(json.dumps(stats, indent=2, default=str))

        # Cache health check
        health = await cache_manager.health_check()
        print("\n🏥 Cache Health:")
        print(json.dumps(health, indent=2, default=str))

    async def warm_cache(self):
        """Warm up cache with common queries"""
        print("🔥 Warming up cache...")
        cache_manager = get_cache_manager()
        warmer = CacheWarmer(cache_manager)

        await warmer.warm_common_queries()
        print("✅ Cache warmed up successfully")

    async def clear_cache(self):
        """Clear all cache entries"""
        print("🧹 Clearing cache...")
        cache_manager = get_cache_manager()

        success = await cache_manager.clear()
        if success:
            print("✅ Cache cleared successfully")
        else:
            print("❌ Failed to clear cache")

    async def start_monitoring(self, interval: int = 30):
        """Start connection pool monitoring"""
        print(f"👁️ Starting connection pool monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop monitoring...")

        pool_manager = await get_pool_manager()
        monitor = ConnectionPoolMonitor(pool_manager)

        try:
            await monitor.start_monitoring(interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            monitor.stop_monitoring()

    async def backup_analytics(self, output_file: str):
        """Backup analytics data to file"""
        print(f"💾 Backing up analytics data to {output_file}...")

        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "demographics": await self.health_analytics.get_patient_demographics(),
            "risk_analytics": await self.health_analytics.get_risk_assessment_analytics(30),
            "symptom_analytics": await self.health_analytics.get_symptom_analytics(),
            "workflow_analytics": await self.health_analytics.get_assessment_workflow_analytics(),
            "executive_summary": await self.health_analytics.generate_executive_summary(30),
            "performance_metrics": await self.performance_analytics.get_database_performance_metrics()
        }

        with open(output_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        print(f"✅ Analytics data backed up to {output_file}")

    async def run_health_check(self):
        """Run comprehensive health check"""
        print("🏥 Running comprehensive health check...")

        issues = []

        # Database connection
        print("\n1. Checking database connection...")
        if await check_db_connection():
            print("   ✅ Database connection: OK")
        else:
            print("   ❌ Database connection: FAILED")
            issues.append("Database connection failed")

        # Connection pool
        print("\n2. Checking connection pool...")
        try:
            pool_manager = await get_pool_manager()
            pool_health = await pool_manager.health_check()
            if pool_health:
                print("   ✅ Connection pool: OK")
            else:
                print("   ❌ Connection pool: FAILED")
                issues.append("Connection pool health check failed")
        except Exception as e:
            print(f"   ❌ Connection pool: ERROR - {e}")
            issues.append(f"Connection pool error: {e}")

        # Cache system
        print("\n3. Checking cache system...")
        try:
            cache_manager = get_cache_manager()
            cache_health = await cache_manager.health_check()
            if cache_health["status"] == "healthy":
                print("   ✅ Cache system: OK")
            else:
                print(f"   ❌ Cache system: {cache_health['status']}")
                issues.append(f"Cache system: {cache_health['status']}")
        except Exception as e:
            print(f"   ❌ Cache system: ERROR - {e}")
            issues.append(f"Cache system error: {e}")

        # Performance benchmark
        print("\n4. Running performance benchmark...")
        try:
            benchmark = await self.performance_analytics.run_performance_benchmark()
            if benchmark["simple_query_time_ms"] < 100:
                print("   ✅ Query performance: OK")
            else:
                print(f"   ⚠️ Query performance: Slow ({benchmark['simple_query_time_ms']:.1f}ms)")
                issues.append("Query performance is slow")
        except Exception as e:
            print(f"   ❌ Performance benchmark: ERROR - {e}")
            issues.append(f"Performance benchmark error: {e}")

        # Summary
        print(f"\n🏥 Health Check Summary:")
        if not issues:
            print("✅ All systems are healthy!")
        else:
            print(f"❌ Found {len(issues)} issues:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Database Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Database commands
    subparsers.add_parser("init", help="Initialize database schema")
    subparsers.add_parser("check", help="Check database connection")
    subparsers.add_parser("pool-status", help="Show connection pool status")

    warm_pool_parser = subparsers.add_parser("warm-pool", help="Warm up connection pool")
    warm_pool_parser.add_argument("--connections", type=int, default=5, help="Number of connections to warm up")

    # Analytics commands
    analytics_parser = subparsers.add_parser("analytics", help="Show analytics")
    analytics_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")

    high_risk_parser = subparsers.add_parser("high-risk", help="Show high-risk patients")
    high_risk_parser.add_argument("--threshold", type=int, default=70, help="Risk score threshold")
    high_risk_parser.add_argument("--limit", type=int, default=10, help="Maximum number of patients to show")

    report_parser = subparsers.add_parser("report", help="Generate executive report")
    report_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")

    # Performance commands
    subparsers.add_parser("performance", help="Show performance metrics")
    subparsers.add_parser("health-check", help="Run comprehensive health check")

    # Cache commands
    subparsers.add_parser("cache-status", help="Show cache status")
    subparsers.add_parser("warm-cache", help="Warm up cache")
    subparsers.add_parser("clear-cache", help="Clear cache")

    # Monitoring commands
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring")
    monitor_parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")

    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Backup analytics data")
    backup_parser.add_argument("output_file", help="Output file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    cli = DatabaseCLI()

    try:
        if args.command == "init":
            await cli.init_database()
        elif args.command == "check":
            await cli.check_connection()
        elif args.command == "pool-status":
            await cli.show_pool_status()
        elif args.command == "warm-pool":
            await cli.warm_up_pool(args.connections)
        elif args.command == "analytics":
            await cli.show_analytics(args.days)
        elif args.command == "high-risk":
            await cli.show_high_risk_patients(args.threshold, args.limit)
        elif args.command == "report":
            await cli.generate_executive_report(args.days)
        elif args.command == "performance":
            await cli.show_performance_metrics()
        elif args.command == "health-check":
            await cli.run_health_check()
        elif args.command == "cache-status":
            await cli.show_cache_status()
        elif args.command == "warm-cache":
            await cli.warm_cache()
        elif args.command == "clear-cache":
            await cli.clear_cache()
        elif args.command == "monitor":
            await cli.start_monitoring(args.interval)
        elif args.command == "backup":
            await cli.backup_analytics(args.output_file)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("CLI command failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
