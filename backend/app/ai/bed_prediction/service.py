from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.admission import Admission, AdmissionStatus
from app.models.ai import (
    AIPrediction,
    AIAlert,
    AIPredictionType,
    AIAlertType,
    AIRiskLevel,
    AIAlertSeverity,
    AIAlertStatus,
)
from app.ai.base import StandardAIExplanation, AIConfidenceHelper
from app.ai.bed_prediction.model import BedCapacityForecastingModel
from app.ai.bed_prediction.schemas import (
    BedPredictionRequest,
    BedPredictionResponse,
    ForecastHorizonPoint,
    WardForecastSummary,
)


class BedPredictionService:
    @staticmethod
    def forecast_beds(
        db: Session,
        request: BedPredictionRequest,
        persist: bool = True,
    ) -> BedPredictionResponse:
        model = BedCapacityForecastingModel()

        # 1. Query Beds
        bed_query = db.query(Bed)
        if request.ward_id:
            bed_query = bed_query.filter(Bed.ward_id == request.ward_id)
        
        all_beds = bed_query.all()
        total_beds = len(all_beds)
        occupied_beds = len([b for b in all_beds if b.status == BedStatus.OCCUPIED])
        available_beds = len([b for b in all_beds if b.status == BedStatus.AVAILABLE])
        current_occ_pct = round((occupied_beds / max(total_beds, 1)) * 100.0, 1)

        # 2. Query Admissions & Discharges
        active_admissions = db.query(Admission).filter(Admission.status == AdmissionStatus.ADMITTED).all()
        admissions_count = len(active_admissions)
        
        # Approximate daily rates
        active_rate = max(4.0, admissions_count * 0.4)
        discharge_rate = max(2.0, admissions_count * 0.25)

        # 3. Model Forecast Horizons
        horizons_raw, overall_risk, provider, reasons = model.forecast_horizons(
            total_beds=total_beds,
            occupied_beds=occupied_beds,
            active_admissions_rate_per_day=active_rate,
            expected_discharges_rate_per_day=discharge_rate,
        )

        horizons = [ForecastHorizonPoint(**h) for h in horizons_raw]

        # 4. Ward Breakdown
        all_wards = db.query(Ward).all()
        ward_breakdown = []
        for w in all_wards:
            w_beds = [b for b in all_beds if b.ward_id == w.id] if not request.ward_id else (all_beds if w.id == request.ward_id else [])
            w_total = len(w_beds)
            if w_total > 0:
                w_occ = len([b for b in w_beds if b.status == BedStatus.OCCUPIED])
                w_avail = len([b for b in w_beds if b.status == BedStatus.AVAILABLE])
                w_pct = round((w_occ / w_total) * 100.0, 1)
                
                # Projected 24h occupancy with ICU/CCU weight
                weight = 1.15 if "ICU" in w.name or "CCU" in w.name or "Emergency" in w.name else 1.05
                proj_24 = min(100.0, round(w_pct * weight, 1))
                w_risk = model.get_risk_level(proj_24)

                ward_breakdown.append(
                    WardForecastSummary(
                        ward_id=w.id,
                        ward_name=w.name,
                        ward_type=w.code or "WARD",
                        total_beds=w_total,
                        occupied_beds=w_occ,
                        available_beds=w_avail,
                        current_occupancy_percent=w_pct,
                        projected_24h_occupancy_percent=proj_24,
                        risk_level=w_risk,
                    )
                )

        ward_name = None
        if request.ward_id:
            w_obj = db.query(Ward).filter(Ward.id == request.ward_id).first()
            if w_obj:
                ward_name = w_obj.name

        # Recommended Action
        if overall_risk in [AIRiskLevel.HIGH, AIRiskLevel.CRITICAL]:
            rec_action = "Initiate Bed Management Protocol: Review discharge-ready patients in step-down wards, hold elective admissions, and mobilize surge capacity beds."
        elif overall_risk == AIRiskLevel.MEDIUM:
            rec_action = "Monitor ward turnover. Coordinate with nursing team to expedite pending discharge summaries."
        else:
            rec_action = "Bed availability is within safe operating margins across all departments."

        p24_pct = horizons[2].projected_occupancy_percent if len(horizons) >= 3 else current_occ_pct
        explanation = StandardAIExplanation(
            summary=f"Projected 24-hour bed capacity risk is {overall_risk.value} (Current: {current_occ_pct:.1f}%, 24h Forecast: {p24_pct:.1f}%).",
            reasons=reasons,
            recommended_action=rec_action,
        )

        confidence = AIConfidenceHelper.calculate_sample_confidence(total_beds, min_samples_for_high=30)
        alert_triggered = False

        # 5. Persist AIPrediction & AIAlert
        if persist:
            pred_record = AIPrediction(
                prediction_type=AIPredictionType.BED_OCCUPANCY,
                entity_type="WARD" if request.ward_id else "HOSPITAL_BEDS",
                entity_id=str(request.ward_id or "ALL"),
                prediction_value={
                    "current_occupancy_percent": current_occ_pct,
                    "projected_6h": horizons[0].projected_occupancy_percent if len(horizons) > 0 else 0,
                    "projected_12h": horizons[1].projected_occupancy_percent if len(horizons) > 1 else 0,
                    "projected_24h": p24_pct,
                    "occupied_beds": occupied_beds,
                    "total_beds": total_beds,
                },
                risk_level=overall_risk,
                confidence=confidence,
                model_name="carex-bed-capacity-engine",
                model_version=model.version,
                model_provider_type=provider,
                explanation=explanation.model_dump(),
                recommended_action=rec_action,
                input_features={
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "active_admissions": admissions_count,
                    "ward_id": request.ward_id,
                },
            )
            db.add(pred_record)

            if overall_risk in [AIRiskLevel.HIGH, AIRiskLevel.CRITICAL]:
                alert_record = AIAlert(
                    alert_type=AIAlertType.BED_CAPACITY_RISK,
                    severity=AIAlertSeverity.HIGH if overall_risk == AIRiskLevel.HIGH else AIAlertSeverity.CRITICAL,
                    title=f"High Bed Capacity Risk ({p24_pct:.0f}% Occupancy Projected) — {ward_name or 'Hospital Wide'}",
                    description=f"Bed occupancy is projected to reach {p24_pct:.1f}% within 24 hours. High admission velocity outpaces expected discharge turnover.",
                    reason=reasons,
                    recommended_action=rec_action,
                    related_entity="BED_MANAGEMENT",
                    related_entity_id=str(request.ward_id or "ALL"),
                    status=AIAlertStatus.ACTIVE,
                )
                db.add(alert_record)
                alert_triggered = True

            db.commit()

        return BedPredictionResponse(
            ward_id=request.ward_id,
            ward_name=ward_name,
            total_beds=total_beds,
            occupied_beds=occupied_beds,
            available_beds=available_beds,
            current_occupancy_percent=current_occ_pct,
            horizons=horizons,
            ward_breakdown=ward_breakdown,
            overall_risk_level=overall_risk,
            confidence=confidence,
            model_provider_type=provider,
            model_version=model.version,
            explanation=explanation,
            recommended_action=rec_action,
            alert_triggered=alert_triggered,
        )
