from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.ai import (
    AIAlert,
    AIPrediction,
    AIAlertSeverity,
    AIRiskLevel,
    AIAlertStatus,
    ModelProviderType,
)
from app.models.audit_log import AuditLog
from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.admission import Admission, AdmissionStatus
from app.models.emergency_case import EmergencyCase, EmergencyCaseStatus, TriageLevel
from app.models.opd_token import OpdToken, TokenStatus
from app.models.appointment import Appointment
from app.models.lab import LabOrder, LabOrderStatus, LabOrderPriority
from app.models.pharmacy import Medicine, MedicineBatch
from app.models.department import Department
from app.models.doctor_profile import DoctorProfile

from app.ai.brain.schemas import (
    HospitalBrainEvent,
    HospitalBrainEventType,
    HospitalBrainSourceModule,
    HospitalBrainExplanation,
    HospitalBrainOverview,
    HospitalSystemStatus,
    TopKPIsSummary,
    DepartmentStatusSummary,
    HospitalCapacityMatrix,
    HospitalBrainActionItem,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from app.ai.brain.priority_scorer import OperationalPriorityScorer
from app.ai.brain.correlator import HospitalBrainCorrelator
from app.ai.brain.simulation import HospitalBrainSimulationEngine


class HospitalBrainService:
    """Central Hospital Brain Orchestrator combining AI predictions, multi-signal correlation,

    operational priority scoring, and action lifecycle management.
    """

    @classmethod
    def get_overview(cls, db: Session) -> HospitalBrainOverview:
        # 1. Gather live telemetry across hospital domains
        opd_data = cls._get_opd_telemetry(db)
        bed_data = cls._get_bed_telemetry(db)
        emergency_data = cls._get_emergency_telemetry(db)
        pharmacy_data = cls._get_pharmacy_telemetry(db)
        lab_data = cls._get_lab_telemetry(db)

        # 2. Correlate cross-domain signals for composite hospital-level risks
        composite_events = HospitalBrainCorrelator.evaluate_correlations(
            opd_data=opd_data,
            bed_data=bed_data,
            emergency_data=emergency_data,
            pharmacy_data=pharmacy_data,
            lab_data=lab_data,
        )

        # 3. Fetch and normalize individual domain AI alerts from ai_alerts table
        db_alerts = (
            db.query(AIAlert)
            .filter(AIAlert.status.in_([AIAlertStatus.ACTIVE, AIAlertStatus.ACKNOWLEDGED]))
            .order_by(desc(AIAlert.created_at))
            .limit(20)
            .all()
        )

        all_events: List[HospitalBrainEvent] = []
        # Prepend composite events
        all_events.extend(composite_events)

        for alert in db_alerts:
            event = cls._map_alert_to_brain_event(alert)
            all_events.append(event)

        # Sort all events by priority score descending
        all_events.sort(key=lambda e: e.priority.score, reverse=True)

        # 4. Compute Department Intelligence Matrix
        dept_matrix = cls._calculate_department_matrix(
            db, opd_data, bed_data, emergency_data, pharmacy_data, lab_data, all_events
        )

        # 5. Determine Overall Hospital Status
        crit_count = sum(1 for e in all_events if e.severity == AIAlertSeverity.CRITICAL and e.status == AIAlertStatus.ACTIVE)
        high_count = sum(1 for e in all_events if e.severity == AIAlertSeverity.HIGH and e.status == AIAlertStatus.ACTIVE)

        if crit_count > 0 or bed_data["occupancy_percent"] >= 90.0:
            hospital_status = HospitalSystemStatus.CRITICAL
        elif high_count > 0 or bed_data["occupancy_percent"] >= 80.0 or opd_data["estimated_wait_minutes"] >= 45:
            hospital_status = HospitalSystemStatus.HIGH_LOAD
        elif len(all_events) > 0 or bed_data["occupancy_percent"] >= 70.0:
            hospital_status = HospitalSystemStatus.WATCH
        else:
            hospital_status = HospitalSystemStatus.STABLE

        # 6. Extract Top Recommended Actions
        top_actions: List[str] = []
        for e in all_events:
            if e.recommended_action and e.recommended_action not in top_actions:
                top_actions.append(e.recommended_action)
            if len(top_actions) >= 4:
                break

        if not top_actions:
            top_actions = [
                "Maintain standard clinical staffing and workflow cadence across departments.",
                "Conduct routine ward bed turnover and pharmacy stock verification.",
            ]

        # 7. Package Top KPIs
        kpis = TopKPIsSummary(
            hospital_capacity_percent=bed_data["occupancy_percent"],
            hospital_status=hospital_status,
            emergency_load_level="CRITICAL" if emergency_data["red_cases_count"] >= 2 else "HIGH" if emergency_data["active_count"] >= 4 else "NORMAL",
            active_emergency_count=emergency_data["active_count"],
            opd_predicted_wait_minutes=opd_data["estimated_wait_minutes"],
            opd_queue_count=opd_data["waiting_count"],
            available_beds_count=bed_data["available_beds"],
            total_beds_count=bed_data["total_beds"],
            pharmacy_critical_depletion_count=pharmacy_data["critical_count"],
            lab_pending_orders_count=lab_data["pending_count"],
            active_intelligence_count=len(all_events),
            critical_alerts_count=crit_count,
            departments_affected_count=sum(1 for d in dept_matrix if d.status != HospitalSystemStatus.STABLE),
        )

        return HospitalBrainOverview(
            hospital_status=hospital_status,
            evaluated_at=datetime.utcnow(),
            kpis=kpis,
            active_events=all_events,
            department_matrix=dept_matrix,
            top_recommended_actions=top_actions,
            is_simulation_mode=False,
        )

    @classmethod
    def get_events(
        cls,
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[HospitalBrainEvent]:
        overview = cls.get_overview(db)
        events = overview.active_events

        if status:
            events = [e for e in events if e.status.value == status.upper()]
        if severity:
            events = [e for e in events if e.severity.value == severity.upper()]

        return events[:limit]

    @classmethod
    def get_event_by_id(cls, db: Session, event_id: int) -> Optional[HospitalBrainEvent]:
        overview = cls.get_overview(db)
        for e in overview.active_events:
            if e.id == event_id:
                return e

        # Check in DB alerts
        alert = db.query(AIAlert).filter(AIAlert.id == event_id).first()
        if alert:
            return cls._map_alert_to_brain_event(alert)

        return None

    @classmethod
    def acknowledge_event(
        cls,
        db: Session,
        event_id: int,
        user_id: int,
        user_name: str,
    ) -> Optional[HospitalBrainEvent]:
        # If composite event ID
        if event_id >= 9000:
            # Create or update corresponding alert in DB
            alert = db.query(AIAlert).filter(AIAlert.id == event_id).first()
            if not alert:
                alert = AIAlert(
                    id=event_id,
                    alert_type="OPERATIONAL_ANOMALY",
                    severity=AIAlertSeverity.HIGH,
                    title="Composite Hospital Capacity Risk",
                    description="Acknowledged composite operational event",
                    reason=["Multiple indicators acknowledged"],
                    recommended_action="Operational review underway",
                    related_entity="HOSPITAL",
                    status=AIAlertStatus.ACKNOWLEDGED,
                    acknowledged_at=datetime.utcnow(),
                    acknowledged_by_id=user_id,
                )
                db.add(alert)
            else:
                alert.status = AIAlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by_id = user_id
        else:
            alert = db.query(AIAlert).filter(AIAlert.id == event_id).first()
            if alert:
                alert.status = AIAlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by_id = user_id

        # Record in AuditLog
        audit = AuditLog(
            user_id=user_id,
            action="HOSPITAL_BRAIN_ACKNOWLEDGE",
            entity="HOSPITAL_BRAIN_EVENT",
            entity_id=str(event_id),
            details={"acknowledged_by": user_name, "timestamp": datetime.utcnow().isoformat()},
        )
        db.add(audit)
        db.commit()

        return cls.get_event_by_id(db, event_id)

    @classmethod
    def resolve_event(
        cls,
        db: Session,
        event_id: int,
        user_id: int,
        user_name: str,
    ) -> Optional[HospitalBrainEvent]:
        alert = db.query(AIAlert).filter(AIAlert.id == event_id).first()
        if alert:
            alert.status = AIAlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_id = user_id

        # Record in AuditLog
        audit = AuditLog(
            user_id=user_id,
            action="HOSPITAL_BRAIN_RESOLVE",
            entity="HOSPITAL_BRAIN_EVENT",
            entity_id=str(event_id),
            details={"resolved_by": user_name, "timestamp": datetime.utcnow().isoformat()},
        )
        db.add(audit)
        db.commit()

        return cls.get_event_by_id(db, event_id)

    @classmethod
    def get_departments_intelligence(cls, db: Session) -> List[DepartmentStatusSummary]:
        overview = cls.get_overview(db)
        return overview.department_matrix

    @classmethod
    def get_capacity_matrix(cls, db: Session) -> HospitalCapacityMatrix:
        bed_data = cls._get_bed_telemetry(db)
        opd_data = cls._get_opd_telemetry(db)

        wards_db = db.query(Ward).options(joinedload(Ward.beds)).all()
        wards_list: List[Dict[str, Any]] = []

        for w in wards_db:
            total = len(w.beds)
            occupied = sum(1 for b in w.beds if b.status == BedStatus.OCCUPIED)
            avail = sum(1 for b in w.beds if b.status == BedStatus.AVAILABLE)
            pct = (occupied / total * 100) if total > 0 else 0.0
            wards_list.append(
                {
                    "id": w.id,
                    "name": w.name,
                    "code": w.code,
                    "floor": w.floor,
                    "wing": w.wing,
                    "total_beds": total,
                    "occupied_beds": occupied,
                    "available_beds": avail,
                    "occupancy_percent": round(pct, 1),
                }
            )

        return HospitalCapacityMatrix(
            total_beds=bed_data["total_beds"],
            occupied_beds=bed_data["occupied_beds"],
            available_beds=bed_data["available_beds"],
            current_occupancy_percent=bed_data["occupancy_percent"],
            projected_24h_occupancy_percent=min(100.0, round(bed_data["occupancy_percent"] * 1.05, 1)),
            icu_total=bed_data["icu_total"],
            icu_occupied=bed_data["icu_occupied"],
            icu_available=bed_data["icu_available"],
            icu_occupancy_percent=bed_data["icu_occupancy_percent"],
            wards=wards_list,
            queue_wait_summary={
                "estimated_wait_minutes": opd_data["estimated_wait_minutes"],
                "waiting_count": opd_data["waiting_count"],
                "delay_minutes": opd_data["predicted_delay_minutes"],
            },
        )

    @classmethod
    def get_action_center(cls, db: Session) -> List[HospitalBrainActionItem]:
        overview = cls.get_overview(db)
        actions: List[HospitalBrainActionItem] = []

        for event in overview.active_events:
            if event.recommended_action:
                resp_dept = event.explanation.affected_departments[0] if event.explanation.affected_departments else "Hospital Operations"
                actions.append(
                    HospitalBrainActionItem(
                        id=event.id,
                        event_id=event.id,
                        title=event.title,
                        recommended_action=event.recommended_action,
                        severity=event.severity,
                        responsible_department=resp_dept,
                        status=event.status,
                        created_at=event.timestamp,
                    )
                )

        return actions

    @classmethod
    def run_simulation(
        cls,
        db: Session,
        req: WhatIfSimulationRequest,
        user_id: int,
        user_name: str,
    ) -> WhatIfSimulationResponse:
        bed_data = cls._get_bed_telemetry(db)
        opd_data = cls._get_opd_telemetry(db)
        emergency_data = cls._get_emergency_telemetry(db)

        baseline = {
            "bed_occupancy_percent": bed_data["occupancy_percent"],
            "icu_occupancy_percent": bed_data["icu_occupancy_percent"],
            "opd_wait_minutes": float(opd_data["estimated_wait_minutes"]),
            "active_emergency_count": float(emergency_data["active_count"]),
        }

        res = HospitalBrainSimulationEngine.execute_simulation(req, baseline)

        # Audit log simulation
        audit = AuditLog(
            user_id=user_id,
            action="HOSPITAL_BRAIN_SIMULATION",
            entity="WHAT_IF_SCENARIO",
            entity_id="SIMULATION",
            details={
                "parameters": req.model_dump(),
                "projected_status": res.projected_hospital_status.value,
                "executed_by": user_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        db.add(audit)
        db.commit()

        return res

    # -------------------------------------------------------------------------
    # Internal Telemetry Ingestion Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _get_opd_telemetry(cls, db: Session) -> Dict[str, Any]:
        today = datetime.utcnow().date()
        waiting_count = db.query(OpdToken).filter(OpdToken.status == TokenStatus.ISSUED).count()
        in_consultation_count = db.query(OpdToken).filter(OpdToken.status.in_([TokenStatus.CALLED, TokenStatus.IN_ROOM])).count()

        # Simple baseline model estimation
        est_wait = max(10, waiting_count * 8)
        baseline_sla = 20
        delay = max(0, est_wait - baseline_sla)

        return {
            "waiting_count": waiting_count,
            "in_consultation_count": in_consultation_count,
            "estimated_wait_minutes": est_wait,
            "historical_baseline_minutes": baseline_sla,
            "predicted_delay_minutes": delay,
        }

    @classmethod
    def _get_bed_telemetry(cls, db: Session) -> Dict[str, Any]:
        total_beds = db.query(Bed).count() or 42
        occupied = db.query(Bed).filter(Bed.status == BedStatus.OCCUPIED).count()
        available = db.query(Bed).filter(Bed.status == BedStatus.AVAILABLE).count()
        occ_pct = (occupied / total_beds * 100) if total_beds > 0 else 0.0

        icu_ward = db.query(Ward).filter(Ward.code == "ICU").first()
        icu_total = db.query(Bed).filter(Bed.ward_id == icu_ward.id).count() if icu_ward else 6
        icu_occ = db.query(Bed).filter(Bed.ward_id == icu_ward.id, Bed.status == BedStatus.OCCUPIED).count() if icu_ward else 4
        icu_avail = icu_total - icu_occ
        icu_occ_pct = (icu_occ / icu_total * 100) if icu_total > 0 else 0.0

        return {
            "total_beds": total_beds,
            "occupied_beds": occupied,
            "available_beds": available,
            "occupancy_percent": round(occ_pct, 1),
            "icu_total": icu_total,
            "icu_occupied": icu_occ,
            "icu_available": icu_avail,
            "icu_occupancy_percent": round(icu_occ_pct, 1),
        }

    @classmethod
    def _get_emergency_telemetry(cls, db: Session) -> Dict[str, Any]:
        since_24h = datetime.utcnow() - timedelta(hours=24)
        active_cases = (
            db.query(EmergencyCase)
            .filter(
                EmergencyCase.created_at >= since_24h,
                EmergencyCase.status.in_([EmergencyCaseStatus.ACTIVE, EmergencyCaseStatus.TRIAGED]),
            )
            .all()
        )

        red_count = sum(1 for c in active_cases if c.triage_level == TriageLevel.RED)
        orange_count = sum(1 for c in active_cases if c.triage_level == TriageLevel.ORANGE)

        return {
            "active_count": len(active_cases),
            "red_cases_count": red_count,
            "orange_cases_count": orange_count,
            "is_surge": len(active_cases) >= 5 or red_count >= 2,
        }

    @classmethod
    def _get_pharmacy_telemetry(cls, db: Session) -> Dict[str, Any]:
        today = datetime.utcnow().date()
        meds = db.query(Medicine).options(joinedload(Medicine.batches)).filter(Medicine.is_active == True).all()

        crit_count = 0
        high_count = 0

        for m in meds:
            stk = sum(b.quantity for b in m.batches if b.is_active and b.expiry_date >= today)
            if stk <= m.reorder_level * 0.5:
                crit_count += 1
            elif stk <= m.reorder_level:
                high_count += 1

        return {
            "total_medicines": len(meds),
            "critical_count": crit_count,
            "high_count": high_count,
        }

    @classmethod
    def _get_lab_telemetry(cls, db: Session) -> Dict[str, Any]:
        pending = (
            db.query(LabOrder)
            .filter(
                LabOrder.status.in_(
                    [LabOrderStatus.PENDING, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_PROGRESS]
                )
            )
            .all()
        )

        stat_count = sum(1 for o in pending if o.priority in [LabOrderPriority.STAT, LabOrderPriority.URGENT])

        return {
            "pending_count": len(pending),
            "stat_pending_count": stat_count,
        }

    @classmethod
    def _map_alert_to_brain_event(cls, alert: AIAlert) -> HospitalBrainEvent:
        # Determine source module
        rel = (alert.related_entity or "").upper()
        if "OPD" in rel:
            source = HospitalBrainSourceModule.OPD
            etype = HospitalBrainEventType.OPD_DELAY
            depts = ["Outpatient Clinics"]
        elif "BED" in rel or "ICU" in rel or "WARD" in rel:
            source = HospitalBrainSourceModule.BED
            etype = HospitalBrainEventType.BED_CAPACITY_RISK
            depts = ["Inpatient Wards", "ICU"]
        elif "PHARMACY" in rel or "MEDICINE" in rel:
            source = HospitalBrainSourceModule.PHARMACY
            etype = HospitalBrainEventType.PHARMACY_DEPLETION
            depts = ["Pharmacy"]
        elif "EMERGENCY" in rel or "TRIAGE" in rel:
            source = HospitalBrainSourceModule.EMERGENCY
            etype = HospitalBrainEventType.EMERGENCY_SURGE
            depts = ["Emergency Department"]
        elif "LAB" in rel:
            source = HospitalBrainSourceModule.LAB
            etype = HospitalBrainEventType.LAB_BACKLOG
            depts = ["Laboratory Diagnostics"]
        else:
            source = HospitalBrainSourceModule.AI_ENGINE
            etype = HospitalBrainEventType.OPERATIONAL_ANOMALY
            depts = ["Hospital Operations"]

        reasons = alert.reason if isinstance(alert.reason, list) else [str(alert.reason)]
        risk = AIRiskLevel.CRITICAL if alert.severity == AIAlertSeverity.CRITICAL else AIRiskLevel.HIGH if alert.severity == AIAlertSeverity.HIGH else AIRiskLevel.MEDIUM

        priority = OperationalPriorityScorer.calculate_score(
            severity=alert.severity,
            risk_level=risk,
            correlated_sources_count=1,
            is_composite=False,
            hours_active=max(0.5, (datetime.utcnow() - alert.created_at).total_seconds() / 3600.0),
        )

        explanation = HospitalBrainExplanation(
            what_is_happening=alert.title,
            what_is_expected=alert.description,
            why_flagged=reasons,
            affected_departments=depts,
            affected_resources=[rel],
            recommended_operational_review=alert.recommended_action,
            data_sources=[f"{source.value} Prediction Engine"],
            model_provider_type=ModelProviderType.STATISTICAL_MODEL,
            model_version="v2.0-brain",
            confidence=0.85,
        )

        return HospitalBrainEvent(
            id=alert.id,
            source_module=source,
            event_type=etype,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            current_value=None,
            predicted_value=None,
            unit=None,
            risk_level=risk,
            priority=priority,
            explanation=explanation,
            recommended_action=alert.recommended_action,
            related_entity_type=alert.related_entity,
            related_entity_id=alert.related_entity_id,
            correlated_sources=[source.value],
            timestamp=alert.created_at,
            status=alert.status,
            is_composite_correlation=False,
        )

    @classmethod
    def _calculate_department_matrix(
        cls,
        db: Session,
        opd_data: Dict[str, Any],
        bed_data: Dict[str, Any],
        emergency_data: Dict[str, Any],
        pharmacy_data: Dict[str, Any],
        lab_data: Dict[str, Any],
        all_events: List[HospitalBrainEvent],
    ) -> List[DepartmentStatusSummary]:
        matrix: List[DepartmentStatusSummary] = []

        # 1. Emergency Department
        er_events = [e for e in all_events if "Emergency" in e.explanation.affected_departments]
        er_status = HospitalSystemStatus.CRITICAL if emergency_data["red_cases_count"] >= 2 else HospitalSystemStatus.HIGH_LOAD if emergency_data["active_count"] >= 4 else HospitalSystemStatus.WATCH if emergency_data["active_count"] >= 2 else HospitalSystemStatus.STABLE
        matrix.append(
            DepartmentStatusSummary(
                department_id=1,
                department_name="Emergency Department",
                department_code="EMR",
                status=er_status,
                load_level="CRITICAL" if er_status == HospitalSystemStatus.CRITICAL else "HIGH" if er_status == HospitalSystemStatus.HIGH_LOAD else "MODERATE",
                active_events_count=len(er_events),
                key_metrics={
                    "active_cases": emergency_data["active_count"],
                    "resuscitation_red": emergency_data["red_cases_count"],
                    "urgent_orange": emergency_data["orange_cases_count"],
                },
                recommended_reviews=[
                    "Monitor resuscitation bay availability.",
                    "Verify fast-track trauma triage protocol.",
                ],
            )
        )

        # 2. Intensive Care Unit (ICU)
        icu_events = [e for e in all_events if "ICU" in e.explanation.affected_departments]
        icu_status = HospitalSystemStatus.CRITICAL if bed_data["icu_occupancy_percent"] >= 90.0 else HospitalSystemStatus.HIGH_LOAD if bed_data["icu_occupancy_percent"] >= 80.0 else HospitalSystemStatus.WATCH if bed_data["icu_occupancy_percent"] >= 70.0 else HospitalSystemStatus.STABLE
        matrix.append(
            DepartmentStatusSummary(
                department_id=2,
                department_name="Intensive Care Unit (ICU)",
                department_code="ICU",
                status=icu_status,
                load_level=f"{bed_data['icu_occupancy_percent']}% Occupied",
                active_events_count=len(icu_events),
                key_metrics={
                    "total_beds": bed_data["icu_total"],
                    "occupied_beds": bed_data["icu_occupied"],
                    "available_beds": bed_data["icu_available"],
                    "occupancy_rate": f"{bed_data['icu_occupancy_percent']}%",
                },
                recommended_reviews=[
                    "Assess candidates for step-down transfer.",
                    "Verify backup ventilator equipment.",
                ],
            )
        )

        # 3. Inpatient Wards (IPD)
        ward_events = [e for e in all_events if "Inpatient Wards" in e.explanation.affected_departments]
        ward_status = HospitalSystemStatus.CRITICAL if bed_data["occupancy_percent"] >= 90.0 else HospitalSystemStatus.HIGH_LOAD if bed_data["occupancy_percent"] >= 80.0 else HospitalSystemStatus.WATCH if bed_data["occupancy_percent"] >= 70.0 else HospitalSystemStatus.STABLE
        matrix.append(
            DepartmentStatusSummary(
                department_id=3,
                department_name="Inpatient Medical Wards",
                department_code="IPD",
                status=ward_status,
                load_level=f"{bed_data['occupancy_percent']}% Occupied",
                active_events_count=len(ward_events),
                key_metrics={
                    "total_beds": bed_data["total_beds"],
                    "occupied_beds": bed_data["occupied_beds"],
                    "available_beds": bed_data["available_beds"],
                },
                recommended_reviews=[
                    "Accelerate morning discharge clearances.",
                    "Coordinate planned elective admissions.",
                ],
            )
        )

        # 4. Outpatient Clinics (OPD)
        opd_events = [e for e in all_events if "Outpatient Clinics" in e.explanation.affected_departments or "OPD" in e.explanation.affected_departments]
        opd_status = HospitalSystemStatus.CRITICAL if opd_data["estimated_wait_minutes"] >= 60 else HospitalSystemStatus.HIGH_LOAD if opd_data["estimated_wait_minutes"] >= 40 else HospitalSystemStatus.WATCH if opd_data["waiting_count"] >= 5 else HospitalSystemStatus.STABLE
        matrix.append(
            DepartmentStatusSummary(
                department_id=4,
                department_name="Outpatient Department (OPD)",
                department_code="OPD",
                status=opd_status,
                load_level=f"{opd_data['estimated_wait_minutes']}m Wait",
                active_events_count=len(opd_events),
                key_metrics={
                    "patients_waiting": opd_data["waiting_count"],
                    "estimated_wait_mins": opd_data["estimated_wait_minutes"],
                    "delay_mins": opd_data["predicted_delay_minutes"],
                },
                recommended_reviews=[
                    "Redistribute tokens to available consultation chambers.",
                    "Monitor consultation durations against baseline SLA.",
                ],
            )
        )

        # 5. Laboratory Diagnostics
        lab_events = [e for e in all_events if "Laboratory" in e.explanation.affected_departments or "LAB" in e.explanation.affected_departments]
        lab_status = HospitalSystemStatus.CRITICAL if lab_data["stat_pending_count"] >= 5 else HospitalSystemStatus.HIGH_LOAD if lab_data["stat_pending_count"] >= 2 else HospitalSystemStatus.WATCH if lab_data["pending_count"] >= 10 else HospitalSystemStatus.STABLE
        matrix.append(
            DepartmentStatusSummary(
                department_id=5,
                department_name="Laboratory Diagnostics",
                department_code="LAB",
                status=lab_status,
                load_level=f"{lab_data['pending_count']} Pending",
                active_events_count=len(lab_events),
                key_metrics={
                    "pending_orders": lab_data["pending_count"],
                    "stat_urgent_orders": lab_data["stat_pending_count"],
                },
                recommended_reviews=[
                    "Prioritize emergency and STAT biochemistry batches.",
                    "Verify analyzer reagent levels.",
                ],
            )
        )

        # 6. Central Pharmacy
        pharm_events = [e for e in all_events if "Pharmacy" in e.explanation.affected_departments]
        pharm_status = HospitalSystemStatus.CRITICAL if pharmacy_data["critical_count"] >= 2 else HospitalSystemStatus.HIGH_LOAD if pharmacy_data["critical_count"] >= 1 else HospitalSystemStatus.WATCH if pharmacy_data["high_count"] >= 3 else HospitalSystemStatus.STABLE
        matrix.append(
            DepartmentStatusSummary(
                department_id=6,
                department_name="Central Hospital Pharmacy",
                department_code="PHARM",
                status=pharm_status,
                load_level=f"{pharmacy_data['critical_count']} Critical Stock",
                active_events_count=len(pharm_events),
                key_metrics={
                    "critical_depletion": pharmacy_data["critical_count"],
                    "reorder_threshold": pharmacy_data["high_count"],
                },
                recommended_reviews=[
                    "Expedite urgent purchase orders for critical antibiotics.",
                    "Prioritize FEFO batch dispensing.",
                ],
            )
        )

        return matrix
