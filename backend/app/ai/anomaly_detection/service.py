from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.opd_token import OpdToken, TokenStatus
from app.models.emergency_case import EmergencyCase, EmergencyCaseStatus, TriageLevel
from app.models.bed import Bed, BedStatus
from app.models.pharmacy import Medicine, MedicineBatch, PharmacyTransaction, PharmacyTransactionType
from app.models.lab import LabOrder, LabOrderStatus
from app.models.ai import (
    AIAlert,
    AIPrediction,
    AIAlertType,
    AIAlertSeverity,
    AIAlertStatus,
    AIPredictionType,
    AIRiskLevel,
    ModelProviderType,
)
from app.ai.anomaly_detection.model import OperationalAnomalyModel
from app.ai.anomaly_detection.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    OperationalAnomalyItem,
)


class AnomalyDetectionService:
    @staticmethod
    def detect_anomalies(
        db: Session,
        request: AnomalyDetectionRequest,
        persist: bool = True,
    ) -> AnomalyDetectionResponse:
        model = OperationalAnomalyModel()
        items: List[OperationalAnomalyItem] = []

        # 1. OPD Queue Volume Anomaly
        waiting_tokens = db.query(OpdToken).filter(OpdToken.status.in_([TokenStatus.ISSUED, TokenStatus.CALLED])).count()
        is_anom, dev, sev, reason, action = model.evaluate_metric(
            domain="OPD",
            title="OPD Queue Arrival Volume",
            current_val=float(waiting_tokens),
            expected_val=6.0,  # Expected nominal queue
            unit="patients waiting",
            warning_threshold_pct=50.0,
            critical_threshold_pct=100.0,
            action_if_high="Reallocate floating clinical staff to busy OPD consultation chambers.",
        )
        items.append(
            OperationalAnomalyItem(
                anomaly_key="OPD_QUEUE_SURGE",
                title="OPD Queue Arrival Volume",
                domain="OPD",
                severity=sev,
                current_value=float(waiting_tokens),
                expected_value=6.0,
                unit="patients waiting",
                percentage_deviation=dev,
                is_anomaly=is_anom,
                explanation_reason=reason,
                recommended_action=action,
            )
        )

        # 2. Emergency Room Arrival Anomaly
        since_24h = datetime.utcnow() - timedelta(hours=24)
        active_er = db.query(EmergencyCase).filter(
            EmergencyCase.created_at >= since_24h,
            EmergencyCase.status.in_([EmergencyCaseStatus.ACTIVE, EmergencyCaseStatus.TRIAGED]),
        ).count()
        is_anom, dev, sev, reason, action = model.evaluate_metric(
            domain="EMERGENCY",
            title="Emergency Department Active Caseload",
            current_val=float(active_er),
            expected_val=4.0,
            unit="active trauma cases",
            warning_threshold_pct=50.0,
            critical_threshold_pct=100.0,
            action_if_high="Activate ED Surge Level II: Prepare trauma resuscitation bays and alert on-call surgical team.",
        )
        items.append(
            OperationalAnomalyItem(
                anomaly_key="EMERGENCY_SURGE",
                title="Emergency Department Active Caseload",
                domain="EMERGENCY",
                severity=sev,
                current_value=float(active_er),
                expected_value=4.0,
                unit="active trauma cases",
                percentage_deviation=dev,
                is_anomaly=is_anom,
                explanation_reason=reason,
                recommended_action=action,
            )
        )

        # 3. Critical Care Bed Saturation
        total_beds = db.query(Bed).count()
        occupied_beds = db.query(Bed).filter(Bed.status == BedStatus.OCCUPIED).count()
        occ_pct = (occupied_beds / max(total_beds, 1)) * 100.0
        is_anom, dev, sev, reason, action = model.evaluate_metric(
            domain="BEDS",
            title="Hospital Inpatient Bed Occupancy",
            current_val=occ_pct,
            expected_val=75.0,
            unit="% occupied",
            warning_threshold_pct=15.0,  # ~86%
            critical_threshold_pct=25.0,  # ~94%
            action_if_high="Initiate hospital discharge lounge transfers and expedite step-down ward bed turnover.",
        )
        items.append(
            OperationalAnomalyItem(
                anomaly_key="BED_OCCUPANCY_SPIKE",
                title="Hospital Inpatient Bed Occupancy",
                domain="BEDS",
                severity=sev,
                current_value=round(occ_pct, 1),
                expected_value=75.0,
                unit="%",
                percentage_deviation=dev,
                is_anomaly=is_anom,
                explanation_reason=reason,
                recommended_action=action,
            )
        )

        # 4. Laboratory Diagnostic Backlog
        pending_labs = db.query(LabOrder).filter(
            LabOrder.status.in_([LabOrderStatus.PENDING, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_PROGRESS])
        ).count()
        is_anom, dev, sev, reason, action = model.evaluate_metric(
            domain="LABORATORY",
            title="Central Laboratory Worklist Backlog",
            current_val=float(pending_labs),
            expected_val=15.0,
            unit="pending orders",
            warning_threshold_pct=60.0,
            critical_threshold_pct=120.0,
            action_if_high="Prioritize STAT/trauma orders on secondary automated hematology analyzers.",
        )
        items.append(
            OperationalAnomalyItem(
                anomaly_key="LAB_BACKLOG_SURGE",
                title="Central Laboratory Worklist Backlog",
                domain="LABORATORY",
                severity=sev,
                current_value=float(pending_labs),
                expected_value=15.0,
                unit="pending orders",
                percentage_deviation=dev,
                is_anomaly=is_anom,
                explanation_reason=reason,
                recommended_action=action,
            )
        )

        # 5. Pharmacy Inventory Depletion Outlier
        critical_stock_meds = db.query(Medicine).join(MedicineBatch).group_by(Medicine.id).having(
            func.sum(MedicineBatch.quantity) <= Medicine.reorder_level
        ).count()
        is_anom, dev, sev, reason, action = model.evaluate_metric(
            domain="PHARMACY",
            title="Low-Stock Pharmaceutical Outliers",
            current_val=float(critical_stock_meds),
            expected_val=3.0,
            unit="SKUs below threshold",
            warning_threshold_pct=50.0,
            critical_threshold_pct=100.0,
            action_if_high="Approve automated batch purchase requisition for formulary restock.",
        )
        items.append(
            OperationalAnomalyItem(
                anomaly_key="PHARMACY_STOCK_DEPLETION",
                title="Low-Stock Pharmaceutical Outliers",
                domain="PHARMACY",
                severity=sev,
                current_value=float(critical_stock_meds),
                expected_value=3.0,
                unit="critical SKUs",
                percentage_deviation=dev,
                is_anomaly=is_anom,
                explanation_reason=reason,
                recommended_action=action,
            )
        )

        # Filter domain if requested
        if request.domain and request.domain != "ALL":
            items = [itm for itm in items if itm.domain.upper() == request.domain.upper()]

        anomalies_detected = [itm for itm in items if itm.is_anomaly]
        critical_count = len([itm for itm in anomalies_detected if itm.severity == AIAlertSeverity.CRITICAL])
        high_count = len([itm for itm in anomalies_detected if itm.severity == AIAlertSeverity.HIGH])

        status_str = "CRITICAL_SURGE" if critical_count > 0 else ("ELEVATED_LOAD" if high_count > 0 else "NORMAL")

        # Persist alert if any critical anomalies found
        if persist and critical_count > 0:
            for anom in anomalies_detected:
                if anom.severity == AIAlertSeverity.CRITICAL:
                    # Check if active alert already exists
                    existing = db.query(AIAlert).filter(
                        AIAlert.title.contains(anom.title),
                        AIAlert.status == AIAlertStatus.ACTIVE,
                    ).first()
                    if not existing:
                        alert = AIAlert(
                            alert_type=AIAlertType.OPERATIONAL_ANOMALY,
                            severity=AIAlertSeverity.CRITICAL,
                            title=f"Operational Anomaly Detected: {anom.title}",
                            description=anom.explanation_reason,
                            reason=[anom.explanation_reason],
                            recommended_action=anom.recommended_action,
                            related_entity=anom.domain,
                            related_entity_id=anom.anomaly_key,
                            status=AIAlertStatus.ACTIVE,
                        )
                        db.add(alert)
            db.commit()

        return AnomalyDetectionResponse(
            total_metrics_evaluated=len(items),
            anomalies_detected_count=len(anomalies_detected),
            critical_anomalies_count=critical_count,
            high_anomalies_count=high_count,
            anomalies=items,
            overall_system_status=status_str,
            model_provider_type=ModelProviderType.STATISTICAL_MODEL,
            model_version=model.version,
        )
