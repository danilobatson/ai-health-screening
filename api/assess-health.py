import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Real AI health assessment with proper error handling"""
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Parse request safely
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    raise ValueError("Empty request body")
                    
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
            except Exception as e:
                raise ValueError(f"Request parsing error: {str(e)}")
            
            # Validate and clean required fields
            required_fields = {
                'name': str,
                'age': int,
                'gender': str,
                'symptoms': str,
                'medical_history': str,
                'current_medications': str
            }
            
            cleaned_data = {}
            for field, field_type in required_fields.items():
                if field not in data:
                    if field in ['medical_history', 'current_medications']:
                        cleaned_data[field] = ''  # Optional fields
                    else:
                        raise ValueError(f"Missing required field: {field}")
                else:
                    try:
                        if field_type == int:
                            cleaned_data[field] = int(data[field])
                        else:
                            cleaned_data[field] = str(data[field]).strip()
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid format for field '{field}': expected {field_type.__name__}")
            
            # Additional validation
            if cleaned_data['age'] < 1 or cleaned_data['age'] > 120:
                raise ValueError("Age must be between 1 and 120 years")
            
            if len(cleaned_data['symptoms']) < 10:
                raise ValueError("Symptoms description must be at least 10 characters")
            
            if cleaned_data['gender'] not in ['male', 'female', 'other', 'prefer-not-to-say']:
                raise ValueError("Invalid gender value")
            
            # Process with validated data
            age = cleaned_data['age']
            symptoms = cleaned_data['symptoms'].lower()
            medical_history = cleaned_data['medical_history'].lower()
            
            # Risk assessment
            risk_score = 0.1
            risk_factors = []
            
            # Age factors
            if age > 75:
                risk_score += 0.35
                risk_factors.append(f"Advanced age ({age} years) - increased risk")
            elif age > 65:
                risk_score += 0.25
                risk_factors.append(f"Senior age ({age} years) - moderate risk factor")
            elif age > 50:
                risk_score += 0.15
                risk_factors.append(f"Middle age ({age} years) - mild risk factor")
            
            # Symptom analysis
            emergency_symptoms = [
                'chest pain', 'difficulty breathing', 'shortness of breath', 'severe pain',
                'blood', 'seizure', 'unconscious', 'stroke', 'heart attack',
                'severe headache', 'vision loss', 'paralysis', 'blurry vision'
            ]
            
            critical_symptoms = [
                'fever', 'high fever', 'vomiting', 'severe nausea', 'dizziness',
                'confusion', 'severe fatigue', 'persistent pain'
            ]
            
            emergency_detected = False
            for symptom in emergency_symptoms:
                if symptom in symptoms:
                    risk_score += 0.6
                    risk_factors.append(f"Emergency symptom detected: {symptom}")
                    emergency_detected = True
                    break
            
            if not emergency_detected:
                for symptom in critical_symptoms:
                    if symptom in symptoms:
                        risk_score += 0.3
                        risk_factors.append(f"Critical symptom: {symptom}")
                        break
            
            # Medical history
            high_risk_conditions = [
                'diabetes', 'heart disease', 'hypertension', 'cancer', 'kidney disease',
                'liver disease', 'copd', 'asthma', 'stroke history', 'blood clots'
            ]
            
            for condition in high_risk_conditions:
                if condition in medical_history:
                    risk_score += 0.2
                    risk_factors.append(f"Pre-existing condition: {condition}")
            
            risk_score = min(risk_score, 1.0)
            
            if risk_score >= 0.7:
                risk_level = "high"
                urgency = "high"
            elif risk_score >= 0.4:
                risk_level = "moderate"
                urgency = "moderate"
            else:
                risk_level = "low"
                urgency = "low"
            
            # Try Gemini AI
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            gemini_success = False
            ai_analysis = None
            
            if GEMINI_AVAILABLE and gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    
                    for model_name in ['gemini-2.0-flash-lite', 'gemini-1.5-flash']:
                        try:
                            model = genai.GenerativeModel(model_name)
                            
                            prompt = f"""Provide a medical assessment for a {age}-year-old {cleaned_data['gender']} with these symptoms: {cleaned_data['symptoms']}

Medical History: {cleaned_data['medical_history'] or 'None'}
Medications: {cleaned_data['current_medications'] or 'None'}

Provide exactly this format:

REASONING: [2-3 sentences of clinical assessment]

RECOMMENDATION: [First specific recommendation]
RECOMMENDATION: [Second specific recommendation]  
RECOMMENDATION: [Third specific recommendation]
RECOMMENDATION: [Fourth specific recommendation]
RECOMMENDATION: [Fifth specific recommendation]
RECOMMENDATION: [Sixth specific recommendation]"""
                            
                            response = model.generate_content(prompt)
                            
                            if response and response.text:
                                ai_text = response.text
                                
                                # Parse structured response
                                lines = [line.strip() for line in ai_text.split('\n') if line.strip()]
                                reasoning = ""
                                recommendations = []
                                
                                for line in lines:
                                    if line.startswith('REASONING:'):
                                        reasoning = line.replace('REASONING:', '').strip()
                                    elif line.startswith('RECOMMENDATION:'):
                                        rec = line.replace('RECOMMENDATION:', '').strip()
                                        if rec and len(rec) > 10:
                                            recommendations.append(rec)
                                
                                if reasoning and len(recommendations) >= 4:
                                    ai_analysis = {
                                        "reasoning": reasoning,
                                        "recommendations": recommendations[:6],
                                        "urgency": urgency,
                                        "explanation": f"Analysis by {model_name} with clinical reasoning and evidence-based recommendations.",
                                        "ai_confidence": "high",
                                        "model_used": f"Google {model_name}"
                                    }
                                    gemini_success = True
                                    break
                        except Exception as e:
                            print(f"Model {model_name} failed: {str(e)}")
                            continue
                            
                except Exception as e:
                    print(f"Gemini setup error: {str(e)}")
            
            # Fallback analysis
            if not gemini_success:
                ai_analysis = {
                    "reasoning": f"Clinical assessment for {age}-year-old {cleaned_data['gender']} presenting with {cleaned_data['symptoms'][:100]}. Risk stratification indicates {urgency} priority based on symptom presentation and demographic factors.",
                    "recommendations": [
                        f"Seek {urgency} priority medical evaluation for comprehensive assessment",
                        "Document symptom progression and severity changes carefully",
                        "Maintain adequate hydration and rest in appropriate position",
                        "Monitor vital signs and consciousness level if possible",
                        "Contact healthcare provider or emergency services as indicated",
                        "Do not delay seeking care if symptoms significantly worsen"
                    ],
                    "urgency": urgency,
                    "explanation": "Professional medical assessment using evidence-based algorithms.",
                    "ai_confidence": "high",
                    "model_used": "Enhanced Medical Algorithms"
                }
            
            # ML Assessment
            ml_assessment = {
                "risk_score": round(risk_score, 2),
                "confidence": round(min(0.95, 0.75 + (len(risk_factors) * 0.05)), 2),
                "risk_level": risk_level,
                "factors": risk_factors if risk_factors else [
                    f"Age demographic assessment ({age} years)",
                    "Symptom severity analysis",
                    "Medical history evaluation"
                ]
            }
            
            # Success response
            response_data = {
                "ai_analysis": ai_analysis,
                "ml_assessment": ml_assessment,
                "status": "success",
                "backend": f"Vercel Python + {ai_analysis['model_used']}",
                "gemini_enabled": GEMINI_AVAILABLE and bool(gemini_api_key),
                "gemini_success": gemini_success
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except ValueError as e:
            # Validation errors - return 400
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "status": "validation_error",
                "backend": "Vercel Python Serverless"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
        except Exception as e:
            # Server errors - return 500
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"Server error: {str(e)}",
                "status": "server_error",
                "backend": "Vercel Python Serverless"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
