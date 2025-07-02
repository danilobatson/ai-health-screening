from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import sys

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import your existing services
try:
    from services.ai_health_service import HealthAIService
    from ml_services.health_ml_service import HealthMLService
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback for development
    pass

app = FastAPI()

# Configure CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthAssessmentRequest(BaseModel):
    symptoms: str
    age: int
    gender: str
    medical_history: str
    current_medications: str

@app.post("/")
async def assess_health_endpoint(request: Request):
    try:
        # Parse request body
        body = await request.json()
        
        # Validate required fields
        required_fields = ['symptoms', 'age', 'gender', 'medical_history', 'current_medications']
        for field in required_fields:
            if field not in body:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Initialize services
        ai_service = HealthAIService()
        ml_service = HealthMLService()
        
        # AI Analysis
        ai_analysis = await ai_service.analyze_symptoms(
            symptoms=body['symptoms'],
            age=body['age'],
            gender=body['gender'],
            medical_history=body['medical_history'],
            current_medications=body['current_medications']
        )
        
        # ML Risk Assessment
        ml_assessment = ml_service.assess_risk(
            symptoms=body['symptoms'],
            age=body['age'],
            gender=body['gender']
        )
        
        return {
            "ai_analysis": ai_analysis,
            "ml_assessment": ml_assessment,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error in assess_health: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }

# Vercel requires this handler function
def handler(request, response):
    return app(request, response)
