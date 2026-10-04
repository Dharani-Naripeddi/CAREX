import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from fastapi import HTTPException, status
from app.models.emergency_case import EmergencyCase, TriageLevel, EmergencyCaseStatus
from app.models.patient import Patient
from app.models.user import User
from app.schemas.emergency import EmergencyCaseCreate, EmergencyCaseUpdate, EmergencyCaseResponse
from app.services.triage_service import TriageService
from app.services.audit_service import AuditService


class EmergencyService:
    @staticmethod
    def generate_case_number(db: Session) -> str:
        """Generate unique sequential emergency case number format: EMR-YYYY-XXXX."""
        current_year = datetime.date.today().year
        prefix = f"EMR-{current_year}-"

        latest = (
            db.query(EmergencyCase)
            .filter(EmergencyCase.case_number.like(f"{prefix}%"))
            .order_by(desc(EmergencyCase.id))
            .first()
        )

        if latest and latest.case_number.startswith(prefix):
            try:
                seq = int(latest.case_number.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    @staticmethod
    def create_case(
        db: Session,
        case_in: EmergencyCaseCreate,
        created_by_id: Optional[int] = None,
    ) -> EmergencyCase:
        """Register emergency case and compute rule-based triage decision support."""
        case_number = EmergencyService.generate_case_number(db)
        arrival_time = case_in.arrival_time or datetime.datetime.now(datetime.timezone.utc)

        # Execute transparent rule-based triage engine
        triage_eval = TriageService.evaluate_triage(
            heart_rate=case_in.heart_rate,
            bp_systolic=case_in.bp_systolic,
            bp_diastolic=case_in.bp_diastolic,
            spo2=case_in.spo2,
            temperature=case_in.temperature,
            respiratory_rate=case_in.respiratory_rate,
            consciousness=case_in.consciousness,
            injury_type=case_in.injury_type or "",
            symptoms=case_in.symptoms,
        )

        # If patient_id passed, populate name if empty
        patient_name = case_in.patient_name
        age = case_in.age
        gender = case_in.gender

        if case_in.patient_id:
            p = db.query(Patient).filter(Patient.id == case_in.patient_id).first()
            if p:
                patient_name = p.full_name
                age = p.age
                gender = p.gender

        emr_case = EmergencyCase(
            case_number=case_number,
            patient_id=case_in.patient_id,
            patient_name=patient_name,
            age=age,
            gender=gender,
            arrival_time=arrival_time,
            symptoms=case_in.symptoms,
            injury_type=case_in.injury_type,
            heart_rate=case_in.heart_rate,
            bp_systolic=case_in.bp_systolic,
            bp_diastolic=case_in.bp_diastolic,
            spo2=case_in.spo2,
            temperature=case_in.temperature,
            respiratory_rate=case_in.respiratory_rate,
            consciousness=case_in.consciousness,
            triage_level=triage_eval.triage_level,
            contributing_factors=triage_eval.contributing_factors,
            recommended_action=triage_eval.recommended_action,
            status=EmergencyCaseStatus.TRIAGED,
            doctor_id=case_in.doctor_id,
            nurse_id=case_in.nurse_id,
        )

        db.add(emr_case)
        db.commit()
        db.refresh(emr_case)

        AuditService.log(
            db=db,
            action="EMERGENCY_CASE_REGISTERED",
            entity="EMERGENCY_CASE",
            entity_id=str(emr_case.id),
            user_id=created_by_id,
            details={
                "case_number": emr_case.case_number,
                "triage_level": emr_case.triage_level.value,
                "patient_name": emr_case.patient_name,
            },
        )

        return emr_case

    @staticmethod
    def get_cases(
        db: Session,
        status: Optional[EmergencyCaseStatus] = None,
        triage_level: Optional[TriageLevel] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EmergencyCaseResponse]:
        """Fetch list of emergency cases with triage priorities."""
        query = (
            db.query(EmergencyCase)
            .options(
                joinedload(EmergencyCase.doctor),
                joinedload(EmergencyCase.nurse),
            )
        )

        if status:
            query = query.filter(EmergencyCase.status == status)

        if triage_level:
            query = query.filter(EmergencyCase.triage_level == triage_level)

        cases = (
            query.order_by(
                # Priority order: RED first, then ORANGE, YELLOW, GREEN, then arrival time
                EmergencyCase.triage_level.asc(),
                EmergencyCase.arrival_time.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        results = []
        for c in cases:
            results.append(
                EmergencyCaseResponse(
                    id=c.id,
                    case_number=c.case_number,
                    patient_id=c.patient_id,
                    patient_name=c.patient_name,
                    age=c.age,
                    gender=c.gender,
                    arrival_time=c.arrival_time,
                    symptoms=c.symptoms,
                    injury_type=c.injury_type,
                    heart_rate=c.heart_rate,
                    bp_systolic=c.bp_systolic,
                    bp_diastolic=c.bp_diastolic,
                    spo2=c.spo2,
                    temperature=c.temperature,
                    respiratory_rate=c.respiratory_rate,
                    consciousness=c.consciousness,
                    triage_level=c.triage_level,
                    contributing_factors=c.contributing_factors or [],
                    recommended_action=c.recommended_action,
                    triage_notes=c.triage_notes,
                    status=c.status,
                    doctor_id=c.doctor_id,
                    nurse_id=c.nurse_id,
                    doctor_name=c.doctor.full_name if c.doctor else None,
                    nurse_name=c.nurse.full_name if c.nurse else None,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )
        return results

    @staticmethod
    def get_case_by_id(db: Session, case_id: int) -> Optional[EmergencyCase]:
        """Fetch emergency case by ID."""
        return (
            db.query(EmergencyCase)
            .options(
                joinedload(EmergencyCase.doctor),
                joinedload(EmergencyCase.nurse),
                joinedload(EmergencyCase.patient),
            )
            .filter(EmergencyCase.id == case_id)
            .first()
        )

    @staticmethod
    def update_case(
        db: Session,
        case_id: int,
        case_in: EmergencyCaseUpdate,
        updated_by_id: Optional[int] = None,
    ) -> EmergencyCase:
        """Update vitals or triage status and re-run triage support if vitals altered."""
        emr_case = EmergencyService.get_case_by_id(db, case_id)
        if not emr_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency case with ID {case_id} not found.",
            )

        update_dict = case_in.model_dump(exclude_unset=True)
        vitals_changed = any(
            k in update_dict
            for k in ["heart_rate", "bp_systolic", "bp_diastolic", "spo2", "temperature", "respiratory_rate", "consciousness", "symptoms", "injury_type"]
        )

        for k, v in update_dict.items():
            setattr(emr_case, k, v)

        if vitals_changed:
            triage_eval = TriageService.evaluate_triage(
                heart_rate=emr_case.heart_rate,
                bp_systolic=emr_case.bp_systolic,
                bp_diastolic=emr_case.bp_diastolic,
                spo2=emr_case.spo2,
                temperature=emr_case.temperature,
                respiratory_rate=emr_case.respiratory_rate,
                consciousness=emr_case.consciousness,
                injury_type=emr_case.injury_type or "",
                symptoms=emr_case.symptoms,
            )
            emr_case.triage_level = triage_eval.triage_level
            emr_case.contributing_factors = triage_eval.contributing_factors
            emr_case.recommended_action = triage_eval.recommended_action

        db.commit()
        db.refresh(emr_case)

        AuditService.log(
            db=db,
            action="EMERGENCY_CASE_UPDATED",
            entity="EMERGENCY_CASE",
            entity_id=str(emr_case.id),
            user_id=updated_by_id,
            details=update_dict,
        )

        return emr_case
