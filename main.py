from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Health Assessment System",
    description="Professional healthcare API with AI-powered risk assessment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI service (we'll do this safely)
ai_service = None
try:
    from services.ai_health_service import AIHealthService
    ai_service = AIHealthService()
    print("✅ AI Service loaded successfully")
except Exception as e:
    print(f"⚠️ AI Service warning: {e}")

# Pydantic models
class SymptomInput(BaseModel):
    name: str
    severity: str  # 'mild', 'moderate', 'severe'
    duration_days: int

class HealthAssessmentRequest(BaseModel):
    name: str
    age: int
    symptoms: List[SymptomInput]
    medical_history: List[str] = []

class HealthAssessmentResponse(BaseModel):
    risk_level: str
    risk_score: int
    urgency: str
    recommendations: List[str]
    confidence_score: float
    clinical_reasoning: str
    red_flags: List[str]
    ai_powered: bool = True

@app.get("/")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check without relying on internal attributes
        ai_status = "healthy" if ai_service is not None else "not_loaded"
        
        return {
            "status": "healthy",
            "message": "AI Health Assessment API is running",
            "ai_service": ai_status,
            "version": "1.0.0",
            "cors_enabled": True,
            "gemini_api_key": "configured" if os.getenv("GEMINI_API_KEY") else "missing"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"Health check warning: {str(e)}",
            "cors_enabled": True
        }

@app.post("/api/assess-health", response_model=HealthAssessmentResponse)
async def assess_health(request: HealthAssessmentRequest):
    """Perform AI-powered health assessment"""
    try:
        print(f"🏥 Received assessment request for: {request.name}, age {request.age}")
        print(f"📋 Symptoms: {[s.name for s in request.symptoms]}")
        
        if ai_service is None:
            raise HTTPException(status_code=500, detail="AI service not available")
        
        # Get AI assessment
        ai_response = await ai_service.assess_health(
            symptoms=request.symptoms,
            age=request.age,
            medical_history=request.medical_history
        )
        
        print(f"🤖 AI Assessment complete - Risk: {ai_response['risk_level']}")
        
        return HealthAssessmentResponse(**ai_response)
        
    except Exception as e:
        print(f"❌ Assessment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
