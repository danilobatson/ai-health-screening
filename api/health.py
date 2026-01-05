import json
import os
from http.server import BaseHTTPRequestHandler

# Import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Check Gemini API key status
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Debug information
        debug_info = {
            "env_vars_present": list(os.environ.keys()),
            "gemini_api_key_exists": "GEMINI_API_KEY" in os.environ,
            "gemini_api_key_value_length": len(gemini_api_key) if gemini_api_key else 0,
            "gemini_api_key_starts_with": gemini_api_key[:5] + "..." if gemini_api_key and len(gemini_api_key) > 5 else None
        }

        gemini_status = {
            "gemini_library_available": GEMINI_AVAILABLE,
            "gemini_api_key_configured": bool(gemini_api_key),
            "gemini_api_key_length": len(gemini_api_key) if gemini_api_key else 0,
            "gemini_enabled": GEMINI_AVAILABLE and bool(gemini_api_key)
        }

        response = {
            "status": "healthy",
            "service": "AI Healthcare Backend",
            "platform": "Vercel Serverless",
            "version": "minimal-production",
            "gemini_status": gemini_status
        }

        self.wfile.write(json.dumps(response).encode("utf-8"))
