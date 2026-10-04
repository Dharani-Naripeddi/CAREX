from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.ai import (
    AIAlert,
    AIPrediction,
    AIFeedback,
    AIAlertStatus,
    AIAlertSeverity,
    AIRiskLevel,
    ModelProviderType,
)
from app.ai.queue_prediction.service import OpdQueuePredictionService
from app.ai.queue_prediction.schemas import OpdQueuePredictionRequest
from app.ai.bed_prediction.service import BedPredictionService
from app.ai.bed_prediction.schemas import BedPredictionRequest
from app.ai.pharmacy_prediction.service import PharmacyPredictionService
from app.ai.pharmacy_prediction.schemas import PharmacyPredictionRequest
from app.ai.anomaly_detection.service import AnomalyDetectionService
from app.ai.anomaly_detection.schemas import AnomalyDetectionRequest


class AIInsightsService:
    @staticmethod
    def get_dashboard_insights(
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        # 1. Query Active Alerts
        alert_query = db.query(AIAlert)
        if status:
            alert_query = alert_query.filter(AIAlert.status == status)
        else:
            alert_query = alert_query.filter(AIAlert.status.in_([AIAlertStatus.ACTIVE, AIAlertStatus.ACKNOWLEDGED]))
            
        if severity:
            alert_query = alert_query.filter(AIAlert.severity == severity)
            
        alerts = alert_query.order_by(AIAlert.created_at.desc()).limit(limit).all()

        # 2. Query Recent Predictions
        predictions = (
            db.query(AIPrediction)
            .order_by(AIPrediction.generated_at.desc())
            .limit(limit)
            .all()
        )

        # 3. Live Quick Telemetry for AI Dashboard
        queue_res = OpdQueuePredictionService.predict_queue(db=db, request=OpdQueuePredictionRequest(), persist=False)
        bed_res = BedPredictionService.forecast_beds(db=db, request=BedPredictionRequest(), persist=False)
        pharm_res = PharmacyPredictionService.forecast_pharmacy(db=db, request=PharmacyPredictionRequest(days_history=30), persist=False)
        anom_res = AnomalyDetectionService.detect_anomalies(db=db, request=AnomalyDetectionRequest(), persist=False)

        # 4. Total Counters
        active_alert_count = db.query(AIAlert).filter(AIAlert.status == AIAlertStatus.ACTIVE).count()
        critical_alert_count = db.query(AIAlert).filter(
            AIAlert.status == AIAlertStatus.ACTIVE,
            AIAlert.severity == AIAlertSeverity.CRITICAL,
        ).count()
        total_predictions_count = db.query(AIPrediction).count()

        return {
            "summary": {
                "active_alerts_count": active_alert_count,
                "critical_alerts_count": critical_alert_count,
                "total_predictions_count": total_predictions_count,
                "overall_system_status": anom_res.overall_system_status,
                "evaluated_at": datetime.utcnow().isoformat(),
            },
            "alerts": [
                {
                    "id": a.id,
                    "alert_type": a.alert_type.value,
                    "severity": a.severity.value,
                    "title": a.title,
                    "description": a.description,
                    "reason": a.reason,
                    "recommended_action": a.recommended_action,
                    "related_entity": a.related_entity,
                    "related_entity_id": a.related_entity_id,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat(),
                    "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                }
                for a in alerts
            ],
            "predictions": [
                {
                    "id": p.id,
                    "prediction_type": p.prediction_type.value,
                    "entity_type": p.entity_type,
                    "entity_id": p.entity_id,
                    "prediction_value": p.prediction_value,
                    "risk_level": p.risk_level.value,
                    "confidence": p.confidence,
                    "model_name": p.model_name,
                    "model_version": p.model_version,
                    "model_provider_type": p.model_provider_type.value,
                    "explanation": p.explanation,
                    "recommended_action": p.recommended_action,
                    "generated_at": p.generated_at.isoformat(),
                }
                for p in predictions
            ],
            "quick_status": {
                "opd": {
                    "waiting_count": queue_res.current_waiting_count,
                    "estimated_wait_minutes": queue_res.estimated_wait_minutes,
                    "delay_minutes": queue_res.predicted_delay_minutes,
                    "risk": queue_res.risk_level.value,
                    "model_provider": queue_res.model_provider_type.value,
                },
                "beds": {
                    "occupancy_percent": bed_res.current_occupancy_percent,
                    "projected_24h_percent": bed_res.horizons[2].projected_occupancy_percent if len(bed_res.horizons) > 2 else bed_res.current_occupancy_percent,
                    "risk": bed_res.overall_risk_level.value,
                    "available_beds": bed_res.available_beds,
                    "total_beds": bed_res.total_beds,
                    "model_provider": bed_res.model_provider_type.value,
                },
                "pharmacy": {
                    "critical_count": pharm_res.critical_depletion_count,
                    "high_count": pharm_res.high_depletion_count,
                    "risk": pharm_res.overall_risk_level.value,
                    "total_stock_value": pharm_res.total_stock_value,
                    "model_provider": pharm_res.model_provider_type.value,
                },
                "anomalies": {
                    "anomalies_detected_count": anom_res.anomalies_detected_count,
                    "critical_count": anom_res.critical_anomalies_count,
                    "overall_status": anom_res.overall_system_status,
                },
            },
        }

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> Optional[AIAlert]:
        alert = db.query(AIAlert).filter(AIAlert.id == alert_id).first()
        if alert:
            alert.status = AIAlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by_id = user_id
            db.commit()
            db.refresh(alert)
        return alert

    @staticmethod
    def resolve_alert(db: Session, alert_id: int, user_id: int) -> Optional[AIAlert]:
        alert = db.query(AIAlert).filter(AIAlert.id == alert_id).first()
        if alert:
            alert.status = AIAlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_id = user_id
            db.commit()
            db.refresh(alert)
        return alert

    @staticmethod
    def submit_feedback(
        db: Session,
        user_id: int,
        rating: str,
        notes: Optional[str] = None,
        prediction_id: Optional[int] = None,
        alert_id: Optional[int] = None,
    ) -> AIFeedback:
        fb = AIFeedback(
            user_id=user_id,
            rating=rating,
            notes=notes,
            prediction_id=prediction_id,
            alert_id=alert_id,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb
