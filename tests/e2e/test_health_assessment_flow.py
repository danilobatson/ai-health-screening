"""
End-to-end tests for health assessment flow
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock

class TestHealthAssessmentFlow:
    """End-to-end test cases for complete health assessment flow"""

    @pytest.mark.asyncio
    async def test_complete_health_assessment_flow(self, client):
        """Test complete flow from request to response"""

        # Mock successful AI service
        mock_ai_service = Mock()
        mock_ai_service.assess_health = AsyncMock(return_value={
            "risk_level": "Moderate",
            "risk_score": 65,
            "urgency": "Monitor",
            "clinical_reasoning": "Patient presents with moderate symptoms that warrant monitoring. The combination of age and symptom presentation suggests a moderate risk level.",
            "recommendations": [
                "Schedule appointment with primary care physician within 1-2 days",
                "Monitor symptoms closely and document any changes",
                "Maintain adequate hydration and rest",
                "Seek immediate care if symptoms worsen significantly"
            ],
            "red_flags": [
                "Severe worsening of symptoms",
                "Development of high fever (>101.5°F)",
                "Difficulty breathing or chest pain"
            ],
            "confidence_score": 0.87,
            "ml_insights": "ML model analysis indicates moderate risk based on demographic and symptom patterns",
            "analysis_type": "Hybrid AI + ML Assessment",
            "ml_prediction": {
                "ml_risk_level": "Moderate",
                "ml_confidence": 0.82,
                "risk_score": 0.65
            },
            "ml_patterns": {
                "similar_patients": {"similar_patient_count": 24},
                "symptom_patterns": {"primary_symptom": "headache", "severity": "moderate"},
                "risk_trends": {"trend": "stable"}
            },
            "hybrid_analysis": True
        })

        # Complete realistic health assessment request
        health_request = {
            "name": "Sarah Johnson",
            "age": 42,
            "gender": "female",
            "symptoms": "Persistent headaches for the past 4 days, accompanied by mild nausea and sensitivity to light. Pain is moderate (6/10) and located primarily in the temples. Symptoms seem to worsen in the afternoon.",
            "medical_history": "Migraine history, hypothyroidism treated with levothyroxine",
            "current_medications": "Levothyroxine 75mcg daily, occasional ibuprofen for headaches"
        }

        with patch('main.ai_service', mock_ai_service):
            # Step 1: Make the assessment request
            response = await client.post("/api/assess-health", json=health_request)

            # Step 2: Verify successful response
            assert response.status_code == 200
            data = response.json()

            # Step 3: Verify complete response structure
            assert "ai_analysis" in data
            assert "ml_assessment" in data
            assert "status" in data
            assert "backend" in data
            assert "gemini_enabled" in data
            assert "gemini_success" in data

            # Step 4: Verify AI analysis completeness
            ai_analysis = data["ai_analysis"]
            assert "reasoning" in ai_analysis
            assert "recommendations" in ai_analysis
            assert "urgency" in ai_analysis
            assert "explanation" in ai_analysis
            assert "ai_confidence" in ai_analysis
            assert "model_used" in ai_analysis

            # Verify recommendations are actionable
            recommendations = ai_analysis["recommendations"]
            assert isinstance(recommendations, list)
            assert len(recommendations) >= 3
            for rec in recommendations:
                assert isinstance(rec, str)
                assert len(rec) > 10  # Meaningful recommendations

            # Step 5: Verify ML assessment completeness
            ml_assessment = data["ml_assessment"]
            assert "risk_score" in ml_assessment
            assert "confidence" in ml_assessment
            assert "risk_level" in ml_assessment
            assert "factors" in ml_assessment

            # Verify numerical values are in correct ranges
            assert 0 <= ml_assessment["risk_score"] <= 1
            assert 0 <= ml_assessment["confidence"] <= 1
            assert ml_assessment["risk_level"] in ["low", "moderate", "high"]

            # Step 6: Verify service was called correctly
            mock_ai_service.assess_health.assert_called_once()
            call_args = mock_ai_service.assess_health.call_args

            # Verify symptoms were passed as string
            assert call_args[1]['symptoms'] == health_request['symptoms']
            assert call_args[1]['age'] == health_request['age']
            assert isinstance(call_args[1]['medical_history'], list)

    @pytest.mark.asyncio
    async def test_high_risk_assessment_flow(self, client):
        """Test flow for high-risk patient scenario"""

        # Mock high-risk AI response
        mock_ai_service = Mock()
        mock_ai_service.assess_health = AsyncMock(return_value={
            "risk_level": "High",
            "risk_score": 85,
            "urgency": "Emergency",
            "clinical_reasoning": "Patient presents with severe symptoms that require immediate medical attention. The combination of chest pain, shortness of breath, and patient's age indicates high risk.",
            "recommendations": [
                "Seek immediate emergency medical care",
                "Call 911 or go to nearest emergency room",
                "Do not drive yourself to the hospital",
                "Have someone stay with you until medical help arrives"
            ],
            "red_flags": [
                "Severe chest pain",
                "Difficulty breathing",
                "Radiating pain to arm or jaw"
            ],
            "confidence_score": 0.95,
            "ml_insights": "ML model indicates high risk requiring immediate intervention",
            "analysis_type": "Hybrid AI + ML Emergency Assessment",
            "ml_prediction": {"ml_risk_level": "High", "ml_confidence": 0.93},
            "ml_patterns": {"similar_patients": {"similar_patient_count": 8}},
            "hybrid_analysis": True
        })

        high_risk_request = {
            "name": "Robert Smith",
            "age": 68,
            "gender": "male",
            "symptoms": "Severe chest pain that started 30 minutes ago, radiating to left arm. Shortness of breath, sweating, and nausea. Pain is crushing and rated 9/10.",
            "medical_history": "Previous heart attack 5 years ago, diabetes, high blood pressure",
            "current_medications": "Metoprolol, Lisinopril, Metformin, Aspirin"
        }

        with patch('main.ai_service', mock_ai_service):
            response = await client.post("/api/assess-health", json=high_risk_request)

            assert response.status_code == 200
            data = response.json()

            # Verify high-risk indicators
            ai_analysis = data["ai_analysis"]
            assert "emergency" in ai_analysis["urgency"].lower() or "urgent" in ai_analysis["urgency"].lower()

            # Verify emergency recommendations
            recommendations = ai_analysis["recommendations"]
            emergency_keywords = ["emergency", "911", "immediate", "hospital"]
            has_emergency_rec = any(
                any(keyword in rec.lower() for keyword in emergency_keywords)
                for rec in recommendations
            )
            assert has_emergency_rec

            # Verify high risk score
            ml_assessment = data["ml_assessment"]
            assert ml_assessment["risk_score"] > 0.7  # High risk threshold

    @pytest.mark.asyncio
    async def test_low_risk_assessment_flow(self, client):
        """Test flow for low-risk patient scenario"""

        # Mock low-risk AI response
        mock_ai_service = Mock()
        mock_ai_service.assess_health = AsyncMock(return_value={
            "risk_level": "Low",
            "risk_score": 20,
            "urgency": "Routine",
            "clinical_reasoning": "Patient presents with mild, common symptoms that are likely self-limiting. No immediate concerns based on age and symptom presentation.",
            "recommendations": [
                "Rest and maintain adequate hydration",
                "Monitor symptoms for any changes",
                "Consider over-the-counter pain relief if needed",
                "Schedule routine follow-up if symptoms persist beyond 1 week"
            ],
            "red_flags": [
                "Symptoms worsen significantly",
                "Development of fever",
                "Severe or persistent pain"
            ],
            "confidence_score": 0.82,
            "ml_insights": "ML model indicates low risk with routine monitoring sufficient",
            "analysis_type": "Hybrid AI + ML Routine Assessment",
            "ml_prediction": {"ml_risk_level": "Low", "ml_confidence": 0.85},
            "ml_patterns": {"similar_patients": {"similar_patient_count": 45}},
            "hybrid_analysis": True
        })

        low_risk_request = {
            "name": "Emily Chen",
            "age": 24,
            "gender": "female",
            "symptoms": "Mild headache and slight fatigue for 1 day. Headache is dull, rated 3/10. No other symptoms.",
            "medical_history": "No significant medical history",
            "current_medications": "None"
        }

        with patch('main.ai_service', mock_ai_service):
            response = await client.post("/api/assess-health", json=low_risk_request)

            assert response.status_code == 200
            data = response.json()

            # Verify low-risk indicators
            ai_analysis = data["ai_analysis"]
            assert "routine" in ai_analysis["urgency"].lower() or "low" in ai_analysis["urgency"].lower()

            # Verify appropriate recommendations for low risk
            recommendations = ai_analysis["recommendations"]
            routine_keywords = ["rest", "monitor", "hydration", "routine"]
            has_routine_rec = any(
                any(keyword in rec.lower() for keyword in routine_keywords)
                for rec in recommendations
            )
            assert has_routine_rec

            # Verify low risk score
            ml_assessment = data["ml_assessment"]
            assert ml_assessment["risk_score"] < 0.4  # Low risk threshold

    @pytest.mark.asyncio
    async def test_pediatric_assessment_flow(self, client):
        """Test flow for pediatric patient"""

        mock_ai_service = Mock()
        mock_ai_service.assess_health = AsyncMock(return_value={
            "risk_level": "Moderate",
            "risk_score": 45,
            "urgency": "Monitor",
            "clinical_reasoning": "Pediatric patient with fever requires careful monitoring. Age-appropriate assessment indicates moderate concern.",
            "recommendations": [
                "Monitor temperature regularly",
                "Ensure adequate fluid intake",
                "Contact pediatrician if fever persists or worsens",
                "Watch for signs of dehydration"
            ],
            "red_flags": [
                "High fever (>102°F)",
                "Signs of dehydration",
                "Difficulty breathing",
                "Unusual lethargy"
            ],
            "confidence_score": 0.88,
            "ml_insights": "Pediatric ML model indicates moderate risk with close monitoring",
            "analysis_type": "Hybrid AI + ML Pediatric Assessment",
            "ml_prediction": {"ml_risk_level": "Moderate", "ml_confidence": 0.84},
            "ml_patterns": {"similar_patients": {"similar_patient_count": 18}},
            "hybrid_analysis": True
        })

        pediatric_request = {
            "name": "Alex Thompson",
            "age": 8,
            "gender": "male",
            "symptoms": "Fever of 100.8°F for 2 days, mild cough, decreased appetite. Child is still active but slightly more tired than usual.",
            "medical_history": "No significant medical history, up to date on vaccinations",
            "current_medications": "Children's Tylenol as needed for fever"
        }

        with patch('main.ai_service', mock_ai_service):
            response = await client.post("/api/assess-health", json=pediatric_request)

            assert response.status_code == 200
            data = response.json()

            # Verify pediatric-appropriate recommendations
            recommendations = data["ai_analysis"]["recommendations"]
            pediatric_keywords = ["pediatrician", "child", "temperature", "fluid"]
            has_pediatric_rec = any(
                any(keyword in rec.lower() for keyword in pediatric_keywords)
                for rec in recommendations
            )
            assert has_pediatric_rec

    @pytest.mark.asyncio
    async def test_elderly_assessment_flow(self, client):
        """Test flow for elderly patient"""

        mock_ai_service = Mock()
        mock_ai_service.assess_health = AsyncMock(return_value={
            "risk_level": "High",
            "risk_score": 75,
            "urgency": "Urgent",
            "clinical_reasoning": "Elderly patient with multiple comorbidities presenting with concerning symptoms. Age and medical history indicate higher risk.",
            "recommendations": [
                "Contact primary care physician immediately",
                "Consider emergency care if symptoms worsen",
                "Monitor blood pressure and blood sugar regularly",
                "Have family member or caregiver assist with monitoring"
            ],
            "red_flags": [
                "Worsening confusion",
                "Difficulty breathing",
                "Chest pain",
                "Fall risk indicators"
            ],
            "confidence_score": 0.91,
            "ml_insights": "Geriatric ML model indicates elevated risk requiring prompt medical attention",
            "analysis_type": "Hybrid AI + ML Geriatric Assessment",
            "ml_prediction": {"ml_risk_level": "High", "ml_confidence": 0.89},
            "ml_patterns": {"similar_patients": {"similar_patient_count": 12}},
            "hybrid_analysis": True
        })

        elderly_request = {
            "name": "Margaret Williams",
            "age": 82,
            "gender": "female",
            "symptoms": "Increasing confusion over past 2 days, mild shortness of breath with walking, decreased appetite. Family reports patient seems 'not herself'.",
            "medical_history": "Diabetes type 2, hypertension, previous stroke 3 years ago, mild cognitive impairment",
            "current_medications": "Metformin, Lisinopril, Aspirin, Donepezil"
        }

        with patch('main.ai_service', mock_ai_service):
            response = await client.post("/api/assess-health", json=elderly_request)

            assert response.status_code == 200
            data = response.json()

            # Verify geriatric-appropriate assessment
            ai_analysis = data["ai_analysis"]

            # Should indicate higher urgency for elderly patients
            assert "urgent" in ai_analysis["urgency"].lower() or "high" in data["ml_assessment"]["risk_level"].lower()

            # Verify elderly-specific recommendations
            recommendations = ai_analysis["recommendations"]
            geriatric_keywords = ["physician", "caregiver", "monitor", "family"]
            has_geriatric_rec = any(
                any(keyword in rec.lower() for keyword in geriatric_keywords)
                for rec in recommendations
            )
            assert has_geriatric_rec
