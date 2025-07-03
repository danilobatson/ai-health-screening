"""
Unit tests for ML Health Service
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from ml_services.health_ml_service import HealthMLService

class TestHealthMLService:
    """Test cases for ML Health Service"""

    @pytest.fixture
    def ml_service(self):
        """Create ML service instance for testing"""
        return HealthMLService()

    def test_ml_service_initialization(self, ml_service):
        """Test ML service initialization"""
        assert ml_service.model_trained == True
        assert ml_service.risk_model is not None
        assert hasattr(ml_service, 'symptom_encoder')
        assert hasattr(ml_service, 'condition_encoder')

    def test_predict_risk_ml_with_string_symptoms(self, ml_service):
        """Test ML prediction with string symptoms"""
        result = ml_service.predict_risk_ml(
            age=30,
            symptoms="mild headache for 2 days",
            medical_history=["no significant history"]
        )

        assert "ml_risk_level" in result
        assert "ml_confidence" in result
        assert "risk_score" in result
        assert "factors" in result
        assert isinstance(result["risk_score"], float)
        assert 0 <= result["risk_score"] <= 1
        assert 0 <= result["ml_confidence"] <= 1

    def test_predict_risk_ml_with_legacy_symptoms(self, ml_service):
        """Test ML prediction with legacy symptom format"""
        legacy_symptoms = [
            {"name": "headache", "severity": "mild", "duration_days": 2}
        ]

        result = ml_service.predict_risk_ml(
            age=45,
            symptoms=legacy_symptoms,
            medical_history=["diabetes"]
        )

        assert "ml_risk_level" in result
        assert result["ml_risk_level"] in ["Low", "Moderate", "High"]

    def test_predict_risk_ml_empty_symptoms(self, ml_service):
        """Test ML prediction with empty symptoms"""
        result = ml_service.predict_risk_ml(
            age=25,
            symptoms="",
            medical_history=[]
        )

        # Should use fallback values
        assert "ml_risk_level" in result
        assert result is not None

    def test_analyze_health_patterns_string_symptoms(self, ml_service):
        """Test health pattern analysis with string symptoms"""
        result = ml_service.analyze_health_patterns(
            age=35,
            symptoms="chest pain and shortness of breath",
            medical_history=["hypertension"]
        )

        assert "similar_patients" in result
        assert "symptom_patterns" in result
        assert "risk_trends" in result
        assert "ml_insights" in result

    def test_analyze_health_patterns_legacy_symptoms(self, ml_service):
        """Test health pattern analysis with legacy symptoms"""
        legacy_symptoms = [
            {"name": "chest pain", "severity": "severe", "duration_days": 1}
        ]

        result = ml_service.analyze_health_patterns(
            age=65,
            symptoms=legacy_symptoms,
            medical_history=["heart disease"]
        )

        assert "similar_patients" in result
        assert "symptom_patterns" in result

    def test_extract_primary_symptom(self, ml_service):
        """Test symptom extraction from text"""
        # Test common symptoms
        assert ml_service._extract_primary_symptom("severe chest pain") == "chest pain"
        assert ml_service._extract_primary_symptom("shortness of breath") == "shortness of breath"
        assert ml_service._extract_primary_symptom("mild headache") == "headache"
        assert ml_service._extract_primary_symptom("feeling dizzy") == "dizziness"

        # Test fallback
        assert ml_service._extract_primary_symptom("unknown symptom") == "fatigue"

    def test_estimate_severity(self, ml_service):
        """Test severity estimation from text"""
        assert ml_service._estimate_severity("severe chest pain") == "severe"
        assert ml_service._estimate_severity("extreme headache") == "severe"
        assert ml_service._estimate_severity("moderate discomfort") == "moderate"
        assert ml_service._estimate_severity("significant pain") == "moderate"
        assert ml_service._estimate_severity("mild headache") == "mild"
        assert ml_service._estimate_severity("slight discomfort") == "mild"

    def test_estimate_duration(self, ml_service):
        """Test duration estimation from text"""
        assert ml_service._estimate_duration("pain for 2 weeks") == 7
        assert ml_service._estimate_duration("headache for 3 days") == 3
        assert ml_service._estimate_duration("started 5 days ago") == 5
        assert ml_service._estimate_duration("sudden onset today") == 1
        assert ml_service._estimate_duration("started this morning") == 1
        assert ml_service._estimate_duration("ongoing symptoms") == 2  # default

    def test_age_group_encoding(self, ml_service):
        """Test age group encoding logic"""
        # Test through predict_risk_ml to verify age encoding
        result_infant = ml_service.predict_risk_ml(3, "fever", [])
        result_child = ml_service.predict_risk_ml(15, "headache", [])
        result_adult = ml_service.predict_risk_ml(30, "fatigue", [])
        result_middle = ml_service.predict_risk_ml(55, "chest pain", [])
        result_elderly = ml_service.predict_risk_ml(75, "dizziness", [])

        # All should return valid results
        for result in [result_infant, result_child, result_adult, result_middle, result_elderly]:
            assert "ml_risk_level" in result
            assert "risk_score" in result

    def test_medical_history_processing(self, ml_service):
        """Test medical history processing"""
        # Test with known conditions
        result_diabetes = ml_service.predict_risk_ml(
            50, "fatigue", ["diabetes"]
        )
        result_heart = ml_service.predict_risk_ml(
            60, "chest pain", ["heart disease"]
        )
        result_none = ml_service.predict_risk_ml(
            30, "headache", []
        )

        # All should return valid results
        for result in [result_diabetes, result_heart, result_none]:
            assert "ml_risk_level" in result
            assert isinstance(result["risk_score"], float)

    def test_model_not_trained_fallback(self, ml_service):
        """Test behavior when model is not trained"""
        # Temporarily disable model
        ml_service.model_trained = False

        result = ml_service.predict_risk_ml(30, "headache", [])

        assert "error" in result
        assert result["error"] == "ML model not trained"

    def test_synthetic_data_generation(self, ml_service):
        """Test synthetic training data generation"""
        # The service should have generated training data
        assert hasattr(ml_service, 'training_data')

        # Re-generate to test the method
        data = ml_service._generate_training_data()

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 1000  # Should generate 1000 samples
        assert 'age' in data.columns
        assert 'symptom' in data.columns
        assert 'risk_score' in data.columns

    def test_calculate_synthetic_risk(self, ml_service):
        """Test synthetic risk calculation"""
        # Test various scenarios
        low_risk = ml_service._calculate_synthetic_risk(25, "headache", "mild", "none", 1)
        high_risk = ml_service._calculate_synthetic_risk(75, "chest pain", "severe", "heart disease", 7)

        assert 0 <= low_risk <= 1
        assert 0 <= high_risk <= 1
        assert high_risk > low_risk  # Elderly with severe symptoms should have higher risk

    def test_ml_model_training_failure(self, monkeypatch):
        """Test ML model training failure handling"""
        def mock_failing_fit(*args, **kwargs):
            raise Exception("Training failed")

        service = HealthMLService()
        # Mock the fit method to fail
        monkeypatch.setattr(service.risk_model, 'fit', mock_failing_fit)

        # Try to retrain
        service._train_models()

        # Should handle the failure gracefully
        assert service.model_trained is True  # Still true from initial training

    def test_predict_risk_ml_with_unknown_condition(self):
        """Test ML prediction with unknown medical condition"""
        ml_service = HealthMLService()
        result = ml_service.predict_risk_ml(
            age=35,
            symptoms="headache",
            medical_history=["unknown_rare_condition"]
        )

        assert "ml_risk_level" in result
        assert "risk_score" in result
        assert isinstance(result["risk_score"], float)

    def test_analyze_health_patterns_empty_symptoms(self):
        """Test pattern analysis with empty symptoms"""
        ml_service = HealthMLService()
        result = ml_service.analyze_health_patterns(
            age=30,
            symptoms=[],
            medical_history=[]
        )

        assert "symptom_patterns" in result
        assert result["symptom_patterns"]["pattern"] == "No symptoms provided"

    def test_find_similar_patients_edge_case(self):
        """Test finding similar patients with edge case ages"""
        ml_service = HealthMLService()

        # Test with very young age
        result = ml_service._find_similar_patients(2, [{"name": "fever", "severity": "mild", "duration_days": 1}], [])
        assert "similar_patient_count" in result
        assert "age_range" in result

        # Test with very old age
        result = ml_service._find_similar_patients(90, [{"name": "fatigue", "severity": "mild", "duration_days": 1}], [])
        assert "similar_patient_count" in result

    def test_duration_estimation_edge_cases(self):
        """Test duration estimation with various text patterns"""
        ml_service = HealthMLService()

        # Test various patterns
        assert ml_service._estimate_duration("started this morning") == 1
        assert ml_service._estimate_duration("for 15 days now") == 15
        assert ml_service._estimate_duration("ongoing for 2 weeks") == 7
        assert ml_service._estimate_duration("several hours ago") == 1
        assert ml_service._estimate_duration("no time information") == 2  # default
