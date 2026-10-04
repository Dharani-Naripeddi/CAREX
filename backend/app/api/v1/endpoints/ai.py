from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.role import RoleEnum
from app.models.ai import (
    AIAlert,
    AIPrediction,
    AIFeedback,
    AIAlertStatus,
    AIAlertSeverity,
    AIPredictionType,
)
from app.schemas.ai import (
    OpdQueuePredictionRequest,
    OpdQueuePredictionResponse,
    BedPredictionRequest,
    BedPredictionResponse,
    PharmacyPredictionRequest,
    PharmacyPredictionResponse,
    TriageAIRequest,
    TriageAIResponse,
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
    ShiftHandoverRequest,
    ShiftHandoverResponse,
    HandoverApprovalRequest,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AIAlertOut,
    AIPredictionOut,
    AIFeedbackCreate,
    AIFeedbackOut,
    SimulationTriggerRequest,
)
from app.ai.queue_prediction.service import OpdQueuePredictionService
from app.ai.bed_prediction.service import BedPredictionService
from app.ai.pharmacy_prediction.service import PharmacyPredictionService
from app.ai.triage.service import TriageAIService
from app.ai.document_ai.service import DocumentAIService
from app.ai.voice.service import VoiceAIService
from app.ai.handover.service import ShiftHandoverService
from app.ai.anomaly_detection.service import AnomalyDetectionService
from app.ai.simulation.service import AISimulationService
from app.ai.insights.service import AIInsightsService

router = APIRouter()


# 1. Unified Insights Stream
@router.get("/insights", summary="Get aggregated AI intelligence insights")
def get_insights(
    status: Optional[str] = Query(None, description="Filter by alert status (ACTIVE, ACKNOWLEDGED, RESOLVED)"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, HIGH, CRITICAL)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return AIInsightsService.get_dashboard_insights(
        db=db,
        status=status,
        severity=severity,
        limit=limit,
    )


# 2. OPD Queue Prediction
@router.post("/queue/predict", response_model=OpdQueuePredictionResponse, summary="Predict OPD queue wait time and delay risk")
def predict_queue(
    payload: OpdQueuePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OpdQueuePredictionService.predict_queue(db=db, request=payload, persist=True)


# 3. Bed Occupancy Forecast
@router.post("/beds/predict", response_model=BedPredictionResponse, summary="Forecast 6h/12h/24h ward and ICU bed capacity")
def predict_beds(
    payload: BedPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return BedPredictionService.forecast_beds(db=db, request=payload, persist=True)


# 4. Pharmacy Stock Depletion
@router.post("/pharmacy/predict", response_model=PharmacyPredictionResponse, summary="Predict pharmacy stock runout and reorders")
def predict_pharmacy(
    payload: PharmacyPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return PharmacyPredictionService.forecast_pharmacy(db=db, request=payload, persist=True)


# 5. Emergency Triage AI Decision Support
@router.post("/triage/assess", response_model=TriageAIResponse, summary="Assess emergency case with AI decision support")
def assess_triage(
    payload: TriageAIRequest,
    case_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return TriageAIService.assess_case(
        db=db,
        request=payload,
        case_id=case_id,
        user_id=current_user.id,
        persist=True,
    )


# 6. Medical Document Intelligence
@router.post("/documents/analyze", response_model=DocumentAnalysisResponse, summary="Extract parameters and summary from medical document")
def analyze_document(
    payload: DocumentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return DocumentAIService.analyze_document(
        db=db,
        request=payload,
        uploaded_by_id=current_user.id,
        persist=True,
    )


@router.post("/documents/{document_id}/verify", summary="Sign off and verify extracted document parameters")
def verify_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doc = DocumentAIService.verify_document(db=db, document_id=document_id, verified_by_id=current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found.")
    return {"status": "success", "is_verified": True, "verified_at": doc.verified_at}


# 7. Voice-to-Clinical-Note
@router.post("/voice/transcribe", response_model=VoiceTranscriptionResponse, summary="Structure speech audio transcript into clinical note")
def transcribe_voice(
    payload: VoiceTranscriptionRequest,
    current_user: User = Depends(get_current_active_user),
):
    return VoiceAIService.process_voice_transcript(request=payload)


# 8. AI Shift Handover
@router.post("/handover/generate", response_model=ShiftHandoverResponse, summary="Generate structured AI nursing shift handover")
def generate_shift_handover(
    payload: ShiftHandoverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return ShiftHandoverService.generate_handover(
        db=db,
        request=payload,
        from_nurse_id=current_user.id,
        persist=True,
    )


@router.post("/handover/{handover_id}/approve", summary="Approve and finalize nursing shift handover")
def approve_shift_handover(
    handover_id: int,
    payload: Optional[HandoverApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    record = ShiftHandoverService.approve_handover(
        db=db,
        handover_id=handover_id,
        approved_by_id=current_user.id,
        payload=payload,
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift handover not found.")
    return {"status": "success", "handover_status": record.status, "approved_at": record.approved_at}


# 9. Operational Anomaly Detection
@router.post("/anomalies/detect", response_model=AnomalyDetectionResponse, summary="Detect hospital operational anomalies")
def detect_anomalies(
    payload: AnomalyDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return AnomalyDetectionService.detect_anomalies(db=db, request=payload, persist=True)


# 10. AI Alerts Lifecycle
@router.get("/alerts", response_model=List[AIAlertOut], summary="List AI alerts")
def list_ai_alerts(
    status: Optional[AIAlertStatus] = Query(None),
    severity: Optional[AIAlertSeverity] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(AIAlert)
    if status:
        q = q.filter(AIAlert.status == status)
    if severity:
        q = q.filter(AIAlert.severity == severity)
    return q.order_by(AIAlert.created_at.desc()).limit(limit).all()


@router.post("/alerts/{alert_id}/acknowledge", response_model=AIAlertOut, summary="Acknowledge active AI alert")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = AIInsightsService.acknowledge_alert(db=db, alert_id=alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=AIAlertOut, summary="Resolve active AI alert")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = AIInsightsService.resolve_alert(db=db, alert_id=alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return alert


# 11. Traceable Prediction History
@router.get("/predictions", response_model=List[AIPredictionOut], summary="List historical AI predictions")
def list_predictions(
    prediction_type: Optional[AIPredictionType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(AIPrediction)
    if prediction_type:
        q = q.filter(AIPrediction.prediction_type == prediction_type)
    return q.order_by(AIPrediction.generated_at.desc()).limit(limit).all()


# 12. User Feedback Submission
@router.post("/feedback", response_model=AIFeedbackOut, status_code=status.HTTP_201_CREATED, summary="Submit user feedback on AI output")
def submit_feedback(
    payload: AIFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return AIInsightsService.submit_feedback(
        db=db,
        user_id=current_user.id,
        rating=payload.rating,
        notes=payload.notes,
        prediction_id=payload.prediction_id,
        alert_id=payload.alert_id,
    )


# 13. Controlled Simulation Trigger
@router.post("/simulation/trigger", summary="Trigger controlled simulation scenario")
def trigger_simulation(
    payload: SimulationTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return AISimulationService.trigger_scenario(db=db, scenario_type=payload.scenario_type)
