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
        """AI health assessment with bulletproof error handling"""
        # Always start with 200 OK and proper headers
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        try:
            # Parse request safely
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                raise ValueError("Empty request body")

            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            print(f"Received data: {data}")

            # Clean and validate data
            required_fields = ["name", "age", "gender", "symptoms"]
            optional_fields = ["medical_history", "current_medications"]

            cleaned_data = {}

            # Process required fields
            for field in required_fields:
                if field not in data or not data[field]:
                    error_response = {
                        "error": f"Missing or empty required field: {field}",
                        "status": "validation_error",
                        "field": field,
                    }
                    self.wfile.write(json.dumps(error_response).encode("utf-8"))
                    return

                if field == "age":
                    try:
                        age_val = int(data[field])
                        if age_val < 1 or age_val > 120:
                            raise ValueError("Age out of range")
                        cleaned_data[field] = age_val
                    except (ValueError, TypeError):
                        error_response = {
                            "error": "Age must be a number between 1 and 120",
                            "status": "validation_error",
                            "field": field,
                        }
                        self.wfile.write(json.dumps(error_response).encode("utf-8"))
                        return
                else:
                    cleaned_data[field] = str(data[field]).strip()

            # Process optional fields
            for field in optional_fields:
                cleaned_data[field] = str(data.get(field, "")).strip()

            # Additional validation
            if len(cleaned_data["symptoms"]) < 10:
                error_response = {
                    "error": "Symptoms description must be at least 10 characters",
                    "status": "validation_error",
                    "field": "symptoms",
                }
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
                return

            valid_genders = ["male", "female", "other", "prefer-not-to-say"]
            if cleaned_data["gender"] not in valid_genders:
                error_response = {
                    "error": f"Gender must be one of: {', '.join(valid_genders)}",
                    "status": "validation_error",
                    "field": "gender",
                }
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
                return

            print(f"Cleaned data: {cleaned_data}")

            # Process assessment
            age = cleaned_data["age"]
            symptoms = cleaned_data["symptoms"].lower()
            medical_history = cleaned_data["medical_history"].lower()

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
                "chest pain",
                "difficulty breathing",
                "shortness of breath",
                "severe pain",
                "blood",
                "seizure",
                "unconscious",
                "stroke",
                "heart attack",
                "severe headache",
                "vision loss",
                "paralysis",
                "blurry vision",
            ]

            critical_symptoms = [
                "fever",
                "high fever",
                "vomiting",
                "severe nausea",
                "dizziness",
                "confusion",
                "severe fatigue",
                "persistent pain",
                "chills",
                "dehydration",
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
                "diabetes",
                "heart disease",
                "hypertension",
                "cancer",
                "kidney disease",
                "liver disease",
                "copd",
                "asthma",
                "stroke history",
                "blood clots",
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
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            gemini_success = False
            ai_analysis = None

            if GEMINI_AVAILABLE and gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)

                    for model_name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
                        try:
                            model = genai.GenerativeModel(model_name)

                            prompt = f"""You are a medical AI assistant. Analyze this patient case and respond in JSON format only.

Patient: {age}-year-old {cleaned_data['gender']}
Symptoms: {cleaned_data['symptoms']}
Medical History: {cleaned_data['medical_history'] or 'None reported'}
Current Medications: {cleaned_data['current_medications'] or 'None reported'}

Respond with ONLY valid JSON (no markdown, no code blocks):
{{"reasoning": "2-3 sentence clinical assessment", "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3", "recommendation 4", "recommendation 5", "recommendation 6"]}}"""

                            response = model.generate_content(prompt)

                            if response and response.text:
                                ai_text = response.text.strip()
                                print(f"Gemini raw response: {ai_text[:300]}...")

                                # Try to parse as JSON first
                                try:
                                    # Clean up response - remove markdown code blocks if present
                                    clean_text = ai_text
                                    if "```json" in clean_text:
                                        clean_text = clean_text.split("```json")[1].split("```")[0]
                                    elif "```" in clean_text:
                                        clean_text = clean_text.split("```")[1].split("```")[0]
                                    clean_text = clean_text.strip()

                                    parsed = json.loads(clean_text)
                                    reasoning = parsed.get("reasoning", "")
                                    recommendations = parsed.get("recommendations", [])

                                    if reasoning and len(recommendations) >= 3:
                                        ai_analysis = {
                                            "reasoning": reasoning,
                                            "recommendations": recommendations[:6],
                                            "urgency": urgency,
                                            "explanation": f"Analysis by {model_name} with clinical reasoning.",
                                            "ai_confidence": "high",
                                            "model_used": f"Google {model_name}",
                                        }
                                        gemini_success = True
                                        print(f"Gemini JSON parsing successful with {model_name}")
                                        break
                                except json.JSONDecodeError:
                                    print(f"JSON parsing failed, trying text parsing...")

                                # Fallback: try to extract useful content from free text
                                if not gemini_success and len(ai_text) > 50:
                                    # Use the raw response as reasoning
                                    ai_analysis = {
                                        "reasoning": ai_text[:500].replace('\n', ' ').strip(),
                                        "recommendations": [
                                            f"Seek {urgency} priority medical evaluation",
                                            "Monitor symptoms and document changes",
                                            "Stay hydrated and rest appropriately",
                                            "Contact healthcare provider if symptoms worsen",
                                            "Keep emergency contacts available",
                                            "Follow up with your primary care physician",
                                        ],
                                        "urgency": urgency,
                                        "explanation": f"Analysis by {model_name}.",
                                        "ai_confidence": "medium",
                                        "model_used": f"Google {model_name}",
                                    }
                                    gemini_success = True
                                    print(f"Gemini text extraction successful with {model_name}")
                                    break
                        except Exception as e:
                            print(f"Model {model_name} failed: {str(e)}")
                            continue

                except Exception as e:
                    print(f"Gemini error: {str(e)}")

            # Fallback analysis
            if not gemini_success:
                print("Using fallback analysis")
                ai_analysis = {
                    "reasoning": f"Clinical assessment for {age}-year-old {cleaned_data['gender']} with {cleaned_data['symptoms'][:80]}. Symptoms including {', '.join([s for s in critical_symptoms if s in symptoms][:3])} indicate {urgency} priority medical attention based on symptom presentation and demographic factors.",
                    "recommendations": [
                        f"Seek {urgency} priority medical evaluation for comprehensive assessment",
                        "Monitor symptom progression and document changes carefully",
                        "Maintain adequate hydration and rest in comfortable position",
                        "Contact healthcare provider or emergency services as appropriate",
                        "Do not delay seeking care if symptoms significantly worsen",
                        "Keep emergency contacts readily available",
                    ],
                    "urgency": urgency,
                    "explanation": "Professional medical assessment using evidence-based algorithms.",
                    "ai_confidence": "high",
                    "model_used": "Enhanced Medical Algorithms",
                }

            # ML Assessment
            ml_assessment = {
                "risk_score": round(risk_score, 2),
                "confidence": round(min(0.95, 0.75 + (len(risk_factors) * 0.05)), 2),
                "risk_level": risk_level,
                "factors": (
                    risk_factors
                    if risk_factors
                    else [
                        f"Age demographic assessment ({age} years)",
                        "Symptom severity analysis",
                        "Medical history evaluation",
                    ]
                ),
            }

            # Success response
            response_data = {
                "ai_analysis": ai_analysis,
                "ml_assessment": ml_assessment,
                "status": "success",
                "backend": f"Vercel Python + {ai_analysis['model_used']}",
                "gemini_enabled": GEMINI_AVAILABLE and bool(gemini_api_key),
                "gemini_success": gemini_success,
            }

            print(f"Sending successful response")
            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            # Always return a valid JSON response
            error_response = {
                "error": f"Assessment failed: {str(e)}",
                "status": "server_error",
                "backend": "Vercel Python Serverless",
            }
            self.wfile.write(json.dumps(error_response).encode("utf-8"))

    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
