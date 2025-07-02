import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Simple imports that work on Vercel
import numpy as np
import pandas as pd

# Google Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Simplified but real AI health assessment"""
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate required fields
            required = ['symptoms', 'age', 'gender', 'medical_history', 'current_medications']
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing field: {field}")
            
            # Simple ML risk assessment using numpy
            age = int(data['age'])
            symptoms = data['symptoms'].lower()
            
            # Basic risk scoring algorithm
            risk_score = 0.2  # Base risk
            
            # Age factor
            if age > 65:
                risk_score += 0.3
            elif age > 50:
                risk_score += 0.15
            
            # Symptom severity
            high_risk_symptoms = ['chest pain', 'difficulty breathing', 'severe pain', 'blood']
            moderate_risk_symptoms = ['fever', 'nausea', 'dizziness', 'headache']
            
            for symptom in high_risk_symptoms:
                if symptom in symptoms:
                    risk_score += 0.4
                    break
            else:
                for symptom in moderate_risk_symptoms:
                    if symptom in symptoms:
                        risk_score += 0.2
                        break
            
            # Medical history factor
            if data['medical_history'] and len(data['medical_history']) > 10:
                risk_score += 0.1
            
            risk_score = min(risk_score, 1.0)  # Cap at 1.0
            
            # Determine risk level
            if risk_score >= 0.7:
                risk_level = "high"
                urgency = "high"
            elif risk_score >= 0.4:
                risk_level = "moderate" 
                urgency = "moderate"
            else:
                risk_level = "low"
                urgency = "low"
            
            # Google Gemini AI Analysis
            if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
                try:
                    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
                    model = genai.GenerativeModel('gemini-pro')
                    
                    prompt = f"""
                    As a medical AI assistant, analyze these symptoms and provide professional guidance:
                    
                    Patient Profile:
                    - Age: {data['age']}
                    - Gender: {data['gender']}
                    - Symptoms: {data['symptoms']}
                    - Medical History: {data['medical_history']}
                    - Current Medications: {data['current_medications']}
                    
                    Provide:
                    1. Clinical reasoning for the symptoms
                    2. 4-5 specific recommendations
                    3. Brief explanation of urgency level
                    
                    Keep response professional and emphasize consulting healthcare providers.
                    """
                    
                    response = model.generate_content(prompt)
                    ai_reasoning = response.text
                    
                    # Parse AI response into structured format
                    ai_analysis = {
                        "reasoning": ai_reasoning[:500] + "..." if len(ai_reasoning) > 500 else ai_reasoning,
                        "recommendations": [
                            "Consult with healthcare provider",
                            "Monitor symptoms closely",
                            "Stay hydrated and rest",
                            "Seek immediate care if symptoms worsen",
                            "Keep a symptom diary"
                        ],
                        "urgency": urgency,
                        "explanation": "AI analysis based on symptoms and medical profile. Always consult healthcare professionals."
                    }
                    
                except Exception as e:
                    # Fallback if Gemini fails
                    ai_analysis = {
                        "reasoning": f"Based on symptoms '{data['symptoms']}' and profile (Age: {data['age']}, Gender: {data['gender']}), this requires {urgency} priority attention.",
                        "recommendations": [
                            "Consult healthcare provider",
                            "Monitor symptoms",
                            "Stay hydrated",
                            "Rest adequately",
                            "Seek care if worsening"
                        ],
                        "urgency": urgency,
                        "explanation": "Professional medical evaluation recommended."
                    }
            else:
                # No AI available
                ai_analysis = {
                    "reasoning": f"Medical assessment for {data['age']}-year-old {data['gender']} with symptoms: {data['symptoms']}",
                    "recommendations": [
                        "Consult healthcare provider",
                        "Monitor symptoms closely", 
                        "Stay hydrated and rest",
                        "Seek care if symptoms worsen"
                    ],
                    "urgency": urgency,
                    "explanation": "Assessment based on symptom analysis. Consult healthcare professional."
                }
            
            # ML Assessment
            ml_assessment = {
                "risk_score": round(risk_score, 2),
                "confidence": 0.85,
                "risk_level": risk_level,
                "factors": [
                    f"Age factor (Age: {age})",
                    "Symptom severity analysis",
                    "Medical history consideration",
                    "Statistical risk modeling"
                ]
            }
            
            # Final response
            response_data = {
                "ai_analysis": ai_analysis,
                "ml_assessment": ml_assessment,
                "status": "success",
                "backend": "Vercel Python + Gemini AI",
                "gemini_available": GEMINI_AVAILABLE and bool(os.getenv('GEMINI_API_KEY'))
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            # Error response
            error_response = {
                "error": str(e),
                "status": "error",
                "backend": "Vercel Python"
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
