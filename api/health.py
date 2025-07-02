import json
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Check environment
        gemini_configured = bool(os.getenv('GEMINI_API_KEY'))
        
        response = {
            "status": "healthy",
            "service": "AI Healthcare Backend",
            "platform": "Vercel Python Serverless",
            "gemini_configured": gemini_configured,
            "version": "simplified-production"
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
