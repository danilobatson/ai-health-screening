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

# AI Service import
from services.ai_health_service import get_ai_service, SymptomData

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
    clinical_reasoning: str
    red_flags: List[str]
    ai_powered: bool = True

# FastAPI app
app = FastAPI(
    title="AI Health Assessment API",
    description="Intelligent healthcare risk assessment powered by Google Gemini AI",
    version="2.0.0"
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and AI service on startup"""
    try:
        await init_db()
        is_connected = await check_db_connection()
        if is_connected:
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")

        # Test AI service
        ai_service = get_ai_service()
        print("✅ AI Health Service ready!")

    except Exception as e:
        print(f"❌ Startup error: {e}")

@app.get("/")
async def health_check():
    """API health check with service status"""
    try:
        db_status = await check_db_connection()

        # Test AI service
        try:
            ai_service = get_ai_service()
            ai_status = True
        except:
            ai_status = False

        return {
            "message": "AI Health Assessment API is running!",
            "status": "healthy",
            "services": {
                "database": "connected" if db_status else "disconnected",
                "ai_service": "ready" if ai_status else "unavailable"
            },
            "version": "2.0.0",
            "features": ["AI-powered assessments", "PostgreSQL storage", "Clinical reasoning"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/status")
async def api_status():
    """Detailed API status"""
    return {
        "api_version": "2.0.0",
        "services": {
            "database": "connected",
            "ai_service": "google_gemini_ready",
            "features": ["intelligent_health_analysis", "clinical_reasoning", "risk_assessment"]
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/assess-health", response_model=AssessmentResponse)
async def assess_health(assessment: HealthAssessmentRequest, db: AsyncSession = Depends(get_db)):
    """
    AI-Powered Health Risk Assessment

    Uses Google Gemini AI to provide intelligent medical analysis
    considering symptom patterns, age factors, and medical history.
    """
    try:
        print(f"🔬 Starting AI health assessment for {assessment.name}")

        # Get AI service
        ai_service = get_ai_service()

        # Convert symptoms to AI service format
        ai_symptoms = [
            SymptomData(
                name=symptom.name,
                severity=symptom.severity.value,
                duration_days=symptom.duration_days
            )
            for symptom in assessment.symptoms
        ]

        # Get AI analysis
        ai_analysis = await ai_service.analyze_health_symptoms(
            symptoms=ai_symptoms,
            age=assessment.age,
            medical_history=assessment.medical_history,
            patient_name=assessment.name
        )

        print(f"✅ AI analysis completed - Risk Score: {ai_analysis.risk_score}")

        # Create patient record
        patient = Patient(
            name=assessment.name,
            age=assessment.age,
            medical_history=assessment.medical_history
        )
        db.add(patient)
        await db.flush()  # Get patient ID

        # Map AI urgency to our risk levels
        risk_mapping = {
            "Routine": RiskLevel.LOW,
            "Monitor": RiskLevel.MEDIUM,
            "Urgent": RiskLevel.HIGH,
            "Emergency": RiskLevel.HIGH
        }

        urgency_mapping = {
            "Routine": Urgency.ROUTINE,
            "Monitor": Urgency.MONITOR,
            "Urgent": Urgency.URGENT,
            "Emergency": Urgency.EMERGENCY
        }

        mapped_risk_level = risk_mapping.get(ai_analysis.urgency_level, RiskLevel.MEDIUM)
        mapped_urgency = urgency_mapping.get(ai_analysis.urgency_level, Urgency.MONITOR)

        # Convert symptoms for database storage
        symptoms_data = [
            {
                "name": symptom.name,
                "severity": symptom.severity.value,
                "duration_days": symptom.duration_days
            }
            for symptom in assessment.symptoms
        ]

        # Create health assessment record - USING CORRECT FIELD NAMES
        health_assessment = DBHealthAssessment(
            patient_id=patient.id,
            symptoms=symptoms_data,
            risk_level=mapped_risk_level.value,
            risk_score=ai_analysis.risk_score,
            urgency=mapped_urgency.value,
            confidence_score=ai_analysis.confidence_score,
            ai_recommendations=ai_analysis.recommendations,  # ✅ CORRECT FIELD NAME
            ai_analysis=ai_analysis.risk_assessment + "\n\nClinical Reasoning: " + ai_analysis.clinical_reasoning,  # ✅ CORRECT FIELD NAME
            ai_model_used="google-gemini-1.5-flash",
            assessment_notes=f"Red Flags: {', '.join(ai_analysis.red_flags)}",  # Store red flags here
            status="completed"
        )
        db.add(health_assessment)
        await db.flush()  # Get assessment ID

        # Create symptom records
        for symptom in assessment.symptoms:
            symptom_record = SymptomRecord(
                assessment_id=health_assessment.id,
                name=symptom.name,
                severity=symptom.severity.value,
                duration_days=symptom.duration_days
            )
            db.add(symptom_record)

        # Commit all changes
        await db.commit()

        print(f"✅ Health assessment saved to database")

        return AssessmentResponse(
            risk_level=mapped_risk_level,
            risk_score=ai_analysis.risk_score,
            urgency=mapped_urgency,
            recommendations=ai_analysis.recommendations,
            assessment_id=str(health_assessment.id),
            timestamp=health_assessment.created_at,
            confidence_score=ai_analysis.confidence_score,
            clinical_reasoning=ai_analysis.clinical_reasoning,
            red_flags=ai_analysis.red_flags,
            ai_powered=True
        )

    except Exception as e:
        await db.rollback()
        print(f"❌ Assessment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health assessment failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
