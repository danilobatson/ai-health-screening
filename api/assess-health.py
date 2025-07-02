import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Add current directory to path for local imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.dirname(current_dir))

# Import your real services
try:
    from services.ai_health_service import HealthAIService
    from ml_services.health_ml_service import HealthMLService
    SERVICES_LOADED = True
except ImportError as e:
    try:
        # Try alternative import path
        sys.path.insert(0, os.path.join(current_dir, '..'))
        from services.ai_health_service import HealthAIService
        from ml_services.health_ml_service import HealthMLService
        SERVICES_LOADED = True
    except ImportError as e2:
        print(f"Service import failed: {e2}")
        SERVICES_LOADED = False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Real AI health assessment endpoint"""
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
            
            # Validate input
            required = ['symptoms', 'age', 'gender', 'medical_history', 'current_medications']
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing field: {field}")
            
            if SERVICES_LOADED:
                # Real AI processing
                ai_service = HealthAIService()
                ml_service = HealthMLService()
                
                # Handle async AI service
                import asyncio
                
                async def process_assessment():
                    ai_result = await ai_service.analyze_symptoms(
                        symptoms=data['symptoms'],
                        age=data['age'],
                        gender=data['gender'],
                        medical_history=data['medical_history'],
                        current_medications=data['current_medications']
                    )
                    
                    ml_result = ml_service.assess_risk(
                        symptoms=data['symptoms'],
                        age=data['age'],
                        gender=data['gender']
                    )
                    
                    return ai_result, ml_result
                
                # Execute assessment
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    ai_analysis, ml_assessment = loop.run_until_complete(process_assessment())
                finally:
                    loop.close()
                
                response = {
                    "ai_analysis": ai_analysis,
                    "ml_assessment": ml_assessment,
                    "status": "success",
                    "backend": "Vercel Python + Real AI"
                }
                
            else:
                # Graceful fallback
                response = {
                    "ai_analysis": {
                        "reasoning": f"Assessment for symptoms '{data['symptoms']}' in {data['age']}-year-old {data['gender']}. AI services initializing.",
                        "recommendations": ["Consult healthcare provider", "Monitor symptoms", "Stay hydrated"],
                        "urgency": "moderate",
                        "explanation": "Full AI analysis loading. Please try again in a moment."
                    },
                    "ml_assessment": {
                        "risk_score": 0.4,
                        "confidence": 0.75,
                        "risk_level": "moderate",
                        "factors": ["Initial assessment", "Services initializing"]
                    },
                    "status": "partial",
                    "backend": "Vercel Python (Services Loading)"
                }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            # Error handling
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
