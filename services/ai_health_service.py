import os
import google.generativeai as genai
from typing import List, Dict, Any
import json
import asyncio

class AIHealthService:
    def __init__(self):
        """Initialize the AI Health Service with Google Gemini"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Google Gemini AI service initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize AI service: {e}")
            raise e

    async def assess_health(self, symptoms, age: int, medical_history: List[str]) -> Dict[str, Any]:
        """THIS IS THE MISSING METHOD - Perform AI-powered health assessment"""
        try:
            print(f"🔍 Starting AI assessment for age {age}")
            
            # Prepare the assessment prompt
            symptoms_text = ", ".join([f"{s.name} ({s.severity} for {s.duration_days} days)" for s in symptoms])
            history_text = ", ".join(medical_history) if medical_history else "None"
            
            print(f"�� Analyzing symptoms: {symptoms_text}")
            print(f"📋 Medical history: {history_text}")
            
            prompt = f"""
            You are a professional medical AI assistant. Analyze the following patient case and provide a comprehensive health assessment.

            Patient Information:
            - Age: {age} years old
            - Medical History: {history_text}
            - Current Symptoms: {symptoms_text}

            Please provide a detailed analysis with the following information:
            1. Risk Level (Low, Moderate, High)
            2. Risk Score (0-100 numeric scale)
            3. Urgency (Routine, Urgent, Emergency)
            4. Clinical Reasoning (detailed medical explanation)
            5. Recommendations (specific actionable advice)
            6. Red Flags (warning signs to watch for)
            7. Confidence Score (0.0-1.0 in your assessment)

            Format your response as JSON with these exact keys:
            {{
                "risk_level": "string",
                "risk_score": number,
                "urgency": "string", 
                "clinical_reasoning": "string",
                "recommendations": ["string1", "string2"],
                "red_flags": ["string1", "string2"],
                "confidence_score": number
            }}

            Focus on professional medical analysis and emergency detection. If chest pain is involved, consider cardiac risks.
            """

            print("🤖 Sending request to Google Gemini...")

            # Get AI response using asyncio.to_thread for sync API
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            response_text = response.text.strip()
            
            print(f"📄 Raw AI response: {response_text[:200]}...")

            # Parse the response
            try:
                # Extract JSON from response
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
                print(f"✅ Successfully parsed AI response")
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing failed: {e}")
                # Fallback response based on symptoms
                risk_level = "High" if any("chest pain" in s.name.lower() for s in symptoms) else "Moderate"
                risk_score = 85 if risk_level == "High" else 60
                urgency = "Emergency" if risk_level == "High" else "Routine"
                
                ai_result = {
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "urgency": urgency,
                    "clinical_reasoning": f"Based on the reported symptoms ({symptoms_text}) and medical history ({history_text}), professional medical evaluation is recommended. The combination of symptoms warrants careful assessment.",
                    "recommendations": [
                        "Seek immediate medical attention" if urgency == "Emergency" else "Schedule appointment with healthcare provider",
                        "Monitor symptoms closely and report any changes",
                        "Keep a detailed symptom diary"
                    ],
                    "red_flags": [
                        "Severe worsening of symptoms",
                        "New chest pain or shortness of breath",
                        "Dizziness or fainting"
                    ],
                    "confidence_score": 0.85
                }

            print(f"🎯 Final assessment: {ai_result['risk_level']} risk, score {ai_result['risk_score']}")
            return ai_result

        except Exception as e:
            print(f"❌ AI assessment error: {e}")
            # Return safe fallback response
            return {
                "risk_level": "Moderate",
                "risk_score": 50,
                "urgency": "Routine",
                "clinical_reasoning": "AI assessment temporarily unavailable. Professional medical evaluation recommended for any health concerns.",
                "recommendations": ["Consult healthcare provider", "Monitor symptoms carefully"],
                "red_flags": ["Any worsening symptoms", "New concerning symptoms"],
                "confidence_score": 0.70
            }
