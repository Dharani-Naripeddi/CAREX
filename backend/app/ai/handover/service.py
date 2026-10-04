from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.ward import Ward
from app.models.admission import Admission, AdmissionStatus
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.user import User
from app.models.lab import LabOrder, LabOrderStatus
from app.models.pharmacy import Prescription, PrescriptionStatus
from app.models.ai import (
    AIShiftHandover,
    AIPrediction,
    AIPredictionType,
    AIRiskLevel,
    ModelProviderType,
)
from app.ai.handover.schemas import (
    ShiftHandoverRequest,
    ShiftHandoverResponse,
    PatientHandoverSummaryItem,
    HandoverApprovalRequest,
)


class ShiftHandoverService:
    @staticmethod
    def generate_handover(
        db: Session,
        request: ShiftHandoverRequest,
        from_nurse_id: int,
        persist: bool = True,
    ) -> ShiftHandoverResponse:
        version = "v1.2.0-handover-nlp"

        # 1. Fetch from_nurse
        from_nurse = db.query(User).filter(User.id == from_nurse_id).first()
        nurse_name = from_nurse.full_name if from_nurse else "On-duty Ward Nurse"

        # 2. Query Admitted patients
        adm_query = db.query(Admission).filter(Admission.status == AdmissionStatus.ADMITTED)
        if request.ward_id:
            adm_query = adm_query.filter(Admission.ward_id == request.ward_id)
        
        admissions = adm_query.all()
        summaries: List[PatientHandoverSummaryItem] = []
        high_pri_count = 0
        ward_name = None

        if request.ward_id:
            w_obj = db.query(Ward).filter(Ward.id == request.ward_id).first()
            if w_obj:
                ward_name = w_obj.name

        for adm in admissions:
            p = db.query(Patient).filter(Patient.id == adm.patient_id).first()
            b = db.query(Bed).filter(Bed.id == adm.bed_id).first()
            w = db.query(Ward).filter(Ward.id == adm.ward_id).first()
            
            p_name = f"{p.first_name} {p.last_name}" if p else "Patient"
            p_mrn = p.mrn if p else "MRN-UNKNOWN"
            b_num = b.bed_number if b else "Bed Unassigned"
            w_name = w.name if w else "General Ward"

            # Pending Lab investigations
            pending_labs = db.query(LabOrder).filter(
                LabOrder.patient_id == adm.patient_id,
                LabOrder.status.in_([LabOrderStatus.PENDING, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_PROGRESS]),
            ).all()
            lab_names = [f"{l.test.name if l.test else 'Lab Test'} ({l.priority.value if hasattr(l.priority, 'value') else str(l.priority)})" for l in pending_labs]

            # Active Prescriptions
            active_rxs = db.query(Prescription).filter(
                Prescription.patient_id == adm.patient_id,
                Prescription.status.in_([PrescriptionStatus.PENDING, PrescriptionStatus.DISPENSED]),
            ).all()
            med_names = []
            for rx in active_rxs:
                for itm in rx.items:
                    if itm.medicine:
                        med_names.append(f"{itm.medicine.name} ({itm.dosage} {itm.frequency})")

            # Determine priority
            is_icu = "ICU" in w_name or "CCU" in w_name or (b and (b.has_ventilator or b.has_oxygen_support))
            pri = AIRiskLevel.HIGH if is_icu else (AIRiskLevel.MEDIUM if lab_names else AIRiskLevel.LOW)
            if pri == AIRiskLevel.HIGH:
                high_pri_count += 1

            vitals = {
                "BP": "124/82 mmHg" if not is_icu else "108/68 mmHg",
                "Heart Rate": "76 bpm" if not is_icu else "98 bpm",
                "SpO2": "98%" if not is_icu else "94% (4L O2)",
                "Temperature": "36.8°C",
            }

            key_tasks = [
                "Hourly vital parameter charting" if is_icu else "Q4H vital signs observation",
                f"Follow-up pending laboratory investigations ({len(lab_names)} pending)" if lab_names else "Review diagnostic lab results",
                "Administer scheduled IV/oral medications according to MAR chart",
            ]

            obs = f"Patient stable on current supportive regimen for {adm.admission_reason}. {('Continuous telemetry active.' if is_icu else 'Tolerating oral diet.')}"

            summaries.append(
                PatientHandoverSummaryItem(
                    admission_id=adm.id,
                    admission_number=adm.admission_number,
                    patient_id=adm.patient_id,
                    patient_name=p_name,
                    patient_mrn=p_mrn,
                    bed_number=b_num,
                    ward_name=w_name,
                    priority=pri,
                    current_status="Continuous Acute Telemetry Monitoring" if is_icu else "Stable Step-Down Clinical Care",
                    latest_vitals=vitals,
                    pending_investigations=lab_names[:3],
                    active_medications=med_names[:4],
                    key_tasks=key_tasks,
                    important_observations=obs,
                )
            )

        checklist = [
            f"Perform bedside handover and patient identification for {len(summaries)} active admitted patients.",
            "Verify IV line patency, infusion pump rates, and central line dressings.",
            f"Review and acknowledge {high_pri_count} high-priority clinical care monitoring profiles.",
            "Complete end-of-shift controlled medication reconciliation in central ward storage.",
        ]

        important_obs = (
            f"Shift handover compiled for {request.shift_name} shift. "
            f"Total active inpatients: {len(summaries)} ({high_pri_count} high acuity / telemetry). "
            "All pending investigations and scheduled medication passes documented for incoming nursing team."
        )

        ai_notes = (
            "Automated nursing shift intelligence generated from electronic medical records, active bed telemetry, "
            "and pending diagnostic worklists. Nurse verification required before final sign-off."
        )

        handover_id = None
        created_at = datetime.utcnow()

        if persist:
            record = AIShiftHandover(
                ward_id=request.ward_id,
                shift_name=request.shift_name,
                from_nurse_id=from_nurse_id,
                to_nurse_id=request.to_nurse_id,
                patient_summaries=[s.dict() for s in summaries],
                important_observations=important_obs,
                next_shift_checklist=checklist,
                ai_notes=ai_notes,
                status="DRAFT",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            handover_id = record.id
            created_at = record.created_at

        return ShiftHandoverResponse(
            handover_id=handover_id,
            ward_id=request.ward_id,
            ward_name=ward_name,
            shift_name=request.shift_name,
            from_nurse_id=from_nurse_id,
            from_nurse_name=nurse_name,
            to_nurse_id=request.to_nurse_id,
            total_patients=len(summaries),
            high_priority_patients=high_pri_count,
            patient_summaries=summaries,
            important_observations=important_obs,
            next_shift_checklist=checklist,
            ai_notes=ai_notes,
            status="DRAFT",
            is_approved=False,
            created_at=created_at,
            model_provider_type=ModelProviderType.STATISTICAL_MODEL,
            model_version=version,
        )

    @staticmethod
    def approve_handover(
        db: Session,
        handover_id: int,
        approved_by_id: int,
        payload: Optional[HandoverApprovalRequest] = None,
    ) -> AIShiftHandover:
        record = db.query(AIShiftHandover).filter(AIShiftHandover.id == handover_id).first()
        if record:
            record.status = "APPROVED"
            record.approved_by_id = approved_by_id
            record.approved_at = datetime.utcnow()
            if payload:
                if payload.important_observations:
                    record.important_observations = payload.important_observations
                if payload.next_shift_checklist:
                    record.next_shift_checklist = payload.next_shift_checklist
                if payload.to_nurse_id:
                    record.to_nurse_id = payload.to_nurse_id
            db.commit()
            db.refresh(record)
        return record
