from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.ai import AIAlertSeverity, AIRiskLevel, ModelProviderType, AIAlertStatus
from app.ai.brain.schemas import (
    HospitalBrainEvent,
    HospitalBrainEventType,
    HospitalBrainSourceModule,
    HospitalBrainExplanation,
)
from app.ai.brain.priority_scorer import OperationalPriorityScorer


class HospitalBrainCorrelator:
    """Multi-signal correlation engine synthesizing cross-domain telemetry into unified hospital-level intelligence."""

    @classmethod
    def evaluate_correlations(
        cls,
        opd_data: Dict[str, Any],
        bed_data: Dict[str, Any],
        emergency_data: Dict[str, Any],
        pharmacy_data: Dict[str, Any],
        lab_data: Dict[str, Any],
    ) -> List[HospitalBrainEvent]:
        composite_events: List[HospitalBrainEvent] = []

        # Extract telemetry parameters
        er_active = emergency_data.get("active_count", 0)
        er_red = emergency_data.get("red_cases_count", 0)
        er_surge = emergency_data.get("is_surge", False)

        bed_occ_pct = bed_data.get("occupancy_percent", 0.0)
        icu_occ_pct = bed_data.get("icu_occupancy_percent", 0.0)
        avail_beds = bed_data.get("available_beds", 0)

        opd_wait_mins = opd_data.get("estimated_wait_minutes", 0)
        opd_delay_mins = opd_data.get("predicted_delay_minutes", 0)
        opd_waiting_count = opd_data.get("waiting_count", 0)

        pharmacy_critical = pharmacy_data.get("critical_count", 0)
        lab_stat_pending = lab_data.get("stat_pending_count", 0)

        # -------------------------------------------------------------------------
        # Correlation Rule 1: Hospital-Wide Capacity Crisis
        # IF (ER Surge OR ER Active >= 4) AND Bed Occupancy >= 80% AND OPD Delay >= 25m
        # -------------------------------------------------------------------------
        if (er_surge or er_active >= 3) and bed_occ_pct >= 75.0 and (opd_delay_mins >= 20 or opd_wait_mins >= 40):
            severity = AIAlertSeverity.CRITICAL if (bed_occ_pct >= 85.0 or er_red >= 2) else AIAlertSeverity.HIGH
            risk = AIRiskLevel.CRITICAL if severity == AIAlertSeverity.CRITICAL else AIRiskLevel.HIGH

            priority = OperationalPriorityScorer.calculate_score(
                severity=severity,
                risk_level=risk,
                correlated_sources_count=3,
                is_composite=True,
                is_critical_resource=True,
            )

            explanation = HospitalBrainExplanation(
                what_is_happening="Multiple hospital capacity indicators are simultaneously elevated across inpatient beds, emergency arrivals, and outpatient clinics.",
                what_is_expected="Inflow velocity exceeds current discharge rate. Hospital-wide bed capacity and emergency staging are projected to reach critical saturation within 4 to 8 hours.",
                why_flagged=[
                    f"Emergency Department active cases elevated ({er_active} active, {er_red} immediate resuscitation)",
                    f"Hospital inpatient bed occupancy at {bed_occ_pct:.1f}% ({avail_beds} available beds remaining)",
                    f"Outpatient consultation queue delayed by +{opd_delay_mins}m (estimated wait {opd_wait_mins}m)",
                ],
                affected_departments=["Emergency", "Inpatient Wards", "ICU", "Outpatient Clinics"],
                affected_resources=["Inpatient Beds", "Emergency Resuscitation Bays", "Attending Physicians", "Nursing Staff"],
                recommended_operational_review="Convene hospital operations coordination team. Review planned discharge clearances, activate surge bed allocation protocols, and redistribute floating clinical staff.",
                data_sources=["OPD Queue Prediction", "Bed Capacity Forecast", "Emergency Triage Telemetry"],
                model_provider_type=ModelProviderType.STATISTICAL_MODEL,
                model_version="v2.0-brain",
                confidence=0.88,
            )

            composite_events.append(
                HospitalBrainEvent(
                    id=9001,
                    source_module=HospitalBrainSourceModule.SYSTEM,
                    event_type=HospitalBrainEventType.HOSPITAL_CAPACITY_RISK,
                    severity=severity,
                    title="Hospital-Wide Capacity & Patient Flow Saturation Risk",
                    description="Multiple operational signals indicate concurrent inflow surges in ER and OPD while total bed occupancy is critically constrained.",
                    current_value=f"{bed_occ_pct:.1f}% Beds | {er_active} ER | {opd_wait_mins}m OPD",
                    predicted_value="Saturation within 4-8h",
                    unit="composite index",
                    risk_level=risk,
                    priority=priority,
                    explanation=explanation,
                    recommended_action="Execute surge bed activation protocol, expedite patient discharge reviews, and coordinate emergency diversion staging.",
                    related_entity_type="HOSPITAL",
                    related_entity_id="ALL_UNITS",
                    correlated_sources=["OPD_QUEUE", "BED_CAPACITY", "EMERGENCY"],
                    status=AIAlertStatus.ACTIVE,
                    is_composite_correlation=True,
                )
            )

        # -------------------------------------------------------------------------
        # Correlation Rule 2: Critical Care / ICU Inflow Bottleneck
        # IF ICU Occupancy >= 80% AND (ER Red Cases >= 1 OR ER Active >= 3)
        # -------------------------------------------------------------------------
        if icu_occ_pct >= 80.0 and (er_red >= 1 or er_active >= 3):
            severity = AIAlertSeverity.CRITICAL if icu_occ_pct >= 90.0 else AIAlertSeverity.HIGH
            risk = AIRiskLevel.CRITICAL if severity == AIAlertSeverity.CRITICAL else AIRiskLevel.HIGH

            priority = OperationalPriorityScorer.calculate_score(
                severity=severity,
                risk_level=risk,
                correlated_sources_count=2,
                is_composite=True,
                is_critical_resource=True,
            )

            explanation = HospitalBrainExplanation(
                what_is_happening="Critical care capacity is constrained while high-acuity resuscitation patients are actively presenting in the Emergency Department.",
                what_is_expected="Potential shortage of ventilator and ICU beds if incoming acute emergency cases require immediate step-up admission.",
                why_flagged=[
                    f"ICU occupancy rate at {icu_occ_pct:.1f}%",
                    f"Emergency Department has {er_red} Level-1 RED resuscitation case(s) under active stabilization",
                ],
                affected_departments=["ICU", "Emergency", "Critical Care"],
                affected_resources=["ICU Beds", "Ventilators", "Intensivists", "Critical Care Nurses"],
                recommended_operational_review="Assess ICU step-down readiness for stable patients to release monitored beds; place Step-Down and CCU units on high-readiness alert.",
                data_sources=["Bed Capacity Forecast", "Emergency Triage Telemetry"],
                model_provider_type=ModelProviderType.RULE_BASED,
                model_version="v2.0-brain",
                confidence=0.92,
            )

            composite_events.append(
                HospitalBrainEvent(
                    id=9002,
                    source_module=HospitalBrainSourceModule.BED,
                    event_type=HospitalBrainEventType.BED_CAPACITY_RISK,
                    severity=severity,
                    title="Critical Care (ICU) Admission Bottleneck Risk",
                    description="ICU occupancy is elevated while active emergency cases require potential critical care admission.",
                    current_value=f"{icu_occ_pct:.1f}% ICU",
                    predicted_value="0-1 beds remaining",
                    unit="occupancy",
                    risk_level=risk,
                    priority=priority,
                    explanation=explanation,
                    recommended_action="Review ICU step-down transfers immediately and verify backup resuscitation bed availability.",
                    related_entity_type="WARD",
                    related_entity_id="ICU",
                    correlated_sources=["BED_CAPACITY", "EMERGENCY"],
                    status=AIAlertStatus.ACTIVE,
                    is_composite_correlation=True,
                )
            )

        # -------------------------------------------------------------------------
        # Correlation Rule 3: Acute Diagnostic & Clinical Backlog
        # IF Lab STAT pending >= 2 AND (er_active >= 2 OR opd_waiting_count >= 8)
        # -------------------------------------------------------------------------
        if lab_stat_pending >= 2 and (er_active >= 2 or opd_waiting_count >= 8):
            priority = OperationalPriorityScorer.calculate_score(
                severity=AIAlertSeverity.WARNING,
                risk_level=AIRiskLevel.MEDIUM,
                correlated_sources_count=2,
                is_composite=True,
            )

            explanation = HospitalBrainExplanation(
                what_is_happening="Urgent diagnostic laboratory order queue is accumulating during elevated outpatient and emergency inflow.",
                what_is_expected="Diagnostic turnaround time delays may extend patient consultation and disposition times.",
                why_flagged=[
                    f"{lab_stat_pending} STAT/Urgent laboratory investigation orders pending processing",
                    f"Outpatient & Emergency arrival volume actively expanding ({opd_waiting_count} waiting in OPD)",
                ],
                affected_departments=["Laboratory", "Emergency", "OPD"],
                affected_resources=["Lab Technicians", "Automated Analyzers"],
                recommended_operational_review="Prioritize STAT emergency and inpatient biochemistry batches; ensure adequate reagent supplies on high-throughput analyzers.",
                data_sources=["Laboratory Telemetry", "OPD Queue Prediction"],
                model_provider_type=ModelProviderType.STATISTICAL_MODEL,
                model_version="v2.0-brain",
                confidence=0.85,
            )

            composite_events.append(
                HospitalBrainEvent(
                    id=9003,
                    source_module=HospitalBrainSourceModule.LAB,
                    event_type=HospitalBrainEventType.LAB_BACKLOG,
                    severity=AIAlertSeverity.WARNING,
                    title="Urgent Diagnostic Investigation Backlog",
                    description="STAT diagnostic orders pending in laboratory may delay clinical decisions in emergency and OPD.",
                    current_value=f"{lab_stat_pending} STAT orders",
                    predicted_value="+15m turnaround delay",
                    unit="orders",
                    risk_level=AIRiskLevel.MEDIUM,
                    priority=priority,
                    explanation=explanation,
                    recommended_action="Prioritize STAT laboratory test queues and allocate additional technician bandwidth.",
                    related_entity_type="DEPARTMENT",
                    related_entity_id="LAB",
                    correlated_sources=["LAB", "OPD_QUEUE"],
                    status=AIAlertStatus.ACTIVE,
                    is_composite_correlation=True,
                )
            )

        return composite_events
