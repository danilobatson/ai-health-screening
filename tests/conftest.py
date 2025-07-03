"""
Test configuration and fixtures for AI Health Assessment System
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from services.ai_health_service import AIHealthService
from ml_services.health_ml_service import HealthMLService

@pytest_asyncio.fixture
async def client():
    """Create test client for FastAPI app"""
    from httpx import ASGITransport, AsyncClient
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    mock_service = Mock(spec=AIHealthService)
    mock_service.assess_health = AsyncMock(return_value={
        "risk_level": "Low",
        "risk_score": 25,
        "urgency": "Routine",
        "clinical_reasoning": "Test assessment based on mild symptoms and young age.",
        "recommendations": [
            "Monitor symptoms and rest",
            "Stay hydrated",
            "Consult healthcare provider if symptoms worsen"
        ],
        "red_flags": ["Severe worsening", "High fever"],
        "confidence_score": 0.85,
        "ml_insights": "ML model suggests low risk",
        "analysis_type": "Hybrid AI + ML",
        "ml_prediction": {"ml_risk_level": "Low", "ml_confidence": 0.8},
        "ml_patterns": {"similar_patients": {"similar_patient_count": 15}},
        "hybrid_analysis": True
    })
    return mock_service

@pytest.fixture
def mock_ml_service():
    """Mock ML service for testing"""
    mock_service = Mock(spec=HealthMLService)
    mock_service.predict_risk_ml.return_value = {
        "ml_risk_level": "Low",
        "ml_confidence": 0.8,
        "risk_score": 0.25,
        "factors": ["Age assessment", "Symptom analysis"]
    }
    mock_service.analyze_health_patterns.return_value = {
        "similar_patients": {"similar_patient_count": 15},
        "symptom_patterns": {"primary_symptom": "headache"},
        "risk_trends": {"trend": "stable"},
        "ml_insights": "Pattern analysis complete"
    }
    return mock_service

@pytest.fixture
def sample_health_request():
    """Sample health assessment request data"""
    return {
        "name": "John Doe",
        "age": 30,
        "gender": "male",
        "symptoms": "Mild headache for 2 days, slight fatigue",
        "medical_history": "No significant medical history",
        "current_medications": "None"
    }

@pytest.fixture
def sample_health_response():
    """Sample expected health assessment response"""
    return {
        "ai_analysis": {
            "reasoning": "Test assessment based on mild symptoms and young age.",
            "recommendations": [
                "Monitor symptoms and rest",
                "Stay hydrated",
                "Consult healthcare provider if symptoms worsen"
            ],
            "urgency": "routine",
            "explanation": "ML model suggests low risk",
            "ai_confidence": "high",
            "model_used": "Hybrid AI + ML"
        },
        "ml_assessment": {
            "risk_score": 0.25,
            "confidence": 0.85,
            "risk_level": "low",
            "factors": ["Age assessment", "Symptom analysis", "ML pattern matching"]
        },
        "status": "success",
        "backend": "FastAPI Development Server + AI",
        "gemini_enabled": True,
        "gemini_success": True
    }

@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("ENVIRONMENT", "test")
