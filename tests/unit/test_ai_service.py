"""
Unit tests for AI Health Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from services.ai_health_service import AIHealthService


class TestAIHealthService:
    """Test cases for AI Health Service"""

    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing"""
        with patch("services.ai_health_service.genai") as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            service = AIHealthService()
            service.model = mock_model
            return service

    @pytest.mark.asyncio
    async def test_assess_health_with_string_symptoms(self, ai_service):
        """Test health assessment with string symptoms"""
        # Mock the model response
        mock_response = Mock()
        mock_response.text = """
        {
            "risk_level": "Low",
            "risk_score": 25,
            "urgency": "Routine",
            "clinical_reasoning": "Based on mild symptoms, low risk assessment.",
            "recommendations": ["Rest", "Stay hydrated", "Monitor symptoms"],
            "red_flags": ["High fever", "Severe pain"],
            "confidence_score": 0.85,
            "ml_insights": "ML analysis complete",
            "analysis_type": "Hybrid AI + ML"
        }
        """

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_response

            # Mock ML service
            with patch("services.ai_health_service.ml_service") as mock_ml:
                mock_ml.predict_risk_ml.return_value = {
                    "ml_risk_level": "Low",
                    "ml_confidence": 0.8,
                }
                mock_ml.analyze_health_patterns.return_value = {
                    "similar_patients": {"similar_patient_count": 10}
                }

                result = await ai_service.assess_health(
                    symptoms="Mild headache for 2 days",
                    age=30,
                    medical_history=["No significant history"],
                )

                assert result["risk_level"] == "Low"
                assert result["risk_score"] == 25
                assert result["urgency"] == "Routine"
                assert "recommendations" in result
                assert len(result["recommendations"]) >= 1
                assert result["confidence_score"] == 0.85

    @pytest.mark.asyncio
    async def test_assess_health_with_legacy_symptoms(self, ai_service):
        """Test health assessment with legacy symptom format"""
        # Mock legacy symptom format
        legacy_symptoms = [{"name": "headache", "severity": "mild", "duration_days": 2}]

        mock_response = Mock()
        mock_response.text = """
        {
            "risk_level": "Moderate",
            "risk_score": 50,
            "urgency": "Monitor",
            "clinical_reasoning": "Moderate symptoms require monitoring.",
            "recommendations": ["See doctor", "Rest"],
            "red_flags": ["Worsening"],
            "confidence_score": 0.75,
            "ml_insights": "Analysis complete",
            "analysis_type": "Hybrid AI + ML"
        }
        """

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_response

            with patch("services.ai_health_service.ml_service") as mock_ml:
                mock_ml.predict_risk_ml.return_value = {
                    "ml_risk_level": "Moderate",
                    "ml_confidence": 0.75,
                }
                mock_ml.analyze_health_patterns.return_value = {
                    "similar_patients": {"similar_patient_count": 5}
                }

                result = await ai_service.assess_health(
                    symptoms=legacy_symptoms, age=45, medical_history=[]
                )

                assert result["risk_level"] == "Moderate"
                assert result["risk_score"] == 50

    @pytest.mark.asyncio
    async def test_assess_health_fallback_on_error(self, ai_service):
        """Test fallback behavior when AI service fails"""

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.side_effect = Exception("AI service error")

            with patch("services.ai_health_service.ml_service") as mock_ml:
                mock_ml.predict_risk_ml.return_value = {
                    "ml_risk_level": "Moderate",
                    "ml_confidence": 0.7,
                }
                mock_ml.analyze_health_patterns.return_value = {
                    "similar_patients": {"similar_patient_count": 0}
                }

                result = await ai_service.assess_health(
                    symptoms="Test symptoms", age=25, medical_history=[]
                )

                # Should return fallback response
                assert "risk_level" in result
                assert "recommendations" in result
                assert result["hybrid_analysis"] == False

    @pytest.mark.asyncio
    async def test_assess_health_json_parsing_fallback(self, ai_service):
        """Test fallback when JSON parsing fails"""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.text = "Invalid JSON response from AI"

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_response

            with patch("services.ai_health_service.ml_service") as mock_ml:
                mock_ml.predict_risk_ml.return_value = {
                    "ml_risk_level": "Low",
                    "ml_confidence": 0.8,
                }
                mock_ml.analyze_health_patterns.return_value = {
                    "similar_patients": {"similar_patient_count": 8}
                }

                result = await ai_service.assess_health(
                    symptoms="Test symptoms", age=35, medical_history=[]
                )

                # Should use ML-based fallback
                assert result["risk_level"] == "Low"  # From ML prediction
                assert "ML model" in result["clinical_reasoning"]
                assert result["hybrid_analysis"] == True

    def test_ai_service_initialization_success(self):
        """Test successful AI service initialization"""
        with patch("services.ai_health_service.genai") as mock_genai:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"}):
                mock_model = Mock()
                mock_genai.GenerativeModel.return_value = mock_model

                service = AIHealthService()

                mock_genai.configure.assert_called_once_with(api_key="test_key")
                mock_genai.GenerativeModel.assert_called_once_with("gemini-2.5-flash-lite")
                assert service.model == mock_model

    def test_ai_service_initialization_failure(self):
        """Test AI service initialization failure"""
        with patch("services.ai_health_service.genai") as mock_genai:
            with patch.dict("os.environ", {}, clear=True):
                with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
                    AIHealthService()
