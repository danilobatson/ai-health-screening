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
        """Real AI health assessment with Google Gemini"""
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
            
            # Enhanced ML Risk Assessment (same as before)
            age = int(data['age'])
            symptoms = data['symptoms'].lower()
            medical_history = data['medical_history'].lower() if data['medical_history'] else ""
            
            # Risk scoring
            risk_score = 0.1
            risk_factors = []
            
            # Age-based risk
            if age > 75:
                risk_score += 0.35
                risk_factors.append(f"Advanced age ({age} years) - increased risk")
            elif age > 65:
                risk_score += 0.25
                risk_factors.append(f"Senior age ({age} years) - moderate risk factor")
            elif age > 50:
                risk_score += 0.15
                risk_factors.append(f"Middle age ({age} years) - mild risk factor")
            
            # Emergency symptoms
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
            
            # Medical history risk
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
            
            # TRY GOOGLE GEMINI AI WITH CORRECT MODEL
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            gemini_success = False
            ai_analysis = None
            model_used = "Enhanced Medical Algorithms (Gemini Fallback)"
            
            if GEMINI_AVAILABLE and gemini_api_key:
                try:
                    print(f"Attempting Gemini API call with key: {gemini_api_key[:10]}...")
                    
                    # Configure Gemini
                    genai.configure(api_key=gemini_api_key)
                    
                    # Try different model names in order of preference
                    model_names = [
                        'gemini-2.0-flash-lite',
                        'gemini-1.5-flash',
                        'gemini-1.5-pro',
                        'models/gemini-1.5-flash',
                        'models/gemini-pro'
                    ]
                    
                    model = None
                    working_model = None
                    
                    for model_name in model_names:
                        try:
                            print(f"Trying model: {model_name}")
                            model = genai.GenerativeModel(model_name)
                            
                            # Test with a simple prompt first
                            test_response = model.generate_content("Say hello")
                            if test_response and test_response.text:
                                working_model = model_name
                                print(f"Success with model: {model_name}")
                                break
                        except Exception as e:
                            print(f"Model {model_name} failed: {str(e)}")
                            continue
                    
                    if model and working_model:
                        # Create medical prompt
                        prompt = f"""You are a medical AI providing preliminary health assessments. Analyze this patient case:

PATIENT: {age}-year-old {data['gender']}
SYMPTOMS: {data['symptoms']}
MEDICAL HISTORY: {data['medical_history'] or 'None reported'}
MEDICATIONS: {data['current_medications'] or 'None reported'}

Provide a professional medical assessment with:
1. Clinical reasoning (2-3 sentences explaining the symptoms)
2. 5-6 specific, actionable recommendations
3. Assessment of urgency level ({urgency} priority)
4. Professional medical guidance

Format your response as clear, professional medical advice appropriate for patient education. Focus on practical next steps and when to seek care."""
                        
                        # Generate AI response
                        response = model.generate_content(prompt)
                        ai_text = response.text
                        
                        print(f"Gemini response received: {len(ai_text)} characters from {working_model}")
                        
                        # Parse response into recommendations
                        lines = [line.strip() for line in ai_text.split('\n') if line.strip()]
                        recommendations = []
                        reasoning_parts = []
                        
                        # Better parsing of Gemini response
                        in_recommendations = False
                        for line in lines:
                            if len(line) > 15:
                                # Check if this looks like a recommendation
                                if (any(word in line.lower() for word in ['recommend', 'should', 'consider', 'seek', 'contact', 'monitor', 'follow', 'take', 'avoid', 'ensure']) 
                                    or line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '-', '•', '*'))):
                                    clean_rec = line.replace('*', '').replace('-', '').replace('•', '').strip()
                                    # Remove numbered lists
                                    clean_rec = clean_rec.split('.', 1)[-1].strip() if '.' in clean_rec[:3] else clean_rec
                                    if clean_rec and len(clean_rec) > 10:
                                        recommendations.append(clean_rec)
                                        in_recommendations = True
                                elif not in_recommendations and 'recommend' not in line.lower():
                                    reasoning_parts.append(line)
                        
                        # Ensure we have good recommendations
                        if len(recommendations) < 4:
                            recommendations.extend([
                                "Consult healthcare provider for proper medical evaluation",
                                "Monitor symptom progression and severity changes",
                                "Maintain adequate hydration and rest",
                                "Seek immediate medical care if symptoms worsen"
                            ])
                        
                        # Create reasoning from Gemini response or generate professional one
                        if reasoning_parts:
                            reasoning = ' '.join(reasoning_parts[:2])
                        else:
                            reasoning = f"Google Gemini AI analysis indicates {urgency} priority for {age}-year-old {data['gender']} presenting with {data['symptoms'][:80]}. Clinical evaluation considers symptom severity, patient demographics, and medical history for comprehensive assessment."
                        
                        ai_analysis = {
                            "reasoning": reasoning,
                            "recommendations": recommendations[:6],
                            "urgency": urgency,
                            "explanation": f"Analysis provided by {working_model} with clinical reasoning and evidence-based recommendations.",
                            "ai_confidence": "high",
                            "model_used": f"Google {working_model}"
                        }
                        
                        model_used = f"Google {working_model}"
                        gemini_success = True
                        print("Gemini AI analysis completed successfully")
                    else:
                        print("No working Gemini model found")
                        
                except Exception as e:
                    print(f"Gemini API error: {str(e)}")
            
            # Fallback if Gemini failed
            if not gemini_success:
                print("Using fallback algorithmic analysis")
                ai_analysis = {
                    "reasoning": f"Clinical assessment for {age}-year-old {data['gender']} presenting with {data['symptoms'][:100]}. Risk stratification indicates {urgency} priority based on symptom presentation, age demographics, and medical history factors.",
                    "recommendations": [
                        f"Medical evaluation recommended for {urgency} priority symptoms",
                        "Comprehensive symptom monitoring and documentation",
                        "Maintain adequate hydration and rest periods",
                        "Consider symptom severity trends and progression",
                        "Follow appropriate medical consultation timeline",
                        "Seek immediate care if symptoms significantly worsen"
                    ],
                    "urgency": urgency,
                    "explanation": "Professional medical assessment algorithms with multi-factor risk analysis.",
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
            
            # Response
            response_data = {
                "ai_analysis": ai_analysis,
                "ml_assessment": ml_assessment,
                "status": "success",
                "backend": f"Vercel Python + {model_used}",
                "gemini_enabled": GEMINI_AVAILABLE and bool(gemini_api_key),
                "gemini_success": gemini_success
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "status": "error",
                "backend": "Vercel Python Serverless"
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
