from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

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


class AISimulationService:
    """Non-destructive controlled simulation scenarios for clinical & administrative AI demonstrations."""
    
    @staticmethod
    def trigger_scenario(db: Session, scenario_type: str) -> Dict[str, Any]:
        """
        Triggers:
        - OPD_DELAY
        - ICU_CAPACITY
        - PHARMACY_DEPLETION
        - EMERGENCY_SURGE
        """
        stype = scenario_type.upper()
        now = datetime.utcnow()

        if stype == "OPD_DELAY":
            alert = AIAlert(
                alert_type=AIAlertType.OPD_DELAY,
                severity=AIAlertSeverity.HIGH,
                title="Simulated OPD Queue Delay: Cardiology Clinic",
                description="Consultation duration is running +65% above baseline (24.8 mins vs 15.0 mins). Projected waiting time: 48 mins for 14 waiting patients.",
                reason=[
                    "Average consultation duration elongated due to complex post-PCI patient reviews.",
                    "12 patients waiting in queue exceeding single-physician throughput ceiling.",
                    "Predicted delay of +26 minutes against standard appointment schedule.",
                ],
                recommended_action="Notify Outpatient Clinic Coordinator. Open secondary consultation chamber with Dr. Emily Watson.",
                related_entity="OPD_DEPARTMENT",
                related_entity_id="CARDIOLOGY",
                status=AIAlertStatus.ACTIVE,
            )
            db.add(alert)
            db.commit()
            return {
                "scenario": "OPD_DELAY",
                "title": "Cardiology OPD Queue Delay Activated",
                "risk_level": "HIGH",
                "message": "Simulated queue delay alert posted. Check /admin/ai/queue to view live wait times and explanation.",
            }

        elif stype == "ICU_CAPACITY":
            alert = AIAlert(
                alert_type=AIAlertType.BED_CAPACITY_RISK,
                severity=AIAlertSeverity.CRITICAL,
                title="Simulated High Bed Capacity Risk: Intensive Care Unit (ICU)",
                description="Projected 24-hour ICU occupancy reaches 96.0%. Only 1 ventilator bed remaining under current admission velocity.",
                reason=[
                    "Current ICU occupancy is 92% (11/12 beds occupied).",
                    "3 emergency STEMI and acute trauma cases triaged in Emergency Department awaiting immediate ICU step-in.",
                    "Expected discharge rate: 0 ICU transfers scheduled for next 12 hours.",
                ],
                recommended_action="Initiate ICU Surge Protocol: Expedite transfer of stable telemetry patients to Step-Down Ward and mobilize surge ICU reserve bed.",
                related_entity="BED_WARD",
                related_entity_id="ICU",
                status=AIAlertStatus.ACTIVE,
            )
            db.add(alert)
            db.commit()
            return {
                "scenario": "ICU_CAPACITY",
                "title": "Critical ICU Bed Capacity Alert Activated",
                "risk_level": "CRITICAL",
                "message": "Simulated capacity crisis generated. Check /admin/ai/bed-forecast for 6h/12h/24h projections.",
            }

        elif stype == "PHARMACY_DEPLETION":
            alert = AIAlert(
                alert_type=AIAlertType.PHARMACY_DEPLETION,
                severity=AIAlertSeverity.CRITICAL,
                title="Simulated Critical Stockout: Azithromycin 500mg",
                description="Current inventory is 8 units (reorder level: 30 units). Estimated stockout in 1.4 days at 5.7 units/day consumption rate.",
                reason=[
                    "Prescription dispensing volume surged +80% over past 48 hours.",
                    "Remaining batch inventory (8 units) is below 30% of mandatory safety buffer.",
                    "Suggested automated replenishment: 72 units to achieve target max stock.",
                ],
                recommended_action="Execute automated purchase requisition PO-PHARM-2026-088 for 72 units of Azithromycin 500mg.",
                related_entity="PHARMACY_MEDICINE",
                related_entity_id="MED-AZI-500",
                status=AIAlertStatus.ACTIVE,
            )
            db.add(alert)
            db.commit()
            return {
                "scenario": "PHARMACY_DEPLETION",
                "title": "Critical Stockout Depletion Alert Activated",
                "risk_level": "CRITICAL",
                "message": "Simulated pharmacy depletion generated. Check /admin/ai/pharmacy for consumption velocity charts.",
            }

        elif stype == "EMERGENCY_SURGE":
            alert = AIAlert(
                alert_type=AIAlertType.EMERGENCY_SURGE,
                severity=AIAlertSeverity.CRITICAL,
                title="Simulated Multi-Casualty Emergency Surge: Mass Transit Incident",
                description="Emergency arrival velocity is 8 acute trauma arrivals in 30 mins (+180% above baseline). 3 RED triage cases active.",
                reason=[
                    "Simulated multi-vehicle collision resulting in rapid high-acuity trauma presentations.",
                    "3 Category RED resuscitation cases requiring concurrent emergency physician assessment.",
                    "Trauma Bays 1 & 2 fully engaged. Mobile diagnostic X-ray and blood bank mobilized.",
                ],
                recommended_action="Activate Code Yellow: Emergency Department Surge Level II. Notify on-call trauma surgeons and open reserve Resuscitation Bay 3.",
                related_entity="EMERGENCY_DEPARTMENT",
                related_entity_id="TRAUMA_SURGE",
                status=AIAlertStatus.ACTIVE,
            )
            db.add(alert)
            db.commit()
            return {
                "scenario": "EMERGENCY_SURGE",
                "title": "Emergency Department Code Yellow Surge Activated",
                "risk_level": "CRITICAL",
                "message": "Simulated trauma surge generated. Check /admin/ai/anomalies to view real-time deviation indicators.",
            }

        else:
            return {
                "scenario": "UNKNOWN",
                "title": "Standard AI Calibration",
                "risk_level": "LOW",
                "message": "Nominal operational telemetry running.",
            }
