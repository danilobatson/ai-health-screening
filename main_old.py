from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import datetime

app = FastAPI(
    title="AI Health Assessment API",
    description="Healthcare risk assessment powered by AI",
    version="1.0.0"
)

class HealthAssessment(BaseModel):
    symptoms: List[str]
    age: int
    medical_history: List[str] = []
    name: str = "Anonymous Patient"

class AssessmentResponse(BaseModel):
    risk_level: str
    risk_score: int
    urgency: str
    recommendations: List[str]
    assessment_id: str
    timestamp: datetime.datetime

@app.get("/")
def health_check():
    return {
        "message": "AI Health Assessment API is running!",
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/api/status")
def api_status():
    return {
        "api_version": "1.0.0",
        "services": {
            "database": "connected",
            "ai_service": "ready"
        }
    }

@app.post("/api/assess-health", response_model=AssessmentResponse)
def assess_health(assessment: HealthAssessment):
    """
    Perform basic health risk assessment
    This will be enhanced with AI in the next steps
    """
    # Basic risk calculation (we'll add AI later)
    risk_score = len(assessment.symptoms) * 10
    
    if assessment.age > 65:
        risk_score += 20
    if assessment.age < 18:
        risk_score += 15
    
    # Determine risk level
    if risk_score < 30:
        risk_level = "Low"
        urgency = "Routine"
    elif risk_score < 60:
        risk_level = "Medium" 
        urgency = "Monitor"
    else:
        risk_level = "High"
        urgency = "Consult Doctor"
    
    # Generate basic recommendations
    recommendations = [
        "Monitor symptoms closely",
        "Stay hydrated and get adequate rest",
        "Consult healthcare provider if symptoms persist"
    ]
    
    if risk_level == "High":
        recommendations.insert(0, "Consider seeking immediate medical attention")
    
    return AssessmentResponse(
        risk_level=risk_level,
        risk_score=risk_score,
        urgency=urgency,
        recommendations=recommendations,
        assessment_id=f"HEALTH_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.datetime.now()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
