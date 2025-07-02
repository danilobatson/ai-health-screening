"""
AI Health Assessment Service - Google Gemini Integration
Transforms basic health data into intelligent medical analysis
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel

# Load environment variables FIRST
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SymptomData(BaseModel):
    name: str
    severity: str
    duration_days: Optional[int] = None

class AIHealthAnalysis(BaseModel):
    risk_assessment: str
    risk_score: int
    urgency_level: str
    clinical_reasoning: str
    recommendations: List[str]
    red_flags: List[str]
    confidence_score: float

class AIHealthService:
    """AI-powered health assessment using Google Gemini"""
    
    def __init__(self):
        # Ensure environment is loaded
        load_dotenv()
        
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            available_keys = [k for k in os.environ.keys() if 'GEMINI' in k.upper()]
            raise ValueError(f"❌ GEMINI_API_KEY not found. Available keys: {available_keys}")
        
        # Configure Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ AI Health Service initialized with Gemini")
        except Exception as e:
            raise ValueError(f"❌ Gemini configuration failed: {str(e)}")
    
    async def analyze_health_symptoms(
        self,
        symptoms: List[SymptomData],
        age: int,
        medical_history: List[str],
        patient_name: str = "Patient"
    ) -> AIHealthAnalysis:
        """Perform comprehensive AI health analysis"""
        try:
            # Build health assessment prompt
            prompt = self._build_health_prompt(symptoms, age, medical_history, patient_name)
            
            # Get AI analysis from Gemini
            response = await self._get_gemini_analysis(prompt)
            
            # Parse and validate response
            analysis = self._parse_health_response(response)
            
            logger.info(f"✅ AI analysis completed for {patient_name}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {str(e)}")
            return self._get_fallback_analysis(symptoms, age)
    
    def _build_health_prompt(self, symptoms, age, medical_history, patient_name) -> str:
        """Build comprehensive health assessment prompt"""
        
        symptoms_text = "\n".join([
            f"- {s.name} (severity: {s.severity}, duration: {s.duration_days or 'unknown'} days)"
            for s in symptoms
        ])
        
        history_text = ", ".join(medical_history) if medical_history else "None reported"
        
        return f"""
You are an expert clinical AI assistant. Analyze this patient data and provide a comprehensive health risk assessment.

**PATIENT INFORMATION:**
- Age: {age} years
- Medical History: {history_text}

**CURRENT SYMPTOMS:**
{symptoms_text}

**REQUIRED JSON RESPONSE:**
{{
    "risk_assessment": "Detailed clinical evaluation of the patient's condition",
    "risk_score": [0-100 integer score],
    "urgency_level": "Routine|Monitor|Urgent|Emergency",
    "clinical_reasoning": "Medical explanation of assessment reasoning",
    "recommendations": ["specific actionable medical advice"],
    "red_flags": ["emergency warning signs or 'None identified'"],
    "confidence_score": [0.0-1.0 confidence level]
}}

Consider age-related risks, symptom patterns, medical history impact, and emergency signs. 
Be conservative - err on side of caution for patient safety.
Always recommend professional medical consultation for serious concerns.
Respond with ONLY the JSON object, no additional text.
"""
    
    async def _get_gemini_analysis(self, prompt: str) -> str:
        """Get analysis from Gemini"""
        response = self.model.generate_content(prompt)
        return response.text
    
    def _parse_health_response(self, response_text: str) -> AIHealthAnalysis:
        """Parse Gemini response into structured analysis"""
        try:
            # Clean JSON response
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            return AIHealthAnalysis(
                risk_assessment=data.get("risk_assessment", "Assessment pending"),
                risk_score=max(0, min(100, int(data.get("risk_score", 50)))),
                urgency_level=data.get("urgency_level", "Monitor"),
                clinical_reasoning=data.get("clinical_reasoning", "Analysis in progress"),
                recommendations=data.get("recommendations", ["Consult healthcare provider"]),
                red_flags=data.get("red_flags", ["None identified"]),
                confidence_score=max(0.0, min(1.0, float(data.get("confidence_score", 0.7))))
            )
            
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {str(e)}")
            return self._get_fallback_analysis([], 30)
    
    def _get_fallback_analysis(self, symptoms: List[SymptomData], age: int) -> AIHealthAnalysis:
        """Fallback when AI is unavailable"""
        risk_score = len(symptoms) * 15
        if age > 65: risk_score += 20
        elif age < 18: risk_score += 10
        
        # Severity adjustments
        for symptom in symptoms:
            if symptom.severity == "severe":
                risk_score += 20
            elif symptom.severity == "moderate":
                risk_score += 10
        
        risk_score = min(100, max(0, risk_score))
        
        urgency = "Urgent" if risk_score >= 75 else "Monitor" if risk_score >= 50 else "Routine"
        
        return AIHealthAnalysis(
            risk_assessment=f"Basic assessment - {len(symptoms)} symptoms reported",
            risk_score=risk_score,
            urgency_level=urgency,
            clinical_reasoning="Fallback assessment based on symptom count, severity, and age factors",
            recommendations=[
                "Monitor symptoms closely",
                "Consult healthcare provider if symptoms persist or worsen",
                "Maintain proper hydration and rest"
            ],
            red_flags=["None identified with basic assessment"],
            confidence_score=0.6
        )

# Global service instance
_ai_service = None

def get_ai_service() -> AIHealthService:
    """Get AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIHealthService()
    return _ai_service
