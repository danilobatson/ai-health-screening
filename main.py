from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import os
from dotenv import load_dotenv

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db, init_db, check_db_connection
from database.models import Patient, HealthAssessment as DBHealthAssessment, SymptomRecord

# Load environment variables
load_dotenv()

# Enums
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

# Pydantic models
class HealthSymptom(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    severity: SymptomSeverity = SymptomSeverity.MILD
    duration_days: Optional[int] = Field(None, ge=0, le=365)

class HealthAssessmentRequest(BaseModel):
    symptoms: List[HealthSymptom] = Field(..., min_items=1, max_items=20)
    age: int = Field(..., ge=0, le=150)
    medical_history: List[str] = Field(default_factory=list, max_items=10)
    name: Optional[str] = Field("Anonymous Patient", max_length=100)
    
    @validator('medical_history')
    def validate_medical_history(cls, v):
        return [item.strip().lower() for item in v if item.strip()]

class AssessmentResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: int = Field(..., ge=0, le=100)
    urgency: Urgency
    recommendations: List[str]
    assessment_id: str
    timestamp: datetime
    confidence_score: float = Field(..., ge=0.0, le=1.0)

# FastAPI app
app = FastAPI(
    title="AI Health Assessment API",
    description="Healthcare risk assessment with PostgreSQL database",
    version="1.0.0"
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await init_db()
        is_connected = await check_db_connection()
        if is_connected:
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

@app.get("/", tags=["Health Check"])
async def health_check():
    """Health check with database status"""
    db_status = await check_db_connection()
    
    return {
        "message": "AI Health Assessment API with PostgreSQL",
        "status": "healthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/status", tags=["System"])
async def api_status():
    """Detailed system status"""
    db_status = await check_db_connection()
    
    return {
        "api_version": "1.0.0",
        "services": {
            "database": "connected" if db_status else "disconnected",
            "ai_service": "ready",
            "health_engine": "active"
        },
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_type": "PostgreSQL (Supabase)"
    }

@app.post("/api/assess-health", response_model=AssessmentResponse, tags=["Assessment"])
async def assess_health(
    assessment: HealthAssessmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform health assessment and save to database
    """
    try:
        # Calculate risk
        severity_weights = {
            SymptomSeverity.MILD: 5,
            SymptomSeverity.MODERATE: 10,
            SymptomSeverity.SEVERE: 20
        }
        
        symptom_risk = sum(
            severity_weights[symptom.severity] for symptom in assessment.symptoms
        )
        
        # Age-based risk
        if assessment.age < 2:
            age_risk = 25
        elif assessment.age < 18:
            age_risk = 10
        elif assessment.age < 65:
            age_risk = 0
        elif assessment.age < 80:
            age_risk = 15
        else:
            age_risk = 25
        
        # Medical history risk
        high_risk_conditions = {
            "diabetes", "heart disease", "hypertension", 
            "cancer", "copd", "kidney disease"
        }
        
        user_conditions = set(assessment.medical_history)
        history_risk = len(user_conditions & high_risk_conditions) * 10
        
        total_risk = min(symptom_risk + age_risk + history_risk, 100)
        
        # Determine risk level
        risk_level, urgency = _calculate_risk_level(total_risk, assessment.symptoms)
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            risk_level, assessment.symptoms, assessment.age, assessment.medical_history
        )
        
        confidence = _calculate_confidence(assessment)
        
        # 🔧 FIXED DATABASE OPERATIONS: Proper flush sequence
        print(f"💾 Creating patient record for: {assessment.name}")
        
        # Step 1: Create patient record
        patient = Patient(
            name=assessment.name,
            age=assessment.age,
            medical_history=assessment.medical_history
        )
        db.add(patient)
        await db.flush()  # Get patient ID
        print(f"✅ Patient created with ID: {patient.id}")
        
        # Step 2: Create health assessment record
        health_assessment = DBHealthAssessment(
            patient_id=patient.id,
            symptoms=[symptom.dict() for symptom in assessment.symptoms],
            risk_level=risk_level.value,
            risk_score=total_risk,
            urgency=urgency.value,
            confidence_score=confidence,
            ai_recommendations=recommendations
        )
        db.add(health_assessment)
        await db.flush()  # 🔧 CRITICAL: Get assessment ID before creating symptom records
        print(f"✅ Health assessment created with ID: {health_assessment.id}")
        
        # Step 3: Create symptom records (now assessment_id exists!)
        for symptom in assessment.symptoms:
            symptom_record = SymptomRecord(
                assessment_id=health_assessment.id,  # ✅ Now this has a value!
                name=symptom.name,
                severity=symptom.severity.value,
                duration_days=symptom.duration_days
            )
            db.add(symptom_record)
            print(f"✅ Symptom record created: {symptom.name}")
        
        # Step 4: Commit all changes
        await db.commit()
        print(f"✅ All data committed to database successfully!")
        
        return AssessmentResponse(
            risk_level=risk_level,
            risk_score=total_risk,
            urgency=urgency,
            recommendations=recommendations,
            assessment_id=health_assessment.id,
            timestamp=datetime.now(),
            confidence_score=confidence
        )
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Database error: {e}")
        raise HTTPException(status_code=400, detail=f"Assessment failed: {str(e)}")

# Helper functions (same as before)
def _calculate_risk_level(risk_score: int, symptoms: List[HealthSymptom]) -> tuple[RiskLevel, Urgency]:
    emergency_symptoms = {"chest pain", "difficulty breathing", "severe headache"}
    symptom_names = {s.name.lower() for s in symptoms}
    
    if emergency_symptoms & symptom_names:
        return RiskLevel.HIGH, Urgency.EMERGENCY
    
    if risk_score < 25:
        return RiskLevel.LOW, Urgency.ROUTINE
    elif risk_score < 60:
        return RiskLevel.MEDIUM, Urgency.MONITOR
    else:
        return RiskLevel.HIGH, Urgency.URGENT

def _generate_recommendations(risk_level, symptoms, age, medical_history) -> List[str]:
    base_recommendations = {
        RiskLevel.LOW: ["Monitor symptoms closely", "Stay hydrated", "Rest as needed"],
        RiskLevel.MEDIUM: ["Schedule healthcare provider appointment", "Monitor for 24-48 hours"],
        RiskLevel.HIGH: ["Seek medical attention promptly", "Consider urgent care"]
    }
    
    recommendations = base_recommendations[risk_level].copy()
    
    if age >= 65:
        recommendations.append("Given your age, consult your doctor for new symptoms")
    
    return recommendations[:5]

def _calculate_confidence(assessment) -> float:
    score = 0.5
    if len(assessment.symptoms) >= 2:
        score += 0.2
    if any(s.severity != SymptomSeverity.MILD for s in assessment.symptoms):
        score += 0.1
    if assessment.medical_history:
        score += 0.1
    return min(score, 1.0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
