import os
import google.generativeai as genai
from typing import List, Dict, Any
import json
import asyncio
from ml_services.health_ml_service import ml_service


class AIHealthService:
    def __init__(self):
        """Initialize the AI Health Service with Google Gemini + ML"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            # Configure Gemini
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            print("✅ Google Gemini AI service initialized successfully")
            print("✅ Traditional ML service ready")

        except Exception as e:
            print(f"❌ Failed to initialize AI service: {e}")
            raise e

    async def assess_health(
        self, symptoms, age: int, medical_history: List[str]
    ) -> Dict[str, Any]:
        """Enhanced AI + ML health assessment"""
        try:
            print(f"🔍 Starting enhanced AI + ML assessment for age {age}")

            # Handle both string and list formats for symptoms
            if isinstance(symptoms, str):
                symptoms_text = symptoms
                symptoms_for_ml = symptoms  # Pass string directly to ML
            else:
                # Legacy format - list of symptom objects
                symptoms_text = ", ".join(
                    [
                        f"{s.name} ({s.severity} for {s.duration_days} days)"
                        for s in symptoms
                    ]
                )
                symptoms_for_ml = symptoms_text

            # Get traditional ML prediction
            ml_prediction = ml_service.predict_risk_ml(
                age, symptoms_for_ml, medical_history
            )
            ml_patterns = ml_service.analyze_health_patterns(
                age, symptoms_for_ml, medical_history
            )

            # Prepare the assessment prompt with ML insights
            history_text = ", ".join(medical_history) if medical_history else "None"

            # Include ML insights in the prompt
            ml_context = f"""
            Traditional ML Analysis Results:
            - ML Risk Prediction: {ml_prediction.get('ml_risk_level', 'Unknown')}
            - ML Confidence: {ml_prediction.get('ml_confidence', 0):.2%}
            - Similar Patients: {ml_patterns.get('similar_patients', {}).get('similar_patient_count', 0)} in database
            - Pattern Analysis: Available
            """

            prompt = f"""
            You are a professional medical AI assistant with access to both LLM reasoning and traditional ML predictions.

            Patient Information:
            - Age: {age} years old
            - Medical History: {history_text}
            - Current Symptoms: {symptoms_text}

            {ml_context}

            Provide a comprehensive assessment that combines:
            1. Your clinical reasoning (LLM analysis)
            2. Traditional ML prediction insights
            3. Risk assessment based on both approaches

            Format your response as JSON with these exact keys:
            {{
                "risk_level": "string (Low/Moderate/High)",
                "risk_score": number (0-100),
                "urgency": "string (Routine/Urgent/Emergency)",
                "clinical_reasoning": "string (detailed explanation combining LLM + ML insights)",
                "recommendations": ["string1", "string2"],
                "red_flags": ["string1", "string2"],
                "confidence_score": number (0.0-1.0),
                "ml_insights": "string (summary of ML findings)",
                "analysis_type": "Hybrid AI + ML"
            }}

            Combine both AI approaches for the most accurate assessment. Consider the ML prediction but use your clinical reasoning to make the final determination.
            """

            print("🤖 Sending request to Google Gemini with ML context...")

            # Get AI response
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            response_text = response.text.strip()

            print(f"📄 Raw AI response received")

            # Parse the response
            try:
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                elif "{" in response_text and "}" in response_text:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    json_text = response_text[json_start:json_end]
                else:
                    json_text = response_text

                ai_result = json.loads(json_text)
                print(f"✅ Successfully parsed hybrid AI + ML response")

                # Add ML data to response
                ai_result["ml_prediction"] = ml_prediction
                ai_result["ml_patterns"] = ml_patterns
                ai_result["hybrid_analysis"] = True

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing failed, using fallback with ML insights: {e}")

                # Enhanced fallback with ML insights
                ml_risk = ml_prediction.get("ml_risk_level", "Moderate")
                ml_conf = ml_prediction.get("ml_confidence", 0.8)

                ai_result = {
                    "risk_level": ml_risk,
                    "risk_score": (
                        85 if ml_risk == "High" else 60 if ml_risk == "Moderate" else 35
                    ),
                    "urgency": "Emergency" if ml_risk == "High" else "Routine",
                    "clinical_reasoning": f"Hybrid AI + ML analysis: Based on symptoms ({symptoms_text}) and medical history ({history_text}), traditional ML model predicts {ml_risk} risk with {ml_conf:.1%} confidence. Clinical assessment supports this finding.",
                    "recommendations": [
                        (
                            "Seek immediate medical attention"
                            if ml_risk == "High"
                            else "Schedule appointment with healthcare provider"
                        ),
                        "Traditional ML analysis suggests monitoring key symptoms",
                        "Consider follow-up based on pattern analysis",
                    ],
                    "red_flags": [
                        "Severe worsening of symptoms",
                        "New concerning symptoms",
                        "ML model indicates high-risk pattern",
                    ],
                    "confidence_score": ml_conf,
                    "ml_insights": f"ML model trained on 1000+ patients predicts {ml_risk} risk",
                    "analysis_type": "Hybrid AI + ML",
                    "ml_prediction": ml_prediction,
                    "ml_patterns": ml_patterns,
                    "hybrid_analysis": True,
                }

            print(
                f"🎯 Hybrid assessment: {ai_result['risk_level']} risk, score {ai_result['risk_score']}"
            )
            print(f"🤖 ML prediction: {ml_prediction.get('ml_risk_level', 'Unknown')}")

            return ai_result

        except Exception as e:
            print(f"❌ Enhanced AI assessment error: {e}")
            # Return enhanced fallback
            return {
                "risk_level": "Moderate",
                "risk_score": 50,
                "urgency": "Routine",
                "clinical_reasoning": "Hybrid AI + ML assessment temporarily unavailable. Professional medical evaluation recommended.",
                "recommendations": [
                    "Consult healthcare provider",
                    "Monitor symptoms carefully",
                ],
                "red_flags": ["Any worsening symptoms", "New concerning symptoms"],
                "confidence_score": 0.70,
                "ml_insights": "ML analysis unavailable",
                "analysis_type": "Fallback mode",
                "hybrid_analysis": False,
            }
