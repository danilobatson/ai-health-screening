from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum
import uuid

# Modern Python: Use Enums for constants
class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Urgency(str, Enum):
    ROUTINE = "Routine"
    MONITOR = "Monitor"
    URGENT = "Urgent"
    EMERGENCY = "Emergency"

class SymptomSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

# Modern Python: Enhanced Pydantic models with validation
class HealthSymptom(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    severity: SymptomSeverity = SymptomSeverity.MILD
    duration_days: Optional[int] = Field(None, ge=0, le=365)

class HealthAssessment(BaseModel):
    symptoms: List[HealthSymptom] = Field(..., min_items=1, max_items=20)
    age: int = Field(..., ge=0, le=150)
    medical_history: List[str] = Field(default_factory=list, max_items=10)
    name: Optional[str] = Field("Anonymous Patient", max_length=100)

    # Modern Python: Custom validator
    @validator('medical_history')
    def validate_medical_history(cls, v):
        if len(v) > 10:
            raise ValueError('Too many medical history items')
        return [item.strip().lower() for item in v if item.strip()]

class AssessmentResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: int = Field(..., ge=0, le=100)
    urgency: Urgency
    recommendations: List[str]
    assessment_id: str
    timestamp: datetime
    confidence_score: float = Field(..., ge=0.0, le=1.0)

# Modern Python: Type hints and better app configuration
app = FastAPI(
    title="AI Health Assessment API",
    description="Healthcare risk assessment powered by AI and modern Python",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Modern Python: Async endpoints (ready for database calls)
@app.get("/", tags=["Health Check"])
async def health_check():
    """Health check endpoint with modern Python async/await"""
    return {
        "message": "AI Health Assessment API is running!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "python_version": "3.12+",
        "framework": "FastAPI"
    }

@app.get("/api/status", tags=["System"])
async def api_status():
    """System status endpoint"""
    return {
        "api_version": "1.0.0",
        "services": {
            "database": "ready",
            "ai_service": "ready",
            "health_engine": "active"
        },
        "environment": "development"
    }

# Modern Python: Enhanced health assessment with better logic
@app.post("/api/assess-health", response_model=AssessmentResponse, tags=["Assessment"])
async def assess_health(assessment: HealthAssessment):
    """
    Perform comprehensive health risk assessment

    Modern Python implementation with:
    - Enhanced symptom analysis
    - Age-based risk factors
    - Medical history correlation
    - Confidence scoring
    """
    try:
        # Modern Python: Dictionary comprehension for symptom analysis
        severity_weights = {
            SymptomSeverity.MILD: 5,
            SymptomSeverity.MODERATE: 10,
            SymptomSeverity.SEVERE: 20
        }

        # Calculate base risk from symptoms
        symptom_risk = sum(
            severity_weights[symptom.severity] for symptom in assessment.symptoms
        )

        # Age-based risk factors (modern Python: match-case statement)
        age_risk = 0
        match assessment.age:
            case age if age < 2:
                age_risk = 25  # Infants need immediate attention
            case age if 2 <= age < 18:
                age_risk = 10  # Children
            case age if 18 <= age < 65:
                age_risk = 0   # Adults baseline
            case age if 65 <= age < 80:
                age_risk = 15  # Elderly
            case age if age >= 80:
                age_risk = 25  # Very elderly

        # Medical history risk (modern Python: set operations)
        high_risk_conditions = {
            "diabetes", "heart disease", "hypertension",
            "cancer", "copd", "kidney disease"
        }

        user_conditions = set(assessment.medical_history)
        history_risk = len(user_conditions & high_risk_conditions) * 10

        # Calculate total risk score
        total_risk = min(symptom_risk + age_risk + history_risk, 100)

        # Modern Python: Determine risk level using ranges
        risk_level, urgency = _calculate_risk_level(total_risk, assessment.symptoms)

        # Generate smart recommendations
        recommendations = _generate_recommendations(
            risk_level, assessment.symptoms, assessment.age, assessment.medical_history
        )

        # Calculate confidence based on data quality
        confidence = _calculate_confidence(assessment)

        return AssessmentResponse(
            risk_level=risk_level,
            risk_score=total_risk,
            urgency=urgency,
            recommendations=recommendations,
            assessment_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            confidence_score=confidence
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Assessment failed: {str(e)}")

# Modern Python: Private helper functions with type hints
def _calculate_risk_level(risk_score: int, symptoms: List[HealthSymptom]) -> tuple[RiskLevel, Urgency]:
    """Calculate risk level and urgency based on score and symptoms"""

    # Check for emergency symptoms
    emergency_symptoms = {"chest pain", "difficulty breathing", "severe headache", "stroke symptoms"}
    symptom_names = {s.name.lower() for s in symptoms}

    if emergency_symptoms & symptom_names:
        return RiskLevel.HIGH, Urgency.EMERGENCY

    # Standard risk calculation
    if risk_score < 25:
        return RiskLevel.LOW, Urgency.ROUTINE
    elif risk_score < 60:
        return RiskLevel.MEDIUM, Urgency.MONITOR
    else:
        return RiskLevel.HIGH, Urgency.URGENT

def _generate_recommendations(
    risk_level: RiskLevel,
    symptoms: List[HealthSymptom],
    age: int,
    medical_history: List[str]
) -> List[str]:
    """Generate personalized recommendations"""

    recommendations = []

    # Base recommendations by risk level
    base_recommendations = {
        RiskLevel.LOW: [
            "Monitor symptoms for any changes",
            "Maintain good hydration and rest",
            "Continue normal activities unless symptoms worsen"
        ],
        RiskLevel.MEDIUM: [
            "Monitor symptoms closely over the next 24-48 hours",
            "Consider scheduling a routine appointment with your healthcare provider",
            "Avoid strenuous activities until symptoms improve"
        ],
        RiskLevel.HIGH: [
            "Seek medical attention promptly",
            "Do not ignore these symptoms",
            "Consider visiting urgent care or emergency room if symptoms worsen"
        ]
    }

    recommendations.extend(base_recommendations[risk_level])

    # Age-specific recommendations
    if age >= 65:
        recommendations.append("Given your age, consider consulting your doctor for any new symptoms")
    elif age < 18:
        recommendations.append("Ensure a parent/guardian is aware of these symptoms")

    # Medical history considerations
    if medical_history:
        recommendations.append("Inform your healthcare provider about your existing medical conditions")

    return recommendations[:5]  # Limit to 5 recommendations

def _calculate_confidence(assessment: HealthAssessment) -> float:
    """Calculate confidence score based on data completeness"""

    score = 0.5  # Base confidence

    # More symptoms = higher confidence
    if len(assessment.symptoms) >= 2:
        score += 0.2

    # Severity information adds confidence
    if any(s.severity != SymptomSeverity.MILD for s in assessment.symptoms):
        score += 0.1

    # Duration information adds confidence
    if any(s.duration_days is not None for s in assessment.symptoms):
        score += 0.1

    # Medical history adds confidence
    if assessment.medical_history:
        score += 0.1

    return min(score, 1.0)

# Modern Python: Error handling
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=422, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
