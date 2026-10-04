import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.demo.schemas import (
    DemoScenario,
    DemoScenarioResult,
    DemoResetResponse,
    DemoPipelineProgress,
    DemoPipelineStep,
    PatientJourneyEvent,
    PatientJourneyResponse,
)
from app.demo.scenarios import DEMO_SCENARIOS, SCENARIO_MAP
from app.models.audit_log import AuditLog
from app.models.ai import AIAlert, AIAlertSeverity, AIAlertStatus, AIRiskLevel, AIAlertType
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.opd_token import OpdToken
from app.models.emergency_case import EmergencyCase
from app.models.admission import Admission
from app.models.bed import Bed
from app.models.lab import LabOrder, LabResult
from app.models.pharmacy import Prescription, Dispensing
from app.models.billing import Invoice
from app.models.role import RoleEnum
from app.ai.brain.service import HospitalBrainService
from app.ai.brain.schemas import HospitalSystemStatus


class DemoService:
    _active_scenario_code: str = "STABLE_HOSPITAL"
    _scenario_launched_at: Optional[datetime.datetime] = None

    @classmethod
    def list_scenarios(cls) -> List[DemoScenario]:
        return DEMO_SCENARIOS

    @classmethod
    def get_active_scenario(cls) -> DemoScenario:
        return SCENARIO_MAP.get(cls._active_scenario_code, DEMO_SCENARIOS[0])

    @classmethod
    def launch_scenario(
        cls,
        db: Session,
        scenario_code: str,
        user_id: int,
        user_name: str,
    ) -> DemoScenarioResult:
        scenario = SCENARIO_MAP.get(scenario_code)
        if not scenario:
            scenario = DEMO_SCENARIOS[0]
            scenario_code = scenario.code

        cls._active_scenario_code = scenario_code
        cls._scenario_launched_at = datetime.datetime.now(datetime.timezone.utc)

        # Seed or adjust live scenario alerts deterministically
        if scenario_code == "OPD_OVERLOAD":
            cls._inject_demo_alert(
                db=db,
                alert_id=8801,
                alert_type=AIAlertType.OPD_DELAY,
                severity=AIAlertSeverity.HIGH,
                title="Cardiology & OPD Queue Surge",
                description="Outpatient queue wait time exceeded 50 minutes due to unexpected influx.",
                reasons=["Consultation backlog in Cardiology", "Registration volume up 45%"],
                action="Open overflow consultation room 4B and notify on-call physician",
                related_entity="OPD",
            )
        elif scenario_code == "EMERGENCY_SURGE":
            cls._inject_demo_alert(
                db=db,
                alert_id=8802,
                alert_type=AIAlertType.EMERGENCY_SURGE,
                severity=AIAlertSeverity.CRITICAL,
                title="Acute Emergency & Trauma Inflow Surge",
                description="Multiple Priority Red & Orange trauma arrivals filling resuscitation bays.",
                reasons=["3 acute trauma cases arrived simultaneously", "Resuscitation bays at 100% capacity"],
                action="Activate Code Yellow surge protocol and mobilize emergency reserve team",
                related_entity="EMERGENCY",
            )
        elif scenario_code == "ICU_CAPACITY_PRESSURE":
            cls._inject_demo_alert(
                db=db,
                alert_id=8803,
                alert_type=AIAlertType.BED_CAPACITY_RISK,
                severity=AIAlertSeverity.HIGH,
                title="ICU Saturation & Step-Down Bottleneck",
                description="ICU occupancy reached 92% with only 1 monitored critical bed available.",
                reasons=["High ventilator utilization", "Delayed step-down ward transfers"],
                action="Conduct immediate ICU step-down candidate audit and prepare transit beds",
                related_entity="BED",
            )
        elif scenario_code == "PHARMACY_DEPLETION":
            cls._inject_demo_alert(
                db=db,
                alert_id=8804,
                alert_type=AIAlertType.PHARMACY_DEPLETION,
                severity=AIAlertSeverity.WARNING,
                title="Critical Antibiotic Stock Depletion Risk",
                description="Azithromycin 500mg and Regular Insulin supply dropped below 3-day buffer.",
                reasons=["Accelerated inpatient consumption", "Supplier shipment pending"],
                action="Issue emergency purchase order PO-PHARM-2026-DEMO and restrict off-formulary use",
                related_entity="PHARMACY",
            )
        elif scenario_code == "LAB_BACKLOG":
            cls._inject_demo_alert(
                db=db,
                alert_id=8805,
                alert_type=AIAlertType.LAB_BACKLOG,
                severity=AIAlertSeverity.WARNING,
                title="Diagnostic Laboratory TAT Delay",
                description="28 pending lab orders with 5 STAT orders delaying emergency disposition.",
                reasons=["Hematology analyzer queue congestion", "High emergency order volume"],
                action="Reassign evening technician to STAT bench and expedite critical panels",
                related_entity="LAB",
            )
        elif scenario_code == "HOSPITAL_CAPACITY_CRISIS":
            # Multi-signal simultaneous injection
            cls._inject_demo_alert(
                db=db,
                alert_id=8801,
                alert_type=AIAlertType.OPD_DELAY,
                severity=AIAlertSeverity.HIGH,
                title="OPD Queue Saturation (58 mins)",
                description="Outpatient queue delays compounding with emergency admissions.",
                reasons=["High OPD token volume", "Delayed doctor consultations"],
                action="Open overflow rooms and redirect walk-ins",
                related_entity="OPD",
            )
            cls._inject_demo_alert(
                db=db,
                alert_id=8802,
                alert_type=AIAlertType.EMERGENCY_SURGE,
                severity=AIAlertSeverity.CRITICAL,
                title="Emergency Center Inflow Surge",
                description="Acute emergency arrivals creating bed intake pressure.",
                reasons=["Multiple ambulance arrivals", "Resuscitation bays full"],
                action="Mobilize on-call trauma team",
                related_entity="EMERGENCY",
            )
            cls._inject_demo_alert(
                db=db,
                alert_id=8803,
                alert_type=AIAlertType.BED_CAPACITY_RISK,
                severity=AIAlertSeverity.HIGH,
                title="Inpatient Ward & ICU Saturation (89%)",
                description="Total bed occupancy at 89% with delayed discharge processing.",
                reasons=["ICU at 94%", "Wards nearing ceiling"],
                action="Expedite pending discharges",
                related_entity="BED",
            )

        # Record in AuditLog
        audit = AuditLog(
            user_id=user_id,
            action="DEMO_SCENARIO_LAUNCH",
            entity="DEMO_SCENARIO",
            entity_id=scenario_code,
            details={
                "scenario_title": scenario.title,
                "launched_by": user_name,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
        db.add(audit)
        db.commit()

        # Fetch live events from Hospital Brain
        events = HospitalBrainService.get_events(db)
        overview = HospitalBrainService.get_overview(db)

        return DemoScenarioResult(
            scenario_code=scenario_code,
            title=scenario.title,
            hospital_status=overview.hospital_status,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            telemetry_impact=scenario.target_metrics,
            generated_events=events,
            pipeline_stage=6 if scenario.is_flagship else 4,
            message=f"Demo Scenario '{scenario.title}' executed successfully. CAREX Hospital Brain updated.",
        )

    @classmethod
    def reset_demo(
        cls,
        db: Session,
        user_id: int,
        user_name: str,
    ) -> DemoResetResponse:
        # Clean up any demo-specific injected alerts (IDs 8801-8805)
        db.query(AIAlert).filter(AIAlert.id.between(8801, 8899)).delete()
        db.commit()

        cls._active_scenario_code = "STABLE_HOSPITAL"
        cls._scenario_launched_at = datetime.datetime.now(datetime.timezone.utc)

        # Record reset in AuditLog
        audit = AuditLog(
            user_id=user_id,
            action="DEMO_RESET",
            entity="DEMO_SCENARIO",
            entity_id="RESET",
            details={
                "reset_by": user_name,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
        db.add(audit)
        db.commit()

        overview = HospitalBrainService.get_overview(db)

        return DemoResetResponse(
            status="SUCCESS",
            message="CAREX Demo Mode reset to clean baseline state. All demo signals cleared.",
            reset_timestamp=datetime.datetime.now(datetime.timezone.utc),
            baseline_kpis={
                "hospital_status": overview.hospital_status.value,
                "capacity_percent": overview.kpis.hospital_capacity_percent,
                "available_beds": overview.kpis.available_beds_count,
                "active_events": len(overview.active_events),
            },
        )

    @classmethod
    def get_pipeline_progress(cls) -> DemoPipelineProgress:
        scenario = cls.get_active_scenario()
        code = scenario.code

        is_flagship = (code == "HOSPITAL_CAPACITY_CRISIS")
        is_emergency = (code in ["EMERGENCY_SURGE", "HOSPITAL_CAPACITY_CRISIS"])
        is_beds = (code in ["ICU_CAPACITY_PRESSURE", "HOSPITAL_CAPACITY_CRISIS"])
        is_opd = (code in ["OPD_OVERLOAD", "HOSPITAL_CAPACITY_CRISIS"])

        steps = [
            DemoPipelineStep(
                step_number=1,
                step_name="Emergency Telemetry Ingestion",
                description="Live monitoring of triage intake, Red/Orange acute cases, and resuscitation bay load.",
                is_completed=is_emergency or is_flagship,
                is_active=is_emergency,
                detected_at=cls._scenario_launched_at if (is_emergency or is_flagship) else None,
                contributing_signals=["Emergency arrival velocity", "Triage severity score"],
            ),
            DemoPipelineStep(
                step_number=2,
                step_name="Bed & Ward Capacity Horizon",
                description="Tracking inpatient ward occupancy, ICU saturation, and projected 24-hour bed turnover.",
                is_completed=is_beds or is_flagship,
                is_active=is_beds,
                detected_at=cls._scenario_launched_at if (is_beds or is_flagship) else None,
                contributing_signals=["ICU occupancy index", "Bed transfer bottlenecks"],
            ),
            DemoPipelineStep(
                step_number=3,
                step_name="Outpatient Queue Delays",
                description="Evaluating token wait times and consultation delays across outpatient departments.",
                is_completed=is_opd or is_flagship,
                is_active=is_opd,
                detected_at=cls._scenario_launched_at if (is_opd or is_flagship) else None,
                contributing_signals=["OPD wait time > 45m", "Token queue backlog"],
            ),
            DemoPipelineStep(
                step_number=4,
                step_name="Cross-Module Signal Correlation",
                description="Correlating simultaneous multi-department signals across ER, Wards, and OPD.",
                is_completed=is_flagship,
                is_active=is_flagship,
                detected_at=cls._scenario_launched_at if is_flagship else None,
                contributing_signals=["Cross-domain pattern matcher", "Priority Scorer 0-100"],
            ),
            DemoPipelineStep(
                step_number=5,
                step_name="Hospital Capacity Risk Generation",
                description="Generating composite HOSPITAL_CAPACITY_RISK alert with explainable factor breakdown.",
                is_completed=is_flagship,
                is_active=is_flagship,
                detected_at=cls._scenario_launched_at if is_flagship else None,
                contributing_signals=["Operational Priority Score = 88/100", "Institutional gridlock risk"],
            ),
            DemoPipelineStep(
                step_number=6,
                step_name="Operational Review Playbook",
                description="Recommending proactive hospital coordination actions for clinical leadership.",
                is_completed=is_flagship,
                is_active=is_flagship,
                detected_at=cls._scenario_launched_at if is_flagship else None,
                contributing_signals=["Expedite stable discharges", "Open overflow consultation rooms"],
            ),
        ]

        summary_rec = (
            "Multiple operational indicators elevated. Conduct coordinated cross-department review."
            if is_flagship
            else f"Scenario '{scenario.title}' active. Monitoring departmental telemetry."
        )

        return DemoPipelineProgress(
            active_scenario_code=scenario.code,
            active_scenario_title=scenario.title,
            hospital_status=HospitalSystemStatus.CRITICAL if is_flagship else HospitalSystemStatus.WATCH,
            steps=steps,
            summary_recommendation=summary_rec,
        )

    @classmethod
    def get_patient_journey(
        cls,
        db: Session,
        patient_id: int,
        role: Optional[RoleEnum] = None,
    ) -> Optional[PatientJourneyResponse]:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            # Fallback to first patient if patient_id not found
            patient = db.query(Patient).first()
            if not patient:
                return None

        stages: List[PatientJourneyEvent] = []
        stage_idx = 1

        # 1. Registration
        stages.append(
            PatientJourneyEvent(
                stage_id=stage_idx,
                stage_name="Patient Registration",
                timestamp=patient.created_at.strftime("%Y-%m-%d %H:%M") if patient.created_at else "2026-09-01 08:30",
                department="Front Desk / Registration",
                responsible_role="RECEPTIONIST",
                status="COMPLETED",
                summary=f"Registered in Master Patient Index (MRN: {patient.mrn})",
                details={
                    "MRN": patient.mrn,
                    "Name": patient.full_name,
                    "Gender": patient.gender,
                    "Blood Group": patient.blood_group or "O+",
                },
                ai_insight="Demographics validated against National Registry format",
            )
        )
        stage_idx += 1

        # 2. Appointments
        appointments = db.query(Appointment).filter(Appointment.patient_id == patient.id).all()
        for appt in appointments:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Appointment Scheduled",
                    timestamp=appt.appointment_date.strftime("%Y-%m-%d %H:%M") if appt.appointment_date else "2026-09-01 09:00",
                    department=appt.department.name if appt.department else "Outpatient Clinic",
                    responsible_role="DOCTOR",
                    status=appt.status.value if hasattr(appt.status, "value") else str(appt.status),
                    summary=f"Consultation scheduled with Dr. {appt.doctor.full_name if appt.doctor else 'Specialist'}",
                    details={
                        "Reason": appt.chief_complaint or appt.notes or "General Consultation",
                        "Type": appt.type.value if hasattr(appt.type, "value") else str(appt.type),
                    },
                    ai_insight="Slot optimized based on historical doctor consultation pacing",
                )
            )
            stage_idx += 1

        # 3. OPD Token Queue
        tokens = db.query(OpdToken).filter(OpdToken.patient_id == patient.id).all()
        for token in tokens:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="OPD Token Queue",
                    timestamp=token.created_at.strftime("%Y-%m-%d %H:%M") if token.created_at else "2026-09-01 09:15",
                    department=token.department.name if token.department else "OPD",
                    responsible_role="RECEPTIONIST",
                    status=token.status.value if hasattr(token.status, "value") else str(token.status),
                    summary=f"Token #{token.token_number} issued for Room {token.doctor_id or 1}",
                    details={
                        "Token Code": token.token_code,
                        "Estimated Wait": f"{token.estimated_wait_minutes or 20} mins",
                    },
                    ai_insight=f"Predicted consultation wait: {token.estimated_wait_minutes or 20} min (ML Queue Forecast)",
                )
            )
            stage_idx += 1

        # 4. Emergency Case (if any)
        emergencies = db.query(EmergencyCase).filter(EmergencyCase.patient_id == patient.id).all()
        for em in emergencies:
            triage_val = em.triage_level.value if hasattr(em.triage_level, "value") else str(em.triage_level)
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Emergency Triage Intake",
                    timestamp=em.arrival_time.strftime("%Y-%m-%d %H:%M") if em.arrival_time else "2026-09-01 10:00",
                    department="Emergency & Trauma Center",
                    responsible_role="TRIAGE_NURSE",
                    status=em.status.value if hasattr(em.status, "value") else str(em.status),
                    summary=f"Triage Level {triage_val} — Case #{em.case_number}",
                    details={
                        "Symptoms": em.symptoms,
                        "Heart Rate": f"{em.heart_rate} bpm" if em.heart_rate else "N/A",
                        "BP": f"{em.bp_systolic}/{em.bp_diastolic} mmHg" if em.bp_systolic else "N/A",
                        "SpO2": f"{em.spo2}%" if em.spo2 else "N/A",
                    },
                    ai_insight=f"Triage Decision Support: Classified as Priority {triage_val} based on vital thresholds",
                    is_clinical_alert=(triage_val in ["RED", "ORANGE"]),
                )
            )
            stage_idx += 1

        # 5. Diagnostic Laboratory Orders
        lab_orders = db.query(LabOrder).filter(LabOrder.patient_id == patient.id).all()
        for order in lab_orders:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Laboratory Diagnostic Order",
                    timestamp=order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "2026-09-01 10:30",
                    department="Central Diagnostic Laboratory",
                    responsible_role="LAB_TECHNICIAN",
                    status=order.status.value if hasattr(order.status, "value") else str(order.status),
                    summary=f"Lab Order #{order.order_number} ({order.priority.value if hasattr(order.priority, 'value') else order.priority})",
                    details={
                        "Order Number": order.order_number,
                        "Tests Count": len(order.test_items) if hasattr(order, "test_items") and order.test_items else 2,
                    },
                    ai_insight="Document AI: Test parameters automatically structured from clinical order",
                )
            )
            stage_idx += 1

        # 6. Prescriptions & Pharmacy
        prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient.id).all()
        for rx in prescriptions:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Electronic Prescription & Pharmacy",
                    timestamp=rx.created_at.strftime("%Y-%m-%d %H:%M") if rx.created_at else "2026-09-01 11:15",
                    department="Hospital Pharmacy",
                    responsible_role="PHARMACIST",
                    status=rx.status.value if hasattr(rx.status, "value") else str(rx.status),
                    summary=f"Prescription #{rx.prescription_number} issued by Dr. {rx.doctor.full_name if rx.doctor else 'Consultant'}",
                    details={
                        "Prescription Number": rx.prescription_number,
                        "Items": len(rx.items) if hasattr(rx, "items") and rx.items else 2,
                    },
                    ai_insight="Pharmacy AI: Automated formulary and drug-interaction safety check completed",
                )
            )
            stage_idx += 1

        # 7. Inpatient Admission (if any)
        admissions = db.query(Admission).filter(Admission.patient_id == patient.id).all()
        for adm in admissions:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Inpatient (IPD) Admission & Bed Allocation",
                    timestamp=adm.admission_date.strftime("%Y-%m-%d %H:%M") if adm.admission_date else "2026-09-01 12:00",
                    department=adm.ward.name if adm.ward else "Inpatient Ward",
                    responsible_role="NURSE",
                    status=adm.status.value if hasattr(adm.status, "value") else str(adm.status),
                    summary=f"Admitted to {adm.ward.name if adm.ward else 'General Ward'} - Bed #{adm.bed.bed_number if adm.bed else 'B-101'}",
                    details={
                        "Admission Number": adm.admission_number,
                        "Diagnosis": adm.admission_reason or "Clinical Observation",
                    },
                    ai_insight="Bed Capacity AI: Bed allocated via automated turnover projection",
                )
            )
            stage_idx += 1

        # 8. Billing & Invoices
        invoices = db.query(Invoice).filter(Invoice.patient_id == patient.id).all()
        for inv in invoices:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Billing & Settlement",
                    timestamp=inv.created_at.strftime("%Y-%m-%d %H:%M") if inv.created_at else "2026-09-01 14:00",
                    department="Billing & Revenue Cycle",
                    responsible_role="BILLING_OFFICER",
                    status=inv.payment_status.value if hasattr(inv.payment_status, "value") else str(inv.payment_status),
                    summary=f"Invoice #{inv.invoice_number} (₹{inv.total_amount:.2f})",
                    details={
                        "Total Amount": f"₹{inv.total_amount:.2f}",
                        "Payment Status": inv.payment_status.value if hasattr(inv.payment_status, "value") else str(inv.payment_status),
                    },
                    ai_insight="Revenue AI: Line-item audit completed with zero tariff discrepancy",
                )
            )
            stage_idx += 1

        # Fallback simulated stages if clean new patient
        if len(stages) <= 2:
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Doctor Consultation",
                    timestamp="2026-09-01 10:15",
                    department="Cardiology Clinic",
                    responsible_role="DOCTOR",
                    status="COMPLETED",
                    summary="Consultation with Dr. Sharma (Vitals & ECG review)",
                    details={"Diagnosis": "Mild Hypertension & Sinus Tachycardia"},
                    ai_insight="Voice-to-Clinical-Note assisted physician documentation",
                )
            )
            stage_idx += 1
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Laboratory Investigation",
                    timestamp="2026-09-01 11:00",
                    department="Central Lab",
                    responsible_role="LAB_TECHNICIAN",
                    status="RELEASED",
                    summary="Complete Blood Count (CBC) & Lipid Profile",
                    details={"Status": "Verified by Pathologist"},
                    ai_insight="Automated Critical Flag Analyzer: All parameters within normal ranges",
                )
            )
            stage_idx += 1
            stages.append(
                PatientJourneyEvent(
                    stage_id=stage_idx,
                    stage_name="Pharmacy Dispensation",
                    timestamp="2026-09-01 11:45",
                    department="Outpatient Pharmacy",
                    responsible_role="PHARMACIST",
                    status="DISPENSED",
                    summary="Amlodipine 5mg & Metoprolol 25mg dispensed",
                    details={"Refills": "1 Remaining"},
                    ai_insight="Pharmacy Inventory: Batch expiry verified > 18 months",
                )
            )
            stage_idx += 1

        adm_status = "ADMITTED" if any("Admission" in s.stage_name for s in stages) else "OUTPATIENT_DISCHARGED"

        return PatientJourneyResponse(
            patient_id=patient.id,
            mrn=patient.mrn,
            patient_name=patient.full_name,
            age=patient.age,
            gender=patient.gender,
            blood_group=patient.blood_group or "O+",
            allergies=patient.allergies or ["None Known"],
            current_medications=patient.current_medications or [],
            admission_status=adm_status,
            events_count=len(stages),
            journey_stages=stages,
        )

    # -------------------------------------------------------------------------
    # Internal Helper
    # -------------------------------------------------------------------------
    @classmethod
    def _inject_demo_alert(
        cls,
        db: Session,
        alert_id: int,
        alert_type: str,
        severity: AIAlertSeverity,
        title: str,
        description: str,
        reasons: List[str],
        action: str,
        related_entity: str,
    ):
        existing = db.query(AIAlert).filter(AIAlert.id == alert_id).first()
        if existing:
            existing.alert_type = alert_type
            existing.severity = severity
            existing.title = title
            existing.description = description
            existing.reason = reasons
            existing.recommended_action = action
            existing.related_entity = related_entity
            existing.status = AIAlertStatus.ACTIVE
            existing.created_at = datetime.datetime.now(datetime.timezone.utc)
        else:
            alert = AIAlert(
                id=alert_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                reason=reasons,
                recommended_action=action,
                related_entity=related_entity,
                status=AIAlertStatus.ACTIVE,
            )
            db.add(alert)
        db.commit()
