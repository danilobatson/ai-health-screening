"""
Integration tests for API endpoints
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock

class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert "message" in data
        assert "version" in data
        assert data["cors_enabled"] == True
        assert "ai_service" in data
    
    @pytest.mark.asyncio
    async def test_assess_health_invalid_age(self, client):
        """Test health assessment with invalid age"""
        invalid_request = {
            "name": "John Doe",
            "age": 150,  # Invalid age
            "gender": "male", 
            "symptoms": "test symptoms",
            "medical_history": "",
            "current_medications": ""
        }
        
        response = await client.post("/api/assess-health", json=invalid_request)
        assert response.status_code == 422
        data = response.json()
        assert "Age must be between 0 and 120" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_assess_health_empty_symptoms(self, client):
        """Test health assessment with empty symptoms"""
        request_with_empty_symptoms = {
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "symptoms": "",  # Empty symptoms
            "medical_history": "",
            "current_medications": ""
        }
        
        response = await client.post("/api/assess-health", json=request_with_empty_symptoms)
        assert response.status_code == 422
        data = response.json()
        assert "Symptoms are required" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_assess_health_ai_service_unavailable(self, client, sample_health_request):
        """Test when AI service is unavailable"""
        
        # Mock AI service as None
        with patch('main.ai_service', None):
            response = await client.post("/api/assess-health", json=sample_health_request)
            
            assert response.status_code == 500
            data = response.json()
            assert "AI service not available" in data["detail"]
