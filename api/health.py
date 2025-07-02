import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Test service imports
try:
    from services.ai_health_service import HealthAIService
    from ml_services.health_ml_service import HealthMLService
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    IMPORT_ERROR = str(e)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "service": "AI Healthcare Backend",
            "platform": "Vercel Python Serverless",
            "services_available": SERVICES_AVAILABLE,
            "python_path": sys.path[:3],  # Show first 3 path entries
            "current_dir": os.getcwd(),
            "environment": {
                "gemini_key_set": bool(os.getenv('GEMINI_API_KEY')),
                "database_url_set": bool(os.getenv('DATABASE_URL'))
            }
        }
        
        if not SERVICES_AVAILABLE:
            response["import_error"] = IMPORT_ERROR
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
