from typing import Optional
from sqlalchemy.orm import Session

from app.models.emergency_case import TriageLevel
from app.models.ai import (
    AIPrediction,
    AIAlert,
    AIPredictionType,
    AIAlertType,
    AIRiskLevel,
    AIAlertSeverity,
    AIAlertStatus,
    ModelProviderType,
)
from app.ai.base import StandardAIExplanation
from app.ai.triage.rules import TriageRulesEngine
from app.ai.triage.schemas import TriageAIRequest, TriageAIResponse


class TriageAIService:
    @staticmethod
    def assess_case(
        db: Session,
        request: TriageAIRequest,
        case_id: Optional[int] = None,
        user_id: Optional[int] = None,
        persist: bool = True,
    ) -> TriageAIResponse:
        engine = TriageRulesEngine()

        triage_level, risk_level, factors, flags, rec_action, target_mins = engine.evaluate(
            age=request.age,
            symptoms=request.symptoms,
            heart_rate=request.heart_rate,
            bp_systolic=request.bp_systolic,
            bp_diastolic=request.bp_diastolic,
            spo2=request.spo2,
            temperature=request.temperature,
            respiratory_rate=request.respiratory_rate,
            consciousness=request.consciousness,
        )

        color_map = {
            TriageLevel.RED: "#ef4444",
            TriageLevel.ORANGE: "#f97316",
            TriageLevel.YELLOW: "#eab308",
            TriageLevel.GREEN: "#10b981",
        }

        explanation = StandardAIExplanation(
            summary=f"Evaluated as {triage_level.value} Priority (Target Time: {target_mins} mins).",
            reasons=factors,
            contributing_factors=flags,
            recommended_action=rec_action,
        )

        if persist:
            pred_record = AIPrediction(
                prediction_type=AIPredictionType.TRIAGE_ASSESSMENT,
                entity_type="EMERGENCY_CASE",
                entity_id=str(case_id or "NEW_TRIAGE"),
                prediction_value={
                    "triage_level": triage_level.value,
                    "target_mins": target_mins,
                    "factors": factors,
                },
                risk_level=risk_level,
                confidence=None,  # Rule-based decision support: no fake confidence
                model_name="carex-clinical-triage-rules",
                model_version=engine.version,
                model_provider_type=ModelProviderType.RULE_BASED,
                explanation=explanation.dict(),
                recommended_action=rec_action,
                input_features={
                    "age": request.age,
                    "symptoms": request.symptoms,
                    "hr": request.heart_rate,
                    "bp_systolic": request.bp_systolic,
                    "spo2": request.spo2,
                    "consciousness": request.consciousness.value,
                },
            )
            db.add(pred_record)
            db.commit()

        return TriageAIResponse(
            triage_level=triage_level,
            color_hex=color_map.get(triage_level, "#10b981"),
            risk_level=risk_level,
            contributing_factors=factors,
            vital_flags=flags,
            recommended_action=rec_action,
            target_assessment_time_minutes=target_mins,
            model_provider_type=ModelProviderType.RULE_BASED,
            model_version=engine.version,
            explanation=explanation,
        )
