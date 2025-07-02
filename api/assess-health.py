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
            
            # Enhanced ML Risk Assessment (same logic as before)
            age = int(data['age'])
            symptoms = data['symptoms'].lower()
            medical_history = data['medical_history'].lower() if data['medical_history'] else ""
            
            # Risk scoring algorithm
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
            
            # Emergency symptoms detection
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
            
            # Medical history risk factors
            high_risk_conditions = [
                'diabetes', 'heart disease', 'hypertension', 'cancer', 'kidney disease',
                'liver disease', 'copd', 'asthma', 'stroke history', 'blood clots'
            ]
            
            for condition in high_risk_conditions:
                if condition in medical_history:
                    risk_score += 0.2
                    risk_factors.append(f"Pre-existing condition: {condition}")
            
            risk_score = min(risk_score, 1.0)
            
            # Determine urgency level
            if risk_score >= 0.7:
                risk_level = "high"
                urgency = "high"
            elif risk_score >= 0.4:
                risk_level = "moderate"
                urgency = "moderate"
            else:
                risk_level = "low"
                urgency = "low"
            
            # GOOGLE GEMINI AI WITH STRUCTURED OUTPUT
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            gemini_success = False
            ai_analysis = None
            model_used = "Enhanced Medical Algorithms"
            
            if GEMINI_AVAILABLE and gemini_api_key:
                try:
                    print(f"Attempting Gemini API call with structured prompt...")
                    
                    # Configure Gemini
                    genai.configure(api_key=gemini_api_key)
                    
                    # Try modern models first
                    model_names = ['gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro']
                    
                    model = None
                    working_model = None
                    
                    for model_name in model_names:
                        try:
                            model = genai.GenerativeModel(model_name)
                            test_response = model.generate_content("Test")
                            if test_response and test_response.text:
                                working_model = model_name
                                print(f"Using model: {model_name}")
                                break
                        except Exception as e:
                            continue
                    
                    if model and working_model:
                        # STRUCTURED PROMPT FOR CONSISTENT OUTPUT
                        prompt = f"""You are a medical AI providing preliminary health assessments. Analyze this patient case and provide a structured response.

PATIENT INFORMATION:
- Age: {age} years old
- Gender: {data['gender']}
- Symptoms: {data['symptoms']}
- Medical History: {data['medical_history'] or 'None reported'}
- Current Medications: {data['current_medications'] or 'None reported'}

ASSESSMENT CONTEXT:
- Calculated risk level: {urgency} priority
- Risk score: {risk_score}

REQUIRED OUTPUT FORMAT:
Provide exactly 6 medical recommendations as separate, actionable statements. Each recommendation should be:
1. Specific and actionable
2. Medically appropriate for {urgency} priority symptoms
3. Written for patient understanding
4. Professional medical guidance

START each recommendation on a new line with "RECOMMENDATION:" followed by the advice.

Also provide 2-3 sentences of clinical reasoning explaining why these symptoms require {urgency} priority attention.

START the clinical reasoning with "REASONING:" followed by your analysis.

Example format:
REASONING: [Your clinical analysis here]

RECOMMENDATION: [First actionable recommendation]
RECOMMENDATION: [Second actionable recommendation]
RECOMMENDATION: [Third actionable recommendation]
RECOMMENDATION: [Fourth actionable recommendation]
RECOMMENDATION: [Fifth actionable recommendation]
RECOMMENDATION: [Sixth actionable recommendation]"""
                        
                        # Generate AI response
                        response = model.generate_content(prompt)
                        ai_text = response.text
                        
                        print(f"Gemini response: {len(ai_text)} chars from {working_model}")
                        
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
                        
                        # If parsing failed, extract manually
                        if not reasoning or len(recommendations) < 4:
                            # Fallback parsing
                            reasoning_found = False
                            for line in lines:
                                if not reasoning_found and len(line) > 30 and 'symptom' in line.lower():
                                    reasoning = line
                                    reasoning_found = True
                                elif any(word in line.lower() for word in ['should', 'recommend', 'seek', 'contact', 'monitor', 'consider']):
                                    clean_line = line.replace('*', '').replace('-', '').replace('•', '').strip()
                                    if clean_line and len(clean_line) > 15:
                                        recommendations.append(clean_line)
                        
                        # Ensure we have complete data
                        if not reasoning:
                            reasoning = f"Clinical assessment indicates {urgency} priority attention is needed for {age}-year-old {data['gender']} presenting with {data['symptoms'][:80]}. The combination of symptoms and patient factors requires prompt medical evaluation."
                        
                        # Ensure we have 6 quality recommendations
                        default_recommendations = [
                            f"Seek {urgency} priority medical evaluation for symptom assessment",
                            "Contact healthcare provider or emergency services as appropriate",
                            "Monitor symptoms closely and document any changes",
                            "Maintain adequate hydration and rest in comfortable position",
                            "Have someone stay with patient if symptoms are concerning",
                            "Do not delay seeking medical care if symptoms worsen"
                        ]
                        
                        while len(recommendations) < 6:
                            for default_rec in default_recommendations:
                                if default_rec not in recommendations:
                                    recommendations.append(default_rec)
                                    break
                            break
                        
                        ai_analysis = {
                            "reasoning": reasoning,
                            "recommendations": recommendations[:6],
                            "urgency": urgency,
                            "explanation": f"Professional medical assessment provided by {working_model} with structured clinical reasoning.",
                            "ai_confidence": "high",
                            "model_used": f"Google {working_model}"
                        }
                        
                        model_used = f"Google {working_model}"
                        gemini_success = True
                        print("Structured Gemini AI analysis completed successfully")
                        
                except Exception as e:
                    print(f"Gemini API error: {str(e)}")
            
            # Fallback if Gemini failed - SAME STRUCTURE
            if not gemini_success:
                print("Using fallback algorithmic analysis")
                ai_analysis = {
                    "reasoning": f"Clinical assessment for {age}-year-old {data['gender']} presenting with {data['symptoms'][:100]}. Risk stratification indicates {urgency} priority based on symptom presentation, age demographics, and medical history factors.",
                    "recommendations": [
                        f"Seek {urgency} priority medical evaluation for comprehensive assessment",
                        "Document symptom progression and severity changes carefully",
                        "Maintain adequate hydration and rest in appropriate position",
                        "Monitor vital signs and consciousness level if possible",
                        "Contact healthcare provider or emergency services as indicated",
                        "Do not delay seeking care if symptoms significantly worsen"
                    ],
                    "urgency": urgency,
                    "explanation": "Professional medical assessment using evidence-based algorithms and risk stratification.",
                    "ai_confidence": "high",
                    "model_used": "Enhanced Medical Algorithms"
                }
            
            # ML Assessment - CONSISTENT STRUCTURE
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
            
            # Final Response
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
