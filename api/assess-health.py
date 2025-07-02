from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_health_service import HealthAIService
from ml_services.health_ml_service import HealthMLService

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_service = HealthAIService()
ml_service = HealthMLService()

class HealthAssessmentRequest(BaseModel):
    symptoms: str
    age: int
    gender: str
    medical_history: str
    current_medications: str

@app.post("/api/assess-health")
async def assess_health(request: HealthAssessmentRequest):
    try:
        # AI Analysis
        ai_analysis = await ai_service.analyze_symptoms(
            symptoms=request.symptoms,
            age=request.age,
            gender=request.gender,
            medical_history=request.medical_history,
            current_medications=request.current_medications
        )
        
        # ML Risk Assessment
        ml_assessment = ml_service.assess_risk(
            symptoms=request.symptoms,
            age=request.age,
            gender=request.gender
        )
        
        return {
            "ai_analysis": ai_analysis,
            "ml_assessment": ml_assessment,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AI Healthcare API"}

# Export for Vercel
app = app
