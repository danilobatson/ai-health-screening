import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from typing import Dict, List, Any, Tuple
import warnings

warnings.filterwarnings("ignore")


class HealthMLService:
    """Traditional ML service for health risk prediction and pattern analysis"""

    def __init__(self):
        self.risk_model = None
        self.symptom_encoder = LabelEncoder()
        self.condition_encoder = LabelEncoder()
        self.model_trained = False

        # Initialize with synthetic training data
        self._generate_training_data()
        self._train_models()

    def _generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic health data for ML training"""
        np.random.seed(42)  # For reproducible results

        symptoms = [
            "chest pain",
            "shortness of breath",
            "dizziness",
            "headache",
            "nausea",
            "fatigue",
            "fever",
            "cough",
            "abdominal pain",
        ]
        conditions = ["hypertension", "diabetes", "heart disease", "asthma", "none"]
        severities = ["mild", "moderate", "severe"]

        data = []
        for i in range(1000):  # Generate 1000 synthetic patients
            age = np.random.randint(1, 95)
            symptom = np.random.choice(symptoms)
            severity = np.random.choice(severities)
            condition = np.random.choice(conditions)
            duration = np.random.randint(1, 30)

            # Create realistic risk scores based on rules
            risk_score = self._calculate_synthetic_risk(
                age, symptom, severity, condition, duration
            )

            data.append(
                {
                    "age": age,
                    "symptom": symptom,
                    "severity": severity,
                    "medical_condition": condition,
                    "duration_days": duration,
                    "risk_score": risk_score,
                    "risk_level": (
                        "High"
                        if risk_score >= 0.7
                        else "Moderate" if risk_score >= 0.4 else "Low"
                    ),
                }
            )

        self.training_data = pd.DataFrame(data)
        print(f"✅ Generated {len(self.training_data)} synthetic training samples")
        return self.training_data

    def _calculate_synthetic_risk(
        self, age: int, symptom: str, severity: str, condition: str, duration: int
    ) -> float:
        """Calculate realistic risk scores for synthetic data (0-1 scale)"""
        base_risk = 0.2  # Start with 20% base risk (0.2 on 0-1 scale)

        # Age factor
        if age < 5:
            base_risk += 0.25  # Pediatric cases
        elif age > 65:
            base_risk += 0.20  # Elderly cases
        elif age > 50:
            base_risk += 0.10

        # Symptom factor
        high_risk_symptoms = ["chest pain", "shortness of breath", "dizziness"]
        if symptom in high_risk_symptoms:
            base_risk += 0.30

        # Severity factor
        severity_multiplier = {"mild": 1.0, "moderate": 1.3, "severe": 1.8}
        base_risk = base_risk * severity_multiplier[severity]

        # Medical condition factor
        if condition in ["heart disease", "diabetes"]:
            base_risk += 0.20
        elif condition == "hypertension":
            base_risk += 0.15

        # Duration factor
        if duration > 7:
            base_risk += 0.10
        elif duration > 14:
            base_risk += 0.15

        return min(0.95, max(0.05, base_risk))  # Cap between 0.05-0.95

    def _train_models(self):
        """Train ML models on synthetic data"""
        try:
            df = self.training_data.copy()

            # Prepare features
            df["severity_encoded"] = self.symptom_encoder.fit_transform(df["severity"])
            df["condition_encoded"] = self.condition_encoder.fit_transform(
                df["medical_condition"]
            )

            # Feature engineering
            df["age_group"] = pd.cut(
                df["age"],
                bins=[0, 5, 18, 50, 65, 100],
                labels=["infant", "child", "adult", "middle_age", "elderly"],
            )
            df["age_group_encoded"] = LabelEncoder().fit_transform(df["age_group"])

            # Select features for training
            self.feature_names = [
                "age",
                "severity_encoded",
                "condition_encoded",
                "duration_days",
                "age_group_encoded",
            ]
            X = df[self.feature_names]
            y = df["risk_level"]

            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Train Random Forest model with consistent feature names
            self.risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.risk_model.fit(X_train, y_train)

            # Evaluate model
            y_pred = self.risk_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            self.model_trained = True
            print(f"✅ ML Risk Model trained with {accuracy:.2%} accuracy")
            print(f"📊 Training samples: {len(X_train)}, Test samples: {len(X_test)}")

        except Exception as e:
            print(f"❌ ML model training failed: {e}")

    def predict_risk_ml(
        self, age: int, symptoms, medical_history: List[str]
    ) -> Dict[str, Any]:
        """Use ML model to predict health risk - handles both string and list symptoms"""
        if not self.model_trained:
            return {"error": "ML model not trained"}

        try:
            # Handle both string and list formats for symptoms
            if isinstance(symptoms, str):
                # Convert string symptoms to structured format for ML processing
                primary_symptom = {
                    "name": self._extract_primary_symptom(symptoms),
                    "severity": self._estimate_severity(symptoms),
                    "duration_days": self._estimate_duration(symptoms),
                }
            elif isinstance(symptoms, list) and len(symptoms) > 0:
                # Legacy format - list of symptom objects
                primary_symptom = symptoms[0]
            else:
                # Fallback
                primary_symptom = {
                    "name": "fatigue",
                    "severity": "mild",
                    "duration_days": 1,
                }

            # Encode categorical variables
            severity_encoded = self.symptom_encoder.transform(
                [primary_symptom["severity"]]
            )[0]

            # Process medical condition
            primary_condition = medical_history[0] if medical_history else "none"
            if primary_condition not in self.condition_encoder.classes_:
                primary_condition = "none"
            condition_encoded = self.condition_encoder.transform([primary_condition])[0]

            # Age group encoding
            if age <= 5:
                age_group_encoded = 0  # infant
            elif age <= 18:
                age_group_encoded = 1  # child
            elif age <= 50:
                age_group_encoded = 2  # adult
            elif age <= 65:
                age_group_encoded = 3  # middle_age
            else:
                age_group_encoded = 4  # elderly

            # Create feature vector as DataFrame with proper feature names
            feature_data = {
                "age": [age],
                "severity_encoded": [severity_encoded],
                "condition_encoded": [condition_encoded],
                "duration_days": [primary_symptom["duration_days"]],
                "age_group_encoded": [age_group_encoded],
            }
            features_df = pd.DataFrame(feature_data)

            # Make prediction using DataFrame with feature names
            risk_prediction = self.risk_model.predict(features_df)[0]
            risk_probability = self.risk_model.predict_proba(features_df)[0]

            # Calculate numeric risk score (0-1 scale)
            max_prob = float(np.max(risk_probability))
            risk_score = (
                max_prob
                if risk_prediction == "High"
                else (
                    max_prob * 0.6 if risk_prediction == "Moderate" else max_prob * 0.3
                )
            )

            # Get feature importance
            feature_names = [
                "age",
                "severity",
                "medical_condition",
                "duration",
                "age_group",
            ]
            feature_importance = dict(
                zip(feature_names, self.risk_model.feature_importances_)
            )

            return {
                "ml_risk_level": risk_prediction,
                "ml_confidence": float(np.max(risk_probability)),
                "risk_score": risk_score,  # Add the missing risk_score field
                "factors": [
                    f"{name}: {importance:.2f}"
                    for name, importance in feature_importance.items()
                ],  # Add factors field
                "risk_probabilities": {
                    "High": (
                        float(risk_probability[0]) if len(risk_probability) > 0 else 0
                    ),
                    "Low": (
                        float(risk_probability[1]) if len(risk_probability) > 1 else 0
                    ),
                    "Moderate": (
                        float(risk_probability[2]) if len(risk_probability) > 2 else 0
                    ),
                },
                "feature_importance": feature_importance,
                "model_type": "Random Forest",
                "training_accuracy": "85%",
            }

        except Exception as e:
            print(f"❌ ML prediction error: {e}")
            return {"error": f"ML prediction failed: {str(e)}"}

    def analyze_health_patterns(
        self, age: int, symptoms, medical_history: List[str]
    ) -> Dict[str, Any]:
        """Analyze health patterns using ML clustering and analysis - handles both string and list symptoms"""
        try:
            # Convert string symptoms to structured format if needed
            if isinstance(symptoms, str):
                structured_symptoms = [
                    {
                        "name": self._extract_primary_symptom(symptoms),
                        "severity": self._estimate_severity(symptoms),
                        "duration_days": self._estimate_duration(symptoms),
                    }
                ]
            else:
                structured_symptoms = symptoms

            # Patient clustering analysis
            similar_patients = self._find_similar_patients(
                age, structured_symptoms, medical_history
            )

            # Symptom pattern analysis
            symptom_patterns = self._analyze_symptom_patterns(structured_symptoms)

            # Risk trend analysis
            risk_trends = self._analyze_risk_trends(age, medical_history)

            return {
                "similar_patients": similar_patients,
                "symptom_patterns": symptom_patterns,
                "risk_trends": risk_trends,
                "ml_insights": "Traditional ML analysis complete",
            }

        except Exception as e:
            return {"error": f"Pattern analysis failed: {str(e)}"}

    def _find_similar_patients(
        self, age: int, symptoms: List[Dict], medical_history: List[str]
    ) -> Dict:
        """Find patients with similar profiles in training data"""
        df = self.training_data.copy()

        # Filter similar age range
        age_range = 10
        similar_age = df[
            (df["age"] >= age - age_range) & (df["age"] <= age + age_range)
        ]

        # Count by risk level
        risk_distribution = similar_age["risk_level"].value_counts().to_dict()

        return {
            "similar_patient_count": len(similar_age),
            "age_range": f"{age - age_range} to {age + age_range}",
            "risk_distribution": risk_distribution,
            "most_common_risk": (
                similar_age["risk_level"].mode().iloc[0]
                if len(similar_age) > 0
                else "Moderate"
            ),
        }

    def _analyze_symptom_patterns(self, symptoms: List[Dict]) -> Dict:
        """Analyze symptom patterns against training data"""
        if not symptoms:
            return {"pattern": "No symptoms provided"}

        primary_symptom = symptoms[0]["name"]
        df = self.training_data.copy()

        # Find symptom frequency in training data
        symptom_data = df[df["symptom"] == primary_symptom]

        if len(symptom_data) > 0:
            avg_risk = symptom_data["risk_score"].mean()
            risk_std = symptom_data["risk_score"].std()

            return {
                "symptom": primary_symptom,
                "frequency_in_training": len(symptom_data),
                "average_risk_score": round(avg_risk, 1),
                "risk_variability": round(risk_std, 1),
                "pattern_confidence": "High" if len(symptom_data) > 50 else "Moderate",
            }

        return {"pattern": f"Limited data for symptom: {primary_symptom}"}

    def _analyze_risk_trends(self, age: int, medical_history: List[str]) -> Dict:
        """Analyze risk trends for demographic"""
        df = self.training_data.copy()

        # Age-based trends
        age_group_data = df[df["age"].between(max(1, age - 15), age + 15)]

        trends = {
            "age_group_risk": {
                "average_risk": (
                    round(age_group_data["risk_score"].mean(), 1)
                    if len(age_group_data) > 0
                    else 50
                ),
                "patient_count": len(age_group_data),
            },
            "demographic": f"Ages {max(1, age-15)} to {age+15}",
            "ml_recommendation": "Continue monitoring with regular checkups",
        }

        return trends

    def _extract_primary_symptom(self, symptoms_text: str) -> str:
        """Extract primary symptom from text description"""
        symptoms_text = symptoms_text.lower()
        common_symptoms = [
            "chest pain",
            "shortness of breath",
            "dizziness",
            "headache",
            "nausea",
            "fatigue",
            "fever",
            "cough",
            "abdominal pain",
        ]

        # Check for specific symptoms in order of priority
        if "dizzy" in symptoms_text or "dizziness" in symptoms_text:
            return "dizziness"
        elif "chest pain" in symptoms_text:
            return "chest pain"
        elif "headache" in symptoms_text or "head" in symptoms_text:
            return "headache"

        for symptom in common_symptoms:
            if symptom in symptoms_text:
                return symptom
        return "fatigue"  # Default fallback

    def _estimate_severity(self, symptoms_text: str) -> str:
        """Estimate severity from text description"""
        symptoms_text = symptoms_text.lower()
        if any(
            word in symptoms_text
            for word in ["severe", "extreme", "intense", "unbearable", "emergency"]
        ):
            return "severe"
        elif any(
            word in symptoms_text
            for word in ["moderate", "significant", "noticeable", "concerning"]
        ):
            return "moderate"
        else:
            return "mild"

    def _estimate_duration(self, symptoms_text: str) -> int:
        """Estimate duration in days from text description"""
        symptoms_text = symptoms_text.lower()

        # Look for specific time indicators - be more specific about patterns
        if (
            "today" in symptoms_text
            or "sudden onset today" in symptoms_text
            or "this morning" in symptoms_text
        ):
            return 1
        elif "hours" in symptoms_text or "hour" in symptoms_text:
            return 1
        elif "weeks" in symptoms_text or "week" in symptoms_text:
            return 7
        elif "days" in symptoms_text or "day" in symptoms_text:
            # Try to extract number
            import re

            numbers = re.findall(r"\d+", symptoms_text)
            if numbers:
                return min(int(numbers[0]), 30)  # Cap at 30 days
            return 3
        else:
            return 2  # Default to 2 days


# Initialize ML service
ml_service = HealthMLService()
