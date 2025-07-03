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
    version="1.0.0",
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


# Pydantic models - Updated to match frontend data structure
class HealthAssessmentRequest(BaseModel):
    name: str
    age: int
    gender: str
    symptoms: str  # Changed from List[SymptomInput] to string
    medical_history: str = ""  # Changed from List[str] to string
    current_medications: str = ""


class HealthAssessmentResponse(BaseModel):
    # Match production API structure that frontend expects
    ai_analysis: dict
    ml_assessment: dict
    status: str
    backend: str
    gemini_enabled: bool = True
    gemini_success: bool = True


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
            "gemini_api_key": (
                "configured" if os.getenv("GEMINI_API_KEY") else "missing"
            ),
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"Health check warning: {str(e)}",
            "cors_enabled": True,
        }


@app.post("/api/assess-health", response_model=HealthAssessmentResponse)
async def assess_health(request: HealthAssessmentRequest):
    """Perform AI-powered health assessment"""
    try:
        print(f"🏥 Received assessment request for: {request.name}, age {request.age}")
        print(f"📋 Symptoms: {request.symptoms}")
        print(f"👤 Gender: {request.gender}")

        # Validate age
        if request.age < 0 or request.age > 120:
            raise HTTPException(status_code=422, detail="Age must be between 0 and 120")

        # Validate required fields
        if not request.symptoms or not request.symptoms.strip():
            raise HTTPException(status_code=422, detail="Symptoms are required")

        if ai_service is None:
            raise HTTPException(status_code=500, detail="AI service not available")

        # Convert string data to list format for AI service
        medical_history_list = (
            [h.strip() for h in request.medical_history.split(",") if h.strip()]
            if request.medical_history
            else []
        )

        # Get AI assessment with updated parameters
        ai_response = await ai_service.assess_health(
            symptoms=request.symptoms,  # Now expecting string
            age=request.age,
            medical_history=medical_history_list,
        )

        print(
            f"🤖 AI Assessment complete - Risk: {ai_response.get('risk_level', 'Unknown')}"
        )

        # Format response to match production API structure that frontend expects
        formatted_response = {
            "ai_analysis": {
                "reasoning": ai_response.get(
                    "clinical_reasoning", "Assessment completed"
                ),
                "recommendations": ai_response.get(
                    "recommendations", ["Consult healthcare provider"]
                ),
                "urgency": ai_response.get("urgency", "moderate"),
                "explanation": ai_response.get("ml_insights", "AI-powered analysis"),
                "ai_confidence": "high",
                "model_used": ai_response.get("analysis_type", "Local AI Service"),
            },
            "ml_assessment": {
                "risk_score": ai_response.get("risk_score", 50)
                / 100.0,  # Convert to 0-1 scale
                "confidence": ai_response.get("confidence_score", 0.8),
                "risk_level": ai_response.get(
                    "risk_level", "moderate"
                ).lower(),  # Ensure lowercase
                "factors": [
                    "Age assessment",
                    "Symptom analysis",
                    "ML pattern matching",
                ],
            },
            "status": "success",
            "backend": "FastAPI Development Server + AI",
            "gemini_enabled": True,
            "gemini_success": True,
        }

        return HealthAssessmentResponse(**formatted_response)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Assessment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
